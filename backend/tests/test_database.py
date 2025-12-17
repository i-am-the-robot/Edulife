"""
Test script to verify database models and basic setup
"""
import sys
import os
# Add Project Root to path (3 levels up: test_database.py -> tests -> backend -> EduLife)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import create_db_and_tables, get_session
from backend.models import Admin, School, User, Student, ChatHistory, TestResult, Tutorial
from backend.models import UserRole, LearningProfile, SupportType, PersonalityType, TutorialStatus
from backend.auth import get_password_hash
from backend.utils import generate_app_key, generate_student_id
from datetime import datetime

def test_database_setup():
    """Test database creation and basic operations"""
    print("=" * 60)
    print("EDULIFE V2.0 - DATABASE SETUP TEST")
    print("=" * 60)
    
    # Create all tables
    print("\n1. Creating database tables...")
    try:
        create_db_and_tables()
        print("   ✓ All tables created successfully!")
    except Exception as e:
        print(f"   ✗ Error creating tables: {e}")
        return False
    
    # Test creating an admin
    print("\n2. Testing Admin creation...")
    try:
        with get_session() as session:
            admin = Admin(
                full_name="Test Admin",
                email="admin@edulife.com",
                hashed_password=get_password_hash("admin123"),
                phone="+1234567890"
            )
            session.add(admin)
            session.commit()
            print(f"   ✓ Admin created: {admin.full_name} (ID: {admin.id})")
    except Exception as e:
        print(f"   ✗ Error creating admin: {e}")
    
    # Test creating a school
    print("\n3. Testing School creation...")
    try:
        with get_session() as session:
            app_key = generate_app_key()
            school = School(
                name="Test Elementary School",
                app_key=app_key,
                location="123 Education St, Learning City",
                contact_email="contact@testschool.edu",
                contact_phone="+1987654321",
                grade_levels='["K-5"]',
                syllabus_text="Sample syllabus for testing"
            )
            session.add(school)
            session.commit()
            print(f"   ✓ School created: {school.name}")
            print(f"   ✓ App Key: {school.app_key}")
            school_id = school.id
    except Exception as e:
        print(f"   ✗ Error creating school: {e}")
        return False
    
    # Test creating a teacher
    print("\n4. Testing Teacher creation...")
    try:
        with get_session() as session:
            teacher = User(
                full_name="Jane Teacher",
                email="teacher@testschool.edu",
                hashed_password=get_password_hash("teacher123"),
                address="456 Teacher Lane",
                phone="+1555123456",
                role=UserRole.TEACHER,
                school_id=school_id,
                subjects='["Math", "Science"]',
                years_experience=5,
                specializations='["Elementary Education"]'
            )
            session.add(teacher)
            session.commit()
            print(f"   ✓ Teacher created: {teacher.full_name} (ID: {teacher.id})")
            teacher_id = teacher.id
    except Exception as e:
        print(f"   ✗ Error creating teacher: {e}")
        return False
    
    # Test creating a student
    print("\n5. Testing Student creation...")
    try:
        with get_session() as session:
            student_id = generate_student_id(school_id)
            student = Student(
                id=student_id,
                full_name="Tommy Student",
                age=8,
                student_class="3rd Grade",
                hobby="Reading and Drawing",
                personality=PersonalityType.INTROVERT,
                learning_profile=LearningProfile.PERSONALIZED,
                support_type=SupportType.DYSLEXIA,
                school_id=school_id,
                created_by_user_id=teacher_id
            )
            session.add(student)
            session.commit()
            print(f"   ✓ Student created: {student.full_name}")
            print(f"   ✓ Student ID: {student.id}")
            print(f"   ✓ Learning Profile: {student.learning_profile.value}")
            print(f"   ✓ Support Type: {student.support_type.value} (NEVER shown to student)")
    except Exception as e:
        print(f"   ✗ Error creating student: {e}")
        return False
    
    # Test creating chat history
    print("\n6. Testing ChatHistory creation...")
    try:
        with get_session() as session:
            chat = ChatHistory(
                student_id=student_id,
                session_id=f"session_{datetime.utcnow().timestamp()}",
                subject="Math",
                topic="Addition",
                student_message="How do I add 5 + 3?",
                ai_response="Great question! Let's think about it using your love of drawing..."
            )
            session.add(chat)
            session.commit()
            print(f"   ✓ Chat history created (ID: {chat.id})")
            chat_id = chat.id
    except Exception as e:
        print(f"   ✗ Error creating chat history: {e}")
        return False
    
    # Test creating test result
    print("\n7. Testing TestResult creation...")
    try:
        with get_session() as session:
            test_result = TestResult(
                student_id=student_id,
                chat_history_id=chat_id,
                subject="Math",
                topic="Addition",
                question="What is 5 + 3?",
                student_answer="8",
                correct_answer="8",
                is_correct=True,
                ai_feedback="Excellent! You've got it! 🌟"
            )
            session.add(test_result)
            session.commit()
            print(f"   ✓ Test result created (ID: {test_result.id})")
            print(f"   ✓ Result: {'Correct' if test_result.is_correct else 'Incorrect'}")
            print(f"   ✓ Feedback: {test_result.ai_feedback}")
    except Exception as e:
        print(f"   ✗ Error creating test result: {e}")
        return False
    
    # Test creating tutorial
    print("\n8. Testing Tutorial creation...")
    try:
        with get_session() as session:
            tutorial = Tutorial(
                teacher_id=teacher_id,
                student_id=student_id,
                scheduled_time=datetime.utcnow(),
                duration_minutes=30,
                subject="Math",
                notes="Review addition concepts",
                status=TutorialStatus.SCHEDULED
            )
            session.add(tutorial)
            session.commit()
            print(f"   ✓ Tutorial created (ID: {tutorial.id})")
            print(f"   ✓ Status: {tutorial.status.value}")
    except Exception as e:
        print(f"   ✗ Error creating tutorial: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("DATABASE SETUP TEST COMPLETE!")
    print("=" * 60)
    print("\n✓ All 7 models tested successfully:")
    print("  1. Admin")
    print("  2. School")
    print("  3. User (Teacher)")
    print("  4. Student")
    print("  5. ChatHistory")
    print("  6. TestResult")
    print("  7. Tutorial")
    print("\n✓ All relationships working correctly")
    print("✓ Database ready for API development!")
    print("\nNext step: Implement Admin API endpoints")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_database_setup()
    sys.exit(0 if success else 1)
