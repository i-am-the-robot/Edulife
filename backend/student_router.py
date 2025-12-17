"""
Student Router
Handles student dashboard functionality: profile, chat history, achievements, schedule
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from .database import get_db_session
from .models import Student, ChatHistory, TestResult, Tutorial, TutorialStatus, Task, Timetable
from .schemas import StudentResponse
from .auth import oauth2_scheme


router = APIRouter(prefix="/api/student", tags=["Student"])

# Helper to get current student from token
async def get_current_student(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session)
) -> Student:
    """Get current authenticated student"""
    from .auth import decode_token
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        student_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        
        if student_id is None or user_type != "student":
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    student = session.get(Student, student_id)
    if student is None:
        raise credentials_exception
    if not student.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    return student

# ============================================================================
# PROFILE & PROGRESS
# ============================================================================

@router.get("/profile", response_model=dict)
async def get_my_profile(
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get my profile and progress (NEVER shows support_type)"""
    # Calculate stats
    total_sessions = session.exec(
        select(func.count(ChatHistory.session_id.distinct())).where(
            ChatHistory.student_id == current_student.id
        )
    ).one()
    
    total_tests = session.exec(
        select(func.count(TestResult.id)).where(
            TestResult.student_id == current_student.id
        )
    ).one()
    
    correct_tests = session.exec(
        select(func.count(TestResult.id)).where(
            (TestResult.student_id == current_student.id) &
            (TestResult.is_correct == True)
        )
    ).one()
    
    success_rate = (correct_tests / total_tests * 100) if total_tests > 0 else 0.0
    
    # Calculate achievements using same logic as /achievements endpoint
    # Count unique active days
    active_days = session.exec(
        select(func.count(func.distinct(func.date(ChatHistory.timestamp)))).where(
            ChatHistory.student_id == current_student.id
        )
    ).one()
    
    # Badge logic (same as achievements endpoint)
    achievements_count = 0
    
    # Session-based achievements
    if total_sessions >= 1:
        achievements_count += 1  # First Steps
    if total_sessions >= 10:
        achievements_count += 1  # Curious Learner
    if total_sessions >= 50:
        achievements_count += 1  # Chat Master
    if total_sessions >= 100:
        achievements_count += 1  # Conversation King
    
    # Test-based achievements
    if total_tests >= 5:
        achievements_count += 1  # Test Taker
    if correct_tests >= 10:
        achievements_count += 1  # Getting Good
    if total_tests > 0 and (correct_tests / total_tests) >= 0.9:
        achievements_count += 1  # Test Champion
    
    # Streak-based achievements
    if active_days >= 3:
        achievements_count += 1  # Streak Keeper
    if active_days >= 7:
        achievements_count += 1  # Week Warrior
    if active_days >= 30:
        achievements_count += 1  # Month Master
        

    
    # Calculate Engagement Breakdown
    # 1. Chat Points: 0.5 per message (user + ai) / 2 = per interaction roughly
    chat_points = total_sessions * 0.5 

    # 2. Quiz Points: 5 per correct test + Bonuses
    quiz_points = correct_tests * 5.0

    # 3. Assignment Points: 20 per completed task (fetch count)
    completed_tasks_count = session.exec(select(func.count(Task.id)).where(
        (Task.student_id == current_student.id) &
        (Task.status == "completed")
    )).one()
    assignment_points = completed_tasks_count * 20.0

    # 4. Tutorial Points: 30 per completed tutorial
    completed_tutorials_count = session.exec(select(func.count(Tutorial.id)).where(
        (Tutorial.student_id == current_student.id) &
        (Tutorial.status == TutorialStatus.COMPLETED)
    )).one()
    tutorial_points = completed_tutorials_count * 30.0
    
    # 5. Time Points (Heuristic from total sessions if strictly time tracking isn't there)
    # Assume avg session is 10 mins -> 2 points. So sessions * 2
    time_points = total_sessions * 2.0

    # Calculate total score from breakdown to ensure consistency
    total_calculated_score = chat_points + quiz_points + assignment_points + tutorial_points + time_points
    
    # Engagement-based achievements (Calculated late)
    # Use the higher of calculated vs persisted score (to account for ad-hoc bonuses)
    final_score = max(total_calculated_score, current_student.engagement_score or 0.0)
    
    if final_score >= 100:
        achievements_count += 1 # Rising Star
    if final_score >= 200:
        achievements_count += 1 # High Flyer
    if final_score >= 500:
        achievements_count += 1 # Elite Scholar
    if final_score >= 1000:
        achievements_count += 1 # Legendary Learner
    
    return {
        "id": current_student.id,
        "full_name": current_student.full_name,
        "age": current_student.age,
        "class": current_student.student_class,
        "hobby": current_student.hobby,
        "personality": current_student.personality,
        "enrollment_date": current_student.enrollment_date,
        # Use calculated score for display consistency
        "engagement_score": round(final_score, 1),
        "engagement_breakdown": {
            "chat": round(chat_points, 1),
            "quizzes": round(quiz_points, 1),
            "assignments": round(assignment_points, 1),
            "tutorials": round(tutorial_points, 1),
            "time": round(time_points, 1)
        },
        "total_sessions": total_sessions,
        "total_tests": total_tests,
        "test_success_rate": round(success_rate, 2),
        "achievements_count": achievements_count,
        "favorite_subjects": current_student.favorite_subjects,
        "last_active": current_student.last_active
    }

