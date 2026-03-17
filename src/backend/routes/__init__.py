"""
Routes package - Modular API endpoints
All routes are organized into logical blueprints
"""

from flask import Blueprint

def register_routes(app, auth_service, mobile_notification, backup_manager, logger):
    """
    Register all route blueprints with the Flask app
    
    Args:
        app: Flask application instance
        auth_service: EnhancedAuthenticationService instance
        mobile_notification: MobileNotificationService instance  
        backup_manager: DatabaseBackup instance
        logger: Application logger
    """
    # Import blueprints
    from .auth_routes import create_auth_blueprint
    from .device_routes import create_device_blueprint
    from .reading_routes import create_reading_blueprint
    from .alert_routes import create_alert_blueprint
    from .admin_routes import create_admin_blueprint
    from .dashboard_routes import create_dashboard_blueprint
    from .settings_routes import create_settings_blueprint
    
    # Create blueprint instances with dependencies
    auth_bp = create_auth_blueprint(auth_service, logger)
    device_bp = create_device_blueprint(logger)
    reading_bp = create_reading_blueprint(logger)
    alert_bp = create_alert_blueprint(logger)
    admin_bp = create_admin_blueprint(backup_manager, logger)
    dashboard_bp = create_dashboard_blueprint(logger)
    settings_bp = create_settings_blueprint(logger)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(device_bp, url_prefix='/api/devices')
    app.register_blueprint(reading_bp, url_prefix='/api')
    app.register_blueprint(alert_bp, url_prefix='/api/alerts')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
    # Log successful registration
    logger.info("✅ All route blueprints registered successfully")
