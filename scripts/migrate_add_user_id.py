"""
Migration script to add user_id to existing ProcessedMedia records.

This script:
1. Creates a default admin user if none exists
2. Assigns all existing ProcessedMedia records to that admin user
3. Handles the case where user_id column might not exist yet

Run this after adding authentication to your existing database.
"""

import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backend.db import SessionLocal, init_db, engine
from src.backend.models import User, ProcessedMedia, Base
from src.backend.auth import get_password_hash
from sqlalchemy import inspect


def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate():
    """Run the migration."""
    print("Starting migration...")
    
    # Initialize database (creates tables if they don't exist)
    init_db()
    
    db = SessionLocal()
    try:
        # Check if user_id column exists in processed_media
        if not check_column_exists('processed_media', 'user_id'):
            print("⚠️  user_id column doesn't exist yet.")
            print("   The column will be created when you restart the server.")
            print("   Run this script again after restarting.")
            return
        
        # Create a default admin user
        admin_email = "admin@example.com"
        admin_password = "changeme123"  # ⚠️ CHANGE THIS IN PRODUCTION!
        
        existing_user = db.query(User).filter(User.email == admin_email).first()
        if not existing_user:
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"✅ Created admin user: {admin_email}")
            print(f"   Password: {admin_password}")
            print(f"   ⚠️  Please change this password after first login!")
        else:
            admin_user = existing_user
            print(f"✅ Using existing admin user: {admin_email}")
        
        # Count media without user_id
        media_without_user = db.query(ProcessedMedia).filter(
            ProcessedMedia.user_id.is_(None)
        ).all()
        
        if media_without_user:
            print(f"\n📦 Found {len(media_without_user)} media files without user_id")
            
            # Assign all existing media to admin user
            for media in media_without_user:
                media.user_id = admin_user.id
            
            db.commit()
            print(f"✅ Assigned {len(media_without_user)} media files to admin user")
        else:
            print("\n✅ No media files need migration")
        
        # Verify migration
        total_media = db.query(ProcessedMedia).count()
        media_with_user = db.query(ProcessedMedia).filter(
            ProcessedMedia.user_id.isnot(None)
        ).count()
        
        print(f"\n📊 Migration Summary:")
        print(f"   Total media files: {total_media}")
        print(f"   Media with user_id: {media_with_user}")
        print(f"   Media without user_id: {total_media - media_with_user}")
        
        if total_media - media_with_user == 0:
            print("\n✅ Migration completed successfully!")
        else:
            print(f"\n⚠️  {total_media - media_with_user} media files still need user_id")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

