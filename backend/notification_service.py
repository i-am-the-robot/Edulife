"""
Agent Notification Service
Enables agents to send notifications to students about activities, quizzes, reminders
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlmodel import Session, select
from .models import Student, AgentNotification, TeacherNotification, User

class NotificationService:
    """
    Service for creating and managing agent notifications
    """
    
    @staticmethod
    def send_notification(
        student_id: str,
        notification_type: str,
        agent_type: str,
        title: str,
        message: str,
        session: Session,
        action_url: Optional[str] = None,
        action_data: Optional[Dict] = None,
        priority: str = "normal",
        expires_in_hours: Optional[int] = None
    ) -> AgentNotification:
        """
        Send a notification to a student
        
        Args:
            student_id: Student ID
            notification_type: Type of notification (quiz_ready, check_in, etc.)
            agent_type: Which agent sent it (tutoring, assessment, etc.)
            title: Short title
            message: Full message
            session: Database session
            action_url: Optional URL to navigate to
            action_data: Optional JSON data
            priority: Priority level (low, normal, high, urgent)
            expires_in_hours: When notification expires
        """
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        notification = AgentNotification(
            student_id=student_id,
            notification_type=notification_type,
            agent_type=agent_type,
            title=title,
            message=message,
            action_url=action_url,
            action_data=json.dumps(action_data) if action_data else None,
            priority=priority,
            expires_at=expires_at
        )
        
        session.add(notification)
        session.commit()
        session.refresh(notification)
        
        return notification
    
    @staticmethod
    def send_quiz_ready_notification(
        student_id: str,
        subject: str,
        num_questions: int,
        difficulty: str,
        session: Session,
        quiz_id: Optional[int] = None
    ):
        """Send notification when quiz is ready"""
        return NotificationService.send_notification(
            student_id=student_id,
            notification_type="quiz_ready",
            agent_type="assessment",
            title=f"📝 {subject} Quiz Ready!",
            message=f"Your {difficulty} quiz on {subject} is ready! {num_questions} questions waiting for you.",
            action_url=f"/quiz/{quiz_id}" if quiz_id else "/quizzes",
            action_data={"subject": subject, "difficulty": difficulty, "num_questions": num_questions},
            priority="high",
            expires_in_hours=48,
            session=session
        )
    
    @staticmethod
    def send_check_in_notification(
        student_id: str,
        message: str,
        days_inactive: int,
        session: Session
    ):
        """Send proactive check-in notification"""
        return NotificationService.send_notification(
            student_id=student_id,
            notification_type="check_in",
            agent_type="motivation",
            title="👋 We Miss You!",
            message=message,
            action_url="/chat",
            action_data={"days_inactive": days_inactive},
            priority="normal",
            expires_in_hours= 24,
            session=session
        )
    
    @staticmethod
    def send_study_reminder_notification(
        student_id: str,
        subject: str,
        topic: str,
        duration_minutes: int,
        session: Session
    ):
        """Send study reminder notification"""
        return NotificationService.send_notification(
            student_id=student_id,
            notification_type="study_reminder",
            agent_type="scheduling",
            title=f"📚 Time to Study {subject}!",
            message=f"Your {duration_minutes}-minute {subject} session on '{topic}' is scheduled now.",
            action_url="/study",
            action_data={"subject": subject, "topic": topic, "duration": duration_minutes},
            priority="high",
            expires_in_hours=2,
            session=session
        )
    
    @staticmethod
    def send_achievement_notification(
        student_id: str,
        achievement: str,
        description: str,
        session: Session
    ):
        """Send achievement/milestone notification"""
        return NotificationService.send_notification(
            student_id=student_id,
            notification_type="achievement",
            agent_type="motivation",
            title=f"🏆 {achievement}!",
            message=description,
            action_url="/achievements",
            action_data={"achievement": achievement},
            priority="normal",
            expires_in_hours=168,  # 1 week
            session=session
        )
    
    @staticmethod
    def send_plan_update_notification(
        student_id: str,
        plan_goal: str,
        update_message: str,
        plan_id: int,
        session: Session
    ):
        """Send study plan update notification"""
        return NotificationService.send_notification(
            student_id=student_id,
            notification_type="plan_update",
            agent_type="coordinator",
            title=f"📅 Plan Update: {plan_goal}",
            message=update_message,
            action_url=f"/plan/{plan_id}",
            action_data={"plan_id": plan_id, "goal": plan_goal},
            priority="normal",
            expires_in_hours=48,
            session=session
        )
    
    @staticmethod
    def get_unread_notifications(
        student_id: str,
        session: Session,
        limit: int = 20
    ) -> List[AgentNotification]:
        """Get unread notifications for a student"""
        notifications = session.exec(
            select(AgentNotification).where(
                (AgentNotification.student_id == student_id) &
                (AgentNotification.is_read == False)
            ).order_by(
                AgentNotification.priority.desc(),
                AgentNotification.created_at.desc()
            ).limit(limit)
        ).all()
        
        return list(notifications)
    
    @staticmethod
    def get_all_notifications(
        student_id: str,
        session: Session,
        limit: int = 50,
        include_read: bool = True
    ) -> List[AgentNotification]:
        """Get all notifications for a student"""
        query = select(AgentNotification).where(
            AgentNotification.student_id == student_id
        )
        
        if not include_read:
            query = query.where(AgentNotification.is_read == False)
        
        notifications = session.exec(
            query.order_by(AgentNotification.created_at.desc()).limit(limit)
        ).all()
        
        return list(notifications)
    
    @staticmethod
    def mark_as_read(
        notification_id: int,
        session: Session
    ):
        """Mark a notification as read"""
        notification = session.get(AgentNotification, notification_id)
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            session.add(notification)
            session.commit()
    
    @staticmethod
    def mark_all_as_read(
        student_id: str,
        session: Session
    ):
        """Mark all notifications as read for a student"""
        notifications = session.exec(
            select(AgentNotification).where(
                (AgentNotification.student_id == student_id) &
                (AgentNotification.is_read == False)
            )
        ).all()
        
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            session.add(notification)
        
        session.commit()
    
    @staticmethod
    def get_notification_count(
        student_id: str,
        session: Session,
        unread_only: bool = True
    ) -> int:
        """Get count of notifications"""
        query = select(AgentNotification).where(
            AgentNotification.student_id == student_id
        )
        
        if unread_only:
            query = query.where(AgentNotification.is_read == False)
        
        count = len(session.exec(query).all())
        return count
    
    @staticmethod
    def delete_expired_notifications(session: Session):
        """Delete expired notifications (cleanup task)"""
        now = datetime.utcnow()
        
        expired = session.exec(
            select(AgentNotification).where(
                (AgentNotification.expires_at.isnot(None)) &
                (AgentNotification.expires_at < now)
            )
        ).all()
        
        for notification in expired:
            session.delete(notification)
        
        session.commit()
        
        return len(expired)

    @staticmethod
    def notify_teacher(
        session: Session,
        student_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        category: str = "general"
    ):
        """
        Send a notification to the student's teacher(s)
        """
        student = session.get(Student, student_id)
        if not student:
            return None
            
        # Notify who created the student (primary teacher)
        if student.created_by_user_id:
            notification = TeacherNotification(
                teacher_id=student.created_by_user_id,
                student_id=student_id,
                title=title,
                message=message,
                type=notification_type,
                category=category,
                is_read=False,
                created_at=datetime.utcnow()
            )
            session.add(notification)
        
        # Also notify assigned teacher if different
        if student.assigned_teacher_id and student.assigned_teacher_id != student.created_by_user_id:
             notification_assigned = TeacherNotification(
                teacher_id=student.assigned_teacher_id,
                student_id=student_id,
                title=title,
                message=message,
                type=notification_type,
                category=category,
                is_read=False,
                created_at=datetime.utcnow()
            )
             session.add(notification_assigned)

        session.commit()
    
    @staticmethod
    def get_teacher_notifications(
        session: Session,
        teacher_id: int,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[TeacherNotification]:
        """Get notifications for a teacher"""
        query = select(TeacherNotification).where(
            TeacherNotification.teacher_id == teacher_id
        )
        
        if unread_only:
            query = query.where(TeacherNotification.is_read == False)
            
        return session.exec(
            query.order_by(TeacherNotification.created_at.desc()).limit(limit)
        ).all()



# Helper function to integrate with existing agent actions
def notify_student(
    student_id: str,
    notification_type: str,
    agent_type: str,
    title: str,
    message: str,
    session: Session,
    **kwargs
):
    """
    Quick helper to send notification
    Used by agents to notify students
    """
    return NotificationService.send_notification(
        student_id=student_id,
        notification_type=notification_type,
        agent_type=agent_type,
        title=title,
        message=message,
        session=session,
        **kwargs
    )
