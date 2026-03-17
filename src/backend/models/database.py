"""
Database Models for IoT Air Quality Monitoring System
SQLite database with ORM using SQLAlchemy
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Device(db.Model):
    """IoT Device Registration"""
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), unique=True, nullable=False)
    device_name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    status = db.Column(db.String(50), default='active')  # active, inactive, maintenance
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    readings = db.relationship('Reading', backref='device', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='device', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'location': self.location,
            'status': self.status,
            'registered_at': self.registered_at.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }


class Reading(db.Model):
    """Sensor Readings with ML Predictions"""
    __tablename__ = 'readings'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Sensor Data
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    mq135 = db.Column(db.Float, nullable=False)
    
    # ML Predictions
    aqi = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    confidence = db.Column(db.String(50))
    
    # Intelligent Analysis
    trend = db.Column(db.String(50))
    anomaly_detected = db.Column(db.Boolean, default=False)
    quality_score = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat(),
            'temperature': round(self.temperature, 2),
            'humidity': round(self.humidity, 2),
            'mq135': round(self.mq135, 2),
            'aqi': round(self.aqi, 2),
            'category': self.category,
            'confidence': self.confidence,
            'trend': self.trend,
            'anomaly_detected': self.anomaly_detected,
            'quality_score': self.quality_score
        }


class Alert(db.Model):
    """Alert History"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    alert_type = db.Column(db.String(50), nullable=False)  # aqi, anomaly, sensor_error
    level = db.Column(db.String(50), nullable=False)  # warning, danger, critical
    message = db.Column(db.Text, nullable=False)
    aqi_value = db.Column(db.Float)
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat(),
            'alert_type': self.alert_type,
            'level': self.level,
            'message': self.message,
            'aqi_value': self.aqi_value,
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


class User(db.Model):
    """Enhanced User Management with Mobile Authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)  # Required for simple registration
    mobile_number = db.Column(db.String(20), unique=True, nullable=True, index=True)  # Optional - for alerts only
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(200))
    role = db.Column(db.String(50), default='user')  # admin, user, viewer
    
    # Mobile verification (for alert system)
    mobile_verified = db.Column(db.Boolean, default=False)
    mobile_verified_at = db.Column(db.DateTime)
    
    # Account status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_locked = db.Column(db.Boolean, default=False)
    locked_until = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    
    # Notification preferences
    notification_preference = db.Column(db.String(20), default='sms')  # sms, whatsapp, both
    alert_enabled = db.Column(db.Boolean, default=True)
    
    # Security
    two_factor_enabled = db.Column(db.Boolean, default=False)
    last_password_change = db.Column(db.DateTime, default=datetime.utcnow)
    password_expiry_days = db.Column(db.Integer, default=90)
    
    # Terms and Privacy
    terms_accepted = db.Column(db.Boolean, default=False)
    terms_accepted_at = db.Column(db.DateTime)
    privacy_accepted = db.Column(db.Boolean, default=False)
    privacy_accepted_at = db.Column(db.DateTime)
    
    # Profile completion
    profile_completed = db.Column(db.Boolean, default=False)
    
    # Email verification (optional)
    email_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    
    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    otp_codes = db.relationship('OTPCode', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.last_password_change = datetime.utcnow()
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_account_locked(self):
        if self.is_locked and self.locked_until:
            if datetime.utcnow() < self.locked_until:
                return True
            else:
                # Auto-unlock after timeout
                self.is_locked = False
                self.locked_until = None
                self.failed_login_attempts = 0
        return False
    
    def is_password_expired(self):
        """Check if password has expired"""
        if not self.password_expiry_days or self.password_expiry_days == 0:
            return False
        expiry_date = self.last_password_change + timedelta(days=self.password_expiry_days)
        return datetime.utcnow() > expiry_date
    
    def days_until_password_expiry(self):
        """Get days until password expires"""
        if not self.password_expiry_days or self.password_expiry_days == 0:
            return None
        expiry_date = self.last_password_change + timedelta(days=self.password_expiry_days)
        delta = expiry_date - datetime.utcnow()
        return max(0, delta.days)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'mobile_number': self.mobile_number,
            'mobile_verified': self.mobile_verified,
            'email_verified': self.email_verified,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'notification_preference': self.notification_preference,
            'two_factor_enabled': self.two_factor_enabled,
            'profile_completed': self.profile_completed,
            'terms_accepted': self.terms_accepted,
            'password_expires_in_days': self.days_until_password_expiry()
        }


class Settings(db.Model):
    """System Settings and Configuration"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(50))  # string, int, float, bool, json
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.get_typed_value(),
            'value_type': self.value_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_typed_value(self):
        """Return value with proper type conversion"""
        if self.value_type == 'int':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'bool':
            return self.value.lower() == 'true'
        elif self.value_type == 'json':
            import json
            return json.loads(self.value)
        return self.value


class Notification(db.Model):
    """Notification Queue for SMS/WhatsApp"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_type = db.Column(db.String(50), nullable=False)  # sms, whatsapp
    recipient = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, sent, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'notification_type': self.notification_type,
            'recipient': self.recipient,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }


class OTPCode(db.Model):
    """OTP Verification Codes"""
    __tablename__ = 'otp_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)  # registration, login, password_reset, mobile_verify
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    attempts = db.Column(db.Integer, default=0)
    
    def is_valid(self):
        if self.used:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        if self.attempts >= 5:
            return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'purpose': self.purpose,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'used': self.used,
            'attempts': self.attempts
        }


class PasswordResetToken(db.Model):
    """Password Reset Tokens"""
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    code = db.Column(db.String(10), nullable=False)  # 6-digit code sent via SMS
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='reset_tokens')
    
    def is_valid(self):
        if self.used:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'used': self.used
        }


class UserSession(db.Model):
    """User Session Management"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(200), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    device_fingerprint = db.Column(db.String(100))
    location = db.Column(db.String(200))  # City, Country
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    remember_me = db.Column(db.Boolean, default=False)
    
    def is_valid(self):
        if not self.is_active:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'location': self.location,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'is_active': self.is_active,
            'remember_me': self.remember_me
        }


class LoginHistory(db.Model):
    """Login Activity Log"""
    __tablename__ = 'login_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    device_fingerprint = db.Column(db.String(100))
    location = db.Column(db.String(200))
    failure_reason = db.Column(db.String(200))
    
    user = db.relationship('User', backref='login_history')
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'ip_address': self.ip_address,
            'location': self.location,
            'failure_reason': self.failure_reason
        }


class ActivityLog(db.Model):
    """User Activity Tracking"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    action = db.Column(db.String(100), nullable=False)  # login, logout, register, password_change, etc.
    resource = db.Column(db.String(200))  # What was accessed
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    details = db.Column(db.Text)  # JSON string with additional details
    status = db.Column(db.String(50))  # success, failure, warning
    
    user = db.relationship('User', backref='activity_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'resource': self.resource,
            'ip_address': self.ip_address,
            'details': self.details,
            'status': self.status
        }


class RememberToken(db.Model):
    """Remember Me Tokens"""
    __tablename__ = 'remember_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(200), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_used = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='remember_tokens')
    
    def is_valid(self):
        if not self.is_active:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'expires_at': self.expires_at.isoformat()
        }
