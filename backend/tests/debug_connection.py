
import urllib.request
import urllib.error
import os
from dotenv import load_dotenv

# Try to load env manually if dotenv not installed, but it should be
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

API_KEY = os.getenv("GROQ_API_KEY")
URL = "https://api.groq.com/openai/v1/models"

print(f"Testing connectivity to {URL}")
print(f"API Key present: {bool(API_KEY)}")

try:
    req = urllib.request.Request(URL)
    req.add_header("Authorization", f"Bearer {API_KEY}")
    
    with urllib.request.urlopen(req) as response:
        print(f"HTTP Status: {response.getcode()}")
        body = response.read().decode('utf-8')
        print("Response Snippet:", body[:200])
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print(e.read().decode('utf-8'))
except urllib.error.URLError as e:
    print(f"URL Error: {e.reason}")
except Exception as e:
    print(f"General Error: {str(e)}")
