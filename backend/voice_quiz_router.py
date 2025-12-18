"""
Voice Quiz Router
API endpoints for voice-activated quiz functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Optional
from pydantic import BaseModel

from .database import get_db_session
from .student_router import get_current_student
from .models import Student
from .quiz_session import quiz_session_manager, QuizSession
from .voice_answer_parser import parse_voice_answer, parse_voice_command, is_answer_input
from .voice_quiz_service import voice_quiz_service
from .specialized_agents import AssessmentAgent

router = APIRouter(prefix="/api/voice-quiz", tags=["Voice Quiz"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class StartVoiceQuizRequest(BaseModel):
    subject: str
    topic: Optional[str] = None
    difficulty: Optional[str] = "medium"
    num_questions: int = 10


class VoiceInputRequest(BaseModel):
    session_id: str
    voice_input: str


class VoiceQuizResponse(BaseModel):
    session_id: str
    voice_output: str
    question_data: Optional[dict] = None
    progress: Optional[dict] = None
    is_complete: bool = False
    results: Optional[dict] = None


# ============================================================================
# VOICE QUIZ ENDPOINTS
# ============================================================================

@router.post("/start", response_model=VoiceQuizResponse)
async def start_voice_quiz(
    request: StartVoiceQuizRequest,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """
    Start a new voice-activated quiz
    
    Returns:
        - session_id: Quiz session ID
        - voice_output: Voice instructions + first question
        - question_data: First question data
        - progress: Current progress
    """
    # Check if student already has an active quiz
    existing_session = quiz_session_manager.get_student_active_session(current_student.id)
    if existing_session:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active quiz. Please complete or cancel it first."
        )
    
    # Generate quiz questions using AssessmentAgent
    assessment_agent = AssessmentAgent(current_student, session)
    
    questions = await assessment_agent.generate_targeted_questions(
        subject=request.subject,
        topic=request.topic or request.subject,
        difficulty=request.difficulty,
        num_questions=request.num_questions
    )
    
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz questions"
        )
    
    # Create quiz session
    quiz_session = quiz_session_manager.create_session(
        student_id=current_student.id,
        subject=request.subject,
        questions=questions,
        is_voice_mode=True
    )
    
    # Generate voice output
    intro = voice_quiz_service.read_quiz_start(request.subject, len(questions))
    first_question = quiz_session.get_current_question()
    question_voice = voice_quiz_service.read_question(first_question, 1, len(questions))
    
    voice_output = f"{intro} {question_voice}"
    
    return VoiceQuizResponse(
        session_id=quiz_session.session_id,
        voice_output=voice_output,
        question_data=first_question,
        progress=quiz_session.get_progress(),
        is_complete=False
    )


@router.post("/answer", response_model=VoiceQuizResponse)
async def submit_voice_answer(
    request: VoiceInputRequest,
    current_student: Student = Depends(get_current_student)
):
    """
    Submit a voice answer to current question
    
    Handles:
    - Answer input (A, B, C, D, or text matching)
    - Commands (next, repeat, submit)
    
    Returns:
        - voice_output: Confirmation + next action
        - question_data: Next question (if applicable)
        - progress: Updated progress
        - is_complete: True if quiz is finished
        - results: Quiz results (if complete)
    """
    # Get quiz session
    quiz_session = quiz_session_manager.get_session(request.session_id)
    if not quiz_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz session not found"
        )
    
    # Verify student owns this session
    if quiz_session.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this quiz"
        )
    
    voice_input = request.voice_input.strip()
    current_question = quiz_session.get_current_question()
    
    if not current_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No current question available"
        )
    
    # Check if input is a command
    command = parse_voice_command(voice_input)
    
    if command == "repeat":
        # Repeat current question
        question_voice = voice_quiz_service.read_question(
            current_question,
            quiz_session.current_question_index + 1,
            len(quiz_session.questions)
        )
        return VoiceQuizResponse(
            session_id=quiz_session.session_id,
            voice_output=question_voice,
            question_data=current_question,
            progress=quiz_session.get_progress(),
            is_complete=False
        )
    
    elif command == "submit":
        # Submit quiz
        quiz_session.is_submitted = True
        results = quiz_session.calculate_score()
        
        # Generate voice explanation
        voice_output = voice_quiz_service.read_score_explanation(
            results,
            current_student.full_name
        )
        
        # Clean up session
        quiz_session_manager.delete_session(quiz_session.session_id)
        
        return VoiceQuizResponse(
            session_id=quiz_session.session_id,
            voice_output=voice_output,
            question_data=None,
            progress=quiz_session.get_progress(),
            is_complete=True,
            results=results
        )
    
    # Try to parse as answer
    if is_answer_input(voice_input):
        options = current_question.get("options", [])
        parsed_answer = parse_voice_answer(voice_input, options)
        
        if not parsed_answer:
            # Unclear input
            voice_output = voice_quiz_service.read_unclear_input()
            return VoiceQuizResponse(
                session_id=quiz_session.session_id,
                voice_output=voice_output,
                question_data=current_question,
                progress=quiz_session.get_progress(),
                is_complete=False
            )
        
        # Submit answer
        quiz_session.submit_answer(parsed_answer)
        
        # Confirm answer
        confirmation = voice_quiz_service.read_answer_confirmation(parsed_answer)
        
        # Check if last question
        if quiz_session.is_last_question():
            # Ask for submission confirmation
            submit_prompt = voice_quiz_service.read_confirmation(
                quiz_session.current_question_index + 1,
                len(quiz_session.questions)
            )
            voice_output = f"{confirmation} {submit_prompt}"
            
            return VoiceQuizResponse(
                session_id=quiz_session.session_id,
                voice_output=voice_output,
                question_data=current_question,
                progress=quiz_session.get_progress(),
                is_complete=False
            )
        else:
            # Move to next question
            quiz_session.move_to_next()
            next_question = quiz_session.get_current_question()
            
            next_question_voice = voice_quiz_service.read_question(
                next_question,
                quiz_session.current_question_index + 1,
                len(quiz_session.questions)
            )
            
            voice_output = f"{confirmation} {next_question_voice}"
            
            return VoiceQuizResponse(
                session_id=quiz_session.session_id,
                voice_output=voice_output,
                question_data=next_question,
                progress=quiz_session.get_progress(),
                is_complete=False
            )
    
    # Unrecognized input
    voice_output = voice_quiz_service.read_unclear_input()
    return VoiceQuizResponse(
        session_id=quiz_session.session_id,
        voice_output=voice_output,
        question_data=current_question,
        progress=quiz_session.get_progress(),
        is_complete=False
    )


@router.get("/current/{session_id}", response_model=VoiceQuizResponse)
async def get_current_question(
    session_id: str,
    current_student: Student = Depends(get_current_student)
):
    """
    Get current question state
    
    Returns:
        - Current question data
        - Progress
        - Voice output for current question
    """
    quiz_session = quiz_session_manager.get_session(session_id)
    if not quiz_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz session not found"
        )
    
    if quiz_session.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this quiz"
        )
    
    current_question = quiz_session.get_current_question()
    if not current_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No current question available"
        )
    
    question_voice = voice_quiz_service.read_question(
        current_question,
        quiz_session.current_question_index + 1,
        len(quiz_session.questions)
    )
    
    return VoiceQuizResponse(
        session_id=quiz_session.session_id,
        voice_output=question_voice,
        question_data=current_question,
        progress=quiz_session.get_progress(),
        is_complete=False
    )


@router.delete("/cancel/{session_id}")
async def cancel_voice_quiz(
    session_id: str,
    current_student: Student = Depends(get_current_student)
):
    """Cancel an active voice quiz"""
    quiz_session = quiz_session_manager.get_session(session_id)
    if not quiz_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz session not found"
        )
    
    if quiz_session.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this quiz"
        )
    
    quiz_session_manager.delete_session(session_id)
    return {"message": "Quiz cancelled successfully"}
