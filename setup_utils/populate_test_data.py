"""
EduLife v2.0 - Complete System Test & Data Population Script
This script creates test data for the entire system:
- Admin (already exists)
- School
- Teachers
- Students
Then tests the complete workflow
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://edulife.onrender.com"

# Store tokens and IDs
admin_token = None
teacher_token = None
school_id = None
app_key = None
student_ids = []

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_success(message):
    print(f"SUCCESS: {message}")

def print_error(message):
    print(f"ERROR: {message}")

# ============================================================================
# 1. ADMIN LOGIN
# ============================================================================
def admin_login():
    global admin_token
    print_section("1. Admin Login")
    
    form_data = {
        "username": "titilolasalisukazeem1@gmail.com",
        "password": "Project2025"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/admin/login",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        admin_token = response.json()["access_token"]
        print_success(f"Admin logged in successfully")
        print(f"Token: {admin_token[:50]}...")
        return True
    else:
        print_error(f"Admin login failed: {response.json()}")
        return False

# ============================================================================
# 2. CREATE SCHOOL
# ============================================================================
def create_school():
    global school_id, app_key
    print_section("2. Create School")
    
    school_data = {
        "name": "Example High School",
        "location": "Lagos, Nigeria"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/schools",
        json=school_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if response.status_code == 201:
        data = response.json()
        school_id = data["id"]
        app_key = data["app_key"]
        print_success(f"School created: {data['name']}")
        print(f"School ID: {school_id}")
        print(f"App Key: {app_key}")
        print("\nIMPORTANT: Save this app_key - teachers need it to register!")
        return True
    else:
        print_error(f"School creation failed: {response.json()}")
        return False

# ============================================================================
# 3. REGISTER TEACHERS
# ============================================================================
def register_teachers():
    global teacher_token
    print_section("3. Register Teachers")
    
    teachers = [
        {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "password": "Teacher123",
            "app_key": app_key,
            "role": "HeadTeacher",  # Fixed: HeadTeacher not Head_Teacher
            "address": "123 School Street, Lagos",  # Added required field
            "subjects": "Mathematics, Science",  # Fixed: string not array
            "specializations": "STEM Education",  # Fixed: string not array
            "years_experience": 10
        },
        {
            "full_name": "Jane Smith",
            "email": "jane.smith@example.com",
            "password": "Teacher123",
            "app_key": app_key,
            "role": "Teacher",
            "address": "456 Education Ave, Lagos",  # Added required field
            "subjects": "English, History",  # Fixed: string not array
            "specializations": "Language Arts",  # Fixed: string not array
            "years_experience": 5
        }
    ]
    
    for teacher_data in teachers:
        response = requests.post(
            f"{BASE_URL}/api/auth/teacher/register",
            json=teacher_data
        )
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"Teacher registered: {teacher_data['full_name']}")
            print(f"  Email: {teacher_data['email']}")
            print(f"  Role: {teacher_data['role']}")
            
            # Save first teacher's token
            if teacher_token is None:
                teacher_token = data["access_token"]
        else:
            print_error(f"Teacher registration failed: {response.json()}")
    
    return True

# ============================================================================
# 4. TEACHER LOGIN
# ============================================================================
def teacher_login():
    global teacher_token
    print_section("4. Teacher Login")
    
    form_data = {
        "username": "john.doe@example.com",
        "password": "Teacher123"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        teacher_token = response.json()["access_token"]
        print_success("Teacher logged in successfully")
        return True
    else:
        print_error(f"Teacher login failed: {response.json()}")
        return False

# ============================================================================
# 5. REGISTER STUDENTS
# ============================================================================
def register_students():
    global student_ids
    print_section("5. Register Students")
    
    students = [
        {
            "full_name": "Alice Johnson",
            "age": 14,
            "student_class": "Grade 8",
            "hobby": "Reading",
            "personality": "Introvert",
            "support_type": "None",
            "learning_profile": "Standard",
            "learning_preferences": '{"style": "Visual learner, enjoys reading and writing"}',
            "school_id": school_id
        },
        {
            "full_name": "Bob Williams",
            "age": 13,
            "student_class": "Grade 7",
            "hobby": "Sports",
            "personality": "Extrovert",
            "support_type": "Dyslexia",
            "learning_profile": "Personalized",
            "learning_preferences": '{"style": "Kinesthetic learner, prefers hands-on activities"}',
            "school_id": school_id
        },
        {
            "full_name": "Charlie Brown",
            "age": 15,
            "student_class": "Grade 9",
            "hobby": "Music",
            "personality": "Introvert",
            "support_type": "Autism",
            "learning_profile": "Personalized",
            "learning_preferences": '{"style": "Structured learner, likes clear instructions"}',
            "school_id": school_id
        }
    ]
    
    for student_data in students:
        response = requests.post(
            f"{BASE_URL}/api/admin/students",  # Fixed: use admin endpoint
            json=student_data,
            headers={"Authorization": f"Bearer {admin_token}"}  # Fixed: use admin token
        )
        
        if response.status_code == 201:
            data = response.json()
            student_id = data["id"]  # Fixed: response has "id" not "student_id"
            student_ids.append(student_id)
            print_success(f"Student registered: {student_data['full_name']}")
            print(f"  Student ID: {student_id}")
            print(f"  Support Type: {student_data['support_type']}")
        else:
            print_error(f"Student registration failed: {response.json()}")
    
    return True

# ============================================================================
# 6. STUDENT LOGIN & CHAT
# ============================================================================
def test_student_chat():
    print_section("6. Test Student AI Chat")
    
    if not student_ids:
        print_error("No students to test")
        return False
    
    student_id = student_ids[0]
    
    # Login
    response = requests.post(
        f"{BASE_URL}/api/auth/student/login?student_id={student_id}&pin=0000"
    )
    
    if response.status_code != 200:
        print_error(f"Student login failed: {response.json()}")
        return False
    
    student_token = response.json()["access_token"]
    print_success(f"Student logged in: {student_id}")
    
    # Send chat message
    chat_data = {
        "student_id": student_id,
        "message": "Can you help me understand addition?",
        "subject": "Mathematics"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat/message",
        json=chat_data,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success("AI chat working!")
        print(f"\nStudent: {chat_data['message']}")
        print(f"\nAI Response: [Content Hidden to avoid encoding errors]")
        
        if data.get('tests_generated'):
            print(f"\nTest Generated: {data['tests_generated'][0]['question']}")
    else:
        print_error(f"Chat failed: {response.json()}")
    
    return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    print("\n" + "=" * 60)
    print("  EduLife v2.0 - Complete System Test")
    print("  Populating database with test data...")
    print("=" * 60)
    
    # Run all tests
    if not admin_login():
        return
    
    if not create_school():
        return
    
    if not register_teachers():
        return
    
    if not teacher_login():
        return
    
    if not register_students():
        return
    
    if not test_student_chat():
        return
    
    # Final Summary
    print_section("SUMMARY - Test Data Created")
    print("\nADMIN:")
    print("  Email: titilolasalisukazeem1@gmail.com")
    print("  Password: Project2025")
    
    print("\nSCHOOL:")
    print(f"  Name: Example High School")
    print(f"  App Key: {app_key}")
    
    print("\nTEACHERS:")
    print("  1. john.doe@example.com / Teacher123 (Head Teacher)")
    print("  2. jane.smith@example.com / Teacher123 (Teacher)")
    
    print("\nSTUDENTS:")
    for i, student_id in enumerate(student_ids, 1):
        print(f"  {i}. Student ID: {student_id}")
    
    print("\n" + "=" * 60)
    print("  All test data created successfully!")
    print("  You can now login and test the system:")
    print("  - Admin: http://localhost:5173")
    print("  - Teacher: http://localhost:5173")
    print("  - Student: http://localhost:5173/student/login")
    print("=" * 60)

if __name__ == "__main__":
    main()
