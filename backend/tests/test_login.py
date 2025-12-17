import requests

# Backend URL
BASE_URL = "http://127.0.0.1:8000"

def test_admin_login():
    """Test admin login with form data"""
    print("Testing admin login with OAuth2 format...")
    
    form_data = {
        "username": "titilolasalisukazeem1@gmail.com",
        "password": "Project2025"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            data=form_data,  # Use data instead of json for form data
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nSUCCESS: Login successful!")
            print(f"Access Token: {data.get('access_token')[:50]}...")
            print(f"Token Type: {data.get('token_type')}")
            return True
        else:
            print(f"\nERROR: {response.json()}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_admin_login()
