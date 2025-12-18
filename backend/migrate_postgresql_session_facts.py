"""
PostgreSQL Migration: Add session_facts column to AgentMemory
Run this on Render.com Shell or via psql
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlmodel import Session

def migrate_session_facts_postgresql():
    """Add session_facts column to agentmemory table on PostgreSQL"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("[ERROR] DATABASE_URL environment variable not set!")
        print("This script must be run on Render.com with DATABASE_URL configured.")
        sys.exit(1)
    
    # Fix for Render's postgres:// URL (SQLAlchemy needs postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"[*] Connecting to PostgreSQL database...")
    print(f"    Host: {database_url.split('@')[-1].split('/')[0] if '@' in database_url else 'hidden'}")
    
    engine = create_engine(database_url)
    
    with Session(engine) as session:
        try:
            # Check if column already exists
            print("[*] Checking if 'session_facts' column exists...")
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='agentmemory' AND column_name='session_facts'
            """)
            
            result = session.exec(check_query).all()
            
            if len(result) > 0:
                print("[OK] Column 'session_facts' already exists. Migration not needed.")
                return
            
            # Add the column
            print("[+] Adding 'session_facts' column to agentmemory table...")
            alter_query = text("ALTER TABLE agentmemory ADD COLUMN session_facts TEXT")
            session.exec(alter_query)
            session.commit()
            
            # Initialize existing records with empty JSON object
            print("[+] Initializing existing records with empty session facts...")
            update_query = text("UPDATE agentmemory SET session_facts = '{}' WHERE session_facts IS NULL")
            session.exec(update_query)
            session.commit()
            
            print("[OK] Migration completed successfully!")
            print("   - Added 'session_facts' column (TEXT)")
            print("   - Initialized existing records with '{}'")
            print("   - Preserved all existing 'user_facts' data")
            print("\n[SUCCESS] Your backend should now work correctly!")
            
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    print("="*60)
    print("PostgreSQL Migration: Add session_facts Column")
    print("="*60)
    migrate_session_facts_postgresql()
