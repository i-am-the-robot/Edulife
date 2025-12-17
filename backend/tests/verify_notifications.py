import sys
import os

# Add backend directory to path (parent of this file's directory)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, SQLModel
try:
    from database import create_db_and_tables
    from models import User, Student, TeacherNotification, PersonalityType, UserRole
    from notification_service import NotificationService
except ImportError as e:
    print(f"Import Error: {e}")
    # Fallback if needed, though adding parent to path should work
    from backend.database import create_db_and_tables
    from backend.models import User, Student, TeacherNotification, PersonalityType, UserRole
    from backend.notification_service import NotificationService
from datetime import datetime, timezone

# Override engine to use edulife.db from backend directory
from sqlmodel import create_engine, text
import os

# Get absolute path to root/database.db
# __file__ is backend/tests/verify_notifications.py
# dirname is backend/tests
# dirname of dirname is backend/
# database.db is in backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
DB_PATH = os.path.join(BASE_DIR, "database.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

print(f"Using Database: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def run_verification():
    print("=== STARTING VERIFICATION ===")
    
    print("1. Initializing DB (Updating Schema)...")
    # Use our local engine to create tables in the correct DB
    SQLModel.metadata.create_all(engine)
    print("   -> Schema checked.")

    # Check tables
    with Session(engine) as session:
        try:
            tables = session.exec(text("SELECT name FROM sqlite_master WHERE type='table';")).all()
            print(f"   -> Tables found: {tables}")
        except Exception as e:
            print(f"   -> Error listing tables: {e}")
    
    with Session(engine) as session:
        print("\n2. Finding a test context (Teacher & Student)...")
        
        # Cleanup potential dirty data for test users
        try:
             session.exec(text("DELETE FROM user WHERE email='test_teacher@edulife.com'"))
             session.exec(text("DELETE FROM user WHERE email='test_student@edulife.com'"))
             session.commit()
             print("   -> Cleaned up old test users.")
        except Exception:
             pass

        # Create Test Teacher
        print("   -> Creating TEST TEACHER...")
        teacher = User(
            email="test_teacher@edulife.com",
            full_name="Test Teacher",
            hashed_password="hashed_secret",
            role="TEACHER",
            phone="1234567890",
            address="123 Test St",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        session.add(teacher)
        session.commit()
        session.refresh(teacher)
        print(f"   -> Using Teacher: {teacher.full_name} (ID: {teacher.id})")
        
        # Create Test Student
        print("   -> Creating TEST STUDENT...")
        # Check if student exists (by ID or name)
        student = session.exec(select(Student).where(Student.full_name == "Test Student")).first()
        
        if not student:
             student = Student(
                 id=f"TEST_STUDENT_{int(datetime.utcnow().timestamp())}",
                 full_name="Test Student",
                 age=10,
                 student_class="5th Grade",
                 grade="5", # keeping both just in case
                 hobby="Coding",
                 disability_type="None",
                 personality=PersonalityType.INTROVERT,
                 created_by_user_id=teacher.id,
                 assigned_teacher_id=teacher.id,
                 school_id=None 
             )
             session.add(student)
             session.commit()
             session.refresh(student)
             print(f"      -> Created Student ID: {student.id}")
        else:
             print(f"      -> Found existing Student ID: {student.id}")
            
        print(f"   -> Using Student: {student.full_name} (ID: {student.id})")
        
        # Ensure student is assigned to teacher for notifications
        if student.assigned_teacher_id != teacher.id:
            student.assigned_teacher_id = teacher.id
            session.add(student)
            session.commit()
            print("   -> Linked student to teacher.")
        
        # Temporarily link student to teacher for the test if not already
        original_creator = student.created_by_user_id
        is_temp_link = False
        
        if student.created_by_user_id != teacher.id:
            print("   -> Linking student to teacher temporarily for test...")
            student.created_by_user_id = teacher.id
            session.add(student)
            session.commit()
            session.refresh(student)
            is_temp_link = True
            
        print("\n3. Testing Notification Creation...")
        try:
            NotificationService.notify_teacher(
                session, 
                student.id, 
                "VERIFICATION_TEST", 
                "This is a test notification generated by the verification script.", 
                "success", 
                "system"
            )
            print("   -> NotificationService.notify_teacher called successfully.")
        except Exception as e:
            print(f"   -> FAILED to create notification: {e}")
            import traceback
            traceback.print_exc()
            return
            
        print("\n4. Verifying Notification Persistence...")
        notifs = NotificationService.get_teacher_notifications(session, teacher.id)
        test_notif = None
        
        print(f"   -> Found {len(notifs)} notifications for teacher.")
        for n in notifs:
            # print(f"      - {n.title}: {n.message}")
            if n.title == "VERIFICATION_TEST":
                test_notif = n
                break
                
        if test_notif:
            print("   -> SUCCESS: Test notification found in database.")
        else:
            print("   -> FAILURE: Test notification NOT found.")
            return

        print("\n5. Testing Mark-as-Read...")
        if not test_notif.is_read:
            test_notif.is_read = True
            session.add(test_notif)
            session.commit()
            session.refresh(test_notif)
            
            if test_notif.is_read:
                 print("   -> SUCCESS: Notification marked as read.")
            else:
                 print("   -> FAILURE: Notification failed to update.")
        else:
            print("   -> Notification was already read (unexpected for new test).")

        print("\n6. Cleaning up...")
        session.delete(test_notif)
        
        if is_temp_link:
            student.created_by_user_id = original_creator
            session.add(student)
            print("   -> Restored student ownership.")
            
        session.commit()
        print("   -> Verification artifacts cleaned up.")
        
    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    run_verification()
