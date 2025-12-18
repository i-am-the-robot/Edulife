"""
Database Migration: Add session_facts column to AgentMemory
This enables session-scoped memory management while preserving permanent facts
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlmodel import Session

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate_session_memory():
    """Add session_facts column to agentmemory table"""
    
    # Determine database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Local SQLite
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")
        database_url = f"sqlite:///{db_path}"
    
    print(f"[*] Connecting to database: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    engine = create_engine(database_url)
    
    with Session(engine) as session:
        try:
            # Check if column already exists
            if "postgresql" in database_url:
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='agentmemory' AND column_name='session_facts'
                """)
            else:
                check_query = text("PRAGMA table_info(agentmemory)")
            
            result = session.exec(check_query).all()
            
            # For SQLite, check if session_facts is in the column list
            if "sqlite" in database_url:
                columns = [row[1] for row in result]  # Column name is at index 1
                column_exists = "session_facts" in columns
            else:
                column_exists = len(result) > 0
            
            if column_exists:
                print("[OK] Column 'session_facts' already exists. Skipping migration.")
                return
            
            # Add the column
            print("[+] Adding 'session_facts' column to agentmemory table...")
            
            if "postgresql" in database_url:
                alter_query = text("ALTER TABLE agentmemory ADD COLUMN session_facts TEXT")
            else:
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
            
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    migrate_session_memory()
