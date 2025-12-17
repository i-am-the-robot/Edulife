"""
Quick test to verify admin login returns correct token
"""
import requests

# Test admin login
response = requests.post(
    "http://127.0.0.1:8000/api/auth/admin/login",
    params={
        "email": "titilolasalisukazeem1@gmail.com",
        "password": "Project2025"
    }
)

print("Status:", response.status_code)
print("Response:", response.json())

if response.status_code == 200:
    token = response.json()["access_token"]
    
    # Decode token to check type
    import jwt
    payload = jwt.decode(token, options={"verify_signature": False})
    print("\nToken payload:")
    print(f"  Email: {payload.get('sub')}")
    print(f"  Type: {payload.get('type')}")
    print(f"  Exp: {payload.get('exp')}")
    
    # Test accessing admin endpoint
    headers = {"Authorization": f"Bearer {token}"}
    test_response = requests.get(
        "http://127.0.0.1:8000/api/admin/schools",
        headers=headers
    )
    print(f"\nTest admin endpoint: {test_response.status_code}")
    if test_response.status_code != 200:
        print(f"Error: {test_response.text}")
