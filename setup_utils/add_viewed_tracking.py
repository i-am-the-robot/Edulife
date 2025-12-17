"""
Add viewed_by_teacher tracking to AssignmentStudySession
"""
import sqlite3
import os

db_path = 'database.db'

print("=" * 60)
print("DATABASE MIGRATION - Add Assignment Viewing Tracking")
print("=" * 60)
print(f"\nDatabase: {os.path.abspath(db_path)}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(assignmentstudysession)")
    columns = [col[1] for col in cursor.fetchall()]
    
    columns_added = []
    
    if 'viewed_by_teacher' not in columns:
        cursor.execute("ALTER TABLE assignmentstudysession ADD COLUMN viewed_by_teacher BOOLEAN DEFAULT 0")
        columns_added.append('viewed_by_teacher')
    
    if 'viewed_at' not in columns:
        cursor.execute("ALTER TABLE assignmentstudysession ADD COLUMN viewed_at DATETIME")
        columns_added.append('viewed_at')
    
    conn.commit()
    
    if columns_added:
        print(f"\n[OK] Added {len(columns_added)} columns:")
        for col in columns_added:
            print(f"  - {col}")
    else:
        print("\n[i] All columns already exist")
    
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()
