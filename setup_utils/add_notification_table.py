"""
Database Migration: Add AgentNotification Table
Enables agents to send notifications to students
"""
import sqlite3
from datetime import datetime

def migrate():
    """Add agentnotification table to database"""
    conn = sqlite3.connect('backend/edulife.db')
    cursor = conn.cursor()
    
    print("[NOTIFICATION SYSTEM] Adding agentnotification table...")
    
    try:
        # Create AgentNotification table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agentnotification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                action_url TEXT,
                action_data TEXT,
                is_read BOOLEAN DEFAULT 0,
                read_at TIMESTAMP,
                priority TEXT DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES student(id)
            )
        """)
        
        # Create indexes for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agentnotification_student 
            ON agentnotification(student_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agentnotification_read 
            ON agentnotification(is_read)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agentnotification_type 
            ON agentnotification(notification_type)
        """)
        
        conn.commit()
        print("[SUCCESS] AgentNotification table created successfully!")
        
        # Verify table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='agentnotification'
        """)
        table = cursor.fetchone()
        print(f"[VERIFIED] Table: {table[0] if table else 'NOT FOUND'}")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("AGENT NOTIFICATION SYSTEM MIGRATION")
    print("=" * 60)
    migrate()
    print("\n[SUCCESS] Migration complete! Agents can now send notifications.")
    print("\nNotification types:")
    print("  - quiz_ready: Quiz is ready to take")
    print("  - check_in: Proactive check-in message")
    print("  - study_reminder: Time to study reminder")
    print("  - achievement: Milestone or achievement")
    print("  - plan_update: Study plan update")
