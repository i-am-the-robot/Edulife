"""
Teacher Router
Handles teacher dashboard functionality: student monitoring, tutorials, and reports
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from .database import get_db_session
from .auth import get_current_teacher
from .utils import get_status_indicator, generate_student_id
from .notification_service import NotificationService
from .schemas import StudentResponse, StudentRegister, StudentDetailedResponse, PasswordChange
from .models import (
    User, Student, ChatHistory, TestResult, Tutorial, TutorialStatus, 
    UserRole, Task, School, AssignmentStudySession, LearningProfile, 
    TeacherNotification
)

router = APIRouter(prefix="/api/teacher", tags=["Teacher"])

# ============================================================================
# STUDENT MANAGEMENT
# ============================================================================

@router.get("/students", response_model=List[dict])
async def get_my_students(
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get all students created by this teacher with status indicators"""
    # For now, allow all teachers to see all students in their school
    # This allows them to see students registered by admins or other teachers
    statement = select(Student).where(
        (Student.is_active == True) &
        (
            (Student.school_id == current_teacher.school_id) |
            (Student.created_by_user_id == current_teacher.id)
        )
    )
    
    students = session.exec(statement).all()
    
    result = []
    for student in students:
        # Calculate status indicator
        status = get_status_indicator(student.engagement_score, student.last_active)
        
        # Get recent activity count
        recent_chats = session.exec(
            select(func.count(ChatHistory.id)).where(
                (ChatHistory.student_id == student.id) &
                (ChatHistory.timestamp >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0))
            )
        ).one()
        
        result.append({
            "id": student.id,
            "full_name": student.full_name,
            "age": student.age,
            "student_class": student.student_class,
            "engagement_score": student.engagement_score,
            "last_active": student.last_active,
            "status": status,
            "recent_activity_count": recent_chats,
            "learning_profile": student.learning_profile,
            "support_type": student.support_type
        })
    
    return result

@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def register_student(
    student_data: StudentRegister,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Register a new student for the teacher's school"""
    # Verify school match
    if student_data.school_id != current_teacher.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only register students for your own school"
        )
    
    # Generate unique student ID
    # Format: {school_id}_student_{timestamp_last_6_digits}
    # In production, use a more robust ID generator or counter
    base_id = f"{student_data.school_id}_student_"
    
    # Try to generate unique ID
    import time
    timestamp = str(int(time.time() * 1000))
    student_id = f"{base_id}{timestamp}"
    
    # Check if ID exists (highly unlikely with timestamp but good practice)
    existing_student = session.get(Student, student_id)
    if existing_student:
        import uuid
        student_id = f"{base_id}{uuid.uuid4().hex[:8]}"
    
    # Create student
    new_student = Student(
        id=student_id,
        full_name=student_data.full_name,
        age=student_data.age,
        student_class=student_data.student_class,
        hobby=student_data.hobby,
        personality=student_data.personality,
        school_id=student_data.school_id,
        created_by_user_id=current_teacher.id,
        learning_profile=student_data.learning_profile,
        support_type=student_data.support_type,
        learning_preferences=student_data.learning_preferences,
        parent_whatsapp=student_data.parent_whatsapp,  # Add parent WhatsApp
        is_active=True,
        enrollment_date=datetime.now(timezone.utc)
    )
    
    session.add(new_student)
    session.commit()
    session.refresh(new_student)
    
    # Send WhatsApp enrollment notification to parent
    if new_student.parent_whatsapp:
        try:
            from .twilio_whatsapp_service import whatsapp_service
            
            # Get school name
            school = session.get(School, new_student.school_id)
            school_name = school.name if school else "EduLife"
            
            enrollment_message = f"""🎓 *Welcome to EduLife!*

Hello! Your child *{new_student.full_name}* has been successfully enrolled on the EduLife platform.

📚 *School:* {school_name}
👤 *Student ID:* {new_student.id}
📅 *Enrollment Date:* {new_student.enrollment_date.strftime("%B %d, %Y")}

Our AI-powered learning system will provide personalized education tailored to your child's needs.

You'll receive regular updates about:
• Quiz results and achievements
• Study progress and milestones  
• Learning recommendations
• Important reminders

Welcome to the future of inclusive education! 🌟

_Edu-Life - Learn Without Limits_"""
            
            whatsapp_service.send_whatsapp_message(
                to_number=new_student.parent_whatsapp,
                message=enrollment_message
            )
        except Exception as e:
            # Log error but don't fail registration
            print(f"[WARNING] Failed to send enrollment WhatsApp: {e}")
    
    return new_student



