"""
Add parent_whatsapp field to the CORRECT database (database.db)
"""
import sqlite3

def migrate():
    """Add parent_whatsapp column to student table in database.db"""
    conn = sqlite3.connect('database.db')  # Correct database!
    cursor = conn.cursor()
    
    print("[WHATSAPP] Adding parent_whatsapp field to student table...")
    print("[INFO] Using database: database.db")
    
    try:
        # Add parent_whatsapp column
        cursor.execute("""
            ALTER TABLE student 
            ADD COLUMN parent_whatsapp TEXT
        """)
        
        conn.commit()
        print("[SUCCESS] parent_whatsapp field added successfully!")
        
        # Verify column exists
        cursor.execute("PRAGMA table_info(student)")
        columns = cursor.fetchall()
        parent_whatsapp_exists = any(col[1] == 'parent_whatsapp' for col in columns)
        
        if parent_whatsapp_exists:
            print("[VERIFIED] parent_whatsapp column exists in student table")
            print(f"[INFO] Total columns in student table: {len(columns)}")
        else:
            print("[WARNING] parent_whatsapp column not found!")
        
    except sqlite3.Error as e:
        if "duplicate column name" in str(e).lower():
            print("[INFO] parent_whatsapp column already exists")
        else:
            print(f"[ERROR] Error during migration: {e}")
            conn.rollback()
            raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("PARENT WHATSAPP FIELD MIGRATION")
    print("=" * 60)
    migrate()
    print("\n[SUCCESS] Migration complete!")
    print("\nParents can now receive WhatsApp notifications about:")
    print("  - Student achievements")
    print("  - Quiz results")
    print("  - Study reminders")
    print("  - Inactivity alerts")
    print("  - Progress updates")
