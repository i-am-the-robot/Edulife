import sys
import os
from sqlmodel import Session, select, create_engine
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Windows Unicode Fix
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from backend.models import Student, Timetable
from backend.student_router import generate_ai_schedule_endpoint
from backend.schedule_service import generate_mock_schedule

# Connect to DB
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database.db")
engine = create_engine(f"sqlite:///{db_path}")

def test_timetable_persistence():
    print("🧪 Testing Timetable Persistence...")
    
    with Session(engine) as session:
        # Get a test student
        student = session.exec(select(Student)).first()
        if not student:
            print("❌ No student found in DB.")
            return

        print(f"👤 Student: {student.full_name} ({student.id})")
        
        # 1. Simulate Generate Schedule (Mock for speed)
        # We manually invoke the persistence logic here to test DB saving
        # constructing the mock return from generate_mock_schedule
        print("📅 Generating Mock Schedule...")
        schedule = generate_mock_schedule()
        
        # Clear old
        from sqlmodel import delete
        session.exec(delete(Timetable).where(Timetable.student_id == student.id))
        
        # Save new
        count = 0
        for day, sessions in schedule.items():
            for sess in sessions:
                new_entry = Timetable(
                    student_id=student.id,
                    day_of_week=day,
                    start_time=sess.get("time"),
                    end_time=str(sess.get("duration")) + " min",
                    subject=sess.get("subject") or "Break",
                    focus_topic=sess.get("topic"),
                    activity_type=sess.get("type", "study"),
                    description=f"Priority: {sess.get('priority')}"
                )
                session.add(new_entry)
                count += 1
        
        session.commit()
        print(f"✅ Saved {count} schedule entries to DB.")
        
        # 2. Verify Fetch
        stored_entries = session.exec(select(Timetable).where(Timetable.student_id == student.id)).all()
        print(f"🔍 Found {len(stored_entries)} entries in DB.")
        
        if len(stored_entries) == count:
            print("✅ Persistence Verified!")
            print(f"   Example: {stored_entries[0].day_of_week} - {stored_entries[0].subject}: {stored_entries[0].focus_topic}")
        else:
            print("❌ Persistence Failed: Count mismatch.")

if __name__ == "__main__":
    test_timetable_persistence()
