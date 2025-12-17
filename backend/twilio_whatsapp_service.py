"""
Twilio WhatsApp Service
Sends WhatsApp notifications to parents about student activities
"""
import os
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class TwilioWhatsAppService:
    """
    Service for sending WhatsApp messages to parents via Twilio
    """
    
    def __init__(self):
        """Initialize Twilio client"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_from = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')  # Twilio Sandbox
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            print("[WARNING] Twilio credentials not found. WhatsApp notifications disabled.")
    
    def send_whatsapp_message(
        self,
        to_number: str,
        message: str
    ) -> bool:
        """
        Send WhatsApp message to parent
        
        Args:
            to_number: Parent's WhatsApp number (format: +234XXXXXXXXXX)
            message: Message content
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"[WHATSAPP] Service disabled. Would send to {to_number}: {message}")
            return False
        
        try:
            # Ensure number has whatsapp: prefix
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            # Send message
            message_obj = self.client.messages.create(
                from_=self.whatsapp_from,
                body=message,
                to=to_number
            )
            
            print(f"[WHATSAPP] Message sent successfully! SID: {message_obj.sid}")
            return True
            
        except TwilioRestException as e:
            print(f"[WHATSAPP ERROR] Failed to send message: {e}")
            return False
        except Exception as e:
            print(f"[WHATSAPP ERROR] Unexpected error: {e}")
            return False
    
    def notify_parent_quiz_completed(
        self,
        parent_whatsapp: str,
        student_name: str,
        subject: str,
        score: float,
        total: int
    ) -> bool:
        """Notify parent when student completes quiz"""
        percentage = (score / total * 100) if total > 0 else 0
        
        message = f"""🎓 *EduLife Update*

Hello! Your child *{student_name}* just completed a {subject} quiz.

📊 *Score:* {score}/{total} ({percentage:.0f}%)

{"🌟 Great job!" if percentage >= 70 else "💪 Keep practicing!"}

_Edu-Life - Learn Without Limits_"""
        
        return self.send_whatsapp_message(parent_whatsapp, message)
    
    def notify_parent_achievement(
        self,
        parent_whatsapp: str,
        student_name: str,
        achievement: str,
        description: str
    ) -> bool:
        """Notify parent about student achievement"""
        message = f"""🏆 *EduLife Achievement*

Congratulations! *{student_name}* has earned an achievement:

*{achievement}*

{description}

Keep up the amazing work! 🌟

_Edu-Life - Learn Without Limits_"""
        
        return self.send_whatsapp_message(parent_whatsapp, message)
    
    def notify_parent_inactivity(
        self,
        parent_whatsapp: str,
        student_name: str,
        days_inactive: int
    ) -> bool:
        """Notify parent about student inactivity"""
        message = f"""📚 *EduLife Reminder*

Hello! We noticed that *{student_name}* hasn't been active on EduLife for {days_inactive} days.

Regular learning helps maintain progress. Please encourage them to log in and continue their learning journey! 💪

_Edu-Life - Learn Without Limits_"""
        
        return self.send_whatsapp_message(parent_whatsapp, message)
    
    def notify_parent_study_plan_created(
        self,
        parent_whatsapp: str,
        student_name: str,
        plan_goal: str,
        deadline: str
    ) -> bool:
        """Notify parent when study plan is created"""
        message = f"""📅 *EduLife Study Plan*

Good news! A personalized study plan has been created for *{student_name}*.

*Goal:* {plan_goal}
*Deadline:* {deadline}

Our AI agents will guide them through each step. You can track their progress on the EduLife platform! 📈

_Edu-Life - Learn Without Limits_"""
        
        return self.send_whatsapp_message(parent_whatsapp, message)
    
    def notify_parent_weekly_summary(
        self,
        parent_whatsapp: str,
        student_name: str,
        quizzes_completed: int,
        avg_score: float,
        active_days: int,
        achievements: int
    ) -> bool:
        """Send weekly progress summary to parent"""
        message = f"""📊 *EduLife Weekly Summary*

Here's how *{student_name}* performed this week:

✅ Quizzes Completed: {quizzes_completed}
📈 Average Score: {avg_score:.0f}%
📅 Active Days: {active_days}/7
🏆 Achievements: {achievements}

{"🌟 Excellent progress!" if avg_score >= 70 and active_days >= 4 else "💪 Encourage more practice!"}

_Edu-Life - Learn Without Limits_"""
        
        return self.send_whatsapp_message(parent_whatsapp, message)
    
    def notify_parent_exam_reminder(
        self,
        parent_whatsapp: str,
        student_name: str,
        exam_subject: str,
        days_until_exam: int
    ) -> bool:
        """Remind parent about upcoming exam"""
        message = f"""⏰ *EduLife Exam Reminder*

*{student_name}* has an exam coming up!

📚 Subject: {exam_subject}
📅 In {days_until_exam} days

Our AI agents have created a preparation plan. Please ensure they follow the study schedule! 💪

_Edu-Life - Learn Without Limits_"""
        
        return self.send_whatsapp_message(parent_whatsapp, message)


# Global instance
whatsapp_service = TwilioWhatsAppService()


# Helper functions for easy use
def notify_parent(
    parent_whatsapp: Optional[str],
    notification_type: str,
    **kwargs
) -> bool:
    """
    Quick helper to send WhatsApp notification to parent
    
    Args:
        parent_whatsapp: Parent's WhatsApp number
        notification_type: Type of notification
        **kwargs: Additional data for the notification
    
    Returns:
        bool: True if sent successfully
    """
    if not parent_whatsapp:
        return False
    
    if notification_type == "quiz_completed":
        return whatsapp_service.notify_parent_quiz_completed(
            parent_whatsapp,
            kwargs.get('student_name'),
            kwargs.get('subject'),
            kwargs.get('score'),
            kwargs.get('total')
        )
    
    elif notification_type == "achievement":
        return whatsapp_service.notify_parent_achievement(
            parent_whatsapp,
            kwargs.get('student_name'),
            kwargs.get('achievement'),
            kwargs.get('description')
        )
    
    elif notification_type == "inactivity":
        return whatsapp_service.notify_parent_inactivity(
            parent_whatsapp,
            kwargs.get('student_name'),
            kwargs.get('days_inactive')
        )
    
    elif notification_type == "study_plan":
        return whatsapp_service.notify_parent_study_plan_created(
            parent_whatsapp,
            kwargs.get('student_name'),
            kwargs.get('plan_goal'),
            kwargs.get('deadline')
        )
    
    elif notification_type == "weekly_summary":
        return whatsapp_service.notify_parent_weekly_summary(
            parent_whatsapp,
            kwargs.get('student_name'),
            kwargs.get('quizzes_completed'),
            kwargs.get('avg_score'),
            kwargs.get('active_days'),
            kwargs.get('achievements')
        )
    
    elif notification_type == "exam_reminder":
        return whatsapp_service.notify_parent_exam_reminder(
            parent_whatsapp,
            kwargs.get('student_name'),
            kwargs.get('exam_subject'),
            kwargs.get('days_until_exam')
        )
    
    return False
