"""
Full-Fledged IoT Air Quality Monitoring Application Server
Features: Database, User Auth, Historical Data, Alerts, Reports, Device Management
Production-Ready: Logging, Rate Limiting, Error Handling, Backups, Validation
"""

from flask import Flask, request, jsonify, send_file, session, render_template_string, send_from_directory
from flask_cors import CORS
from flask_session import Session
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
import json
import io
from functools import wraps

# Import database models
from database import db, Device, Reading, Alert, User, Settings, Notification, OTPCode, PasswordResetToken, UserSession

# Import new services
from mobile_notification import MobileNotificationService
from enhanced_auth import EnhancedAuthenticationService
from forecasting import forecaster

# Import production utilities
from logging_config import setup_logger, log_api_call, log_audit, log_error_with_context
from backup_manager import DatabaseBackup, auto_backup_scheduler
from validation import validate_json, validate_sensor_data, validate_username, validate_password, validate_mobile_number
from rate_limiter import rate_limit, rate_limit_moderate, rate_limit_strict, rate_limiter
from scheduled_tasks import ScheduledTasks, run_manual_cleanup

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
app.config['SECRET_KEY'] = 'iot-ml-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{PROJECT_ROOT}/data/database/iot_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize extensions
db.init_app(app)
Session(app)

# Initialize logger
logger = setup_logger('iot_aqi', level=20)  # INFO level

# Initialize backup manager
db_path = PROJECT_ROOT / 'data' / 'database' / 'iot_data.db'
backup_manager = DatabaseBackup(db_path, max_backups=30)

# Model paths
MODEL_PATH = PROJECT_ROOT / 'models' / 'air_quality_model_advanced.joblib'
SCALER_PATH = PROJECT_ROOT / 'models' / 'scaler.joblib'
FEATURE_NAMES_PATH = PROJECT_ROOT / 'models' / 'feature_names.joblib'
METADATA_PATH = PROJECT_ROOT / 'models' / 'model_metadata_advanced.json'

# Global state
reading_buffer = deque(maxlen=30)
model = None
scaler = None
feature_names = []
metadata = {}
TEMP_MEAN = 25.0
HUM_MEAN = 50.0
MQ_MEAN = 200.0
TEMP_STD = 5.0
HUM_STD = 15.0
MQ_STD = 50.0
START_TIME = datetime.utcnow()  # Track actual server start time

# Initialize mobile notification service (configure via settings)
mobile_notification = MobileNotificationService()
auth_service = EnhancedAuthenticationService(mobile_notification)

# Initialize scheduled tasks (will be started after app initialization)
scheduled_tasks = None

# ==================== INITIALIZATION ====================

def load_ml_model():
    """Load ML model and related files"""
    global model, scaler, feature_names, metadata
    global TEMP_MEAN, HUM_MEAN, MQ_MEAN, TEMP_STD, HUM_STD, MQ_STD
    
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        feature_names = joblib.load(FEATURE_NAMES_PATH) if FEATURE_NAMES_PATH.exists() else []
        
        if METADATA_PATH.exists():
            with open(METADATA_PATH, 'r') as f:
                metadata = json.load(f)
            
            # Extract baselines for feature engineering
            baselines = metadata.get('baseline_values', {})
            TEMP_MEAN = baselines.get('temp_mean', 25.0)
            HUM_MEAN = baselines.get('hum_mean', 50.0)
            MQ_MEAN = baselines.get('mq_mean', 200.0)
            TEMP_STD = baselines.get('temp_std', 5.0)
            HUM_STD = baselines.get('hum_std', 15.0)
            MQ_STD = baselines.get('mq_std', 50.0)
            print(f"✓ Baselines loaded: T={TEMP_MEAN:.1f}, H={HUM_MEAN:.1f}, MQ={MQ_MEAN:.1f}")
        
        print("✓ ML Model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Error loading ML model: {str(e)}")
        return False


