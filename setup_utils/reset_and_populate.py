"""
Reset and Populate Database (Idempotent)
Checks if data exists before creating to avoid Unique Constraint errors.
"""
from sqlmodel import Session, select
from backend.models import *
from backend.database import engine, create_db_and_tables
from backend.auth import get_password_hash
from datetime import datetime, timedelta

def main():
    print("Initializing database tables...")
    create_db_and_tables()
    
    with Session(engine) as session:
        # 1. Admin
        print("Checking Admin...")
        admin = session.exec(select(Admin).where(Admin.email == "admin@edulife.com")).first()
        if not admin:
            admin = Admin(
                email="admin@edulife.com",
                hashed_password=get_password_hash("admin123"),
                full_name="System Admin",
                role=UserRole.ADMIN
            )
            session.add(admin)
            session.commit()
            print("[OK] Admin created")
        else:
            print("[SKIP] Admin already exists")
            
        # 2. School
        print("Checking School...")
        school = session.exec(select(School).where(School.app_key == "GW123")).first()
        if not school:
            school = School(
                name="Greenwood High",
                address="123 Education Lane",
                contact_email="contact@greenwood.edu",
                app_key="GW123"
            )
            session.add(school)
            session.commit()
            # Need to refresh to get ID
            session.refresh(school)
            print("[OK] School created")
        else:
            print("[SKIP] School already exists")
            
        # 3. Teacher
        print("Checking Teacher...")
        teacher = session.exec(select(User).where(User.email == "teacher@edulife.com")).first()
        if not teacher:
            teacher = User(
                email="teacher@edulife.com",
                hashed_password=get_password_hash("teacher123"),
                full_name="Mr. Anderson",
                role=UserRole.TEACHER,
                school_id=school.id,
                subject_specialization="Mathematics",
                address="123 Teacher Lane",
                phone="555-0123"
            )
            session.add(teacher)
            session.commit()
            print("[OK] Teacher created")
        else:
            print("[SKIP] Teacher already exists")
            
        # 4. Student
        print("Checking Student...")
        # Since ID is timestamp-based, we hardcode a specific ID for testing to verify existence
        test_student_id = f"{school.id}_student_alex"
        student = session.get(Student, test_student_id)
        
        if not student:
            student = Student(
                id=test_student_id,
                full_name="Alex Student",
                pin="1234", # Simple PIN
                age=15,
                student_class="Grade 10",
                hobby="Gaming",
                school_id=school.id,
                learning_style=LearningProfile.STANDARD,
                personality=PersonalityType.INTROVERT,
                support_needs=SupportType.NONE
            )
            session.add(student)
            session.commit()
            session.refresh(student)
            print(f"[OK] Student created (ID: {test_student_id} / PIN: 1234)")
        else:
            print(f"[SKIP] Student already exists (ID: {test_student_id})")
        
        # 5. Task
        print("Checking Task...")
        # Check if this student has any tasks
        task = session.exec(select(Task).where(Task.student_id == student.id)).first()
        if not task:
            task = Task(
                title="Algebra Basics",
                description="Learn about variables and equations",
                due_date=datetime.utcnow() + timedelta(days=7),
                teacher_id=teacher.id if teacher else 1, # Fallback if teacher skipped but ID needed
                student_id=student.id,
                status="pending"
            )
            session.add(task)
            session.commit()
            print("[OK] Task created")
            print(f"[SKIP] Task already exists: {task.title}")
            # Ensure we have task ID if it was skipped
            task_id = task.id
        
    # Save credentials for test script
    import json
    credentials = {
        "student_id": test_student_id,
        "pin": "1234",
        "task_id": task.id if 'task' in locals() else 1
    }
    
    with open("test_credentials.json", "w") as f:
        json.dump(credentials, f)
        
    print("\nDatabase check/population complete! Credentials saved to test_credentials.json")

if __name__ == "__main__":
    main()
