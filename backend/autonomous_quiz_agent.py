"""
Autonomous Quiz Generation Agent
Decides when and what quizzes to generate based on student activity
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from sqlmodel import Session, select, func
from .models import Student, ChatHistory, TestResult
from .agent_memory import get_student_memory
from .agent_service import log_agent_action
from .ai_service import generate_context_quiz

class QuizGenerationAgent:
    """
    Autonomous agent that decides when to generate quizzes
    """
    
    def __init__(self, student: Student, session: Session):
        self.student = student
        self.session = session
        self.memory = get_student_memory(student.id, session)
    
    def should_generate_quiz(self, subject: Optional[str] = None) -> Dict:
        """
        Decide if a quiz should be generated
        Returns dict with decision and reasoning
        """
        # Get recent conversation count
        recent_chats = self.session.exec(
            select(func.count(ChatHistory.id)).where(
                (ChatHistory.student_id == self.student.id) &
                (ChatHistory.timestamp >= datetime.utcnow() - timedelta(hours=24))
            )
        ).one()
        
        # Get last quiz time
        last_quiz = self.session.exec(
            select(TestResult).where(
                TestResult.student_id == self.student.id
            ).order_by(TestResult.timestamp.desc()).limit(1)
        ).first()
        
        hours_since_quiz = 999
        if last_quiz:
            hours_since_quiz = (datetime.utcnow() - last_quiz.timestamp).total_seconds() / 3600
        
        # Decision logic
        reasons = []
        should_quiz = False
        
        # Rule 1: After 5+ conversations in 24 hours
        if recent_chats >= 5:
            should_quiz = True
            reasons.append(f"High activity: {recent_chats} conversations in 24 hours")
        
        # Rule 2: No quiz in last 24 hours and had conversations
        if hours_since_quiz > 24 and recent_chats > 0:
            should_quiz = True
            reasons.append(f"No quiz in {int(hours_since_quiz)} hours")
        
        # Rule 3: Check performance drop
        if subject:
            performance = self._get_subject_performance(subject)
            if performance and performance < 0.6:
                should_quiz = True
                reasons.append(f"Performance drop in {subject}: {performance*100:.0f}%")
        
        # Rule 4: Weekly review (if it's been 7 days)
        if hours_since_quiz > 168:  # 7 days
            should_quiz = True
            reasons.append("Weekly review quiz due")
        
        return {
            "should_generate": should_quiz,
            "reasoning": "; ".join(reasons) if reasons else "No quiz needed yet",
            "recent_chats": recent_chats,
            "hours_since_last_quiz": hours_since_quiz
        }
    
    def _get_subject_performance(self, subject: str) -> Optional[float]:
        """Get recent performance in a subject"""
        results = self.session.exec(
            select(TestResult).where(
                (TestResult.student_id == self.student.id) &
                (TestResult.subject == subject) &
                (TestResult.timestamp >= datetime.utcnow() - timedelta(days=7))
            )
        ).all()
        
        if not results:
            return None
        
        correct = sum(1 for r in results if r.is_correct)
        return correct / len(results)
    
    def generate_adaptive_quiz(
        self,
        subject: str,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> Dict:
        """
        Generate an adaptive quiz based on student's current state
        """
        # Get recent conversation history for context
        recent_chats = self.session.exec(
            select(ChatHistory).where(
                (ChatHistory.student_id == self.student.id) &
                (ChatHistory.subject == subject if subject else True)
            ).order_by(ChatHistory.timestamp.desc()).limit(10)
        ).all()
        
        # Convert to conversation format
        conversation_history = []
        for chat in reversed(recent_chats):
            conversation_history.append({"role": "user", "content": chat.student_message})
            conversation_history.append({"role": "assistant", "content": chat.ai_response})
        
        # Determine difficulty if not specified
        if not difficulty:
            performance = self._get_subject_performance(subject)
            if performance is None or performance < 0.4:
                difficulty = "easy"
            elif performance < 0.7:
                difficulty = "medium"
            else:
                difficulty = "hard"
        
        # Generate quiz using existing AI service
        questions = generate_context_quiz(
            self.student,
            conversation_history,
            subject,
            num_questions=5
        )
        
        # Log the action
        action = log_agent_action(
            student_id=self.student.id,
            action_type="quiz_generated",
            action_data={
                "subject": subject,
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": len(questions),
                "trigger": "autonomous"
            },
            reasoning=f"Generated {difficulty} quiz for {subject}",
            session=self.session
        )
        
        # Update agent memory
        self.memory.add_goal(f"Complete quiz on {subject}")
        
        return {
            "questions": questions,
            "subject": subject,
            "difficulty": difficulty,
            "action_id": action.id,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def evaluate_quiz_effectiveness(
        self,
        action_id: int,
        quiz_results: Dict
    ):
        """
        Evaluate how effective the quiz was
        Updates agent memory and action log
        """
        score = quiz_results.get("score", 0)
        total = quiz_results.get("total", 1)
        percentage = (score / total) * 100
        
        # Determine effectiveness
        if percentage >= 80:
            effectiveness = 1.0
            self.memory.add_effective_strategy("quiz_after_high_activity")
        elif percentage >= 60:
            effectiveness = 0.7
        else:
            effectiveness = 0.4
            self.memory.add_ineffective_strategy("quiz_too_difficult")
        
        # Update action outcome
        from .agent_service import update_action_outcome
        update_action_outcome(
            action_id=action_id,
            outcome="completed",
            student_response=f"Score: {score}/{total}",
            effectiveness_score=effectiveness,
            session=self.session
        )
        
        # Update memory based on results
        if percentage < 60:
            subject = quiz_results.get("subject")
            if subject:
                self.memory.add_topic_to_revisit(
                    subject,
                    f"Quiz score: {percentage:.0f}%"
                )
        elif percentage >= 90:
            subject = quiz_results.get("subject")
            if subject:
                self.memory.mark_topic_mastered(subject)
                self.memory.add_milestone(
                    f"Mastered {subject}",
                    {"quiz_score": percentage}
                )


def check_and_generate_quizzes(session: Session) -> Dict:
    """
    Check all active students and generate quizzes where needed
    Called by background scheduler
    """
    students = session.exec(
        select(Student).where(Student.is_active == True)
    ).all()
    
    results = {
        "students_checked": len(students),
        "quizzes_generated": 0,
        "quiz_details": []
    }
    
    for student in students:
        agent = QuizGenerationAgent(student, session)
        
        # Check if quiz should be generated
        decision = agent.should_generate_quiz()
        
        if decision["should_generate"]:
            # Get student's most active subject
            most_active_subject = session.exec(
                select(
                    ChatHistory.subject,
                    func.count(ChatHistory.id).label('count')
                ).where(
                    (ChatHistory.student_id == student.id) &
                    (ChatHistory.subject.isnot(None)) &
                    (ChatHistory.timestamp >= datetime.utcnow() - timedelta(days=7))
                ).group_by(ChatHistory.subject)
                .order_by(func.count(ChatHistory.id).desc())
                .limit(1)
            ).first()
            
            if most_active_subject:
                subject = most_active_subject[0]
                
                # Generate quiz
                quiz = agent.generate_adaptive_quiz(subject)
                
                results["quizzes_generated"] += 1
                results["quiz_details"].append({
                    "student_id": student.id,
                    "student_name": student.full_name,
                    "subject": subject,
                    "num_questions": len(quiz["questions"]),
                    "reasoning": decision["reasoning"]
                })
    
    return results