def initialize_database():
    """Initialize database with default settings"""
    with app.app_context():
        db.create_all()
        
        # Create default device if none exists
        if Device.query.count() == 0:
            default_device = Device(
                device_id='ESP32_001',
                device_name='Main Air Quality Monitor',
                location='Office',
                status='active'
            )
            db.session.add(default_device)
            print("✓ Created default device")
        
        # Create default admin user if none exists
        if User.query.count() == 0:
            admin = User(
                username='admin',
                mobile_number='+11234567890',  # Change in production!
                email='admin@iot.local',
                full_name='System Administrator',
                role='admin',
                is_active=True,
                mobile_verified=True,  # Skip verification for default admin
                notification_preference='sms'
            )
            admin.set_password('admin123')  # Change in production!
            db.session.add(admin)
            print("✓ Created default admin user (username: admin, mobile: +11234567890, password: admin123)")
        
        # Initialize default settings (matches ESP32 buzzer thresholds)
        default_settings = [
            ('alert_threshold_unhealthy', '151', 'int', 'AQI threshold for unhealthy alerts (matches ESP32 buzzer)'),
            ('alert_threshold_dangerous', '201', 'int', 'AQI threshold for dangerous alerts'),
            ('alert_cooldown_minutes', '5', 'int', 'Minutes between similar alerts'),
            ('data_retention_days', '30', 'int', 'Days to keep historical data'),
            ('enable_mobile_alerts', 'false', 'bool', 'Enable mobile notifications (SMS/WhatsApp)'),
            ('enable_buzzer_alerts', 'true', 'bool', 'Enable ESP32 buzzer alerts'),
            ('reading_interval_seconds', '10', 'int', 'Seconds between ESP32 readings'),
            ('anomaly_sensitivity', 'medium', 'string', 'Anomaly detection sensitivity (low/medium/high)'),
            ('admin_mobile_number', '', 'string', 'Admin mobile number for notifications (E.164 format)'),
            ('notification_type', 'sms', 'string', 'Notification type (sms, whatsapp, both)'),
            ('twilio_account_sid', '', 'string', 'Twilio Account SID'),
            ('twilio_auth_token', '', 'string', 'Twilio Auth Token'),
            ('twilio_phone_number', '', 'string', 'Twilio phone number (E.164 format)'),
            ('twilio_whatsapp_number', '', 'string', 'Twilio WhatsApp number'),
        ]
        
        for key, value, value_type, description in default_settings:
            if not Settings.query.filter_by(key=key).first():
                setting = Settings(key=key, value=value, value_type=value_type, description=description)
                db.session.add(setting)
        
        db.session.commit()
        print("✓ Database initialized successfully")
        
        # Initialize scheduled tasks
        global scheduled_tasks
        scheduled_tasks = ScheduledTasks(db, backup_manager, logger)
        scheduled_tasks.start()
        logger.info("Scheduled tasks started successfully")
        print("✓ Scheduled tasks started (backups, cleanup, vacuum)")


# ==================== DECORATORS ====================

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


# ==================== ERROR HANDLERS ====================

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    logger.warning(f"Bad Request: {error}")
    return jsonify({
        'error': 'Bad Request',
        'message': str(error)
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized errors"""
    logger.warning(f"Unauthorized access attempt: {request.remote_addr}")
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication required'
    }), 401

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors"""
    logger.warning(f"Forbidden access: {session.get('username', 'unknown')}")
    return jsonify({
        'error': 'Forbidden',
        'message': 'Insufficient permissions'
    }), 403

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'Resource not found'
    }),404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle 429 Too Many Requests errors"""
    logger.warning(f"Rate limit exceeded: {request.remote_addr}")
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    logger.error(f"Internal error: {error}", exc_info=True)
    db.session.rollback()
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions"""
    log_error_with_context(logger, error, {
        'endpoint': request.endpoint,
        'method': request.method,
        'ip': request.remote_addr
    })
    db.session.rollback()
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


# ==================== HELPER FUNCTIONS ====================

def engineer_features(temp, humidity, mq135):
    """Engineer features for ML model - uses baselines from metadata"""
    
    # Calculate deviations
    temp_dev = temp - TEMP_MEAN
    humidity_dev = humidity - HUM_MEAN
    mq135_dev = mq135 - MQ_MEAN
    
    # Calculate z-scores
    temp_z = (temp - TEMP_MEAN) / (TEMP_STD + 1e-6)
    humidity_z = (humidity - HUM_MEAN) / (HUM_STD + 1e-6)
    mq135_z = (mq135 - MQ_MEAN) / (MQ_STD + 1e-6)
    
    # Calculate normalized values (0-1 range)
    temp_norm = (temp - 0) / (50 + 1e-10)  # 0-50°C range
    humidity_norm = humidity / (100 + 1e-10)  # 0-100% range
    
    # Discomfort Index: DI = T - 0.55(1 - RH/100)(T - 58)
    discomfort = temp - 0.55 * (1 - humidity/100) * (temp - 14.4)
    
    # Heat Index (simplified): HI = c1 + c2*T + c3*RH + c4*T*RH
    heat_idx = -8.78 + 1.61*temp + 2.34*humidity + (-0.15)*temp*humidity
    
    # Feature dictionary with EXACT column names from training data
    features = {
        'temperature_c': temp,
        'humidity_rh': humidity,
        'mq135_proxy': mq135,
        'temp_x_humidity': temp * humidity,
        'temp_x_mq135': temp * mq135,
        'humidity_x_mq135': humidity * mq135,
        'temp_x_hum_x_mq': temp * humidity * mq135,
        'temp_squared': temp ** 2,
        'humidity_squared': humidity ** 2,
        'mq135_squared': mq135 ** 2,
        'temp_to_humidity_ratio': temp / (humidity + 1e-10),
        'mq135_to_temp_ratio': mq135 / (temp + 1e-10),
        'mq135_to_humidity_ratio': mq135 / (humidity + 1e-10),
        'temp_deviation': temp_dev,
        'humidity_deviation': humidity_dev,
        'mq135_deviation': mq135_dev,
        'temp_zscore': temp_z,
        'humidity_zscore': humidity_z,
        'mq135_zscore': mq135_z,
        'discomfort_index': discomfort,
        'heat_index': heat_idx,
        'temp_normalized': temp_norm,
        'humidity_normalized': humidity_norm
    }
    return pd.DataFrame([features])


