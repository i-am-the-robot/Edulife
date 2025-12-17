"""
Chat Router
Handles AI chat interactions with auto-testing and conversation recording
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from .database import get_db_session
from .models import Student, ChatHistory, TestResult, ConversationAnswer
from .schemas import ChatMessage, ChatResponse, TestSubmission, TestFeedback
from .student_router import get_current_student
from .ai_service import (
    generate_ai_response,
    should_generate_test,
    generate_test_question,
    generate_encouraging_feedback,
    evaluate_answer,
    detect_question_in_message,
    evaluate_conversation_answer
)
from .utils import calculate_engagement_score

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_data: ChatMessage,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """
    Send message to AI buddy
    - Records conversation to ChatHistory
    - Auto-generates tests based on conversation
    - Adapts responses based on learning profile (invisible to student)
    - Triggers Multi-Agent System (Tutoring, Assessment, Scheduling, Motivation)
    """
    # Verify student ID matches authenticated user
    if chat_data.student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate or use existing session ID
    session_id = chat_data.session_id or str(uuid.uuid4())
    
    # Get recent conversation history for context
    recent_chats = session.exec(
        select(ChatHistory).where(
            (ChatHistory.student_id == current_student.id) &
            (ChatHistory.session_id == session_id)
        ).order_by(ChatHistory.timestamp.desc()).limit(6)
    ).all()
    
    # Build conversation history for AI
    conversation_history = []
    for chat in reversed(recent_chats):
        conversation_history.append({"role": "user", "content": chat.student_message})
        conversation_history.append({"role": "assistant", "content": chat.ai_response})
    
    # Detect subject and topic from conversation if not provided
    subject = chat_data.subject
    topic = None
    
    # Simple topic extraction from message
    # Infer subject if not provided
    if not subject:
        message_lower = chat_data.message.lower()
        if any(word in message_lower for word in ["math", "number", "calculate", "add", "subtract", "algebra", "equation"]):
            subject = "Mathematics"
        elif any(word in message_lower for word in ["science", "experiment", "nature", "animal", "biology", "physics"]):
            subject = "Science"
        elif any(word in message_lower for word in ["read", "story", "write", "book", "grammar", "essay"]):
            subject = "English"
        else:
            subject = "General"

    # ============================================================================
    # MULTI-AGENT SYSTEM ACTIVATION
    # ============================================================================
    from .agent_coordinator import AgentCoordinator
    import asyncio
    
    # Initialize Coordinator
    coordinator = AgentCoordinator(current_student, session)
    
    # Run the coordination flow
    # Note: Some underlying agents might use sync calls (like Groq via standard client if not async)
    # But we updated specialized_agents to use AsyncGroq, so awaiting should be fine.
    # The Coordinator.handle_student_question is async.
    
    coord_response = await coordinator.handle_student_question(chat_data.message, subject)
    
    # Extract main response
    ai_response_text = coord_response.get("explanation", "")
    
    # If using RAG or basic response was better, we might merge strategies.
    # But AgentCoordinator uses TutoringAgent which uses RAG/LLM.
    
    # If explanation is empty (e.g. only motivation), fallback or use what we have
    if not ai_response_text:
        ai_response_text = coord_response.get("encouragement", "I'm listening. Tell me more!")

    # Append any specific notes (like schedule created)
    if coord_response.get("break_suggestion"):
        ai_response_text += f"\n\n{coord_response['break_suggestion']}"
    
    # Record conversation to ChatHistory
    new_chat = ChatHistory(
        student_id=current_student.id,
        session_id=session_id,
        timestamp=datetime.now(timezone.utc),
        subject=subject,
        topic=topic,
        student_message=chat_data.message,
        ai_response=ai_response_text,
        is_favorite=False
    )
    
    session.add(new_chat)
    session.commit()
    session.refresh(new_chat)
    
    # Update conversation count in AssignmentStudySession if this is part of an assignment
    from .models import AssignmentStudySession
    study_session = session.exec(select(AssignmentStudySession).where(
        (AssignmentStudySession.chat_session_id == session_id) &
        (AssignmentStudySession.student_id == current_student.id)
    )).first()
    
    if study_session:
        study_session.conversation_count += 1
        session.commit()
    
    # Award Engagement Points
    from .engagement_service import EngagementService
    # Base points for chatting
    points = 0.5 
    # Bonus points for agent interactions (e.g. taking a quiz, making a schedule)
    if "generated_quiz" in coord_response.get("actions_taken", []): points += 2.0
    if "scheduled_practice" in coord_response.get("actions_taken", []): points += 3.0
    
    engagement_result = EngagementService.award_points(session, current_student.id, points, "chat_interaction")
    
    # Handle Achievements
    if engagement_result.get("new_achievements"):
        for ach in engagement_result["new_achievements"]:
            background_tasks.add_task(
                notify_parent_achievement_task, 
                current_student.id, 
                ach["title"], 
                ach["description"]
            )
            
    # Update student's last active
    current_student.last_active = datetime.now(timezone.utc)
    session.add(current_student)
    session.commit()

    # Format the response
    return ChatResponse(
        session_id=session_id,
        ai_response=ai_response_text,
        tests_generated=[], # We pass quiz separately now via agent fields
        current_engagement_score=engagement_result.get("score"),
        points_awarded=points,
        # Multi-Agent Fields
        agents_involved=coord_response.get("agents_involved", []),
        actions_taken=coord_response.get("actions_taken", []),
        quiz=coord_response.get("quiz"),
        practice_schedule=coord_response.get("practice_schedule"),
        encouragement=coord_response.get("encouragement")
    )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def update_student_engagement(student_id: str, db_session: Session) -> float:
    """Update student's engagement score based on activity and RETURN it"""
    from sqlmodel import func
    from datetime import timedelta
    
    student = db_session.get(Student, student_id)
    if not student:
        return 0.0
    
    # Calculate login frequency (sessions per week)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    recent_sessions = db_session.exec(
        select(func.count(ChatHistory.session_id.distinct())).where(
            (ChatHistory.student_id == student_id) &
            (ChatHistory.timestamp >= week_ago)
        )
    ).one()
    
    # Total sessions
    total_sessions = db_session.exec(
        select(func.count(ChatHistory.session_id.distinct())).where(
            ChatHistory.student_id == student_id
        )
    ).one()
    
    # Total tests
    total_tests = db_session.exec(
        select(func.count(TestResult.id)).where(
            TestResult.student_id == student_id
        )
    ).one()
    
    # Test success rate
    correct_tests = db_session.exec(
        select(func.count(TestResult.id)).where(
            (TestResult.student_id == student_id) &
            (TestResult.is_correct == True)
        )
    ).one()
    
    test_success_rate = (correct_tests / total_tests * 100) if total_tests > 0 else 0.0
    
    # Calculate engagement score
    engagement_score = calculate_engagement_score(
        login_frequency=recent_sessions,
        total_sessions=total_sessions,
        total_tests=total_tests,
        test_success_rate=test_success_rate
    )
    
    # Update student
    student.engagement_score = engagement_score
    student.login_frequency = recent_sessions
    student.last_active = datetime.now(timezone.utc)
    
    db_session.add(student)
    db_session.commit()
    
    return engagement_score

