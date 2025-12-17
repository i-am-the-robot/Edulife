import sys
import os
from sqlmodel import Session, select, create_engine
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Windows Unicode Fix
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from backend.models import Student
from backend.twilio_whatsapp_service import TwilioWhatsAppService

# Connect to DB
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database.db")
engine = create_engine(f"sqlite:///{db_path}")

def resend_badge():
    whatsapp_service = TwilioWhatsAppService()
    
    with Session(engine) as session:
        # fuzzy search for Olasubomi
        students = session.exec(select(Student)).all()
        target_student = None
        for s in students:
            if "olasubomi" in s.full_name.lower():
                target_student = s
                break
        
        if not target_student:
            print("❌ Student 'Olasubomi' not found.")
            return

        print(f"✅ Found Student: {target_student.full_name}")
        print(f"📞 Parent WhatsApp: {target_student.parent_whatsapp}")
        
        if not target_student.parent_whatsapp:
            print("❌ No parent number defined.")
            return

        # Badge Details
        badge_name = "First Steps"
        badge_desc = "Completed your first session! 🚀"
        
        print(f"Sending Badge: {badge_name}...")
        
        success = whatsapp_service.notify_parent_achievement(
            target_student.parent_whatsapp,
            target_student.full_name,
            badge_name,
            badge_desc
        )
        
        if success:
            print("✅ Notification Sent Successfully!")
        else:
            print("❌ Failed to send notification.")

if __name__ == "__main__":
    resend_badge()
