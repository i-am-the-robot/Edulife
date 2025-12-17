"""
Database Migration Script
Adds missing streak columns to student table
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'database.db')

print(f"Migrating database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if columns exist
    cursor.execute("PRAGMA table_info(student)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"Current columns: {columns}")
    
    # Add missing columns if they don't exist
    if 'current_streak' not in columns:
        print("Adding current_streak column...")
        cursor.execute("ALTER TABLE student ADD COLUMN current_streak INTEGER DEFAULT 0")
        print("✓ Added current_streak")
    
    if 'longest_streak' not in columns:
        print("Adding longest_streak column...")
        cursor.execute("ALTER TABLE student ADD COLUMN longest_streak INTEGER DEFAULT 0")
        print("✓ Added longest_streak")
    
    if 'last_activity_date' not in columns:
        print("Adding last_activity_date column...")
        cursor.execute("ALTER TABLE student ADD COLUMN last_activity_date DATETIME")
        print("✓ Added last_activity_date")
    
    if 'streak_freeze_count' not in columns:
        print("Adding streak_freeze_count column...")
        cursor.execute("ALTER TABLE student ADD COLUMN streak_freeze_count INTEGER DEFAULT 0")
        print("✓ Added streak_freeze_count")
    
    # Commit changes
    conn.commit()
    print("\n✅ Migration completed successfully!")
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()
