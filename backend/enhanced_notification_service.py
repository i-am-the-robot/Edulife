"""
Enhanced Notification Service with WhatsApp Integration
Sends both in-app and WhatsApp notifications
"""
from typing import Optional, Dict
from sqlmodel import Session
from .models import Student
from .notification_service import NotificationService
from .twilio_whatsapp_service import notify_parent

class EnhancedNotificationService:
    """
    Sends notifications both in-app and via WhatsApp to parents
    """
    
    @staticmethod
    def send_quiz_notification(
        student: Student,
        subject: str,
        num_questions: int,
        difficulty: str,
        score: Optional[int] = None,
        total: Optional[int] = None,
        session: Session = None,
        quiz_id: Optional[int] = None
    ):
        """
        Send quiz notification (in-app + WhatsApp)
        
        If score is provided, it's a completion notification
        Otherwise, it's a "quiz ready" notification
        """
        if score is not None and total is not None:
            # Quiz completed - notify parent
            if student.parent_whatsapp:
                notify_parent(
                    student.parent_whatsapp,
                    "quiz_completed",
                    student_name=student.full_name,
                    subject=subject,
                    score=score,
                    total=total
                )
        else:
            # Quiz ready - send in-app notification
            if session:
                NotificationService.send_quiz_ready_notification(
                    student_id=student.id,
                    subject=subject,
                    num_questions=num_questions,
                    difficulty=difficulty,
                    session=session,
                    quiz_id=quiz_id
                )
    
    @staticmethod
    def send_achievement_notification(
        student: Student,
        achievement: str,
        description: str,
        session: Session
    ):
        """Send achievement notification (in-app + WhatsApp)"""
        # In-app notification
        NotificationService.send_achievement_notification(
            student_id=student.id,
            achievement=achievement,
            description=description,
            session=session
        )
        
        # WhatsApp to parent
        if student.parent_whatsapp:
            notify_parent(
                student.parent_whatsapp,
                "achievement",
                student_name=student.full_name,
                achievement=achievement,
                description=description
            )
    
    @staticmethod
    def send_inactivity_notification(
        student: Student,
        message: str,
        days_inactive: int,
        session: Session
    ):
        """Send inactivity notification (in-app + WhatsApp)"""
        # In-app notification
        NotificationService.send_check_in_notification(
            student_id=student.id,
            message=message,
            days_inactive=days_inactive,
            session=session
        )
        
        # WhatsApp to parent
        if student.parent_whatsapp:
            notify_parent(
                student.parent_whatsapp,
                "inactivity",
                student_name=student.full_name,
                days_inactive=days_inactive
            )
    
    @staticmethod
    def send_study_plan_notification(
        student: Student,
        plan_goal: str,
        plan_id: int,
        deadline: str,
        session: Session
    ):
        """Send study plan notification (in-app + WhatsApp)"""
        # In-app notification
        NotificationService.send_plan_update_notification(
            student_id=student.id,
            plan_goal=plan_goal,
            update_message=f"Your personalized study plan is ready!",
            plan_id=plan_id,
            session=session
        )
        
        # WhatsApp to parent
        if student.parent_whatsapp:
            notify_parent(
                student.parent_whatsapp,
                "study_plan",
                student_name=student.full_name,
                plan_goal=plan_goal,
                deadline=deadline
            )


# Example usage in agents:
"""
# In Assessment Agent after quiz completion:
from .enhanced_notification_service import EnhancedNotificationService

EnhancedNotificationService.send_quiz_notification(
    student=self.student,
    subject=subject,
    num_questions=len(questions),
    difficulty=difficulty,
    score=correct_answers,
    total=len(questions),
    session=self.session
)

# In Motivation Agent for achievements:
EnhancedNotificationService.send_achievement_notification(
    student=self.student,
    achievement="Mastered Algebra",
    description="Completed all algebra topics with 90%+ scores!",
    session=self.session
)

# In Task Planning Agent:
EnhancedNotificationService.send_study_plan_notification(
    student=self.student,
    plan_goal=plan.goal,
    plan_id=plan.id,
    deadline=plan.deadline.strftime("%Y-%m-%d"),
    session=self.session
)
"""
