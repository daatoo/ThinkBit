"""
Quick migration script for authentication setup.

This script:
1. Creates the users table if it doesn't exist
2. Creates a default admin user
3. Assigns existing ProcessedMedia to admin user (if user_id column exists)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backend.db import SessionLocal, init_db, engine
from src.backend.models import User, ProcessedMedia, Base
from src.backend.auth import get_password_hash
from sqlalchemy import inspect, text


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate():
    """Run the migration."""
    print("=" * 60)
    print("AUTHENTICATION MIGRATION")
    print("=" * 60)
    
    # Initialize database (creates all tables)
    print("\n1. Initializing database...")
    try:
        init_db()
        print("   OK: Database initialized")
    except Exception as e:
        print(f"   WARNING: {e}")
        print("   Continuing anyway...")
    
    db = SessionLocal()
    try:
        # Check if users table exists
        if not table_exists('users'):
            print("\n2. Users table doesn't exist - will be created on server start")
            print("   ⚠️  Start the server once to create tables, then run this script again")
            return
        
        print("   ✅ Users table exists")
        
        # Create default admin user
        print("\n2. Creating admin user...")
        admin_email = "admin@example.com"
        admin_password = "admin123"  # ⚠️ CHANGE THIS!
        
        existing_user = db.query(User).filter(User.email == admin_email).first()
        if not existing_user:
            # Ensure password is not too long for bcrypt (72 bytes max)
            if len(admin_password.encode('utf-8')) > 72:
                admin_password = admin_password[:72]
            
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"   OK: Created admin user: {admin_email}")
            print(f"   WARNING: Password: {admin_password} - CHANGE THIS!")
        else:
            admin_user = existing_user
            print(f"   OK: Admin user already exists: {admin_email}")
        
        # Check if processed_media table has user_id column
        if not table_exists('processed_media'):
            print("\n3. processed_media table doesn't exist yet")
            print("   ✅ No migration needed")
            return
        
        if not column_exists('processed_media', 'user_id'):
            print("\n3. user_id column doesn't exist in processed_media")
            print("   ⚠️  The column will be created when you restart the server")
            print("   ⚠️  Run this script again after restarting")
            return
        
        print("   ✅ user_id column exists")
        
        # Migrate existing media
        print("\n3. Migrating existing media...")
        media_without_user = db.query(ProcessedMedia).filter(
            ProcessedMedia.user_id.is_(None)
        ).all()
        
        if media_without_user:
            print(f"   Found {len(media_without_user)} media files without user_id")
            for media in media_without_user:
                media.user_id = admin_user.id
            db.commit()
            print(f"   ✅ Assigned {len(media_without_user)} media files to admin user")
        else:
            print("   ✅ No media files need migration")
        
        # Summary
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        total_users = db.query(User).count()
        total_media = db.query(ProcessedMedia).count()
        media_with_user = db.query(ProcessedMedia).filter(
            ProcessedMedia.user_id.isnot(None)
        ).count()
        
        print(f"Total users: {total_users}")
        print(f"Total media: {total_media}")
        print(f"Media with user_id: {media_with_user}")
        print(f"Media without user_id: {total_media - media_with_user}")
        print("\n✅ Migration completed!")
        print("\nNext steps:")
        print("1. Set SECRET_KEY environment variable")
        print("2. Start the server: python -m src.backend.main")
        print("3. Test login at http://localhost:8080/docs")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