def get_aqi_category(aqi):
    """Get AQI category and color"""
    if aqi <= 50:
        return 'Good', 'success', '#00e400'
    elif aqi <= 100:
        return 'Moderate', 'info', '#ffff00'
    elif aqi <= 150:
        return 'Unhealthy for Sensitive Groups', 'warning', '#ff7e00'
    elif aqi <= 200:
        return 'Unhealthy', 'warning', '#ff0000'
    elif aqi <= 300:
        return 'Very Unhealthy', 'danger', '#8f3f97'
    else:
        return 'Hazardous', 'danger', '#7e0023'


def analyze_trend():
    """Analyze trend from buffer"""
    if len(reading_buffer) < 5:
        return {'available': False}
    
    aqi_values = [r['aqi'] for r in list(reading_buffer)[-10:]]
    x = np.arange(len(aqi_values))
    slope, _ = np.polyfit(x, aqi_values, 1)
    volatility = np.std(aqi_values)
    
    if slope > 1:
        trend = 'Worsening'
    elif slope < -1:
        trend = 'Improving'
    else:
        trend = 'Stable'
    
    return {
        'available': True,
        'trend': trend,
        'slope': round(slope, 2),
        'volatility': round(volatility, 2),
        'buffer_size': len(reading_buffer)
    }


def detect_anomaly(current_aqi):
    """Detect anomalies in readings"""
    if len(reading_buffer) < 10:
        return {'detected': False, 'details': []}
    
    recent_readings = list(reading_buffer)[-10:]
    aqi_values = [r['aqi'] for r in recent_readings]
    mean_aqi = np.mean(aqi_values)
    std_aqi = np.std(aqi_values)
    
    anomalies = []
    
    # Z-score anomaly
    if std_aqi > 0:
        z_score = abs((current_aqi - mean_aqi) / std_aqi)
        if z_score > 2.5:
            anomalies.append(('aqi_spike', f'Unusual AQI spike detected (Z-score: {z_score:.2f})'))
    
    # Sudden change
    if len(recent_readings) >= 2:
        prev_aqi = recent_readings[-1]['aqi']
        change = abs(current_aqi - prev_aqi)
        if change > 30:
            anomalies.append(('sudden_change', f'Rapid AQI change: {change:.1f} points'))
    
    return {
        'detected': len(anomalies) > 0,
        'details': anomalies,
        'mean_aqi': round(mean_aqi, 2),
        'std_aqi': round(std_aqi, 2)
    }


def check_alert_needed(aqi, device_id):
    """Check if alert should be triggered - matches ESP32 buzzer thresholds"""
    settings_map = {s.key: s.get_typed_value() for s in Settings.query.all()}
    
    # Match ESP32 buzzer thresholds: 151 (Unhealthy), 201 (Very Unhealthy)
    threshold_unhealthy = settings_map.get('alert_threshold_unhealthy', 151)  # Changed from 101 to 151
    threshold_dangerous = settings_map.get('alert_threshold_dangerous', 201)  # Changed from 151 to 201
    cooldown_minutes = settings_map.get('alert_cooldown_minutes', 15)
    
    if aqi < threshold_unhealthy:
        return None
    
    # Check cooldown
    recent_alert = Alert.query.filter_by(device_id=device_id)\
        .filter(Alert.timestamp > datetime.utcnow() - timedelta(minutes=cooldown_minutes))\
        .first()
    
    if recent_alert:
        return None
    
    # Determine alert level
    if aqi >= threshold_dangerous:
        level = 'danger'
        message = f'DANGEROUS air quality detected! AQI: {aqi:.1f}'
        action = 'Evacuate area immediately. Use air purifiers and masks.'
    else:
        level = 'warning'
        message = f'UNHEALTHY air quality detected! AQI: {aqi:.1f}'
        action = 'Limit outdoor activities. Close windows and use air purifiers.'
    
    return {
        'level': level,
        'type': 'aqi_threshold',
        'message': message,
        'action': action,
        'aqi': aqi
    }


# ==================== AUTHENTICATION ENDPOINTS ====================

