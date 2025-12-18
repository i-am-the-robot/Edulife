
import os
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

    # Create engine without automatic transaction if possible, or just handle manually
    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            conn.commit() # Ensure we are not in a failed state
            
            # Check if column exists
            print("Checking for 'user_facts' column in 'agentmemory'...")
            column_exists = False
            try:
                # Try to select the column to see if it exists
                conn.execute(text("SELECT user_facts FROM agentmemory LIMIT 1"))
                print("  Column 'user_facts' already exists. No action needed.")
                column_exists = True
            except Exception:
                # IMPORTANT: If SELECT failed, the transaction is poisoned. We MUST rollback.
                print("  Column Check resulted in exception (expected if missing). Rolling back transaction...")
                conn.rollback()
                
            if not column_exists:
                print("  Adding 'user_facts'...")
                # New transaction attempt
                conn.execute(text("ALTER TABLE agentmemory ADD COLUMN user_facts TEXT"))
                conn.commit()
                print("  SUCCESS: Column 'user_facts' added.")

    except Exception as e:
        print(f"Migration FAILED: {e}")

if __name__ == "__main__":
    migrate()
