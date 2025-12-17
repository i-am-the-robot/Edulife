"""
Database Migration: Add Timetable Table
Adds a table to store automatically generated student schedules.
"""
import sqlite3
import os

def migrate():
    """Add timetable table to database"""
    # Adjust path to point to root database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")
    
    print(f"[TIMETABLE] Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Creating timetable table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                day_of_week TEXT NOT NULL, -- Monday, Tuesday...
                start_time TEXT NOT NULL, -- "16:00"
                end_time TEXT NOT NULL,   -- "17:00"
                subject TEXT,
                focus_topic TEXT,
                description TEXT,
                activity_type TEXT DEFAULT 'study', -- study, quiz, break
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES student(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timetable_student 
            ON timetable(student_id)
        """)
        
        conn.commit()
        print("[SUCCESS] Timetable table created successfully!")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
