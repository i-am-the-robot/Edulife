"""
Admin Router
Handles school, teacher, and student management for administrators
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime, timedelta

from .database import get_db_session
from .models import Admin, School, User, Student, ChatHistory, TestResult, UserRole
from .schemas import (
    SchoolCreate, SchoolUpdate, SchoolResponse,
    TeacherRegister, TeacherUpdate, TeacherResponse,
    StudentRegister, StudentUpdate, StudentDetailedResponse,
    SystemOverview, SchoolAnalytics, PasswordChange
)
from .auth import get_current_admin, get_password_hash
from .utils import generate_app_key, generate_student_id

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ============================================================================
# SCHOOL MANAGEMENT
# ============================================================================

@router.post("/schools", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreate,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Create a new school with auto-generated app_key"""
    # Generate unique app_key
    app_key = generate_app_key()
    
    # Ensure uniqueness
    while session.exec(select(School).where(School.app_key == app_key)).first():
        app_key = generate_app_key()
    
    new_school = School(
        name=school_data.name,
        app_key=app_key,
        location=school_data.location,
        contact_email=school_data.contact_email,
        contact_phone=school_data.contact_phone,
        grade_levels=school_data.grade_levels,
        syllabus_text=school_data.syllabus_text,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    session.add(new_school)
    session.commit()
    session.refresh(new_school)
    
    # Get counts
    teacher_count = session.exec(
        select(func.count(User.id)).where(User.school_id == new_school.id)
    ).one()
    student_count = session.exec(
        select(func.count(Student.id)).where(Student.school_id == new_school.id)
    ).one()
    
    response = SchoolResponse.model_validate(new_school)
    response.teacher_count = teacher_count
    response.student_count = student_count
    
    return response

@router.get("/schools", response_model=List[SchoolResponse])
async def list_schools(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """List all schools with teacher and student counts"""
    statement = select(School)
    
    if is_active is not None:
        statement = statement.where(School.is_active == is_active)
    
    statement = statement.offset(skip).limit(limit)
    schools = session.exec(statement).all()
    
    result = []
    for school in schools:
        teacher_count = session.exec(
            select(func.count(User.id)).where(User.school_id == school.id)
        ).one()
        student_count = session.exec(
            select(func.count(Student.id)).where(Student.school_id == school.id)
        ).one()
        
        school_response = SchoolResponse.model_validate(school)
        school_response.teacher_count = teacher_count
        school_response.student_count = student_count
        result.append(school_response)
    
    return result

@router.get("/schools/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: int,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get school details"""
    school = session.get(School, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    teacher_count = session.exec(
        select(func.count(User.id)).where(User.school_id == school.id)
    ).one()
    student_count = session.exec(
        select(func.count(Student.id)).where(Student.school_id == school.id)
    ).one()
    
    response = SchoolResponse.model_validate(school)
    response.teacher_count = teacher_count
    response.student_count = student_count
    
    return response

@router.put("/schools/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: int,
    school_data: SchoolUpdate,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update school information"""
    school = session.get(School, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    # Update fields
    update_data = school_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(school, key, value)
    
    session.add(school)
    session.commit()
    session.refresh(school)
    
    teacher_count = session.exec(
        select(func.count(User.id)).where(User.school_id == school.id)
    ).one()
    student_count = session.exec(
        select(func.count(Student.id)).where(Student.school_id == school.id)
    ).one()
    
    response = SchoolResponse.model_validate(school)
    response.teacher_count = teacher_count
    response.student_count = student_count
    
    return response

@router.delete("/schools/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_school(
    school_id: int,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Deactivate a school"""
    school = session.get(School, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    school.is_active = False
    session.add(school)
    session.commit()
    
    return None

# ============================================================================
# TEACHER MANAGEMENT
# ============================================================================

@router.post("/teachers", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: TeacherRegister,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Register a new teacher (admin version)"""
    # Validate school
    statement = select(School).where(School.app_key == teacher_data.app_key)
    school = session.exec(statement).first()
    if not school:
        raise HTTPException(status_code=400, detail="Invalid school app key")
    
    # Check email
    if session.exec(select(User).where(User.email == teacher_data.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(teacher_data.password)
    new_teacher = User(
        full_name=teacher_data.full_name,
        email=teacher_data.email,
        hashed_password=hashed_password,
        address=teacher_data.address,
        phone=teacher_data.phone,
        role=teacher_data.role,
        school_id=school.id,
        subjects=teacher_data.subjects,
        years_experience=teacher_data.years_experience,
        specializations=teacher_data.specializations,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    session.add(new_teacher)
    session.commit()
    session.refresh(new_teacher)
    
    student_count = session.exec(
        select(func.count(Student.id)).where(Student.created_by_user_id == new_teacher.id)
    ).one()
    
    response = TeacherResponse.model_validate(new_teacher)
    response.student_count = student_count
    
    return response

@router.get("/teachers", response_model=List[TeacherResponse])
async def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    school_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """List all teachers with filters"""
    statement = select(User)
    
    if school_id is not None:
        statement = statement.where(User.school_id == school_id)
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)
    
    statement = statement.offset(skip).limit(limit)
    teachers = session.exec(statement).all()
    
    result = []
    for teacher in teachers:
        student_count = session.exec(
            select(func.count(Student.id)).where(Student.created_by_user_id == teacher.id)
        ).one()
        
        teacher_response = TeacherResponse.model_validate(teacher)
        teacher_response.student_count = student_count
        result.append(teacher_response)
    
    return result

@router.get("/teachers/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get teacher details"""
    teacher = session.get(User, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    student_count = session.exec(
        select(func.count(Student.id)).where(Student.created_by_user_id == teacher.id)
    ).one()
    
    response = TeacherResponse.model_validate(teacher)
    response.student_count = student_count
    
    return response

@router.put("/teachers/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update teacher information"""
    teacher = session.get(User, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    update_data = teacher_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(teacher, key, value)
    
    session.add(teacher)
    session.commit()
    session.refresh(teacher)
    
    student_count = session.exec(
        select(func.count(Student.id)).where(Student.created_by_user_id == teacher.id)
    ).one()
    
    response = TeacherResponse.model_validate(teacher)
    response.student_count = student_count
    
    return response

@router.delete("/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_teacher(
    teacher_id: int,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Deactivate a teacher"""
    teacher = session.get(User, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    teacher.is_active = False
    session.add(teacher)
    session.commit()
    
    return None

# ============================================================================
# STUDENT MANAGEMENT
# ============================================================================

@router.post("/students", response_model=StudentDetailedResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentRegister,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Register a new student"""
    # Validate school
    school = session.get(School, student_data.school_id)
    if not school or not school.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive school")
    
    # Generate student ID
    student_id = generate_student_id(student_data.school_id)
    
    new_student = Student(
        id=student_id,
        full_name=student_data.full_name,
        age=student_data.age,
        student_class=student_data.student_class,
        hobby=student_data.hobby,
        personality=student_data.personality,
        learning_profile=student_data.learning_profile,
        support_type=student_data.support_type,
        school_id=student_data.school_id,
        parent_whatsapp=student_data.parent_whatsapp,
        created_by_user_id=current_admin.id,  # Admin who registered the student
        assigned_teacher_id=student_data.assigned_teacher_id,  # Teacher assigned to manage student
        enrollment_date=datetime.utcnow(),
        is_active=True
    )
    
    session.add(new_student)
    session.commit()
    session.refresh(new_student)
    
    # Send WhatsApp enrollment notification to parent
    if new_student.parent_whatsapp:
        try:
            from .twilio_whatsapp_service import whatsapp_service
            
            # Get school name
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
    
    return StudentDetailedResponse.model_validate(new_student)


@router.get("/students", response_model=List[StudentDetailedResponse])
async def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    school_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """List all students with filters"""
    statement = select(Student)
    
    if school_id is not None:
        statement = statement.where(Student.school_id == school_id)
    if is_active is not None:
        statement = statement.where(Student.is_active == is_active)
    
    statement = statement.offset(skip).limit(limit)
    students = session.exec(statement).all()
    
    return [StudentDetailedResponse.model_validate(s) for s in students]

@router.get("/students/search", response_model=List[StudentDetailedResponse])
async def search_students(
    query: str = Query(..., min_length=1),
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Search students by name or ID"""
    statement = select(Student).where(
        (Student.full_name.contains(query)) | (Student.id.contains(query))
    )
    students = session.exec(statement).all()
    
    return [StudentDetailedResponse.model_validate(s) for s in students]

@router.get("/students/{student_id}", response_model=StudentDetailedResponse)
async def get_student(
    student_id: str,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get student details"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return StudentDetailedResponse.model_validate(student)

@router.put("/students/{student_id}", response_model=StudentDetailedResponse)
async def update_student(
    student_id: str,
    student_data: StudentUpdate,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update student information"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    update_data = student_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(student, key, value)
    
    session.add(student)
    session.commit()
    session.refresh(student)
    
    return StudentDetailedResponse.model_validate(student)

@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_student(
    student_id: str,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Deactivate a student"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student.is_active = False
    session.add(student)
    session.commit()
    
    return None

# ============================================================================
# ANALYTICS
# ============================================================================

@router.get("/analytics/overview", response_model=SystemOverview)
async def get_system_overview(
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get system-wide analytics overview"""
    total_schools = session.exec(select(func.count(School.id))).one()
    total_teachers = session.exec(select(func.count(User.id))).one()
    total_students = session.exec(select(func.count(Student.id))).one()
    
    # Active students today
    today = datetime.utcnow().date()
    active_today = session.exec(
        select(func.count(Student.id)).where(
            func.date(Student.last_active) == today
        )
    ).one()
    
    total_chats = session.exec(select(func.count(ChatHistory.id))).one()
    total_tests = session.exec(select(func.count(TestResult.id))).one()
    
    # Average engagement
    avg_engagement = session.exec(
        select(func.avg(Student.engagement_score)).where(Student.engagement_score.isnot(None))
    ).one() or 0.0
    
    return SystemOverview(
        total_schools=total_schools,
        total_teachers=total_teachers,
        total_students=total_students,
        active_students_today=active_today,
        total_chat_sessions=total_chats,
        total_tests_taken=total_tests,
        average_engagement_score=round(avg_engagement, 2)
    )

@router.get("/analytics/schools", response_model=List[SchoolAnalytics])
async def get_school_analytics(
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get analytics for all schools"""
    schools = session.exec(select(School)).all()
    
    result = []
    for school in schools:
        teacher_count = session.exec(
            select(func.count(User.id)).where(User.school_id == school.id)
        ).one()
        
        student_count = session.exec(
            select(func.count(Student.id)).where(Student.school_id == school.id)
        ).one()
        
        avg_engagement = session.exec(
            select(func.avg(Student.engagement_score)).where(
                (Student.school_id == school.id) & 
                (Student.engagement_score.isnot(None))
            )
        ).one() or 0.0
        
        total_chats = session.exec(
            select(func.count(ChatHistory.id)).where(
                ChatHistory.student_id.in_(
                    select(Student.id).where(Student.school_id == school.id)
                )
            )
        ).one()
        
        total_tests = session.exec(
            select(func.count(TestResult.id)).where(
                TestResult.student_id.in_(
                    select(Student.id).where(Student.school_id == school.id)
                )
            )
        ).one()
        
        correct_tests = session.exec(
            select(func.count(TestResult.id)).where(
                (TestResult.student_id.in_(
                    select(Student.id).where(Student.school_id == school.id)
                )) &
                (TestResult.is_correct == True)
            )
        ).one()
        
        success_rate = (correct_tests / total_tests * 100) if total_tests > 0 else 0.0
        
        result.append(SchoolAnalytics(
            school_id=school.id,
            school_name=school.name,
            teacher_count=teacher_count,
            student_count=student_count,
            average_engagement=round(avg_engagement, 2),
            total_chat_sessions=total_chats,
            total_tests_taken=total_tests,
            test_success_rate=round(success_rate, 2)
        ))
    
    return result

# ============================================================================
# ADMIN ACCOUNT MANAGEMENT
# ============================================================================

@router.put("/change-password")
async def change_admin_password(
    password_data: "PasswordChange",
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Change admin password"""
    from .auth import verify_password, get_password_hash
    
    # Verify current password
    if not verify_password(password_data.current_password, current_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_admin.hashed_password = get_password_hash(password_data.new_password)
    session.add(current_admin)
    session.commit()
    
    return {"message": "Password changed successfully"}

@router.put("/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: str,
    user_type: str,  # "teacher" or "student"
    new_password: str,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Admin resets any user's password"""
    if user_type == "teacher":
        user = session.get(User, int(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="Teacher not found")
        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        session.commit()
        return {"message": f"Teacher password reset successfully"}
    
    elif user_type == "student":
        student = session.get(Student, user_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        student.pin = new_password  # For students, reset PIN
        session.add(student)
        session.commit()
        return {"message": f"Student PIN reset successfully"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid user type")
