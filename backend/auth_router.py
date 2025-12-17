"""
Authentication Router
Handles registration and login for Admin, Teacher, and Student
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone

from .database import get_db_session
from .models import Admin, User, Student, School, UserRole
from .schemas import (
    AdminRegister, AdminResponse, TeacherRegister, TeacherResponse, 
    StudentResponse, Token, StudentRegister
)
from .auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user_or_admin
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ============================================================================
# ADMIN AUTHENTICATION
# ============================================================================

@router.post("/admin/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_admin(
    admin_data: AdminRegister,
    session: Session = Depends(get_db_session)
):
    """Register a new admin"""
    # Check if email already exists
    statement = select(Admin).where(Admin.email == admin_data.email)
    existing_admin = session.exec(statement).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin
    hashed_password = get_password_hash(admin_data.password)
    new_admin = Admin(
        full_name=admin_data.full_name,
        email=admin_data.email,
        hashed_password=hashed_password,
        phone=admin_data.phone,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    session.add(new_admin)
    session.commit()
    session.refresh(new_admin)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": new_admin.email, "type": "admin"}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/admin/login", response_model=Token)
async def login_admin(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db_session)
):
    """Admin login"""
    statement = select(Admin).where(Admin.email == form_data.username)
    admin = session.exec(statement).first()
    
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    admin.last_login = datetime.utcnow()
    session.add(admin)
    session.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": admin.email, "type": "admin"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": admin.id,
        "full_name": admin.full_name,
        "email": admin.email
    }

# ============================================================================
# TEACHER AUTHENTICATION
# ============================================================================

@router.post("/teacher/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_teacher(
    teacher_data: TeacherRegister,
    session: Session = Depends(get_db_session)
):
    """Register a new teacher with school app_key validation"""
    # Validate school app_key
    statement = select(School).where(School.app_key == teacher_data.app_key)
    school = session.exec(statement).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid school app key"
        )
    
    if not school.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School is not active"
        )
    
    # Check if email already exists
    statement = select(User).where(User.email == teacher_data.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new teacher
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
    
    # Create access token
    access_token = create_access_token(
        data={"sub": new_teacher.email, "type": "teacher"}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/teacher/login", response_model=Token)
async def login_teacher(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db_session)
):
    """Teacher login"""
    statement = select(User).where(User.email == form_data.username)
    teacher = session.exec(statement).first()
    
    if not teacher or not verify_password(form_data.password, teacher.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not teacher.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    teacher.last_login = datetime.utcnow()
    session.add(teacher)
    session.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": teacher.email, "type": "teacher"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": teacher.id,
        "full_name": teacher.full_name,
        "email": teacher.email,
        "school_id": teacher.school_id,
        "role": teacher.role.value if hasattr(teacher.role, 'value') else teacher.role
    }

# ============================================================================
# STUDENT AUTHENTICATION
# ============================================================================

@router.post("/student/register", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def register_student_public(
    student_data: StudentRegister,
    session: Session = Depends(get_db_session)
):
    """
    Register a new student.
    - If school_id is provided, validates it.
    - If school_id is NULL, registers as Independent Student.
    """
    # 1. Validate School if provided
    if student_data.school_id:
        school = session.get(School, student_data.school_id)
        if not school:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid school ID"
            )
        base_id = f"{student_data.school_id}_student_"
    else:
        # Independent Student
        base_id = "IND_student_"
    
    # 2. Generate Unique ID
    import time
    import uuid
    timestamp = str(int(time.time() * 1000))
    student_id = f"{base_id}{timestamp}"
    
    # Double check uniqueness (paranoid check)
    if session.get(Student, student_id):
         student_id = f"{base_id}{uuid.uuid4().hex[:8]}"
    
    # 3. Create Student
    new_student = Student(
        id=student_id,
        full_name=student_data.full_name,
        age=student_data.age,
        student_class=student_data.student_class,
        hobby=student_data.hobby,
        personality=student_data.personality,
        school_id=student_data.school_id, # Can be None
        created_by_user_id=None, # Self-registered
        learning_profile=student_data.learning_profile,
        support_type=student_data.support_type,
        learning_preferences=student_data.learning_preferences,
        parent_whatsapp=student_data.parent_whatsapp,
        is_active=True,
        enrollment_date=datetime.now(timezone.utc)
    )
    
    session.add(new_student)
    session.commit()
    session.refresh(new_student)
    
    # 4. Send WhatsApp Notification (Asyncish)
    if new_student.parent_whatsapp:
        try:
            from .twilio_whatsapp_service import whatsapp_service
            
            # Determine organization name
            org_name = "EduLife (Independent)"
            if new_student.school_id:
                 school = session.get(School, new_student.school_id)
                 if school: org_name = school.name
            
            enrollment_message = f"""🎓 *Welcome to EduLife!*

Hello! Your child *{new_student.full_name}* has been successfully enrolled on the EduLife platform.

📚 *Organization:* {org_name}
👤 *Student ID:* {new_student.id}
PIN code: {new_student.pin} (Default: 0000)

Our AI-powered learning system is ready to help!
            
_Edu-Life - Learn Without Limits_"""
            
            whatsapp_service.send_whatsapp_message(
                to_number=new_student.parent_whatsapp,
                message=enrollment_message
            )
        except Exception as e:
            print(f"[WARNING] Failed to send enrollment WhatsApp: {e}")
            
    return new_student

@router.post("/student/login")
async def login_student(
    student_id: str,
    pin: str = Query(..., min_length=4, max_length=4),
    session: Session = Depends(get_db_session)
):
    """Student login using unique student ID and 4-digit PIN"""
    statement = select(Student).where(Student.id == student_id)
    student = session.exec(statement).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid student ID"
        )
            
    # Verify PIN (simple comparison for now, in production should be hashed)
    if student.pin != pin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN"
        )
    
    if not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last active
    student.last_active = datetime.utcnow()
    session.add(student)
    session.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": student.id, "type": "student", "school_id": student.school_id}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "id": student.id,
        "full_name": student.full_name,
        "school_id": student.school_id
    }

# ============================================================================
# CURRENT USER
# ============================================================================

@router.get("/me")
async def get_current_user(
    current_user = Depends(get_current_user_or_admin),
    session: Session = Depends(get_db_session)
):
    """Get current authenticated user information"""
    if isinstance(current_user, Admin):
        return {
            "user_type": "admin",
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "is_active": current_user.is_active
        }
    elif isinstance(current_user, User):
        return {
            "user_type": "teacher",
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role,
            "school_id": current_user.school_id,
            "is_active": current_user.is_active
        }
    else:
        # Student
        statement = select(Student).where(Student.id == current_user)
        student = session.exec(statement).first()
        if student:
            return {
                "user_type": "student",
                "id": student.id,
                "full_name": student.full_name,
                "school_id": student.school_id,
                "is_active": student.is_active
            }
    
    raise HTTPException(status_code=404, detail="User not found")
