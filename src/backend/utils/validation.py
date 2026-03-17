"""
Input Validation Utilities
Provides decorators and functions for validating API inputs
"""

from functools import wraps
from flask import request, jsonify
import re

def validate_json(required_fields=None, optional_fields=None):
    """
    Decorator to validate JSON request body
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names with default values dict
    
    Example:
        @validate_json(required_fields=['temperature', 'humidity'])
        def my_endpoint():
            data = request.json
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.json
            
            if not data:
                return jsonify({'error': 'Request body is empty'}), 400
            
            # Check required fields
            if required_fields:
                missing = [field for field in required_fields if field not in data]
                if missing:
                    return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_sensor_data(data):
    """
    Validate sensor reading data
    
    Args:
        data: Dictionary with sensor values
    
    Returns:
        tuple: (is_valid, error_message)
    """
    errors = []
    
    # Temperature validation (-40 to 80 Celsius)
    if 'temperature' in data:
        temp = data['temperature']
        if not isinstance(temp, (int, float)):
            errors.append("Temperature must be a number")
        elif temp < -40 or temp > 80:
            errors.append("Temperature out of range (-40 to 80°C)")
    
    # Humidity validation (0 to 100%)
    if 'humidity' in data:
        humidity = data['humidity']
        if not isinstance(humidity, (int, float)):
            errors.append("Humidity must be a number")
        elif humidity < 0 or humidity > 100:
            errors.append("Humidity out of range (0 to 100%)")
    
    # MQ135 validation (0 to 5000 ppm)
    if 'mq135' in data:
        mq135 = data['mq135']
        if not isinstance(mq135, (int, float)):
            errors.append("MQ135 must be a number")
        elif mq135 < 0 or mq135 > 5000:
            errors.append("MQ135 out of range (0 to 5000 ppm)")
    
    # Device ID validation
    if 'device_id' in data:
        device_id = data['device_id']
        if not isinstance(device_id, str):
            errors.append("Device ID must be a string")
        elif len(device_id) < 3 or len(device_id) > 100:
            errors.append("Device ID length must be 3-100 characters")
    
    is_valid = len(errors) == 0
    error_message = "; ".join(errors) if errors else None
    
    return is_valid, error_message

def validate_email(email):
    """
    Validate email format
    
    Args:
        email: Email string
    
    Returns:
        bool: True if valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """
    Validate username format
    
    Args:
        username: Username string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, dash and underscore"
    
    return True, None

def validate_password(password):
    """
    Validate password strength
    
    Args:
        password: Password string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    if len(password) > 100:
        return False, "Password must be less than 100 characters"
    
    return True, None


def validate_mobile_number(mobile_number):
    """
    Validate mobile number format (E.164 format)
    
    Args:
        mobile_number: Mobile number string (should start with +)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not mobile_number or not isinstance(mobile_number, str):
        return False, "Mobile number is required"
    
    if not mobile_number.startswith('+'):
        return False, "Mobile number must start with + (E.164 format: +country_code_number)"
    
    # Remove + and check if remaining is digits
    digits = mobile_number[1:]
    if not digits.isdigit():
        return False, "Mobile number must contain only digits after +"
    
    if len(digits) < 10 or len(digits) > 15:
        return False, "Mobile number must be 10-15 digits (including country code)"
    
    return True, None

def sanitize_string(value, max_length=200):
    """
    Sanitize string input
    
    Args:
        value: Input string
        max_length: Maximum allowed length
    
    Returns:
        str: Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove dangerous characters
    value = value.strip()
    value = re.sub(r'[<>"\']', '', value)
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value

def validate_time_range(hours):
    """
    Validate time range parameter
    
    Args:
        hours: Number of hours
    
    Returns:
        tuple: (is_valid, error_message, converted_value)
    """
    try:
        hours = int(hours)
        if hours < 1:
            return False, "Time range must be at least 1 hour", None
        if hours > 8760:  # 1 year
            return False, "Time range cannot exceed 1 year (8760 hours)", None
        return True, None, hours
    except (ValueError, TypeError):
        return False, "Time range must be a valid number", None

def validate_aqi_threshold(value):
    """
    Validate AQI threshold value
    
    Args:
        value: AQI threshold
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        value = float(value)
        if value < 0 or value > 500:
            return False, "AQI threshold must be between 0 and 500"
        return True, None
    except (ValueError, TypeError):
        return False, "AQI threshold must be a valid number"
