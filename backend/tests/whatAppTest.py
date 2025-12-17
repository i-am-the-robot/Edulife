import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify credentials are loaded
print(f"Account SID loaded: {os.getenv('TWILIO_ACCOUNT_SID')[:10]}..." if os.getenv('TWILIO_ACCOUNT_SID') else "❌ Not found")
print(f"Auth Token loaded: {os.getenv('TWILIO_AUTH_TOKEN')[:10]}..." if os.getenv('TWILIO_AUTH_TOKEN') else "❌ Not found")
print()

import sys
# Add Project Root to path (3 levels up)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Fix Windows Unicode Output
sys.stdout.reconfigure(encoding='utf-8')

from backend.twilio_whatsapp_service import whatsapp_service

# Replace with YOUR WhatsApp number (that joined the sandbox)
# OR fetch from first student in DB
from sqlmodel import Session, select, create_engine
from backend.models import Student

# Correct path logic (Root of EduLife)
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
db_path = os.path.join(base_dir, "database.db")

print(f"Using DB Path: {db_path}")
engine = create_engine(f"sqlite:///{db_path}")

to_number = "+2348165220426" # Default/Fallback

try:
    with Session(engine) as session:
        # Try to find a student with a parent number
        student = session.exec(select(Student).where(Student.parent_whatsapp != None)).first()
        if student:
            print(f"Found student {student.full_name} with parent number {student.parent_whatsapp}")
            to_number = student.parent_whatsapp
        else:
            print("No student with parent number found in DB. Using default.")
except Exception as e:
    print(f"DB Error (using default): {e}")

print(f"Sending test message to: {to_number}")

result = whatsapp_service.send_whatsapp_message(
    to_number=to_number,  # Your number here
    message="🎓 Hello from EduLife! This is a test from the AI agent system. 🤖"
)

if result:
    print("✅ Message sent successfully!")
else:
    print("❌ Failed. Check if you joined the sandbox.")
