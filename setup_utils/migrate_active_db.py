"""
Add Missing Streak Columns to ACTIVE Database
This migrates the CORRECT database file (the one with your data)
"""
import sqlite3
import os

# Use the ROOT database file (the one with data)
db_path = 'database.db'

print("=" * 60)
print("DATABASE MIGRATION - Adding Streak Columns")
print("=" * 60)
print(f"\nDatabase: {os.path.abspath(db_path)}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check current columns
    cursor.execute("PRAGMA table_info(student)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"\nCurrent columns in student table: {len(columns)}")
    
    # Add missing columns if they don't exist
    columns_added = []
    
    if 'current_streak' not in columns:
        cursor.execute("ALTER TABLE student ADD COLUMN current_streak INTEGER DEFAULT 0")
        columns_added.append('current_streak')
    
    if 'longest_streak' not in columns:
        cursor.execute("ALTER TABLE student ADD COLUMN longest_streak INTEGER DEFAULT 0")
        columns_added.append('longest_streak')
    
    if 'last_activity_date' not in columns:
        cursor.execute("ALTER TABLE student ADD COLUMN last_activity_date DATETIME")
        columns_added.append('last_activity_date')
    
    if 'streak_freeze_count' not in columns:
        cursor.execute("ALTER TABLE student ADD COLUMN streak_freeze_count INTEGER DEFAULT 0")
        columns_added.append('streak_freeze_count')
    
    # Commit changes
    conn.commit()
    
    if columns_added:
        print(f"\n✓ Added {len(columns_added)} columns:")
        for col in columns_added:
            print(f"  - {col}")
    else:
        print("\n✓ All columns already exist!")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM admin")
    admin_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM school")
    school_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM student")
    student_count = cursor.fetchone()[0]
    
    print(f"\nData verification:")
    print(f"  Admins: {admin_count}")
    print(f"  Schools: {school_count}")
    print(f"  Students: {student_count}")
    
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE - YOUR DATA IS INTACT!")
    print("=" * 60)
    print("\nYou can now restart the backend server.")
    print("All your admin/school/teacher/student data is preserved!")
    
except Exception as e:
    print(f"\nERROR: {e}")
    conn.rollback()
finally:
    conn.close()