@app.route('/api/auth/register', methods=['POST'])
@rate_limit_strict
@validate_json(required_fields=['username', 'password', 'email', 'full_name'])
def register():
    """User registration with email (mobile optional - added later for alerts)"""
    data = request.get_json()
    
    # Validate username
    is_valid, error = validate_username(data['username'])
    if not is_valid:
        return jsonify({'error': error}), 400
    
    # Validate email
    if not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    # Validate password
    is_valid, error = validate_password(data['password'])
    if not is_valid:
        return jsonify({'error': error}), 400
    
    # Register user (simple registration without mobile)
    result = auth_service.register_user_simple(
        username=data['username'],
        password=data['password'],
        email=data['email'],
        full_name=data['full_name'],
        terms_accepted=data.get('terms_accepted', False),
        privacy_accepted=data.get('privacy_accepted', False),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    if result['success']:
        log_audit(logger, 'user_registered', data['username'], f'IP: {request.remote_addr}')
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@app.route('/api/auth/verify-mobile', methods=['POST'])
@rate_limit_moderate
@validate_json(required_fields=['user_id', 'otp_code'])
def verify_mobile():
    """Verify mobile number with OTP"""
    data = request.get_json()
    
    result = auth_service.verify_mobile(
        user_id=data['user_id'],
        otp_code=data['otp_code']
    )
    
    if result['success']:
        log_audit(logger, 'mobile_verified', f"User ID: {data['user_id']}", f'IP: {request.remote_addr}')
    
    return jsonify(result), 200 if result['success'] else 400


@app.route('/api/auth/resend-otp', methods=['POST'])
@rate_limit_moderate
@validate_json(required_fields=['user_id'])
def resend_otp():
    """Resend OTP for mobile verification"""
    data = request.get_json()
    
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    result = auth_service.send_verification_otp(user.id, user.mobile_number)
    return jsonify(result), 200 if result['success'] else 400


@app.route('/api/auth/login', methods=['POST'])
@rate_limit_strict
@validate_json(required_fields=['username', 'password'])
def login():
    """User login with session management"""
    data = request.get_json()
    
    result = auth_service.login(
        username=data['username'],
        password=data['password'],
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    if result['success']:
        session['user_id'] = result['user']['id']
        session['username'] = result['user']['username']
        session['role'] = result['user']['role']
        session['session_token'] = result['session_token']
        
        log_audit(logger, 'login', data['username'], f'IP: {request.remote_addr}')
        
        return jsonify(result)
    else:
        logger.warning(f"Failed login attempt for: {data['username']} from {request.remote_addr}")
        return jsonify(result), 401


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    session_token = session.get('session_token')
    
    if session_token:
        auth_service.logout(session_token)
    
    session.clear()
    return jsonify({'success': True})


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'authenticated': True,
                'user': user.to_dict()
            })
    
    return jsonify({'authenticated': False})


@app.route('/api/auth/request-password-reset', methods=['POST'])
@rate_limit_moderate
@validate_json(required_fields=['username_or_mobile'])
def request_password_reset():
    """Request password reset code via SMS"""
    data = request.get_json()
    
    result = auth_service.request_password_reset(data['username_or_mobile'])
    return jsonify(result), 200


@app.route('/api/auth/reset-password', methods=['POST'])
@rate_limit_moderate
@validate_json(required_fields=['reset_token', 'reset_code', 'new_password'])
def reset_password():
    """Reset password with SMS code"""
    data = request.get_json()
    
    # Validate new password
    is_valid, error = validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'error': error}), 400
    
    result = auth_service.reset_password(
        reset_token=data['reset_token'],
        reset_code=data['reset_code'],
        new_password=data['new_password']
    )
    
    if result['success']:
        log_audit(logger, 'password_reset', f"Reset token: {data['reset_token'][:10]}...", f'IP: {request.remote_addr}')
    
    return jsonify(result), 200 if result['success'] else 400


@app.route('/api/auth/change-password', methods=['POST'])
@login_required
@rate_limit_moderate
@validate_json(required_fields=['old_password', 'new_password'])
def change_password():
    """Change user password"""
    data = request.get_json()
    user_id = session.get('user_id')
    
    # Validate new password
    is_valid, error = validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'error': error}), 400
    
    result = auth_service.change_password(
        user_id=user_id,
        old_password=data['old_password'],
        new_password=data['new_password']
    )
    
    if result['success']:
        log_audit(logger, 'password_changed', session.get('username'), f'IP: {request.remote_addr}')
    
    return jsonify(result), 200 if result['success'] else 400


@app.route('/api/auth/update-notification-preference', methods=['POST'])
@login_required
@rate_limit_moderate
@validate_json(required_fields=['preference'])
def update_notification_preference():
    """Update user notification preference (sms/whatsapp/both)"""
    data = request.get_json()
    user_id = session.get('user_id')
    
    result = auth_service.update_notification_preference(
        user_id=user_id,
        preference=data['preference']
    )
    
    return jsonify(result), 200 if result['success'] else 400


