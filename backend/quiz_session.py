"""
Quiz Session Management
Handles voice-activated quiz sessions with state tracking
"""
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid

@dataclass
class QuizSession:
    """Manages a single quiz session for voice or text mode"""
    session_id: str
    student_id: str
    subject: str
    questions: List[Dict]
    current_question_index: int = 0
    answers: Dict[int, str] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    is_voice_mode: bool = False
    is_submitted: bool = False
    
    def get_current_question(self) -> Optional[Dict]:
        """Get the current question"""
        if self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def submit_answer(self, answer: str) -> bool:
        """Submit answer for current question"""
        if self.current_question_index < len(self.questions):
            self.answers[self.current_question_index] = answer
            return True
        return False
    
    def move_to_next(self) -> bool:
        """Move to next question"""
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            return True
        return False
    
    def is_last_question(self) -> bool:
        """Check if current question is the last one"""
        return self.current_question_index == len(self.questions) - 1
    
    def calculate_score(self) -> Dict:
        """Calculate quiz score and detailed results"""
        correct_count = 0
        total_questions = len(self.questions)
        detailed_results = []
        
        for idx, question in enumerate(self.questions):
            student_answer = self.answers.get(idx, "")
            correct_answer = question.get("correct_answer", "")
            is_correct = student_answer.upper() == correct_answer.upper()
            
            if is_correct:
                correct_count += 1
            
            detailed_results.append({
                "question_number": idx + 1,
                "question": question.get("question", ""),
                "options": question.get("options", []),
                "student_answer": student_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", "")
            })
        
        percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        return {
            "score": correct_count,
            "total": total_questions,
            "percentage": percentage,
            "detailed_results": detailed_results,
            "completion_time": (datetime.now() - self.start_time).total_seconds()
        }
    
    def get_progress(self) -> Dict:
        """Get current progress"""
        return {
            "current": self.current_question_index + 1,
            "total": len(self.questions),
            "answered": len(self.answers),
            "is_last": self.is_last_question()
        }


class QuizSessionManager:
    """Manages multiple quiz sessions"""
    
    def __init__(self):
        self._sessions: Dict[str, QuizSession] = {}
    
    def create_session(
        self,
        student_id: str,
        subject: str,
        questions: List[Dict],
        is_voice_mode: bool = False
    ) -> QuizSession:
        """Create a new quiz session"""
        session_id = str(uuid.uuid4())
        session = QuizSession(
            session_id=session_id,
            student_id=student_id,
            subject=subject,
            questions=questions,
            is_voice_mode=is_voice_mode
        )
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[QuizSession]:
        """Get existing quiz session"""
        return self._sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete quiz session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def get_student_active_session(self, student_id: str) -> Optional[QuizSession]:
        """Get student's active quiz session"""
        for session in self._sessions.values():
            if session.student_id == student_id and not session.is_submitted:
                return session
        return None
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old quiz sessions"""
        now = datetime.now()
        to_delete = []
        
        for session_id, session in self._sessions.items():
            age_hours = (now - session.start_time).total_seconds() / 3600
            if age_hours > max_age_hours:
                to_delete.append(session_id)
        
        for session_id in to_delete:
            del self._sessions[session_id]


# Global session manager instance
quiz_session_manager = QuizSessionManager()
