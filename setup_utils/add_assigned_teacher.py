"""
Database Migration: Add assigned_teacher_id to Student table
Allows admins to assign teachers to students
"""
import sqlite3

def migrate():
    """Add assigned_teacher_id column to student table"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    print("[TEACHER ASSIGNMENT] Adding assigned_teacher_id field to student table...")
    
    try:
        # Add assigned_teacher_id column
        cursor.execute("""
            ALTER TABLE student 
            ADD COLUMN assigned_teacher_id INTEGER
        """)
        
        # Add foreign key constraint (SQLite doesn't enforce FK on ALTER, but we document it)
        # FOREIGN KEY (assigned_teacher_id) REFERENCES user(id)
        
        conn.commit()
        print("[SUCCESS] assigned_teacher_id field added successfully!")
        
        # Verify column exists
        cursor.execute("PRAGMA table_info(student)")
        columns = cursor.fetchall()
        assigned_teacher_exists = any(col[1] == 'assigned_teacher_id' for col in columns)
        
        if assigned_teacher_exists:
            print("[VERIFIED] assigned_teacher_id column exists in student table")
            print(f"[INFO] Total columns in student table: {len(columns)}")
        else:
            print("[WARNING] assigned_teacher_id column not found!")
        
    except sqlite3.Error as e:
        if "duplicate column name" in str(e).lower():
            print("[INFO] assigned_teacher_id column already exists")
        else:
            print(f"[ERROR] Error during migration: {e}")
            conn.rollback()
            raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("TEACHER ASSIGNMENT FIELD MIGRATION")
    print("=" * 60)
    migrate()
    print("\n[SUCCESS] Migration complete!")
    print("\nAdmins can now:")
    print("  - Assign teachers to students during registration")
    print("  - Reassign teachers as needed")
    print("  - Track which teacher manages each student")
