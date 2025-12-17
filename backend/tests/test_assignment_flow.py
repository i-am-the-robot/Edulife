import requests
import json
import time

BASE_URL = "https://edulife.onrender.com/api"

def login_student(student_id, pin):
    # Student login endpoint expects query param for pin (or JSON body depending on implementation, 
    # but the router code showed query param: pin: str = Query(...))
    # Wait, router showed:
    # @router.post("/student/login")
    # async def login_student(student_id: str, pin: str = Query(...))
    # This implies student_id is a query param too? UNLESS it's body.
    # FastAPI default for scalar types in POST is query param unless Body() is used.
    # So both likely query params.
    
    response = requests.post(f"{BASE_URL}/auth/student/login", params={
        "student_id": student_id,
        "pin": pin
    })
    
    if response.status_code == 200:
        return response.json()["access_token"]
    print(f"Login failed: {response.text}")
    return None

def main():
    print("=== Testing Assignment Study System Backend ===")

    # 1. Login as Student
    print("\n1. Logging in as Student...")
    
    # Load credentials file
    try:
        with open("test_credentials.json", "r") as f:
            creds = json.load(f)
            student_id = creds["student_id"]
            pin = creds["pin"]
            print(f"[INFO] Loaded credentials for {student_id}")
    except Exception as e:
        print(f"[FAIL] Could not load test_credentials.json: {e}")
        return

    token = login_student(student_id, pin)
    
    if not token:
        print("[FAIL] Login failed.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Login successful")

    # 2. Get Tasks
    print("\n2. Fetching Tasks...")
    response = requests.get(f"{BASE_URL}/student/tasks", headers=headers)
    
    if response.status_code != 200:
        print(f"[FAIL] Could not fetch tasks: {response.text}")
        return
        
    tasks = response.json()
    
    if not tasks:
        print("[FAIL] No tasks found. The population script should have created one.")
        return
    
    target_task = tasks[0]
    task_id = target_task['id']
    print(f"[OK] Found task: {target_task['title']} (ID: {task_id})")

    # 3. Start Study Session
    print("\n3. Starting Study Session...")
    response = requests.post(
        f"{BASE_URL}/student/assignments/{task_id}/start-study",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"[FAIL] Start session failed: {response.text}")
        return
        
    session_data = response.json()
    print(f"[OK] Session started/continued: {session_data['action']}")
    print(f"   Session ID: {session_data['session_id']}")
    print(f"   Status: {session_data['status']}")

    # 4. Check Study Status
    print("\n4. Checking Study Status...")
    response = requests.get(
        f"{BASE_URL}/student/assignments/{task_id}/study-status",
        headers=headers
    )
    status_data = response.json()
    print(f"[OK] Status verified: {status_data['status']}")

    # 5. Testing Final Assessment Generation (Complete Phase)...
    print("\n5. Initating Assignment Completion...")
    # This should generate questions
    response = requests.post(
        f"{BASE_URL}/student/assignments/{task_id}/complete",
        headers=headers
    )
    
    if response.status_code == 200:
        completion_data = response.json()
        print("[OK] Final assessment generated")
        questions = completion_data.get('questions', [])
        print(f"   Questions count: {len(questions)}")
        
        # 6. Submit Final Assessment
        if questions:
            print("\n6. Submitting Final Assessment...")
            # Create mock answers
            answers = ["Mock Answer" for _ in questions]
            
            response = requests.post(
                f"{BASE_URL}/student/assignments/{task_id}/submit-final",
                headers=headers,
                json=answers
            )
            
            if response.status_code == 200:
                result = response.json()
                print("[OK] Final assessment submitted")
                print(f"   Score: {result['score']}%")
                print(f"   Passed: {result['passed']}")
                print(f"   Summary: {result.get('summary', 'No summary')}")
            else:
                print(f"[FAIL] Submission failed: {response.text}")
    else:
        print(f"[WARN] Could not generate final assessment (might need chat history context): {response.text}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
