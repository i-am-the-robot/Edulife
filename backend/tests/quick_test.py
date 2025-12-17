"""Test health endpoint"""
import requests

# Test root
response = requests.get("http://127.0.0.1:8000/")
print(f"Root - Status: {response.status_code}, Response: {response.json()}")

# Test health
response = requests.get("http://127.0.0.1:8000/health")
print(f"Health - Status: {response.status_code}, Response: {response.json()}")

# Test admin register
response = requests.post(
    "http://127.0.0.1:8000/api/auth/admin/register",
    json={"full_name": "Test", "email": "test@test.com", "password": "test123"}
)
print(f"Admin Register - Status: {response.status_code}, Response: {response.json()}")
