"""
Reset Admin Credentials Script
Run this to set admin credentials to: admin / Admin@123
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'src' / 'backend'
sys.path.insert(0, str(backend_path))

from core.app import app, db
from models.database import User
from sqlalchemy import text

NEW_USERNAME = 'admin'
NEW_PASSWORD = 'Admin@123'

def reset_admin_credentials():
    """Delete existing admin(s) and create a fresh admin account."""
    with app.app_context():
        # Remove all existing admin users
        existing_admins = User.query.filter_by(role='admin').all()
        if existing_admins:
            admin_ids = [u.id for u in existing_admins]
            # Delete login_history rows first (NOT NULL constraint)
            for uid in admin_ids:
                db.session.execute(text("DELETE FROM login_history WHERE user_id = :uid"), {"uid": uid})
            db.session.commit()
            for u in existing_admins:
                db.session.delete(u)
            db.session.commit()
            print(f"✓ Removed {len(existing_admins)} existing admin account(s)")

        # Create new admin
        admin = User(
            username=NEW_USERNAME,
            mobile_number='+11234567890',
            email='admin@iot.local',
            full_name='System Administrator',
            role='admin',
            is_active=True,
            mobile_verified=True,
            notification_preference='sms'
        )
        admin.set_password(NEW_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print("✓ Created new admin user")

        print("\n" + "="*50)
        print("Admin Credentials Set Successfully")
        print("="*50)
        print(f"Username: {NEW_USERNAME}")
        print(f"Password: {NEW_PASSWORD}")
        print(f"Role: {admin.role}")
        print(f"Email: {admin.email}")
        print(f"Mobile: {admin.mobile_number}")
        print("="*50)
        print("\nYou can now login at: http://localhost:5000")
        print("\n")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Resetting Admin Credentials")
    print("="*50 + "\n")
    
    try:
        reset_admin_credentials()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
