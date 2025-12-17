"""
Assignment Study Session Router
Handles study sessions with periodic quizzes and final assessments
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime
import uuid
import json

from .database import get_db_session
from .models import Student, AssignmentStudySession, Task, ChatHistory
from .student_router import get_current_student
from .quiz_service import (
    generate_periodic_quiz,
    generate_final_assessment,
    grade_quiz_answers,
    generate_study_summary
)
from .ai_service import generate_personalized_completion_feedback

router = APIRouter(prefix="/api/student/assignments", tags=["Assignment Study"])

@router.post("/{task_id}/start-study", response_model=dict)
async def start_study_session(
    task_id: int,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Start or continue a study session for an assignment"""
    # Verify task exists and belongs to student
    task = session.exec(select(Task).where(
        (Task.id == task_id) & (Task.student_id == current_student.id)
    )).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check for existing study session
    existing_session = session.exec(select(AssignmentStudySession).where(
        (AssignmentStudySession.task_id == task_id) &
        (AssignmentStudySession.student_id == current_student.id)
    )).first()
    
    if existing_session:
        return {
            "action": "continue",
            "session_id": existing_session.chat_session_id,
            "conversation_count": existing_session.conversation_count,
            "status": existing_session.status,
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description
            }
        }
    
    # Create new study session
    chat_session_id = str(uuid.uuid4())
    new_session = AssignmentStudySession(
        task_id=task_id,
        student_id=current_student.id,
        chat_session_id=chat_session_id,
        status="in_progress"
    )
    
    session.add(new_session)
    session.commit()
    session.refresh(new_session)
    
    return {
        "action": "start",
        "session_id": chat_session_id,
        "conversation_count": 0,
        "status": "in_progress",
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description
        }
    }

