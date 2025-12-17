"""
Test script for schedule generation endpoint
"""
import requests
import json

# Test the schedule generation endpoint
url = "http://127.0.0.1:8000/api/student/generate-schedule"

# You'll need to get a valid token by logging in first
# For now, let's test if the endpoint exists
try:
    response = requests.post(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