@router.get("/subjects", response_model=List[dict])
async def get_my_subjects(
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get my subjects and lessons based on chat history"""
    # Get subjects from chat history
    subject_stats = session.exec(
        select(
            ChatHistory.subject,
            func.count(ChatHistory.id).label('session_count'),
            func.max(ChatHistory.timestamp).label('last_session')
        ).where(
            (ChatHistory.student_id == current_student.id) &
            (ChatHistory.subject.isnot(None))
        ).group_by(ChatHistory.subject)
    ).all()
    
    result = []
    for subject, session_count, last_session in subject_stats:
        # Get test stats for this subject
        total_tests = session.exec(
            select(func.count(TestResult.id)).where(
                (TestResult.student_id == current_student.id) &
                (TestResult.subject == subject)
            )
        ).one()
        
        correct_tests = session.exec(
            select(func.count(TestResult.id)).where(
                (TestResult.student_id == current_student.id) &
                (TestResult.subject == subject) &
                (TestResult.is_correct == True)
            )
        ).one()
        
        success_rate = (correct_tests / total_tests * 100) if total_tests > 0 else 0.0
        
        result.append({
            "subject": subject,
            "session_count": session_count,
            "last_session": last_session,
            "total_tests": total_tests,
            "success_rate": round(success_rate, 2)
        })
    
    return result

@router.get("/achievements", response_model=dict)
async def get_my_achievements(
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get my achievements and badges"""
    # Calculate achievements
    total_sessions = session.exec(
        select(func.count(ChatHistory.session_id.distinct())).where(
            ChatHistory.student_id == current_student.id
        )
    ).one()
    
    total_tests = session.exec(
        select(func.count(TestResult.id)).where(
            TestResult.student_id == current_student.id
        )
    ).one()
    
    correct_tests = session.exec(
        select(func.count(TestResult.id)).where(
            (TestResult.student_id == current_student.id) &
            (TestResult.is_correct == True)
        )
    ).one()
    
    # Count consecutive days active
    # Simple implementation: count unique days with activity
    active_days = session.exec(
        select(func.count(func.distinct(func.date(ChatHistory.timestamp)))).where(
            ChatHistory.student_id == current_student.id
        )
    ).one()
    
    # Badge logic (must match profile endpoint exactly)
    badges = []
    
    # Session-based achievements
    if total_sessions >= 1:
        badges.append({"name": "First Steps", "description": "Completed your first session", "icon": "🌟"})
    if total_sessions >= 10:
        badges.append({"name": "Curious Learner", "description": "Completed 10 sessions", "icon": "📚"})
    if total_sessions >= 50:
        badges.append({"name": "Chat Master", "description": "Completed 50 sessions", "icon": "🎓"})
    if total_sessions >= 100:
        badges.append({"name": "Conversation King", "description": "Completed 100 sessions", "icon": "👑"})
    
    # Test-based achievements
    if total_tests >= 5:
        badges.append({"name": "Test Taker", "description": "Completed 5 tests", "icon": "📝"})
    if correct_tests >= 10:
        badges.append({"name": "Getting Good", "description": "Answered 10 questions correctly", "icon": "💡"})
    if total_tests > 0 and (correct_tests / total_tests) >= 0.9:
        badges.append({"name": "Test Champion", "description": "90%+ success rate", "icon": "🏆"})
    
    # Streak-based achievements
    if active_days >= 3:
        badges.append({"name": "Streak Keeper", "description": "Active for 3 days", "icon": "🔥"})
    if active_days >= 7:
        badges.append({"name": "Week Warrior", "description": "Active for 7 days", "icon": "⭐"})
    if active_days >= 30:
        badges.append({"name": "Month Master", "description": "Active for 30 days", "icon": "🎖️"})
        
    # Engagement-based achievements
    # Calculate Engagement Breakdown (Simplified for speed but consistent with profile)
    # 1. Chat Points
    chat_points = total_sessions * 0.5 
    
    # 2. Quiz Points
    quiz_points = correct_tests * 5.0

    # 3. Assignment Points
    completed_tasks_count = session.exec(select(func.count(Task.id)).where(
        (Task.student_id == current_student.id) &
        (Task.status == "completed")
    )).one()
    assignment_points = completed_tasks_count * 20.0

    # 4. Tutorial Points
    completed_tutorials_count = session.exec(select(func.count(Tutorial.id)).where(
        (Tutorial.student_id == current_student.id) &
        (Tutorial.status == TutorialStatus.COMPLETED)
    )).one()
    tutorial_points = completed_tutorials_count * 30.0
    
    # 5. Time Points
    time_points = total_sessions * 2.0

    total_calculated_score = chat_points + quiz_points + assignment_points + tutorial_points + time_points
    
    # Use the higher of calculated vs persisted score (to account for ad-hoc bonuses)
    final_score = max(total_calculated_score, current_student.engagement_score or 0.0)

    if final_score >= 100: 
         badges.append({"name": "Rising Star", "description": "Earned 100+ engagement points", "icon": "🌟"})
    if final_score >= 200: 
         badges.append({"name": "High Flyer", "description": "Earned 200+ engagement points", "icon": "🚀"})
    if final_score >= 500: 
         badges.append({"name": "Elite Scholar", "description": "Earned 500+ engagement points", "icon": "🎓"})
    if final_score >= 1000: 
         badges.append({"name": "Legendary Learner", "description": "Earned 1000+ engagement points", "icon": "👑"})
    
    

    return {
        "full_name": current_student.full_name,
        "age": current_student.age,
        "engagement_score": round(final_score, 1), # Return correct score
        "total_sessions": total_sessions,
        "total_tests": total_tests,
        "correct_tests": correct_tests,
        "active_days": active_days,
        "engagement_score": current_student.engagement_score or 0.0,
        "badges": badges
    }

@router.get("/schedule", response_model=List[dict])
async def get_my_schedule(
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get my tutorial schedule"""
    # Get upcoming tutorials
    tutorials = session.exec(
        select(Tutorial).where(
            (Tutorial.student_id == current_student.id) &
            (Tutorial.status == TutorialStatus.SCHEDULED) &
            (Tutorial.scheduled_time >= datetime.now(timezone.utc))
        ).order_by(Tutorial.scheduled_time)
    ).all()
    
    result = []
    for tutorial in tutorials:
        from .models import User
        teacher = session.get(User, tutorial.teacher_id)
        
        result.append({
            "id": tutorial.id,
            "teacher_name": teacher.full_name if teacher else "Unknown",
            "scheduled_time": tutorial.scheduled_time,
            "duration_minutes": tutorial.duration_minutes,
            "subject": tutorial.subject,
            "notes": tutorial.notes,
            "status": tutorial.status
        })
    
    return result

@router.post("/generate-schedule", response_model=dict)
async def generate_ai_schedule_endpoint(
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Generate AI-powered weekly study schedule"""
    from .schedule_service import create_and_save_schedule
    
    # Use shared logic
    return create_and_save_schedule(session, current_student)

@router.get("/ai-schedule", response_model=dict)
async def get_my_ai_schedule(
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get persisted AI schedule"""
    timetables = session.exec(select(Timetable).where(Timetable.student_id == current_student.id)).all()
    
    if not timetables:
        return {"schedule": None}
        
    schedule = {}
    for entry in timetables:
        day = entry.day_of_week
        if day not in schedule:
            schedule[day] = []
        
        # Parse duration from end_time hack (e.g. "30 min")
        duration = 30
        try:
            if "min" in entry.end_time:
                duration = int(entry.end_time.replace("min", "").strip())
        except: pass
            
        schedule[day].append({
            "time": entry.start_time,
            "duration": duration,
            "subject": entry.subject if entry.subject != "Break" else None,
            "topic": entry.focus_topic,
            "type": entry.activity_type,
            "priority": entry.description.replace("Priority: ", "") if entry.description else None
        })
        
    # Sort by time? Assuming insertion order or sort client side. 
    # Frontend expects simple dict
    return {"schedule": schedule}

# ============================================================================
# CHAT HISTORY
# ============================================================================

@router.get("/chat-sessions", response_model=List[dict])
async def get_my_chat_sessions(
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get my chat sessions grouped by session_id"""
    # Get unique sessions with metadata
    sessions_data = session.exec(
        select(
            ChatHistory.session_id,
            func.max(ChatHistory.subject).label('subject'),
            func.min(ChatHistory.timestamp).label('start_time'),
            func.max(ChatHistory.timestamp).label('last_message_time'),
            func.count(ChatHistory.id).label('message_count')
        ).where(
            (ChatHistory.student_id == current_student.id) &
            (ChatHistory.session_id.isnot(None))
        ).group_by(ChatHistory.session_id)
        .order_by(func.max(ChatHistory.timestamp).desc())
    ).all()
    
    result = []
    for session_id, subject, start_time, last_message_time, message_count in sessions_data:
        # Get last message preview
        last_message = session.exec(
            select(ChatHistory).where(
                (ChatHistory.student_id == current_student.id) &
                (ChatHistory.session_id == session_id)
            ).order_by(ChatHistory.timestamp.desc()).limit(1)
        ).first()
        
        result.append({
            "session_id": session_id,
            "subject": subject or "General",
            "start_time": start_time,
            "last_message_time": last_message_time,
            "message_count": message_count,
            "last_message_preview": last_message.student_message[:100] if last_message else ""
        })
    
    return result

@router.get("/chat-history", response_model=List[dict])
async def get_my_chat_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    subject: Optional[str] = None,
    session_id: Optional[str] = None,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get my chat history organized by date and subject, optionally filtered by session"""
    statement = select(ChatHistory).where(ChatHistory.student_id == current_student.id)
    
    if subject:
        statement = statement.where(ChatHistory.subject == subject)
    
    if session_id:
        statement = statement.where(ChatHistory.session_id == session_id)
    
    # Order by timestamp - ascending if filtering by session (chronological), descending otherwise
    if session_id:
        statement = statement.order_by(ChatHistory.timestamp.asc()).offset(skip).limit(limit)
    else:
        statement = statement.order_by(ChatHistory.timestamp.desc()).offset(skip).limit(limit)
    
    chats = session.exec(statement).all()
    
    # Group by date
    grouped = {}
    for chat in chats:
        date_key = chat.timestamp.date().isoformat()
        if date_key not in grouped:
            grouped[date_key] = []
        
        grouped[date_key].append({
            "id": chat.id,
            "session_id": chat.session_id,
            "timestamp": chat.timestamp,
            "subject": chat.subject,
            "topic": chat.topic,
            "student_message": chat.student_message,
            "ai_response": chat.ai_response,
            "is_favorite": chat.is_favorite
        })
    
    # Convert to list format
    result = [
        {
            "date": date,
            "conversations": convs
        }
        for date, convs in grouped.items()
    ]
    
    return result

@router.put("/chat-history/{chat_id}/favorite", response_model=dict)
async def mark_conversation_favorite(
    chat_id: int,
    is_favorite: bool,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Mark a conversation as favorite"""
    chat = session.get(ChatHistory, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if chat.student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    chat.is_favorite = is_favorite
    session.add(chat)
    session.commit()
    session.refresh(chat)
    
    return {
        "id": chat.id,
        "is_favorite": chat.is_favorite,
        "message": "Conversation marked as favorite" if is_favorite else "Conversation unmarked as favorite"
    }

@router.post("/generate-quiz", response_model=dict)
async def generate_quiz(
    session_id: Optional[str] = None,
    subject: str = "General",
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Generate context-aware quiz questions based on conversation history"""
    from .ai_service import generate_context_quiz
    
    # Get recent conversation history
    statement = select(ChatHistory).where(
        ChatHistory.student_id == current_student.id
    )
    
    if session_id:
        statement = statement.where(ChatHistory.session_id == session_id)
    
    statement = statement.order_by(ChatHistory.timestamp.desc()).limit(10)
    chats = session.exec(statement).all()
    
    print(f"[QUIZ DEBUG] Found {len(chats)} chat messages for student {current_student.id}")
    print(f"[QUIZ DEBUG] Session ID: {session_id}, Subject: {subject}")
    
    # Convert to conversation history format
    conversation_history = []
    for chat in reversed(chats):  # Reverse to get chronological order
        conversation_history.append({"role": "user", "content": chat.student_message})
        conversation_history.append({"role": "assistant", "content": chat.ai_response})
    
    print(f"[QUIZ DEBUG] Conversation history length: {len(conversation_history)}")
    
    # Generate quiz questions
    questions = generate_context_quiz(current_student, conversation_history, subject)
    
    print(f"[QUIZ DEBUG] Generated {len(questions)} questions")
    
    return {
        "questions": questions,
        "session_id": session_id,
        "subject": subject
    }

# ============================================================================
# TASK MANAGEMENT
# ============================================================================

@router.get("/tasks", response_model=List[dict])
async def get_my_tasks(
    status_filter: Optional[str] = None,  # pending, completed
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Get my assigned tasks"""
    # Get tasks assigned specifically to me OR generic class tasks (if we had logic for that, currently assumes student_id assignment)
    # For now, we only implemented direct assignment in models.py logic comments, but let's stick to what we built: student_id link
    statement = select(Task).where(Task.student_id == current_student.id)
    
    if status_filter:
        statement = statement.where(Task.status == status_filter)
    
    statement = statement.order_by(Task.due_date)
    tasks = session.exec(statement).all()
    
    result = []
    for task in tasks:
        from .models import User
        teacher = session.get(User, task.teacher_id)
        
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "teacher_name": teacher.full_name if teacher else "Unknown",
            "status": task.status,
            "created_at": task.created_at
        })
    
    return result

@router.put("/tasks/{task_id}/complete", response_model=dict)
async def complete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """Mark a task as completed"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    task.status = "completed"
    session.add(task)
    
    # Award Engagement Points
    from .engagement_service import EngagementService
    result = EngagementService.award_points(session, current_student.id, 20.0, "task_completion")
    
    # Notify Teacher of completion
    from .notification_service import NotificationService
    NotificationService.notify_teacher(
        session,
        current_student.id,
        title=f"✅ Task Completed: {task.title}",
        message=f"{current_student.full_name} has completed the task '{task.title}'",
        notification_type="success",
        category="academic"
    )
    
    # Handle Achievements
    if result.get("new_achievements"):
        for ach in result["new_achievements"]:
            background_tasks.add_task(
                notify_parent_achievement_task, 
                current_student.id, 
                ach["title"], 
                ach["description"]
            )
    
    session.commit()
    
    return {"message": "Task marked as completed", "task_id": task_id, "points_earned": 20.0}

# ============================================================================
# VOICE CHAT
# ============================================================================

from fastapi import BackgroundTasks
from datetime import datetime
from .models import TestResult # Assuming TestResult is defined in .models

@router.post("/chat/voice")
async def voice_chat(
    text: str,
    background_tasks: BackgroundTasks,
    session_id: str = None,
    session: Session = Depends(get_db_session),
    current_student: Student = Depends(get_current_student)
):
    """
    Process voice chat input from student using Streaming Response.
    """
    from fastapi.responses import StreamingResponse
    from .agent_coordinator import AgentCoordinator
    from .database import engine 
    import uuid
    import json
    
    # 1. Ensure Session ID exists
    if not session_id:
        session_id = str(uuid.uuid4())
        
    # 2. Extract Subject (Simple Heuristic for initialization)
    subject = "General"
    message_lower = text.lower()
    if any(word in message_lower for word in ["math", "number", "calculate", "add"]): subject = "Mathematics"
    elif any(word in message_lower for word in ["science", "biology", "physics"]): subject = "Science"
    elif any(word in message_lower for word in ["read", "write", "book"]): subject = "English"

    # Capture ID to use in new session
    student_id = current_student.id
    
    async def response_generator():
        # Create NEW session for the long-running stream
        # This prevents "Instance not bound to Session" errors when the request session closes
        with Session(engine) as stream_session:
            try:
                # Re-fetch student in this session
                active_student = stream_session.get(Student, student_id)
                if not active_student:
                    yield json.dumps({"type": "response", "content": "Error: Student not found"}) + "\n"
                    return
                
                # Yield Session Info immediately
                yield json.dumps({
                    "type": "session_info", 
                    "session_id": session_id,
                    "subject": subject
                }) + "\n"
                
                # Initialize Coordinator with NEW session
                coordinator = AgentCoordinator(active_student, stream_session)
            
                # Delegate to Agent Coordinator Steam
                async for chunk in coordinator.handle_student_question_stream(text, subject):
                    yield chunk
            except Exception as e:
                print(f"Stream Error: {e}")
                yield json.dumps({"type": "response", "content": "Connection error during stream."}) + "\n"

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")





async def run_agent_coordination_task(student_id: str, user_text: str):
    """
    Background task to run the full Multi-Agent System.
    Creates its own DB session to avoid 'Session closed' errors.
    """
    from .database import engine
    from .models import Student
    from .agent_coordinator import AgentCoordinator
    from .ai_service import detect_question_in_message
    
    with Session(engine) as session:
        try:
            # Re-fetch student to ensure session attachment
            student = session.get(Student, student_id)
            if not student: return
            
            # Detect if it's a question worth analyzing
            if detect_question_in_message(user_text):
                print(f"[AGENTS] Activating Multi-Agent System for: {user_text[:30]}...")
                
                # Initialize Coordinator
                coordinator = AgentCoordinator(student, session)
                
                # Determine subject (heuristic or default)
                subject = "General" 
                
                # Run coordination
                await coordinator.handle_student_question(user_text, subject)
        except Exception as e:
            print(f"Error in agent coordination task: {e}")
            import traceback
            traceback.print_exc()
            
            print(f"[AGENTS] Multi-Agent coordination complete.")

async def notify_parent_achievement_task(student_id: str, title: str, description: str):
    """
    Background task to notify parent of student achievement via WhatsApp
    """
    from .database import engine
    from .models import Student
    from .twilio_whatsapp_service import notify_parent
    
    with Session(engine) as session:
        try:
            student = session.get(Student, student_id)
            if not student or not student.parent_whatsapp:
                return
            
            print(f"[PARENT-CONNECT] Notifying parent of {student.full_name} about achievement: {title}")
            
            print(f"[PARENT-CONNECT] Notifying parent of {student.full_name} about achievement: {title}")
            
            # Use ParentConnectAgent for personalized AI message
            from .specialized_agents import ParentConnectAgent
            agent = ParentConnectAgent(student, session)
            await agent.notify_achievement(title, description)
            
        except Exception as e:
            print(f"Error in parent notification task: {e}")
            



async def update_student_memory_task(student_id: str, user_text: str, ai_text: str):
    """Background task to update agent memory from conversation"""
    try:
        from .database import engine
        from .agent_memory import get_student_memory
        
        with Session(engine) as session:
            memory_service = get_student_memory(student_id, session)
            memory_service.update_interaction()
            
            # Simple heuristic learning: 
            # If user expresses confusion ("I don't understand", "Explain again"), add to revisit
            msg_lower = user_text.lower()
            if "don't understand" in msg_lower or "confused" in msg_lower:
                # Try to extract topic or just mark generic
                memory_service.add_topic_to_revisit("Recent Topic", "Student expressed confusion")
                
            # If user says "I get it" or "understood", mark as success (simplified)
            if "i get it" in msg_lower or "understood" in msg_lower:
                 memory_service.add_effective_strategy("Explanation") # Placeholder
                 
    except Exception as e:
        print(f"Memory update error: {e}")

async def generate_test_task(student: Student, chat_id: int, user_text: str, ai_text: str, session: Session):
    """Background task to generation quiz questions"""
    try:
        # Check if we should generate a test
        # We need the full history, but for speed we might just use the current context
        # Or fetch history here.
        
        # Assuming these functions are defined or imported from ai_service or a quiz_service
        from .ai_service import should_generate_test, generate_test_question 

        # Re-fetch history for context
        recent_chats = session.exec(
            select(ChatHistory).where(ChatHistory.student_id == student.id).order_by(ChatHistory.timestamp.desc()).limit(6)
        ).all()
        
        conversation_history = []
        for chat in reversed(recent_chats):
            conversation_history.append({"role": "user", "content": chat.student_message})
            conversation_history.append({"role": "assistant", "content": chat.ai_response})
            
        if should_generate_test(conversation_history):
            # Generate test question
            conversation_context = f"Student: {user_text}\nAI: {ai_text}"
            test_data = generate_test_question(
                student=student,
                subject="General", # We could infer subject
                topic="Recent discussion",
                conversation_context=conversation_context
            )
            
            if test_data:
                new_test = TestResult(
                    student_id=student.id,
                    chat_history_id=chat_id,
                    timestamp=datetime.now(timezone.utc),
                    subject="General",
                    topic=test_data["topic"],
                    question=test_data["question"],
                    student_answer="",
                    correct_answer=test_data["correct_answer"],
                    is_correct=False,
                    attempt_number=1,
                    ai_feedback=""
                )
                session.add(new_test)
                session.commit()
                print(f"Check-in quiz generated for student {student.id}")
                
    except Exception as e:
        print(f"Test key-generation background error: {e}")