@router.get("/{task_id}/study-status", response_model=dict)
async def get_study_status(
    task_id: int,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get current study session status"""
    study_session = session.exec(select(AssignmentStudySession).where(
        (AssignmentStudySession.task_id == task_id) &
        (AssignmentStudySession.student_id == current_student.id)
    )).first()
    
    if not study_session:
        return {"exists": False}
    
    return {
        "exists": True,
        "status": study_session.status,
        "conversation_count": study_session.conversation_count,
        "chat_session_id": study_session.chat_session_id,
        "quiz_score": study_session.quiz_score,
        "final_score": study_session.final_score
    }

@router.post("/{task_id}/submit-quiz", response_model=dict)
async def submit_periodic_quiz(
    task_id: int,
    answers: List[str],
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Submit answers to periodic quiz"""
    study_session = session.exec(select(AssignmentStudySession).where(
        (AssignmentStudySession.task_id == task_id) &
        (AssignmentStudySession.student_id == current_student.id)
    )).first()
    
    if not study_session:
        raise HTTPException(status_code=404, detail="Study session not found")
    
    if not study_session.quiz_questions:
        raise HTTPException(status_code=400, detail="No quiz questions available")
    
    # Parse questions and grade answers
    questions = json.loads(study_session.quiz_questions)
    grading_result = grade_quiz_answers(questions, answers)
    
    # Update session with answers and score
    study_session.quiz_answers = json.dumps(answers)
    study_session.quiz_score = grading_result["score"]
    study_session.last_quiz_at = study_session.conversation_count
    
    study_session.last_quiz_at = study_session.conversation_count
    
    # Award Engagement Points
    if grading_result["passed"]:
         from .engagement_service import EngagementService
         # 5 points base + bonus for good score
         points = 5.0 + (grading_result["score"] / 20.0) # Max ~10 pts total
         EngagementService.award_points(session, current_student.id, points, "periodic_quiz")

    session.commit()
    
    return {
        "score": grading_result["score"],
        "passed": grading_result["passed"],
        "feedback": grading_result["detailed_feedback"]
    }

@router.post("/{task_id}/complete", response_model=dict)
async def initiate_assignment_completion(
    task_id: int,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Generate final assessment questions"""
    study_session = session.exec(select(AssignmentStudySession).where(
        (AssignmentStudySession.task_id == task_id) &
        (AssignmentStudySession.student_id == current_student.id)
    )).first()
    
    if not study_session:
        raise HTTPException(status_code=404, detail="Study session not found")
    
    # Get task details
    task = session.exec(select(Task).where(Task.id == task_id)).first()
    
    # Get full conversation history
    chat_history = session.exec(select(ChatHistory).where(
        (ChatHistory.student_id == current_student.id) &
        (ChatHistory.session_id == study_session.chat_session_id)
    ).order_by(ChatHistory.timestamp.asc())).all()
    
    conversation = []
    for chat in chat_history:
        conversation.append({"role": "user", "content": chat.student_message})
        conversation.append({"role": "assistant", "content": chat.ai_response})
    
    # Generate final assessment
    final_questions = generate_final_assessment(
        current_student,
        conversation,
        chat_history[0].subject if chat_history else "General",
        task.title
    )
    
    # Store questions in session
    study_session.final_questions = json.dumps(final_questions)
    study_session.status = "quiz_pending"
    session.commit()
    
    return {
        "message": "Final assessment generated",
        "questions": final_questions
    }

@router.post("/{task_id}/submit-final", response_model=dict)
async def submit_final_assessment(
    task_id: int,
    answers: List[str],
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Submit final assessment and complete assignment"""
    study_session = session.exec(select(AssignmentStudySession).where(
        (AssignmentStudySession.task_id == task_id) &
        (AssignmentStudySession.student_id == current_student.id)
    )).first()
    
    if not study_session:
        raise HTTPException(status_code=404, detail="Study session not found")
    
    if not study_session.final_questions:
        raise HTTPException(status_code=400, detail="No final assessment available")
    
    # Parse questions and grade answers
    questions = json.loads(study_session.final_questions)
    grading_result = grade_quiz_answers(questions, answers)
    
    # Get conversation for summary
    chat_history = session.exec(select(ChatHistory).where(
        (ChatHistory.student_id == current_student.id) &
        (ChatHistory.session_id == study_session.chat_session_id)
    ).order_by(ChatHistory.timestamp.asc())).all()
    
    conversation = []
    for chat in chat_history:
        conversation.append({"role": "user", "content": chat.student_message})
        conversation.append({"role": "assistant", "content": chat.ai_response})
    
    # Get task details
    task = session.exec(select(Task).where(Task.id == task_id)).first()
    
    # Generate summary for teacher
    summary = generate_study_summary(
        current_student,
        conversation,
        study_session.quiz_score or 0,
        grading_result["score"],
        chat_history[0].subject if chat_history else "General",
        task.title
    )
    
    # Update session
    study_session.final_answers = json.dumps(answers)
    study_session.final_score = grading_result["score"]
    study_session.summary = summary
    study_session.status = "completed"
    study_session.completed_at = datetime.utcnow()
    study_session.submitted_to_teacher = True
    
    # Mark task as completed
    task.status = "completed"
    
    task.status = "completed"
    
    # Award Engagement Points
    if grading_result["passed"]:
         from .engagement_service import EngagementService
         # 20 points base + bonus
         points = 20.0 + (grading_result["score"] / 10.0) # Max ~30 pts
         EngagementService.award_points(session, current_student.id, points, "final_assessment")
         
    session.commit()
    
    # Generate personalized feedback for student
    personalized_feedback = generate_personalized_completion_feedback(
        student=current_student,
        score=grading_result["score"],
        passed=grading_result["passed"]
    )
    
    return {
        "score": grading_result["score"],
        "passed": grading_result["passed"],
        "feedback": personalized_feedback,  # Personalized, friendly message
        "summary": summary,
        "hide_raw_score": True  # Flag for frontend to hide percentage
    }
