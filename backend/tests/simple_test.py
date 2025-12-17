"""
Simple Backend Test - Tests core functionality step by step
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

print("="*60)
print("  EduLife v2.0 Backend Test")
print("="*60)

# Test 1: Server is running
print("\n[TEST 1] Server Health Check")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        print("[PASS] Server is running")
    else:
        print("[FAIL] Server returned unexpected status")
        exit(1)
except Exception as e:
    print(f"[FAIL] Cannot connect to server: {e}")
    exit(1)

# Test 2: Admin Registration
print("\n[TEST 2] Admin Registration")
try:
    email = f"admin_{int(datetime.now().timestamp())}@edulife.com"
    response = requests.post(
        f"{BASE_URL}/api/auth/admin/register",
        json={
            "full_name": "Test Admin",
            "email": email,
            "password": "admin123"
        },
        timeout=5
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        admin_token = data["access_token"]
        print(f"[PASS] Admin registered successfully")
        print(f"Token: {admin_token[:30]}...")
    else:
        print(f"[FAIL] Registration failed: {response.json()}")
        exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    exit(1)

# Test 3: Create School
print("\n[TEST 3] Create School")
try:
    response = requests.post(
        f"{BASE_URL}/api/admin/schools",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test School",
            "location": "Test City",
            "contact_email": "contact@testschool.edu"
        },
        timeout=5
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        school_data = response.json()
        school_id = school_data["id"]
        school_app_key = school_data["app_key"]
        print(f"[PASS] School created")
        print(f"School ID: {school_id}")
        print(f"App Key: {school_app_key}")
    else:
        print(f"[FAIL] School creation failed: {response.json()}")
        exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    exit(1)

# Test 4: Register Student
print("\n[TEST 4] Register Student")
try:
    response = requests.post(
        f"{BASE_URL}/api/admin/students",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": "Test Student",
            "age": 10,
            "student_class": "Grade 5",
            "hobby": "Reading",
            "personality": "Extrovert",
            "school_id": school_id,
            "learning_profile": "Standard",
            "support_type": "None"
        },
        timeout=5
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        student_data = response.json()
        student_id = student_data["id"]
        print(f"[PASS] Student registered")
        print(f"Student ID: {student_id}")
    else:
        print(f"[FAIL] Student registration failed: {response.json()}")
        exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    exit(1)

# Test 5: Student Login
print("\n[TEST 5] Student Login")
try:
    response = requests.post(
        f"{BASE_URL}/api/auth/student/login",
        params={"student_id": student_id},
        timeout=5
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        student_token = response.json()["access_token"]
        print(f"[PASS] Student logged in")
        print(f"Token: {student_token[:30]}...")
    else:
        print(f"[FAIL] Login failed: {response.json()}")
        exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    exit(1)

# Test 6: AI Chat with Groq
print("\n[TEST 6] AI Chat with Groq")
try:
    response = requests.post(
        f"{BASE_URL}/api/chat/message",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "student_id": student_id,
            "message": "Hello! Can you help me with math?",
            "subject": "Mathematics"
        },
        timeout=30  # Longer timeout for AI response
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        chat_data = response.json()
        print(f"[PASS] AI Chat working!")
        print(f"\nAI Response:")
        print(f"{chat_data['ai_response']}")
        print(f"\nSession ID: {chat_data['session_id']}")
        print(f"Tests Generated: {len(chat_data.get('tests_generated', []))}")
    else:
        print(f"[FAIL] Chat failed: {response.json()}")
        exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    exit(1)

# Summary
print("\n" + "="*60)
print("  ALL TESTS PASSED!")
print("="*60)
print(f"\nTest Summary:")
print(f"  - Server: Running")
print(f"  - Authentication: Working")
print(f"  - School Management: Working")
print(f"  - Student Management: Working")
print(f"  - AI Chat with Groq: Working")
print(f"\nBackend is fully functional!")
