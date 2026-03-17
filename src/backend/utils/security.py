"""
Security Utilities for Authentication System
Password strength validation, rate limiting, security headers
"""

import re
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from collections import defaultdict

class PasswordValidator:
    """Password strength validation and enforcement"""
    
    def __init__(self):
        self.min_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special = True
        self.common_passwords = set([
            'password', 'password123', '12345678', 'qwerty', 'abc123',
            'monkey', '1234567890', 'letmein', 'trustno1', 'dragon',
            'baseball', 'iloveyou', 'master', 'sunshine', 'ashley',
            'bailey', 'shadow', '123123', '654321', 'superman',
            'qazwsx', 'michael', 'football', 'welcome', 'jesus',
            'ninja', 'mustang', 'password1', '123456789', 'admin',
            'admin123', 'root', 'toor', 'pass', 'test'
        ])
    
    def validate(self, password):
        """
        Validate password strength
        
        Returns:
            dict: {
                'valid': bool,
                'score': int (0-100),
                'strength': str ('weak', 'fair', 'good', 'strong', 'very_strong'),
                'errors': list,
                'suggestions': list
            }
        """
        errors = []
        suggestions = []
        score = 0
        
        # Check length
        if len(password) < self.min_length:
            errors.append(f'Password must be at least {self.min_length} characters')
            suggestions.append('Use a longer password')
        else:
            score += min(25, len(password) * 2)
        
        # Check for uppercase
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
            suggestions.append('Add uppercase letters (A-Z)')
        else:
            score += 15
        
        # Check for lowercase
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
            suggestions.append('Add lowercase letters (a-z)')
        else:
            score += 15
        
        # Check for digits
        if self.require_digits and not re.search(r'\d', password):
            errors.append('Password must contain at least one number')
            suggestions.append('Add numbers (0-9)')
        else:
            score += 15
        
        # Check for special characters
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', password):
            errors.append('Password must contain at least one special character')
            suggestions.append('Add special characters (!@#$%^&*)')
        else:
            score += 15
        
        # Check for common passwords
        if password.lower() in self.common_passwords:
            errors.append('Password is too common')
            suggestions.append('Use a unique password')
            score = max(0, score - 30)
        
        # Check for sequential characters
        if self._has_sequential(password):
            suggestions.append('Avoid sequential characters (abc, 123)')
            score -= 10
        
        # Check for repeated characters
        if self._has_repeated(password):
            suggestions.append('Avoid repeated characters (aaa, 111)')
            score -= 10
        
        # Determine strength
        score = max(0, min(100, score))
        if score < 30:
            strength = 'weak'
        elif score < 50:
            strength = 'fair'
        elif score < 70:
            strength = 'good'
        elif score < 90:
            strength = 'strong'
        else:
            strength = 'very_strong'
        
        return {
            'valid': len(errors) == 0,
            'score': score,
            'strength': strength,
            'errors': errors,
            'suggestions': suggestions
        }
    
    def _has_sequential(self, password):
        """Check for sequential characters"""
        sequential_patterns = [
            'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij',
            'ijk', 'jkl', 'klm', 'lmn', 'mno', 'nop', 'opq', 'pqr',
            'qrs', 'rst', 'stu', 'tuv', 'uvw', 'vwx', 'wxy', 'xyz',
            '123', '234', '345', '456', '567', '678', '789', '890'
        ]
        password_lower = password.lower()
        return any(pattern in password_lower for pattern in sequential_patterns)
    
    def _has_repeated(self, password):
        """Check for repeated characters"""
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                return True
        return False


class RateLimiter:
    """Simple in-memory rate limiter for authentication endpoints"""
    
    def __init__(self):
        self.attempts = defaultdict(list)
        self.lockout_duration = 900  # 15 minutes
        self.max_attempts = {
            'login': 5,
            'register': 3,
            'password_reset': 3,
            'otp_verify': 5
        }
        self.window = {
            'login': 300,  # 5 minutes
            'register': 3600,  # 1 hour
            'password_reset': 3600,  # 1 hour
            'otp_verify': 300  # 5 minutes
        }
    
    def is_allowed(self, identifier, action='login'):
        """
        Check if action is allowed for identifier
        
        Args:
            identifier: IP address or user identifier
            action: Type of action (login, register, etc.)
        
        Returns:
            tuple: (allowed: bool, retry_after: int)
        """
        now = datetime.utcnow()
        key = f"{action}:{identifier}"
        
        # Clean old attempts
        self.attempts[key] = [
            timestamp for timestamp in self.attempts[key]
            if now - timestamp < timedelta(seconds=self.window.get(action, 300))
        ]
        
        # Check if locked out
        if len(self.attempts[key]) >= self.max_attempts.get(action, 5):
            oldest_attempt = min(self.attempts[key])
            retry_after = int((oldest_attempt + timedelta(seconds=self.window[action]) - now).total_seconds())
            return False, max(0, retry_after)
        
        return True, 0
    
    def record_attempt(self, identifier, action='login'):
        """Record an attempt"""
        key = f"{action}:{identifier}"
        self.attempts[key].append(datetime.utcnow())
    
    def clear_attempts(self, identifier, action='login'):
        """Clear attempts after successful action"""
        key = f"{action}:{identifier}"
        if key in self.attempts:
            del self.attempts[key]


def rate_limit(action='login'):
    """Decorator for rate limiting endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limiter = getattr(f, '_rate_limiter', None)
            if limiter:
                identifier = request.remote_addr
                allowed, retry_after = limiter.is_allowed(identifier, action)
                
                if not allowed:
                    return jsonify({
                        'success': False,
                        'error': f'Too many attempts. Please try again in {retry_after} seconds.',
                        'retry_after': retry_after
                    }), 429
                
                limiter.record_attempt(identifier, action)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


class DeviceFingerprint:
    """Generate device fingerprint for tracking"""
    
    @staticmethod
    def generate(user_agent, ip_address):
        """Generate unique device fingerprint"""
        data = f"{user_agent}:{ip_address}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]


class SecurityHeaders:
    """Security headers for Flask responses"""
    
    @staticmethod
    def get_headers():
        """Get security headers dictionary"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https://cdn.jsdelivr.net;",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }
    
    @staticmethod
    def apply_to_response(response):
        """Apply security headers to Flask response"""
        for key, value in SecurityHeaders.get_headers().items():
            response.headers[key] = value
        return response


class CSRFProtection:
    """CSRF token generation and validation"""
    
    @staticmethod
    def generate_token():
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_token(token, stored_token):
        """Validate CSRF token"""
        return secrets.compare_digest(token, stored_token)


class SessionManager:
    """Enhanced session management"""
    
    @staticmethod
    def create_remember_token():
        """Create remember me token"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def hash_remember_token(token):
        """Hash remember token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()


def sanitize_input(text, max_length=255):
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return text
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>\"\'%;()&+]', '', text)
    
    # Limit length
    text = text[:max_length]
    
    # Strip whitespace
    text = text.strip()
    
    return text


def validate_mobile_number(mobile):
    """Validate mobile number in E.164 format"""
    pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(pattern, mobile))


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username):
    """Validate username format"""
    # Username: 3-30 characters, alphanumeric, underscore, dash
    pattern = r'^[a-zA-Z0-9_-]{3,30}$'
    return bool(re.match(pattern, username))


# Create global instances
password_validator = PasswordValidator()
rate_limiter = RateLimiter()
