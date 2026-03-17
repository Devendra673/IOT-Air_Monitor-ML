"""
Scheduled Tasks for IoT AQI Monitoring System
Handles automated cleanup, backups, and maintenance
"""

from datetime import datetime, timedelta
from pathlib import Path
import threading
import time

class ScheduledTasks:
    """Manager for scheduled background tasks"""
    
    def __init__(self, db, backup_manager, logger):
        """
        Initialize scheduled tasks
        
        Args:
            db: SQLAlchemy database instance
            backup_manager: DatabaseBackup instance
            logger: Logger instance
        """
        self.db = db
        self.backup_manager = backup_manager
        self.logger = logger
        self.running = False
        self.thread = None
    
    def start(self):
        """Start background task scheduler"""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        self.logger.info("Scheduled tasks started")
    
    def stop(self):
        """Stop background task scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("Scheduled tasks stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        last_cleanup = None
        last_backup = None
        last_vacuum = None
        
        while self.running:
            current_time = datetime.now()
            current_hour = current_time.hour
            
            # Daily cleanup at 1 AM
            if current_hour == 1 and (last_cleanup is None or (current_time - last_cleanup).days >= 1):
                try:
                    self.cleanup_old_data()
                    last_cleanup = current_time
                except Exception as e:
                    self.logger.error(f"Cleanup task failed: {e}")
            
            # Daily backup at 2 AM
            if current_hour == 2 and (last_backup is None or (current_time - last_backup).days >= 1):
                try:
                    self.create_backup()
                    last_backup = current_time
                except Exception as e:
                    self.logger.error(f"Backup task failed: {e}")
            
            # Weekly database vacuum at 3 AM on Sundays
            if current_time.weekday() == 6 and current_hour == 3 and (last_vacuum is None or (current_time - last_vacuum).days >= 7):
                try:
                    self.vacuum_database()
                    last_vacuum = current_time
                except Exception as e:
                    self.logger.error(f"Vacuum task failed: {e}")
            
            # Sleep for 1 hour
            time.sleep(3600)
    
    def cleanup_old_data(self):
        """Remove old data based on retention settings"""
        from database import Reading, Alert, Settings
        
        self.logger.info("Starting data cleanup task")
        
        # Get retention setting
        retention_days = 365  # Default
        try:
            setting = Settings.query.filter_by(key='data_retention_days').first()
            if setting:
                retention_days = int(setting.value)
        except Exception as e:
            self.logger.warning(f"Could not get retention setting: {e}")
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Delete old readings
        try:
            deleted_readings = Reading.query.filter(Reading.timestamp < cutoff_date).delete()
            self.logger.info(f"Deleted {deleted_readings} old readings")
        except Exception as e:
            self.logger.error(f"Failed to delete old readings: {e}")
        
        # Delete acknowledged alerts older than 90 days
        alert_cutoff = datetime.utcnow() - timedelta(days=90)
        try:
            deleted_alerts = Alert.query.filter(
                Alert.timestamp < alert_cutoff,
                Alert.acknowledged == True
            ).delete()
            self.logger.info(f"Deleted {deleted_alerts} old acknowledged alerts")
        except Exception as e:
            self.logger.error(f"Failed to delete old alerts: {e}")
        
        # Commit changes
        try:
            self.db.session.commit()
            self.logger.info("Data cleanup completed successfully")
        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Failed to commit cleanup changes: {e}")
    
    def create_backup(self):
        """Create automated database backup"""
        self.logger.info("Starting automated backup")
        
        try:
            backup_path = self.backup_manager.create_backup(compress=True)
            self.logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None
    
    def vacuum_database(self):
        """Vacuum database to optimize and reclaim space"""
        self.logger.info("Starting database vacuum")
        
        try:
            result = self.backup_manager.vacuum_database()
            self.logger.info(f"Vacuum completed: Saved {result['saved_mb']} MB")
            return result
        except Exception as e:
            self.logger.error(f"Vacuum failed: {e}")
            return None
    
    def cleanup_old_sessions(self, max_age_days=7):
        """Clean up old Flask session files"""
        self.logger.info("Cleaning up old session files")
        
        session_dir = Path(__file__).parent / 'flask_session'
        if not session_dir.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cleaned = 0
        
        try:
            for session_file in session_dir.iterdir():
                if session_file.is_file():
                    file_time = datetime.fromtimestamp(session_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        session_file.unlink()
                        cleaned += 1
            
            self.logger.info(f"Cleaned {cleaned} old session files")
        except Exception as e:
            self.logger.error(f"Session cleanup failed: {e}")


def run_manual_cleanup(db, logger):
    """
    Manually trigger cleanup tasks
    
    Args:
        db: Database instance
        logger: Logger instance
    
    Returns:
        dict: Cleanup results
    """
    from database import Reading, Alert
    
    results = {
        'started': datetime.now().isoformat(),
        'tasks': []
    }
    
    # Cleanup old data
    try:
        retention_days = 365
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        deleted_readings = Reading.query.filter(Reading.timestamp < cutoff_date).delete()
        deleted_alerts = Alert.query.filter(
            Alert.timestamp < cutoff_date,
            Alert.acknowledged == True
        ).delete()
        
        db.session.commit()
        
        results['tasks'].append({
            'task': 'data_cleanup',
            'status': 'success',
            'deleted_readings': deleted_readings,
            'deleted_alerts': deleted_alerts
        })
        
        logger.info(f"Manual cleanup: {deleted_readings} readings, {deleted_alerts} alerts")
        
    except Exception as e:
        db.session.rollback()
        results['tasks'].append({
            'task': 'data_cleanup',
            'status': 'failed',
            'error': str(e)
        })
        logger.error(f"Manual cleanup failed: {e}")
    
    results['completed'] = datetime.now().isoformat()
    return results
