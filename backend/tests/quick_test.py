"""Test health endpoint"""
import requests

# Test root
response = requests.get("https://edulife.onrender.com/")
print(f"Root - Status: {response.status_code}, Response: {response.json()}")

# Test health
response = requests.get("https://edulife.onrender.com/health")
print(f"Health - Status: {response.status_code}, Response: {response.json()}")

# Test admin register
response = requests.post(
    "https://edulife.onrender.com/api/auth/admin/register",
    json={"full_name": "Test", "email": "test@test.com", "password": "test123"}
)
print(f"Admin Register - Status: {response.status_code}, Response: {response.json()}")
