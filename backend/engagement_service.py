from datetime import datetime, timezone
from sqlmodel import Session, select
from .models import Student, Achievement, StudentAchievement, SessionMetrics

class EngagementService:
    @staticmethod
    def award_points(session: Session, student_id: str, points: float, source: str, description: str = "") -> dict:
        """
        Award engagement points and check for milestones.
        Returns: {"score": float, "new_achievements": List[Dict]}
        """
        try:
            student = session.get(Student, student_id)
            if not student:
                return {"score": 0.0, "new_achievements": []}
            
            # Initial State
            if not student.engagement_score:
                student.engagement_score = 0.0
                
            old_score = student.engagement_score
            new_score = old_score + points
            
            # Update Score
            student.engagement_score = new_score
            student.last_active = datetime.now(timezone.utc)
            
            print(f"[ENGAGEMENT] Awarded {points}pts to {student.full_name} for {source}. Total: {new_score:.1f}")
            
            # Check for milestones (Simplified Logic)
            new_achievements = []
            
            milestones = [
                (10, "First Steps", "Earned your first 10 points!"),
                (50, "Rising Star", "Reached 50 engagement points!"),
                (100, "Century Club", "Reached 100 engagement points!"),
                (250, "High Flyer", "Reached 250 engagement points!"),
                (500, "Brainiac", "Reached 500 engagement points!"),
                (1000, "Legendary Learner", "Reached 1000 engagement points!")
            ]
            
            for threshold, title, desc in milestones:
                if old_score < threshold <= new_score:
                    new_achievements.append({
                        "title": title,
                        "description": desc,
                        "threshold": threshold
                    })
                    print(f"[ACHIEVEMENT] Unlocked: {title}")
                    
                    # Notify Teacher
                    from .notification_service import NotificationService
                    NotificationService.notify_teacher(
                        session,
                        student_id,
                        title=f"🏆 Achievement Unlocked: {title}",
                        message=f"{student.full_name} has unlocked '{title}': {desc}",
                        notification_type="success",
                        category="engagement"
                    )
                    
            session.add(student)
            session.commit()
            session.refresh(student)
            
            return {
                "score": student.engagement_score,
                "new_achievements": new_achievements,
                "points_awarded": points
            }

        except Exception as e:
            print(f"Error awarding points: {e}")
            return {"score": 0.0, "new_achievements": []}

    @staticmethod
    def log_time_spent(session: Session, student_id: str, minutes: int):
        """
        Log time spent and award points
        """
        points = minutes * 0.2
        EngagementService.award_points(session, student_id, points, "time_spent")