@app.route('/api/auth/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user profile"""
    user = User.query.get(session.get('user_id'))
    return jsonify({
        'success': True,
        'user': user.to_dict()
    })


@app.route('/api/auth/profile', methods=['PUT'])
@login_required
@rate_limit_moderate
def update_profile():
    """Update user profile"""
    data = request.get_json()
    user = User.query.get(session.get('user_id'))
    
    try:
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        
        if 'email' in data:
            user.email = data.get('email')
        
        if 'alert_enabled' in data:
            user.alert_enabled = bool(data['alert_enabled'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/auth/sessions', methods=['GET'])
@login_required
def get_user_sessions():
    """Get all active sessions for current user"""
    user_id = session.get('user_id')
    sessions_list = UserSession.query.filter_by(user_id=user_id, is_active=True).all()
    
    return jsonify({
        'success': True,
        'sessions': [s.to_dict() for s in sessions_list]
    })


@app.route('/api/auth/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def terminate_session(session_id):
    """Terminate a specific session"""
    user_id = session.get('user_id')
    user_session = UserSession.query.filter_by(id=session_id, user_id=user_id).first()
    
    if not user_session:
        return jsonify({'error': 'Session not found'}), 404
    
    user_session.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Session terminated'
    })


# ==================== IOT PREDICTION ENDPOINT ====================

@app.route('/api/predict', methods=['POST'])
@rate_limit_moderate  # 30 requests per minute
@validate_json(required_fields=['temperature', 'humidity', 'mq135'])
def predict():
    """Main prediction endpoint for IoT devices"""
    try:
        data = request.get_json()
        
        # Validate sensor data ranges
        is_valid, error_msg = validate_sensor_data(data)
        if not is_valid:
            logger.warning(f"Invalid sensor data from {request.remote_addr}: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # Get device (create if not exists)
        device_id_str = data.get('device_id', 'ESP32_001')
        device = Device.query.filter_by(device_id=device_id_str).first()
        
        if not device:
            device = Device(
                device_id=device_id_str,
                device_name=f'Device {device_id_str}',
                location='Unknown',
                status='active'
            )
            db.session.add(device)
            db.session.commit()
        
        # Update last seen
        device.last_seen = datetime.utcnow()
        
        # Extract sensor data
        temp = float(data['temperature'])
        humidity = float(data['humidity'])
        mq135 = float(data['mq135'])
        
        # Engineer features and predict
        features_df = engineer_features(temp, humidity, mq135)
        features_scaled = scaler.transform(features_df)
        aqi_prediction = model.predict(features_scaled)[0]
        
        # Get category
        category, _, color = get_aqi_category(aqi_prediction)
        
        # Determine confidence
        if metadata.get('test_r2', 0) > 0.9:
            confidence = 'High'
        elif metadata.get('test_r2', 0) > 0.7:
            confidence = 'Medium'
        else:
            confidence = 'Low'
        
        # Analyze trend
        trend_analysis = analyze_trend()
        
        # Detect anomalies
        anomaly_info = detect_anomaly(aqi_prediction)
        
        # Check for alerts
        alert_info = check_alert_needed(aqi_prediction, device.id)
        
        # Save reading to database
        reading = Reading(
            device_id=device.id,
            temperature=temp,
            humidity=humidity,
            mq135=mq135,
            aqi=aqi_prediction,
            category=category,
            confidence=confidence,
            trend=trend_analysis.get('trend'),
            anomaly_detected=anomaly_info['detected'],
            quality_score='Good' if not anomaly_info['detected'] else 'Warning'
        )
        db.session.add(reading)
        
        # Save alert if triggered
        if alert_info:
            alert = Alert(
                device_id=device.id,
                alert_type=alert_info['type'],
                level=alert_info['level'],
                message=alert_info['message'],
                aqi_value=aqi_prediction
            )
            db.session.add(alert)
            
            # Send mobile notification if enabled
            settings_map = {s.key: s.get_typed_value() for s in Settings.query.all()}
            if settings_map.get('enable_mobile_alerts', False):
                admin_mobile = settings_map.get('admin_mobile_number', '')
                notification_type = settings_map.get('notification_type', 'sms')
                
                if admin_mobile and mobile_notification.enabled:
                    mobile_notification.send_aqi_alert(
                        to_number=admin_mobile,
                        aqi=aqi_prediction,
                        level=alert_info['level'],
                        message=alert_info['message'],
                        device_name=device.device_name,
                        location=device.location,
                        notification_type=notification_type
                    )
        
        db.session.commit()
        
        # Add to forecaster for predictive analytics
        forecaster.add_reading(
            timestamp=datetime.utcnow(),
            aqi=aqi_prediction,
            temperature=temp,
            humidity=humidity
        )
        
        # Add to buffer
        reading_buffer.append({
            'timestamp': datetime.utcnow().isoformat(),
            'temperature': temp,
            'humidity': humidity,
            'mq135': mq135,
            'aqi': aqi_prediction
        })
        
        # Build response
        response = {
            'success': True,
            'prediction': {
                'aqi': round(aqi_prediction, 2),
                'category': category,
                'confidence': confidence,
                'color': color
            },
            'sensor_data': {
                'temperature': temp,
                'humidity': humidity,
                'mq135': mq135
            },
            'trend_analysis': trend_analysis,
            'anomaly_detection': anomaly_info,
            'alert': alert_info,
            'timestamp': datetime.utcnow().isoformat(),
            'device_id': device.device_id
        }
        
        return jsonify(response)
        
    except Exception as e:
        error_msg = f"Error in prediction: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        logger.error(error_msg)
        return jsonify({'success': False, 'error': str(e), 'details': error_msg}), 500


# ==================== DEVICE MANAGEMENT ====================

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all devices"""
    devices = Device.query.all()
    return jsonify([d.to_dict() for d in devices])


@app.route('/api/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """Get specific device"""
    device = Device.query.get_or_404(device_id)
    return jsonify(device.to_dict())


@app.route('/api/devices', methods=['POST'])
@login_required
def create_device():
    """Register new device"""
    data = request.get_json()
    
    device = Device(
        device_id=data['device_id'],
        device_name=data['device_name'],
        location=data.get('location', ''),
        status='active'
    )
    
    db.session.add(device)
    db.session.commit()
    
    return jsonify(device.to_dict()), 201


@app.route('/api/devices/<int:device_id>', methods=['PUT'])
@login_required
def update_device(device_id):
    """Update device information"""
    device = Device.query.get_or_404(device_id)
    data = request.get_json()
    
    device.device_name = data.get('device_name', device.device_name)
    device.location = data.get('location', device.location)
    device.status = data.get('status', device.status)
    
    db.session.commit()
    
    return jsonify(device.to_dict())


@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
@admin_required
def delete_device(device_id):
    """Delete device"""
    device = Device.query.get_or_404(device_id)
    db.session.delete(device)
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== READINGS & HISTORICAL DATA ====================

@app.route('/api/readings', methods=['GET'])
def get_readings():
    """Get historical readings with filters"""
    device_id = request.args.get('device_id', type=int)
    hours = request.args.get('hours', default=24, type=int)
    limit = request.args.get('limit', default=100, type=int)
    
    query = Reading.query
    
    if device_id:
        query = query.filter_by(device_id=device_id)
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(Reading.timestamp >= cutoff_time)
    
    readings = query.order_by(Reading.timestamp.desc()).limit(limit).all()
    
    return jsonify([r.to_dict() for r in readings])


@app.route('/api/readings/latest', methods=['GET'])
def get_latest_reading():
    """Get latest reading from buffer"""
    if reading_buffer:
        return jsonify(list(reading_buffer)[-1])
    return jsonify({'error': 'No readings available'}), 404


@app.route('/api/readings/stats', methods=['GET'])
def get_reading_stats():
    """Get statistical summary of readings"""
    device_id = request.args.get('device_id', type=int)
    hours = request.args.get('hours', default=24, type=int)
    
    query = Reading.query
    
    if device_id:
        query = query.filter_by(device_id=device_id)
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    readings = query.filter(Reading.timestamp >= cutoff_time).all()
    
    if not readings:
        return jsonify({'error': 'No data available'}), 404
    
    aqi_values = [r.aqi for r in readings]
    temp_values = [r.temperature for r in readings]
    hum_values = [r.humidity for r in readings]
    
    stats = {
        'count': len(readings),
        'period_hours': hours,
        'aqi': {
            'current': round(aqi_values[-1], 2),
            'average': round(np.mean(aqi_values), 2),
            'min': round(np.min(aqi_values), 2),
            'max': round(np.max(aqi_values), 2),
            'std': round(np.std(aqi_values), 2)
        },
        'temperature': {
            'average': round(np.mean(temp_values), 2),
            'min': round(np.min(temp_values), 2),
            'max': round(np.max(temp_values), 2)
        },
        'humidity': {
            'average': round(np.mean(hum_values), 2),
            'min': round(np.min(hum_values), 2),
            'max': round(np.max(hum_values), 2)
        }
    }
    
    return jsonify(stats)


#==================== ALERTS ====================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get alerts with filters"""
    device_id = request.args.get('device_id', type=int)
    acknowledged = request.args.get('acknowledged', type=bool)
    hours = request.args.get('hours', default=24, type=int)
    limit = request.args.get('limit', default=50, type=int)
    
    query = Alert.query
    
    if device_id:
        query = query.filter_by(device_id=device_id)
    
    if acknowledged is not None:
        query = query.filter_by(acknowledged=acknowledged)
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(Alert.timestamp >= cutoff_time)
    
    alerts = query.order_by(Alert.timestamp.desc()).limit(limit).all()
    
    return jsonify([a.to_dict() for a in alerts])


@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    alert = Alert.query.get_or_404(alert_id)
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(alert.to_dict())


# ==================== SETTINGS ====================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all settings"""
    settings = Settings.query.all()
    return jsonify({s.key: s.to_dict() for s in settings})


@app.route('/api/settings/<key>', methods=['PUT'])
@login_required
def update_setting(key):
    """Update a setting"""
    setting = Settings.query.filter_by(key=key).first_or_404()
    data = request.get_json()
    
    setting.value = str(data['value'])
    setting.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(setting.to_dict())


# ==================== DATA EXPORT ====================

@app.route('/api/export/csv', methods=['GET'])
@login_required
def export_csv():
    """Export readings as CSV"""
    device_id = request.args.get('device_id', type=int)
    hours = request.args.get('hours', default=24, type=int)
    
    query = Reading.query
    
    if device_id:
        query = query.filter_by(device_id=device_id)
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    readings = query.filter(Reading.timestamp >= cutoff_time).order_by(Reading.timestamp).all()
    
    # Convert to DataFrame
    data = [{
        'timestamp': r.timestamp.isoformat(),
        'device_id': r.device_id,
        'temperature': r.temperature,
        'humidity': r.humidity,
        'mq135': r.mq135,
        'aqi': r.aqi,
        'category': r.category,
        'trend': r.trend,
        'anomaly': r.anomaly_detected
    } for r in readings]
    
    df = pd.DataFrame(data)
    
    # Create CSV
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'iot_readings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@app.route('/api/export/json', methods=['GET'])
@login_required
def export_json():
    """Export readings as JSON"""
    device_id = request.args.get('device_id', type=int)
    hours = request.args.get('hours', default=24, type=int)
    
    query = Reading.query
    
    if device_id:
        query = query.filter_by(device_id=device_id)
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    readings = query.filter(Reading.timestamp >= cutoff_time).order_by(Reading.timestamp).all()
    
    data = {
        'export_time': datetime.utcnow().isoformat(),
        'period_hours': hours,
        'count': len(readings),
        'readings': [r.to_dict() for r in readings]
    }
    
    return send_file(
        io.BytesIO(json.dumps(data, indent=2).encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name=f'iot_readings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    )

# ==================== FORECASTING ENDPOINTS ====================

@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    """Get AQI forecast for next hours"""
    hours = request.args.get('hours', default=6, type=int)
    hours = min(hours, 24)  # Max 24 hours
    
    if not forecaster.can_forecast():
        return jsonify({
            'success': False,
            'error': f'Need at least {forecaster.min_history_size} readings for forecasting',
            'current_readings': len(forecaster.history)
        }), 400
    
    forecast_result = forecaster.forecast_simple(hours)
    
    if not forecast_result['success']:
        return jsonify(forecast_result), 400
    
    return jsonify(forecast_result)


@app.route('/api/forecast/stats', methods=['GET'])
def get_forecast_stats():
    """Get forecaster statistics"""
    stats = forecaster.get_statistics()
    
    if not stats:
        return jsonify({
            'success': False,
            'error': 'No historical data available'
        }), 400
    
    return jsonify({
        'success': True,
        'statistics': stats,
        'can_forecast': forecaster.can_forecast()
    })

# ==================== SYSTEM INFO ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """System health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'model_loaded': model is not None,
        'database_connected': True,
        'devices_count': Device.query.count(),
        'readings_count': Reading.query.count()
    })


@app.route('/health', methods=['GET'])
def health_check_simple():
    """Simple health check endpoint for ESP32"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/dashboard/summary', methods=['GET'])
def dashboard_summary():
    """Get dashboard summary statistics"""
    devices = Device.query.count()
    total_readings = Reading.query.count()
    active_alerts = Alert.query.filter_by(acknowledged=False).count()
    
    # Latest readings per device
    latest_readings = []
    for device in Device.query.all():
        latest = Reading.query.filter_by(device_id=device.id)\
            .order_by(Reading.timestamp.desc()).first()
        if latest:
            latest_readings.append({
                'device': device.to_dict(),
                'reading': latest.to_dict()
            })
    
    # Recent alerts
    recent_alerts = Alert.query.filter_by(acknowledged=False)\
        .order_by(Alert.timestamp.desc()).limit(5).all()
    
    return jsonify({
        'summary': {
            'total_devices': devices,
            'total_readings': total_readings,
            'active_alerts': active_alerts,
            'uptime_hours': (datetime.utcnow() - START_TIME).total_seconds() / 3600
        },
        'latest_readings': latest_readings,
        'recent_alerts': [a.to_dict() for a in recent_alerts]
    })


# ==================== SERVE FRONTEND ====================

@app.route('/')
def serve_frontend():
    """Serve frontend application"""
    dashboard_path = PROJECT_ROOT / 'src' / 'frontend' / 'index.html'
    if dashboard_path.exists():
        return send_file(dashboard_path)
    return jsonify({'message': 'Frontend not found. Access API at /api/*'}), 404


# ==================== ADMIN ENDPOINTS ====================

@app.route('/api/admin/backup', methods=['POST'])
@login_required
@admin_required
def create_manual_backup():
    """Create database backup manually"""
    try:
        backup_path = backup_manager.create_backup(compress=True)
        log_audit(logger, 'manual_backup', session.get('username'), f'Created: {backup_path}')
        return jsonify({
            'success': True,
            'backup_file': str(backup_path),
            'message': 'Backup created successfully'
        })
    except Exception as e:
        log_error_with_context(logger, e, {'action': 'manual_backup'})
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/backups', methods=['GET'])
@login_required
@admin_required
def list_backups():
    """List all available backups"""
    try:
        backups = backup_manager.list_backups()
        return jsonify({
            'success': True,
            'backups': backups
        })
    except Exception as e:
        log_error_with_context(logger, e, {'action': 'list_backups'})
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/restore', methods=['POST'])
@login_required
@admin_required
def restore_backup():
    """Restore database from backup"""
    try:
        data = request.get_json()
        backup_file = data.get('backup_file')
        
        if not backup_file:
            return jsonify({'success': False, 'error': 'backup_file required'}), 400
        
        backup_manager.restore_backup(backup_file)
        log_audit(logger, 'restore_backup', session.get('username'), f'Restored from: {backup_file}')
        
        return jsonify({
            'success': True,
            'message': 'Database restored successfully'
        })
    except Exception as e:
        log_error_with_context(logger, e, {'action': 'restore_backup', 'file': backup_file})
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/cleanup', methods=['POST'])
@login_required
@admin_required
def manual_cleanup():
    """Manually trigger data cleanup"""
    try:
        # Use scheduled_tasks cleanup if available
        if scheduled_tasks:
            scheduled_tasks.cleanup_old_data()
            log_audit(logger, 'manual_cleanup', session.get('username'), 'Data cleanup executed')
            return jsonify({
                'success': True,
                'message': 'Cleanup completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Scheduled tasks not initialized'
            }), 500
    except Exception as e:
        log_error_with_context(logger, e, {'action': 'manual_cleanup'})
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/vacuum', methods=['POST'])
@login_required
@admin_required
def vacuum_database():
    """Optimize database (VACUUM)"""
    try:
        backup_manager.vacuum_database()
        log_audit(logger, 'database_vacuum', session.get('username'), 'Database optimized')
        return jsonify({
            'success': True,
            'message': 'Database optimized successfully'
        })
    except Exception as e:
        log_error_with_context(logger, e, {'action': 'vacuum_database'})
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/stats', methods=['GET'])
@login_required
@admin_required
def get_system_stats():
    """Get system statistics"""
    try:
        # Database stats
        db_stats = backup_manager.get_database_stats()
        
        # Count records
        total_readings = Reading.query.count()
        total_devices = Device.query.count()
        total_users = User.query.count()
        total_alerts = Alert.query.count()
        
        # Recent activity
        recent_readings = Reading.query.order_by(Reading.timestamp.desc()).limit(1).first()
        last_reading_time = recent_readings.timestamp.isoformat() if recent_readings else None
        
        # Backup info
        backups = backup_manager.list_backups()
        
        return jsonify({
            'success': True,
            'statistics': {
                'database': db_stats,
                'counts': {
                    'readings': total_readings,
                    'devices': total_devices,
                    'users': total_users,
                    'alerts': total_alerts
                },
                'activity': {
                    'last_reading': last_reading_time
                },
                'backups': {
                    'total': len(backups),
                    'latest': backups[0] if backups else None
                }
            }
        })
    except Exception as e:
        log_error_with_context(logger, e, {'action': 'get_system_stats'})
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    static_dir = PROJECT_ROOT / 'src' / 'frontend'
    return send_from_directory(static_dir, path)


# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  IoT AIR QUALITY MONITORING - FULL APPLICATION SERVER")
    print("="*70)
    
    # Load ML model
    if not load_ml_model():
        print("Warning: ML model not loaded. Prediction features will not work.")
    
    # Initialize database
    initialize_database()
    
    print("\n" + "="*70)
    print("  SERVER STARTING")
    print("="*70)
    print(f"  🌐 API Base URL: http://127.0.0.1:5000/api")
    print(f"  📊 Dashboard: http://127.0.0.1:5000")
    print(f"  🔐 Default Login: admin / admin123")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
