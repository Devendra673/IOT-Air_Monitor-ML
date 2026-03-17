"""
Logging Configuration for IoT AQI Monitoring System
Provides structured logging with file rotation and different log levels
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

# Create logs directory
# logger.py is in src/backend/utils/, go up 4 levels to project root
LOGS_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name='iot_aqi', level=logging.INFO):
    """
    Setup structured logging with file rotation
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler - General log (rotating, 10MB max, keep 5 backups)
    general_log = LOGS_DIR / 'app.log'
    file_handler = logging.handlers.RotatingFileHandler(
        general_log,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # File handler - Error log (rotating, 10MB max, keep 10 backups)
    error_log = LOGS_DIR / 'error.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_log,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # File handler - Audit log (time-rotating, daily, keep 90 days)
    audit_log = LOGS_DIR / 'audit.log'
    audit_handler = logging.handlers.TimedRotatingFileHandler(
        audit_log,
        when='midnight',
        interval=1,
        backupCount=90,
        encoding='utf-8'
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(detailed_formatter)
    # Add separate audit logger
    audit_logger = logging.getLogger(f'{name}.audit')
    audit_logger.addHandler(audit_handler)
    
    logger.info(f"Logger '{name}' initialized | Level: {logging.getLevelName(level)}")
    
    return logger

def log_api_call(logger, endpoint, method, user=None, status=None, duration=None):
    """Log API call with details"""
    user_info = user if user else "Anonymous"
    status_info = f"Status: {status}" if status else ""
    duration_info = f"Duration: {duration:.2f}s" if duration else ""
    logger.info(f"API Call | {method} {endpoint} | User: {user_info} | {status_info} | {duration_info}")

def log_audit(logger, action, user, details=None):
    """Log audit trail for user actions"""
    audit_logger = logging.getLogger(f'{logger.name}.audit')
    details_str = f" | Details: {details}" if details else ""
    audit_logger.info(f"AUDIT | User: {user} | Action: {action}{details_str}")

def log_error_with_context(logger, error, context=None):
    """Log error with additional context"""
    context_str = f" | Context: {context}" if context else ""
    logger.error(f"ERROR | {type(error).__name__}: {str(error)}{context_str}", exc_info=True)
