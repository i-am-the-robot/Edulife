
import os
import sqlalchemy
from sqlalchemy import create_engine, text

# Get Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not found.")
        return

    print("Starting PostgreSQL Migration...")
    
    # Fix for sqlalchemy-postgres connection string if needed
    db_url = DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            # Commit any pending transaction
            conn.commit()
            
            # Check if column exists
            print("Checking for 'user_facts' column in 'agentmemory'...")
            try:
                # Try to select the column to see if it exists
                conn.execute(text("SELECT user_facts FROM agentmemory LIMIT 1"))
                print("  Column 'user_facts' already exists. No action needed.")
            except Exception:
                # Column doesn't exist, so add it
                print("  Column not found. Adding 'user_facts'...")
                # Start new transaction for ALTER
                with conn.begin():
                    conn.execute(text("ALTER TABLE agentmemory ADD COLUMN user_facts TEXT"))
                print("  SUCCESS: Column 'user_facts' added.")

    except Exception as e:
        print(f"Migration FAILED: {e}")

if __name__ == "__main__":
    migrate()