@router.get("/students/{student_id}", response_model=dict)
async def get_student_detailed(
    student_id: str,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get detailed view of a specific student"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check access rights
    if current_teacher.role == UserRole.HEAD_TEACHER:
        if student.school_id != current_teacher.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if student.created_by_user_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get statistics
    total_sessions = session.exec(
        select(func.count(ChatHistory.session_id.distinct())).where(
            ChatHistory.student_id == student_id
        )
    ).one()
    
    total_tests = session.exec(
        select(func.count(TestResult.id)).where(TestResult.student_id == student_id)
    ).one()
    
    correct_tests = session.exec(
        select(func.count(TestResult.id)).where(
            (TestResult.student_id == student_id) &
            (TestResult.is_correct == True)
        )
    ).one()
    
    test_success_rate = (correct_tests / total_tests * 100) if total_tests > 0 else 0.0
    
    # Get favorite subjects
    subject_counts = session.exec(
        select(ChatHistory.subject, func.count(ChatHistory.id)).where(
            (ChatHistory.student_id == student_id) &
            (ChatHistory.subject.isnot(None))
        ).group_by(ChatHistory.subject).order_by(func.count(ChatHistory.id).desc())
    ).all()
    
    favorite_subjects = [subject for subject, _ in subject_counts[:3]]
    
    return {
        **StudentDetailedResponse.model_validate(student).model_dump(),
        "total_sessions": total_sessions,
        "total_tests": total_tests,
        "test_success_rate": round(test_success_rate, 2),
        "favorite_subjects": favorite_subjects,
        "status": get_status_indicator(student.engagement_score, student.last_active)
    }

@router.get("/students/{student_id}/chat-history", response_model=List[dict])
async def get_student_chat_history(
    student_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """View student's chat history"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check access
    if current_teacher.role == UserRole.HEAD_TEACHER:
        if student.school_id != current_teacher.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if student.created_by_user_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    statement = select(ChatHistory).where(
        ChatHistory.student_id == student_id
    ).order_by(ChatHistory.timestamp.desc()).offset(skip).limit(limit)
    
    chats = session.exec(statement).all()
    
    return [
        {
            "id": chat.id,
            "session_id": chat.session_id,
            "timestamp": chat.timestamp,
            "subject": chat.subject,
            "topic": chat.topic,
            "student_message": chat.student_message,
            "ai_response": chat.ai_response,
            "is_favorite": chat.is_favorite
        }
        for chat in chats
    ]

@router.get("/students/{student_id}/test-results", response_model=List[dict])
async def get_student_test_results(
    student_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """View student's test results"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check access
    if current_teacher.role == UserRole.HEAD_TEACHER:
        if student.school_id != current_teacher.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if student.created_by_user_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    statement = select(TestResult).where(
        TestResult.student_id == student_id
    ).order_by(TestResult.timestamp.desc()).offset(skip).limit(limit)
    
    tests = session.exec(statement).all()
    
    return [
        {
            "id": test.id,
            "timestamp": test.timestamp,
            "subject": test.subject,
            "topic": test.topic,
            "question": test.question,
            "student_answer": test.student_answer,
            "correct_answer": test.correct_answer,
            "is_correct": test.is_correct,
            "attempt_number": test.attempt_number,
            "time_spent_seconds": test.time_spent_seconds,
            "ai_feedback": test.ai_feedback
        }
        for test in tests
    ]

@router.get("/students/{student_id}/analytics", response_model=dict)
async def get_student_analytics(
    student_id: str,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get detailed analytics for a student"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check access
    if current_teacher.role == UserRole.HEAD_TEACHER:
        if student.school_id != current_teacher.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if student.created_by_user_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Overall stats
    total_sessions = session.exec(
        select(func.count(ChatHistory.session_id.distinct())).where(
            ChatHistory.student_id == student_id
        )
    ).one()
    
    total_tests = session.exec(
        select(func.count(TestResult.id)).where(TestResult.student_id == student_id)
    ).one()
    
    correct_tests = session.exec(
        select(func.count(TestResult.id)).where(
            (TestResult.student_id == student_id) &
            (TestResult.is_correct == True)
        )
    ).one()
    
    # Subject breakdown
    subject_stats = session.exec(
        select(
            TestResult.subject,
            func.count(TestResult.id).label('total'),
            func.sum(func.cast(TestResult.is_correct, int)).label('correct')
        ).where(
            TestResult.student_id == student_id
        ).group_by(TestResult.subject)
    ).all()
    
    subject_performance = [
        {
            "subject": subject,
            "total_tests": total,
            "correct_tests": correct or 0,
            "success_rate": round((correct or 0) / total * 100, 2) if total > 0 else 0.0
        }
        for subject, total, correct in subject_stats
    ]
    
    # Recent activity (last 7 days)
    seven_days_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0) - timedelta(days=7)
    recent_sessions = session.exec(
        select(func.count(ChatHistory.session_id.distinct())).where(
            (ChatHistory.student_id == student_id) &
            (ChatHistory.timestamp >= seven_days_ago)
        )
    ).one()
    
    return {
        "student_id": student_id,
        "engagement_score": student.engagement_score or 0.0,
        "total_sessions": total_sessions,
        "total_tests": total_tests,
        "correct_tests": correct_tests,
        "overall_success_rate": round((correct_tests / total_tests * 100), 2) if total_tests > 0 else 0.0,
        "subject_performance": subject_performance,
        "recent_sessions_7days": recent_sessions,
        "login_frequency": student.login_frequency or 0,
        "last_active": student.last_active
    }

# ============================================================================
# CONVERSATION ANSWERS
# ============================================================================

@router.get("/students/{student_id}/conversation-answers", response_model=dict)
async def get_student_conversation_answers(
    student_id: str,
    limit: int = Query(50, ge=1, le=100),
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get conversation answers for a student"""
    from .models import ConversationAnswer
    
    # Verify access
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if teacher has access to this student
    if current_teacher.role != UserRole.HEAD_TEACHER:
        if student.created_by_user_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif student.school_id != current_teacher.school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get total count and points
    total_count = session.exec(
        select(func.count(ConversationAnswer.id)).where(
            ConversationAnswer.student_id == student_id
        )
    ).one()
    
    total_points = session.exec(
        select(func.sum(ConversationAnswer.points_awarded)).where(
            ConversationAnswer.student_id == student_id
        )
    ).one() or 0.0
    
    # Get recent conversation answers
    answers = session.exec(
        select(ConversationAnswer).where(
            ConversationAnswer.student_id == student_id
        ).order_by(ConversationAnswer.timestamp.desc()).limit(limit)
    ).all()
    
    return {
        "student_id": student_id,
        "total_count": total_count,
        "total_points": round(total_points, 1),
        "answers": [
            {
                "id": answer.id,
                "timestamp": answer.timestamp,
                "question": answer.question,
                "student_answer": answer.student_answer,
                "points_awarded": answer.points_awarded,
                "subject": answer.subject,
                "topic": answer.topic
            }
            for answer in answers
        ]
    }

# ============================================================================
# ASSIGNMENT SUBMISSIONS
# ============================================================================

@router.get("/students/{student_id}/assignment-submissions", response_model=List[dict])
async def get_student_assignment_submissions(
    student_id: str,
    status_filter: Optional[str] = None,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get all assignment submissions for a specific student"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check access
    if current_teacher.role == UserRole.HEAD_TEACHER:
        if student.school_id != current_teacher.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if student.created_by_user_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Build query
    statement = select(AssignmentStudySession).where(
        AssignmentStudySession.student_id == student_id
    )
    
    if status_filter:
        statement = statement.where(AssignmentStudySession.status == status_filter)
    
    statement = statement.order_by(AssignmentStudySession.started_at.desc())
    
    submissions = session.exec(statement).all()
    
    result = []
    for submission in submissions:
        # Get task details
        task = session.get(Task, submission.task_id)
        if not task:
            continue
        
        result.append({
            "id": submission.id,
            "task_id": submission.task_id,
            "task_title": task.title,
            "task_description": task.description,
            "task_due_date": task.due_date,
            "status": submission.status,
            "conversation_count": submission.conversation_count,
            "quiz_score": submission.quiz_score,
            "final_score": submission.final_score,
            "started_at": submission.started_at,
            "completed_at": submission.completed_at,
            "submitted_to_teacher": submission.submitted_to_teacher,
            "has_summary": submission.summary is not None
        })
    
    return result

@router.get("/assignments/{submission_id}/details", response_model=dict)
async def get_assignment_submission_details(
    submission_id: int,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get detailed view of a specific assignment submission"""
    import json
    
    submission = session.get(AssignmentStudySession, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Assignment submission not found")
    
    # Get student and verify access
    student = session.get(Student, submission.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check access
    if current_teacher.role == UserRole.HEAD_TEACHER:
        if student.school_id != current_teacher.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if student.created_by_user_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get task details
    task = session.get(Task, submission.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Mark as viewed by teacher
    if not submission.viewed_by_teacher:
        submission.viewed_by_teacher = True
        submission.viewed_at = datetime.now(timezone.utc)
        session.add(submission)
        session.commit()
    
    # Get conversation history for this study session
    chat_history = session.exec(select(ChatHistory).where(
        (ChatHistory.student_id == submission.student_id) &
        (ChatHistory.session_id == submission.chat_session_id)
    ).order_by(ChatHistory.timestamp.asc())).all()
    
    # Parse JSON fields
    quiz_questions = json.loads(submission.quiz_questions) if submission.quiz_questions else []
    quiz_answers = json.loads(submission.quiz_answers) if submission.quiz_answers else []
    final_questions = json.loads(submission.final_questions) if submission.final_questions else []
    final_answers = json.loads(submission.final_answers) if submission.final_answers else []
    
    # Calculate time spent
    time_spent_minutes = None
    if submission.completed_at and submission.started_at:
        time_delta = submission.completed_at - submission.started_at
        time_spent_minutes = int(time_delta.total_seconds() / 60)
    
    return {
        "submission_id": submission.id,
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "student_class": student.student_class
        },
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date
        },
        "status": submission.status,
        "conversation_count": submission.conversation_count,
        "time_spent_minutes": time_spent_minutes,
        "quiz": {
            "questions": quiz_questions,
            "answers": quiz_answers,
            "score": submission.quiz_score
        },
        "final_assessment": {
            "questions": final_questions,
            "answers": final_answers,
            "score": submission.final_score
        },
        "summary": submission.summary,
        "conversation_history": [
            {
                "timestamp": chat.timestamp,
                "student_message": chat.student_message,
                "ai_response": chat.ai_response,
                "subject": chat.subject
            }
            for chat in chat_history
        ],
        "started_at": submission.started_at,
        "completed_at": submission.completed_at,
        "submitted_to_teacher": submission.submitted_to_teacher
    }

@router.get("/assignments/pending", response_model=dict)
async def get_pending_assignments(
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get count and list of pending assignment submissions for dashboard"""
    # Get all students for this teacher
    if current_teacher.role == UserRole.HEAD_TEACHER:
        students = session.exec(select(Student).where(
            (Student.school_id == current_teacher.school_id) &
            (Student.is_active == True)
        )).all()
    else:
        students = session.exec(select(Student).where(
            (Student.created_by_user_id == current_teacher.id) &
            (Student.is_active == True)
        )).all()
    
    student_ids = [s.id for s in students]
    
    # Get completed but unreviewed submissions
    pending_submissions = session.exec(select(AssignmentStudySession).where(
        (AssignmentStudySession.student_id.in_(student_ids)) &
        (AssignmentStudySession.status == "completed") &
        (AssignmentStudySession.submitted_to_teacher == True)
    ).order_by(AssignmentStudySession.completed_at.desc()).limit(10)).all()
    
    result = []
    for submission in pending_submissions:
        student = session.get(Student, submission.student_id)
        task = session.get(Task, submission.task_id)
        if student and task:
            result.append({
                "submission_id": submission.id,
                "student_id": student.id,
                "student_name": student.full_name,
                "task_title": task.title,
                "final_score": submission.final_score,
                "completed_at": submission.completed_at
            })
    
    return {
        "pending_count": len(pending_submissions),
        "recent_submissions": result
    }

# ============================================================================
# TUTORIAL MANAGEMENT
# ============================================================================

@router.post("/tutorials", response_model=dict, status_code=status.HTTP_201_CREATED)
async def schedule_tutorial(
    student_id: str,
    scheduled_time: datetime,
    duration_minutes: int,
    subject: Optional[str] = None,
    notes: Optional[str] = None,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Schedule a tutorial with a student"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check access
    if current_teacher.role == UserRole.HEAD_TEACHER:
        if student.school_id != current_teacher.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if student.created_by_user_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    new_tutorial = Tutorial(
        teacher_id=current_teacher.id,
        student_id=student_id,
        scheduled_time=scheduled_time,
        duration_minutes=duration_minutes,
        subject=subject,
        notes=notes,
        status=TutorialStatus.SCHEDULED,
        created_at=datetime.now(timezone.utc)
    )
    
    session.add(new_tutorial)
    session.commit()
    session.refresh(new_tutorial)
    
    return {
        "id": new_tutorial.id,
        "teacher_id": new_tutorial.teacher_id,
        "student_id": new_tutorial.student_id,
        "student_name": student.full_name,
        "scheduled_time": new_tutorial.scheduled_time,
        "duration_minutes": new_tutorial.duration_minutes,
        "subject": new_tutorial.subject,
        "notes": new_tutorial.notes,
        "status": new_tutorial.status,
        "created_at": new_tutorial.created_at
    }

@router.get("/tutorials", response_model=List[dict])
async def get_my_tutorials(
    status_filter: Optional[TutorialStatus] = None,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """List all tutorials for this teacher"""
    statement = select(Tutorial).where(Tutorial.teacher_id == current_teacher.id)
    
    if status_filter:
        statement = statement.where(Tutorial.status == status_filter)
    
    statement = statement.order_by(Tutorial.scheduled_time.desc())
    tutorials = session.exec(statement).all()
    
    result = []
    for tutorial in tutorials:
        student = session.get(Student, tutorial.student_id)
        result.append({
            "id": tutorial.id,
            "student_id": tutorial.student_id,
            "student_name": student.full_name if student else "Unknown",
            "scheduled_time": tutorial.scheduled_time,
            "duration_minutes": tutorial.duration_minutes,
            "subject": tutorial.subject,
            "notes": tutorial.notes,
            "status": tutorial.status,
            "created_at": tutorial.created_at
        })
    
    return result

@router.put("/tutorials/{tutorial_id}", response_model=dict)
async def update_tutorial(
    tutorial_id: int,
    scheduled_time: Optional[datetime] = None,
    duration_minutes: Optional[int] = None,
    subject: Optional[str] = None,
    notes: Optional[str] = None,
    status: Optional[TutorialStatus] = None,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Update a tutorial"""
    tutorial = session.get(Tutorial, tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    if tutorial.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if scheduled_time:
        tutorial.scheduled_time = scheduled_time
    if duration_minutes:
        tutorial.duration_minutes = duration_minutes
    if subject is not None:
        tutorial.subject = subject
    if notes is not None:
        tutorial.notes = notes
    if status:
        # Check if marking as completed for the first time or re-completing
        if status == TutorialStatus.COMPLETED and tutorial.status != TutorialStatus.COMPLETED:
             # Award Engagement Points
             from .engagement_service import EngagementService
             EngagementService.award_points(session, tutorial.student_id, 30.0, "tutorial_completion")
             
        tutorial.status = status
    
    session.add(tutorial)
    session.commit()
    session.refresh(tutorial)
    
    student = session.get(Student, tutorial.student_id)
    
    return {
        "id": tutorial.id,
        "student_id": tutorial.student_id,
        "student_name": student.full_name if student else "Unknown",
        "scheduled_time": tutorial.scheduled_time,
        "duration_minutes": tutorial.duration_minutes,
        "subject": tutorial.subject,
        "notes": tutorial.notes,
        "status": tutorial.status
    }

@router.delete("/tutorials/{tutorial_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_tutorial(
    tutorial_id: int,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Cancel a tutorial"""
    tutorial = session.get(Tutorial, tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    if tutorial.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    tutorial.status = TutorialStatus.CANCELLED
    session.add(tutorial)
    session.commit()
    
    return None

# ============================================================================
# REPORTS
# ============================================================================

@router.get("/students/{student_id}/report", response_model=dict)
async def generate_student_report(
    student_id: str,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate comprehensive student progress report"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check access
    if current_teacher.role == UserRole.HEAD_TEACHER:
        if student.school_id != current_teacher.school_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        if student.created_by_user_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get comprehensive stats
    analytics = await get_student_analytics(student_id, session, current_teacher)
    
    # Get recent conversations
    recent_chats = session.exec(
        select(ChatHistory).where(
            ChatHistory.student_id == student_id
        ).order_by(ChatHistory.timestamp.desc()).limit(10)
    ).all()
    
    # Get upcoming tutorials
    upcoming_tutorials = session.exec(
        select(Tutorial).where(
            (Tutorial.student_id == student_id) &
            (Tutorial.status == TutorialStatus.SCHEDULED) &
            (Tutorial.scheduled_time >= datetime.utcnow())
        ).order_by(Tutorial.scheduled_time)
    ).all()
    
    return {
        "student_info": {
            "id": student.id,
            "full_name": student.full_name,
            "age": student.age,
            "class": student.student_class,
            "hobby": student.hobby,
            "personality": student.personality,
            "learning_profile": student.learning_profile,
            "support_type": student.support_type
        },
        "analytics": analytics,
        "recent_activity": [
            {
                "timestamp": chat.timestamp,
                "subject": chat.subject,
                "topic": chat.topic
            }
            for chat in recent_chats
        ],
        "upcoming_tutorials": [
            {
                "scheduled_time": t.scheduled_time,
                "duration_minutes": t.duration_minutes,
                "subject": t.subject
            }
            for t in upcoming_tutorials
        ],
        "status": get_status_indicator(student.engagement_score, student.last_active),
        "generated_at": datetime.utcnow()
    }

# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

@router.put("/change-password")
async def change_teacher_password(
    password_data: PasswordChange,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Change teacher password"""
    from .auth import verify_password, get_password_hash
    
    # Verify current password
    if not verify_password(password_data.current_password, current_teacher.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_teacher.hashed_password = get_password_hash(password_data.new_password)
    session.add(current_teacher)
    session.commit()
    
    return {"message": "Password changed successfully"}

# ============================================================================
# TASK MANAGEMENT
# ============================================================================

@router.post("/tasks", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_task(
    title: str,
    description: str,
    due_date: datetime,
    student_id: Optional[str] = None,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Create a new task assignment"""
    # Verify student if provided
    if student_id:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Check access
        if current_teacher.role == UserRole.HEAD_TEACHER:
            if student.school_id != current_teacher.school_id:
                raise HTTPException(status_code=403, detail="Access denied")
        else:
            if student.created_by_user_id != current_teacher.id:
                raise HTTPException(status_code=403, detail="Access denied")
    
    new_task = Task(
        title=title,
        description=description,
        due_date=due_date,
        teacher_id=current_teacher.id,
        student_id=student_id,
        status="pending",
        created_at=datetime.utcnow()
    )
    
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    
    return {
        "id": new_task.id,
        "title": new_task.title,
        "description": new_task.description,
        "due_date": new_task.due_date.isoformat(),
        "teacher_id": new_task.teacher_id,
        "student_id": new_task.student_id,
        "status": new_task.status,
        "created_at": new_task.created_at.isoformat()
    }

@router.get("/tasks", response_model=List[dict])
async def list_teacher_tasks(
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """List tasks created by this teacher"""
    statement = select(Task).where(Task.teacher_id == current_teacher.id).order_by(Task.due_date)
    tasks = session.exec(statement).all()
    
    result = []
    for task in tasks:
        student_name = "All Students"
        if task.student_id:
            student = session.get(Student, task.student_id)
            if student:
                student_name = student.full_name
        
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "student_id": task.student_id,
            "student_name": student_name,
            "status": task.status,
            "created_at": task.created_at
        })
    return result

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Delete a task"""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    session.delete(task)
    session.commit()
    return None

# ============================================================================
# SYLLABUS MANAGEMENT
# ============================================================================

@router.post("/syllabus/upload")
async def upload_syllabus(
    syllabus_text: str,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Update school syllabus text"""
    # Only allow for teachers with a school
    if not current_teacher.school_id:
         raise HTTPException(status_code=400, detail="Teacher not assigned to a school")
         
    school = session.get(School, current_teacher.school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    school.syllabus_text = syllabus_text
    session.add(school)
    session.commit()
    
    return {"message": "Syllabus updated successfully"}

# ============================================================================
# NOTIFICATIONS & ACTIVITY FEED
# ============================================================================

@router.get("/notifications", response_model=List[dict])
async def get_my_notifications(
    unread_only: bool = False,
    limit: int = 20,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get teacher notifications / activity feed"""
    notifications = NotificationService.get_teacher_notifications(
        session, 
        current_teacher.id, 
        limit=limit, 
        unread_only=unread_only
    )
    
    result = []
    for notif in notifications:
        student_name = "System"
        if notif.student_id:
            student = session.get(Student, notif.student_id)
            if student:
                student_name = student.full_name
                
        result.append({
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "type": notif.type,
            "category": notif.category,
            "is_read": notif.is_read,
            "created_at": notif.created_at,
            "student_name": student_name,
            "student_id": notif.student_id
        })
        
    return result

@router.put("/notifications/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    notification_id: int,
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Mark a notification as read"""
    notification = session.get(TeacherNotification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    if notification.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    notification.is_read = True
    session.add(notification)
    session.commit()
    
    return {"status": "success"}

@router.put("/notifications/read-all", response_model=dict)
async def mark_all_notifications_read(
    session: Session = Depends(get_db_session),
    current_teacher: User = Depends(get_current_teacher)
):
    """Mark all notifications as read"""
    statement = select(TeacherNotification).where(
        (TeacherNotification.teacher_id == current_teacher.id) &
        (TeacherNotification.is_read == False)
    )
    notifications = session.exec(statement).all()
    
    for notif in notifications:
        notif.is_read = True
        session.add(notif)
        
    session.commit()
    return {"count": len(notifications)}

