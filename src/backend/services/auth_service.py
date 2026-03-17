"""
Enhanced Professional Authentication Service
Complete authentication with all professional features
"""

import secrets
import string
import json
from datetime import datetime, timedelta
from models.database import db, User, OTPCode, PasswordResetToken, UserSession, LoginHistory, ActivityLog, RememberToken
from utils.security import (
    password_validator, rate_limiter, DeviceFingerprint, 
    SessionManager, sanitize_input, validate_mobile_number,
    validate_email, validate_username
)


class EnhancedAuthenticationService:
    """Professional authentication service with advanced features"""
    
    def __init__(self, notification_service=None):
        """
        Initialize enhanced authentication service
        
        Args:
            notification_service: MobileNotificationService instance
        """
        self.notification_service = notification_service
        self.otp_expiry_minutes = 10
        self.reset_token_expiry_minutes = 30
        self.session_expiry_hours = 24
        self.remember_me_days = 30
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self.password_validator = password_validator
        self.rate_limiter = rate_limiter
    
    def generate_otp(self, length=6):
        """Generate random OTP code"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    def generate_token(self, length=32):
        """Generate secure random token"""
        return secrets.token_urlsafe(length)
    
    def log_activity(self, user_id, action, status, ip_address=None, user_agent=None, details=None, resource=None):
        """Log user activity"""
        try:
            log = ActivityLog(
                user_id=user_id,
                action=action,
                status=status,
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps(details) if details else None,
                resource=resource
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f"Failed to log activity: {e}")
    
    def log_login_attempt(self, user_id, success, ip_address=None, user_agent=None, 
                         location=None, failure_reason=None):
        """Log login attempt"""
        try:
            device_fingerprint = DeviceFingerprint.generate(user_agent or '', ip_address or '')
            
            log = LoginHistory(
                user_id=user_id,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                location=location,
                failure_reason=failure_reason
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f"Failed to log login attempt: {e}")
    
    def validate_password_strength(self, password):
        """Validate password strength"""
        return self.password_validator.validate(password)
    
    def register_user_simple(self, username, password, full_name='', email=None, 
                            role='user', terms_accepted=False, privacy_accepted=False,
                            ip_address=None, user_agent=None):
        """
        Simple user registration without mobile verification
        
        Args:
            username: Unique username
            password: User password
            full_name: User's full name
            email: Email address (required)
            role: User role (default: 'user')
            terms_accepted: Terms of service acceptance
            privacy_accepted: Privacy policy acceptance
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            dict: Registration result with user info
        """
        # Sanitize inputs
        username = sanitize_input(username, 30)
        full_name = sanitize_input(full_name, 200)
        
        # Validate username format
        if not validate_username(username):
            return {
                'success': False, 
                'error': 'Username must be 3-30 characters, alphanumeric, underscore or dash only'
            }
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            return {'success': False, 'error': 'Username already exists'}
        
        # Validate email (required for simple registration)
        if not email:
            return {'success': False, 'error': 'Email is required'}
        
        email = sanitize_input(email, 200)
        if not validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
        
        if User.query.filter_by(email=email).first():
            return {'success': False, 'error': 'Email already registered'}
        
        # Validate password strength
        password_check = self.validate_password_strength(password)
        if not password_check['valid']:
            return {
                'success': False,
                'error': 'Password does not meet requirements',
                'password_errors': password_check['errors'],
                'password_suggestions': password_check['suggestions']
            }
        
        # Check terms acceptance
        if not terms_accepted:
            return {'success': False, 'error': 'You must accept the terms of service'}
        
        try:
            # Create user without mobile number (will be added later for alerts)
            user = User(
                username=username,
                mobile_number=None,  # No mobile during registration
                full_name=full_name,
                email=email,
                role=role,
                mobile_verified=False,
                email_verified=False,
                is_active=True,
                terms_accepted=terms_accepted,
                terms_accepted_at=datetime.utcnow() if terms_accepted else None,
                privacy_accepted=privacy_accepted,
                privacy_accepted_at=datetime.utcnow() if privacy_accepted else None,
                profile_completed=bool(full_name and email)
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Log registration
            self.log_activity(
                user.id, 'register', 'success',
                ip_address=ip_address,
                user_agent=user_agent,
                details={'email': email}
            )
            
            return {
                'success': True,
                'user': user.to_dict(),
                'message': 'Account created successfully. You can now login.',
                'password_strength': password_check['strength']
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def register_user(self, username, password, mobile_number, full_name='', email=None, 
                     role='user', send_otp=True, terms_accepted=False, privacy_accepted=False,
                     ip_address=None, user_agent=None):
        """
        Register new user with comprehensive validation
        
        Args:
            username: Unique username
            password: User password
            mobile_number: Mobile number in E.164 format (+1234567890)
            full_name: User's full name
            email: Optional email address
            role: User role (default: 'user')
            send_otp: Whether to send OTP for verification
            terms_accepted: Terms of service acceptance
            privacy_accepted: Privacy policy acceptance
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            dict: Registration result with user info and OTP status
        """
        # Sanitize inputs
        username = sanitize_input(username, 30)
        full_name = sanitize_input(full_name, 200)
        
        # Validate username format
        if not validate_username(username):
            return {
                'success': False, 
                'error': 'Username must be 3-30 characters, alphanumeric, underscore or dash only'
            }
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            return {'success': False, 'error': 'Username already exists'}
        
        # Validate mobile number format
        if not validate_mobile_number(mobile_number):
            return {
                'success': False, 
                'error': 'Mobile number must be in E.164 format (+country_code_number)'
            }
        
        # Check if mobile number exists
        if User.query.filter_by(mobile_number=mobile_number).first():
            return {'success': False, 'error': 'Mobile number already registered'}
        
        # Validate email if provided
        if email:
            email = sanitize_input(email, 200)
            if not validate_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            if User.query.filter_by(email=email).first():
                return {'success': False, 'error': 'Email already registered'}
        
        # Validate password strength
        password_check = self.validate_password_strength(password)
        if not password_check['valid']:
            return {
                'success': False,
                'error': 'Password does not meet requirements',
                'password_errors': password_check['errors'],
                'password_suggestions': password_check['suggestions']
            }
        
        # Check terms acceptance
        if not terms_accepted:
            return {'success': False, 'error': 'You must accept the terms of service'}
        
        try:
            # Create user
            user = User(
                username=username,
                mobile_number=mobile_number,
                full_name=full_name,
                email=email,
                role=role,
                mobile_verified=False,
                email_verified=False,
                is_active=True,
                terms_accepted=terms_accepted,
                terms_accepted_at=datetime.utcnow() if terms_accepted else None,
                privacy_accepted=privacy_accepted,
                privacy_accepted_at=datetime.utcnow() if privacy_accepted else None,
                profile_completed=bool(full_name and email)
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Log registration
            self.log_activity(
                user.id, 'register', 'success',
                ip_address=ip_address,
                user_agent=user_agent,
                details={'email': email, 'mobile': mobile_number}
            )
            
            # Generate and send OTP if requested
            otp_sent = False
            if send_otp:
                otp_result = self.send_verification_otp(user.id, user.mobile_number)
                otp_sent = otp_result['success']
            
            return {
                'success': True,
                'user': user.to_dict(),
                'otp_sent': otp_sent,
                'message': 'User registered successfully. Please verify your mobile number.',
                'password_strength': password_check['strength']
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def send_verification_otp(self, user_id, mobile_number, notification_type='sms'):
        """
        Generate and send OTP for mobile verification
        
        Args:
            user_id: User ID
            mobile_number: Mobile number to send OTP
            notification_type: 'sms' or 'whatsapp'
        
        Returns:
            dict: OTP generation and sending result
        """
        try:
            # Generate OTP
            otp_code = self.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
            
            # Save OTP to database
            otp = OTPCode(
                user_id=user_id,
                code=otp_code,
                purpose='mobile_verify',
                expires_at=expires_at
            )
            db.session.add(otp)
            db.session.commit()
            
            # Send OTP via SMS/WhatsApp
            if self.notification_service:
                sent = self.notification_service.send_otp(mobile_number, otp_code, notification_type)
                if sent:
                    self.log_activity(user_id, 'otp_sent', 'success', details={'type': notification_type})
                    return {'success': True, 'message': 'OTP sent successfully', 'otp_id': otp.id}
                else:
                    return {'success': False, 'error': 'Failed to send OTP'}
            else:
                # For testing without notification service
                print(f"🔐 OTP Code for {mobile_number}: {otp_code}")
                return {'success': True, 'message': f'OTP generated: {otp_code}', 'otp_id': otp.id}
        
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def verify_mobile(self, user_id, otp_code, ip_address=None, user_agent=None):
        """
        Verify mobile number with OTP
        
        Args:
            user_id: User ID
            otp_code: OTP code entered by user
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            dict: Verification result
        """
        try:
            # Find latest unused OTP for mobile verification
            otp = OTPCode.query.filter_by(
                user_id=user_id,
                purpose='mobile_verify',
                used=False
            ).order_by(OTPCode.created_at.desc()).first()
            
            if not otp:
                return {'success': False, 'error': 'No verification code found'}
            
            # Increment attempts
            otp.attempts += 1
            db.session.commit()
            
            if not otp.is_valid():
                return {'success': False, 'error': 'Verification code expired or invalid'}
            
            if otp.code != otp_code:
                return {'success': False, 'error': 'Invalid verification code'}
            
            # Mark OTP as used
            otp.used = True
            otp.used_at = datetime.utcnow()
            
            # Update user as verified
            user = User.query.get(user_id)
            user.mobile_verified = True
            user.mobile_verified_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log verification
            self.log_activity(
                user_id, 'mobile_verified', 'success',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                'success': True,
                'message': 'Mobile number verified successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def login(self, username, password, remember_me=False, ip_address=None, user_agent=None):
        """
        Authenticate user and create session with comprehensive checks
        
        Args:
            username: Username or mobile number
            password: User password
            remember_me: Remember me flag
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            dict: Login result with session token
        """
        try:
            # Find user by username or mobile number
            user = User.query.filter(
                (User.username == username) | (User.mobile_number == username)
            ).first()
            
            if not user:
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Check if account is locked
            if user.is_account_locked():
                locked_until_str = user.locked_until.strftime("%Y-%m-%d %H:%M:%S")
                self.log_login_attempt(
                    user.id, False, ip_address, user_agent, 
                    failure_reason='Account locked'
                )
                return {
                    'success': False,
                    'error': f'Account is locked until {locked_until_str}',
                    'locked': True
                }
            
            # Check if account is active
            if not user.is_active:
                self.log_login_attempt(
                    user.id, False, ip_address, user_agent,
                    failure_reason='Account deactivated'
                )
                return {'success': False, 'error': 'Account is deactivated'}
            
            # Verify password
            if not user.check_password(password):
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                # Lock account if too many failed attempts
                if user.failed_login_attempts >= self.max_failed_attempts:
                    user.is_locked = True
                    user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
                    db.session.commit()
                    
                    self.log_login_attempt(
                        user.id, False, ip_address, user_agent,
                        failure_reason='Too many failed attempts - locked'
                    )
                    
                    return {
                        'success': False,
                        'error': f'Account locked due to too many failed attempts. Try again in {self.lockout_duration_minutes} minutes.',
                        'locked': True
                    }
                
                db.session.commit()
                remaining_attempts = self.max_failed_attempts - user.failed_login_attempts
                
                self.log_login_attempt(
                    user.id, False, ip_address, user_agent,
                    failure_reason='Invalid password'
                )
                
                return {
                    'success': False,
                    'error': f'Invalid username or password. {remaining_attempts} attempts remaining.'
                }
            
            # Check if mobile is verified
            if not user.mobile_verified and user.mobile_number:
                return {
                    'success': False,
                    'error': 'Please verify your mobile number to receive alerts',
                    'requires_verification': True,
                    'user_id': user.id
                }
            
            # Check if password has expired
            if user.is_password_expired():
                return {
                    'success': False,
                    'error': 'Your password has expired. Please reset it.',
                    'password_expired': True
                }
            
            # Warn if password expiring soon (within 7 days)
            days_until_expiry = user.days_until_password_expiry()
            password_warning = None
            if days_until_expiry is not None and days_until_expiry <= 7:
                password_warning = f'Your password expires in {days_until_expiry} days'
            
            # Reset failed attempts
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            
            # Create session
            session_token = self.generate_token()
            expires_at = datetime.utcnow() + timedelta(
                days=self.remember_me_days if remember_me else 0,
                hours=0 if remember_me else self.session_expiry_hours
            )
            
            device_fingerprint = DeviceFingerprint.generate(user_agent or '', ip_address or '')
            
            session = UserSession(
                user_id=user.id,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                expires_at=expires_at,
                remember_me=remember_me
            )
            db.session.add(session)
            
            # Create remember me token if requested
            remember_token = None
            if remember_me:
                remember_token = SessionManager.create_remember_token()
                remember_token_hash = SessionManager.hash_remember_token(remember_token)
                
                remember_token_obj = RememberToken(
                    user_id=user.id,
                    token_hash=remember_token_hash,
                    expires_at=datetime.utcnow() + timedelta(days=self.remember_me_days)
                )
                db.session.add(remember_token_obj)
            
            db.session.commit()
            
            # Log successful login
            self.log_login_attempt(user.id, True, ip_address, user_agent)
            self.log_activity(
                user.id, 'login', 'success',
                ip_address=ip_address,
                user_agent=user_agent,
                details={'remember_me': remember_me}
            )
            
            response = {
                'success': True,
                'user': user.to_dict(),
                'session_token': session_token,
                'expires_at': expires_at.isoformat()
            }
            
            if remember_token:
                response['remember_token'] = remember_token
            
            if password_warning:
                response['warning'] = password_warning
            
            return response
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def logout(self, session_token, ip_address=None, user_agent=None):
        """
        Logout user and invalidate session
        
        Args:
            session_token: Session token to invalidate
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            dict: Logout result
        """
        try:
            session = UserSession.query.filter_by(session_token=session_token).first()
            if session:
                session.is_active = False
                db.session.commit()
                
                # Log logout
                self.log_activity(
                    session.user_id, 'logout', 'success',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            return {'success': True, 'message': 'Logged out successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_session(self, session_token):
        """
        Validate session token
        
        Args:
            session_token: Session token to validate
        
        Returns:
            dict: Validation result with user info
        """
        session = UserSession.query.filter_by(session_token=session_token).first()
        
        if not session or not session.is_valid():
            return {'valid': False, 'error': 'Invalid or expired session'}
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        db.session.commit()
        
        user = User.query.get(session.user_id)
        
        return {
            'valid': True,
            'user': user.to_dict(),
            'session': session.to_dict()
        }
    
    def get_login_history(self, user_id, limit=10):
        """Get user's login history"""
        history = LoginHistory.query.filter_by(user_id=user_id)\
            .order_by(LoginHistory.timestamp.desc())\
            .limit(limit)\
            .all()
        
        return [h.to_dict() for h in history]
    
    def get_active_sessions(self, user_id):
        """Get user's active sessions"""
        sessions = UserSession.query.filter_by(user_id=user_id, is_active=True)\
            .filter(UserSession.expires_at > datetime.utcnow())\
            .all()
        
        return [s.to_dict() for s in sessions]
    
    def revoke_session(self, session_id, user_id):
        """Revoke a specific session"""
        session = UserSession.query.filter_by(id=session_id, user_id=user_id).first()
        if session:
            session.is_active = False
            db.session.commit()
            return {'success': True, 'message': 'Session revoked'}
        return {'success': False, 'error': 'Session not found'}
    
    def revoke_all_sessions(self, user_id, except_session_token=None):
        """Revoke all sessions except current"""
        query = UserSession.query.filter_by(user_id=user_id, is_active=True)
        
        if except_session_token:
            query = query.filter(UserSession.session_token != except_session_token)
        
        query.update({'is_active': False})
        db.session.commit()
        
        return {'success': True, 'message': 'All sessions revoked'}
