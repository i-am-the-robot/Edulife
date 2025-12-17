import requests
import json

# Backend URL
BASE_URL = "https://edulife.onrender.com"

def create_admin():
    """Create admin account"""
    print("Creating admin account...")
    
    admin_data = {
        "email": "titilolasalisukazeem1@gmail.com",
        "password": "Project2025",
        "full_name": "Titilola Salisu Kazeem"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/admin/register", json=admin_data)
        
        if response.status_code == 201:
            print("SUCCESS: Admin account created successfully!")
            print(f"Email: {admin_data['email']}")
            print(f"Password: {admin_data['password']}")
            print("\nYou can now login at: http://localhost:5175")
            return response.json()
        else:
            print(f"ERROR: {response.status_code}")
            print(response.json())
            return None
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend server")
        print("Please make sure the backend is running on https://edulife.onrender.com")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("EduLife Admin Account Creation")
    print("=" * 50)
    print()
    
    admin = create_admin()
    
    if admin:
        print("\n" + "=" * 50)
        print("Admin account ready!")
        print("=" * 50)
