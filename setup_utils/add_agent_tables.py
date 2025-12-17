"""
Database Migration: Add Agentic AI Tables
Adds AgentMemory, AgentAction, and TaskPlan tables for autonomous AI agent capabilities
"""
import sqlite3
from datetime import datetime

def migrate():
    """Add agentic AI tables to database"""
    conn = sqlite3.connect('backend/edulife.db')
    cursor = conn.cursor()
    
    print("[AGENTIC AI] Adding agent tables...")
    
    try:
        # 1. AgentMemory table
        print("Creating agentmemory table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agentmemory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                learning_style TEXT,
                effective_strategies TEXT,
                ineffective_strategies TEXT,
                topics_to_revisit TEXT,
                mastered_topics TEXT,
                current_focus_topics TEXT,
                last_interaction TIMESTAMP,
                interaction_count INTEGER DEFAULT 0,
                agent_goals TEXT,
                progress_milestones TEXT,
                preferred_examples TEXT,
                optimal_session_length INTEGER,
                best_time_of_day TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES student(id)
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agentmemory_student 
            ON agentmemory(student_id)
        """)
        
        # 2. AgentAction table
        print("Creating agentaction table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agentaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_data TEXT,
                reasoning TEXT,
                outcome TEXT,
                student_response TEXT,
                effectiveness_score REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context TEXT,
                FOREIGN KEY (student_id) REFERENCES student(id)
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agentaction_student 
            ON agentaction(student_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agentaction_type 
            ON agentaction(action_type)
        """)
        
        # 3. TaskPlan table
        print("Creating taskplan table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS taskplan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                goal TEXT NOT NULL,
                plan_type TEXT NOT NULL,
                steps TEXT NOT NULL,
                current_step INTEGER DEFAULT 0,
                completed_steps TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deadline TIMESTAMP,
                completed_at TIMESTAMP,
                adjustments_made TEXT,
                success_rate REAL,
                FOREIGN KEY (student_id) REFERENCES student(id)
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_taskplan_student 
            ON taskplan(student_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_taskplan_status 
            ON taskplan(status)
        """)
        
        conn.commit()
        print("[SUCCESS] Agentic AI tables created successfully!")
        
        # Verify tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('agentmemory', 'agentaction', 'taskplan')
        """)
        tables = cursor.fetchall()
        print(f"[VERIFIED] Tables: {[t[0] for t in tables]}")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("AGENTIC AI DATABASE MIGRATION")
    print("=" * 60)
    migrate()
    print("\n[SUCCESS] Migration complete! Agentic AI features are now enabled.")
    print("\nNew tables:")
    print("  - agentmemory: Persistent agent memory for each student")
    print("  - agentaction: Log of autonomous agent actions")
    print("  - taskplan: Multi-step plans created by agent")
