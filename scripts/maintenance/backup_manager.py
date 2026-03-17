"""
Database Backup and Restore Utilities
Provides automated backup with rotation and restore functionality
"""

import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json
import gzip

BACKUP_DIR = Path(__file__).parent.parent.parent / 'data' / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

class DatabaseBackup:
    """Handle database backup and restore operations"""
    
    def __init__(self, db_path, max_backups=30):
        """
        Initialize backup manager
        
        Args:
            db_path: Path to SQLite database file
            max_backups: Maximum number of backups to keep
        """
        self.db_path = Path(db_path)
        self.max_backups = max_backups
    
    def create_backup(self, compress=True):
        """
        Create database backup
        
        Args:
            compress: Whether to compress backup with gzip
        
        Returns:
            Path to backup file
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"iot_data_backup_{timestamp}.db"
        
        if compress:
            backup_name += ".gz"
            backup_path = BACKUP_DIR / backup_name
            
            # Compress backup
            with open(self.db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            backup_path = BACKUP_DIR / backup_name
            shutil.copy2(self.db_path, backup_path)
        
        # Create metadata file
        metadata = {
            'created': timestamp,
            'original_size': self.db_path.stat().st_size,
            'backup_size': backup_path.stat().st_size,
            'compressed': compress,
            'database': str(self.db_path)
        }
        
        metadata_path = backup_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Cleanup old backups
        self._cleanup_old_backups()
        
        return backup_path
    
    def restore_backup(self, backup_path, create_backup_first=True):
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
            create_backup_first: Create backup of current DB before restoring
        
        Returns:
            bool: Success status
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        
        # Create backup of current database first
        if create_backup_first and self.db_path.exists():
            self.create_backup()
        
        # Restore from backup
        if backup_path.suffix == '.gz':
            # Decompress first
            with gzip.open(backup_path, 'rb') as f_in:
                with open(self.db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(backup_path, self.db_path)
        
        return True
    
    def list_backups(self):
        """
        List all available backups
        
        Returns:
            list: List of backup files with metadata
        """
        backups = []
        
        for backup_file in BACKUP_DIR.glob("iot_data_backup_*.db*"):
            if backup_file.suffix in ['.db', '.gz']:
                metadata_file = backup_file.with_suffix('.json')
                
                backup_info = {
                    'file': str(backup_file),
                    'name': backup_file.name,
                    'size': backup_file.stat().st_size,
                    'created': datetime.fromtimestamp(backup_file.stat().st_mtime)
                }
                
                # Load metadata if exists
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        backup_info['metadata'] = json.load(f)
                
                backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return backups
    
    def _cleanup_old_backups(self):
        """Remove old backups exceeding max_backups limit"""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            # Remove oldest backups
            for backup in backups[self.max_backups:]:
                backup_path = Path(backup['file'])
                metadata_path = backup_path.with_suffix('.json')
                
                backup_path.unlink(missing_ok=True)
                metadata_path.unlink(missing_ok=True)
    
    def get_database_stats(self):
        """
        Get database statistics
        
        Returns:
            dict: Database statistics
        """
        if not self.db_path.exists():
            return {'error': 'Database not found'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'file_size': self.db_path.stat().st_size,
            'file_size_mb': round(self.db_path.stat().st_size / (1024 * 1024), 2),
            'modified': datetime.fromtimestamp(self.db_path.stat().st_mtime).isoformat(),
            'tables': {}
        }
        
        # Get table statistics
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table_name, in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            stats['tables'][table_name] = {'row_count': count}
        
        conn.close()
        
        return stats
    
    def vacuum_database(self):
        """
        Vacuum database to reclaim space and optimize
        
        Returns:
            dict: Size before and after vacuum
        """
        size_before = self.db_path.stat().st_size
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("VACUUM")
        conn.close()
        
        size_after = self.db_path.stat().st_size
        
        return {
            'size_before': size_before,
            'size_after': size_after,
            'saved': size_before - size_after,
            'saved_mb': round((size_before - size_after) / (1024 * 1024), 2)
        }


def auto_backup_scheduler(db_path, backup_hour=2):
    """
    Check if backup is needed (daily at specified hour)
    
    Args:
        db_path: Path to database
        backup_hour: Hour of day to perform backup (0-23)
    
    Returns:
        Path to backup file if created, None otherwise
    """
    current_hour = datetime.now().hour
    
    if current_hour != backup_hour:
        return None
    
    # Check if backup already exists for today
    today = datetime.now().strftime('%Y%m%d')
    existing_backups = list(BACKUP_DIR.glob(f"iot_data_backup_{today}_*.db*"))
    
    if existing_backups:
        return None  # Already backed up today
    
    # Create backup
    backup_manager = DatabaseBackup(db_path)
    return backup_manager.create_backup(compress=True)
