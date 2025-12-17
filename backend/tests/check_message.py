import sys
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Windows Unicode Fix
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

sid = "SMcd54955835ef1514a" # Default/Placeholder

if len(sys.argv) > 1:
    sid = sys.argv[1]

try:
    message = client.messages(sid).fetch()
    print(f"To: {message.to}")
    print(f"From: {message.from_}")
    print(f"Status: {message.status}")
    print(f"Body: {message.body}")
    print(f"Date: {message.date_created}")
except Exception as e:
    print(f"Error fetching message: {e}")
