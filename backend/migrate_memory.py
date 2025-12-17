import sqlite3
import os

# Database file path
DB_FILE = "database.db"

def migrate():
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found!")
        return

    print(f"Migrating {DB_FILE}...")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(agentmemory)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "user_facts" not in columns:
            print("  Adding 'user_facts' column to table 'agentmemory'...")
            cursor.execute("ALTER TABLE agentmemory ADD COLUMN user_facts TEXT")
            print("  Column added successfully.")
        else:
            print("  Column 'user_facts' already exists.")
            
        conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
