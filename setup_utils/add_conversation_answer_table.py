"""
Add ConversationAnswer table to database
"""
import sqlite3
import os

db_path = 'database.db'

print("=" * 60)
print("DATABASE MIGRATION - Add ConversationAnswer Table")
print("=" * 60)
print(f"\nDatabase: {os.path.abspath(db_path)}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversationanswer'")
    if cursor.fetchone():
        print("\n[i] ConversationAnswer table already exists")
    else:
        # Create the table
        cursor.execute("""
            CREATE TABLE conversationanswer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                chat_history_id INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                question TEXT NOT NULL,
                student_answer TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                points_awarded REAL DEFAULT 0.1,
                subject TEXT,
                topic TEXT,
                FOREIGN KEY (student_id) REFERENCES student(id),
                FOREIGN KEY (chat_history_id) REFERENCES chathistory(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX ix_conversationanswer_student_id ON conversationanswer(student_id)")
        cursor.execute("CREATE INDEX ix_conversationanswer_timestamp ON conversationanswer(timestamp)")
        
        conn.commit()
        print("\n[OK] ConversationAnswer table created successfully!")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM conversationanswer")
    count = cursor.fetchone()[0]
    print(f"\nConversation answers in DB: {count}")
    
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()