# ============================================================================
# TEST ENDPOINTS
# ============================================================================

@router.post("/test/submit", response_model=TestFeedback)
async def submit_test_answer(
    submission: TestSubmission,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """
    Submit answer to a test question
    - Records to TestResult
    - Provides encouraging feedback
    - Updates engagement score
    """
    # Get test result
    test = session.get(TestResult, submission.test_result_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Verify ownership
    if test.student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if already answered
    if test.student_answer:
        # This is a retry
        test.attempt_number += 1
    
    # Evaluate answer
    is_correct = evaluate_answer(submission.student_answer, test.correct_answer)
    
    # Generate encouraging feedback
    feedback = generate_encouraging_feedback(
        student=current_student,
        is_correct=is_correct,
        student_answer=submission.student_answer,
        correct_answer=test.correct_answer,
        attempt_number=test.attempt_number
    )
    
    # Update test result
    test.student_answer = submission.student_answer
    test.is_correct = is_correct
    test.ai_feedback = feedback
    
    session.add(test)
    session.commit()
    
    # Update student engagement score
    await update_student_engagement(current_student.id, session)
    
    return TestFeedback(
        is_correct=is_correct,
        feedback=feedback,
        correct_answer=test.correct_answer if not is_correct else None
    )

@router.get("/test/{test_id}", response_model=dict)
async def get_test_question(
    test_id: int,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get a specific test question"""
    test = session.get(TestResult, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test.student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "test_id": test.id,
        "question": test.question,
        "subject": test.subject,
        "topic": test.topic,
        "is_answered": bool(test.student_answer),
        "is_correct": test.is_correct if test.student_answer else None
    }


