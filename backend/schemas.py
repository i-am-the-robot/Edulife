"""
Pydantic schemas for API requests and responses
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from .models import UserRole, LearningProfile, SupportType, PersonalityType, TutorialStatus

# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    user_type: Optional[str] = None

# ============================================================================
# ADMIN SCHEMAS
# ============================================================================

class AdminRegister(BaseModel):
    """Admin registration request"""
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class AdminResponse(BaseModel):
    """Admin response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    school_id: Optional[int]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str

# ============================================================================
# SCHOOL SCHEMAS
# ============================================================================

class SchoolCreate(BaseModel):
    """School creation request"""
    name: str
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    grade_levels: Optional[str] = None  # JSON string
    syllabus_text: Optional[str] = None

class SchoolUpdate(BaseModel):
    """School update request"""
    name: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    grade_levels: Optional[str] = None
    syllabus_text: Optional[str] = None
    is_active: Optional[bool] = None

class SchoolResponse(BaseModel):
    """School response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    app_key: str
    location: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    grade_levels: Optional[str]
    syllabus_text: Optional[str]
    is_active: bool
    created_at: datetime
    teacher_count: int = 0
    student_count: int = 0

# ============================================================================
# TEACHER/USER SCHEMAS
# ============================================================================

class TeacherRegister(BaseModel):
    """Teacher registration request"""
    full_name: str
    email: EmailStr
    password: str
    address: str
    app_key: str  # School app key
    phone: Optional[str] = None
    subjects: Optional[str] = None  # JSON string
    years_experience: Optional[int] = None
    specializations: Optional[str] = None  # JSON string
    role: UserRole = UserRole.TEACHER

class TeacherUpdate(BaseModel):
    """Teacher update request"""
    full_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    subjects: Optional[str] = None
    years_experience: Optional[int] = None
    specializations: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class TeacherResponse(BaseModel):
    """Teacher response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    full_name: str
    email: str
    address: str
    role: UserRole
    phone: Optional[str]
    subjects: Optional[str]
    years_experience: Optional[int]
    specializations: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    school_id: Optional[int]
    student_count: int = 0

# ============================================================================
# STUDENT SCHEMAS
# ============================================================================

class StudentRegister(BaseModel):
    """Student registration request"""
    full_name: str
    age: int
    student_class: str
    hobby: str
    personality: PersonalityType
    school_id: Optional[int] = None
    learning_profile: LearningProfile = LearningProfile.STANDARD
    support_type: SupportType = SupportType.NONE
    learning_preferences: Optional[str] = None
    parent_whatsapp: Optional[str] = None  # Parent's WhatsApp number for notifications
    assigned_teacher_id: Optional[int] = None  # Teacher assigned to manage this student (admin only)


class StudentUpdate(BaseModel):
    """Student update request"""
    full_name: Optional[str] = None
    age: Optional[int] = None
    student_class: Optional[str] = None
    hobby: Optional[str] = None
    personality: Optional[PersonalityType] = None
    learning_profile: Optional[LearningProfile] = None
    support_type: Optional[SupportType] = None
    learning_preferences: Optional[str] = None
    is_active: Optional[bool] = None

class StudentResponse(BaseModel):
    """Student response - NEVER includes support_type"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    full_name: str
    age: int
    student_class: str
    hobby: str
    personality: PersonalityType
    enrollment_date: datetime
    engagement_score: Optional[float]
    login_frequency: Optional[int]
    last_active: Optional[datetime]
    favorite_subjects: Optional[str]
    is_active: bool
    school_id: Optional[int]
    created_by_user_id: Optional[int]

class StudentDetailedResponse(StudentResponse):
    """Detailed student response for teachers/admins - includes learning profile"""
    learning_profile: LearningProfile
    support_type: SupportType  # Only for teachers/admins
    learning_preferences: Optional[str]

# ============================================================================
# CHAT & TEST SCHEMAS
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message request"""
    student_id: str
    message: str
    subject: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response with AI reply"""
    session_id: str
    ai_response: str
    tests_generated: List[dict] = []
    current_engagement_score: Optional[float] = None
    points_awarded: Optional[float] = None
    
    # Extended Multi-Agent Fields
    agents_involved: List[str] = []
    actions_taken: List[str] = []
    quiz: Optional[dict] = None
    practice_schedule: Optional[dict] = None
    encouragement: Optional[str] = None

class TestSubmission(BaseModel):
    """Test answer submission"""
    test_result_id: int
    student_answer: str

class TestFeedback(BaseModel):
    """Test feedback response"""
    is_correct: bool
    feedback: str
    correct_answer: Optional[str] = None

# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class SystemOverview(BaseModel):
    """System-wide analytics"""
    total_schools: int
    total_teachers: int
    total_students: int
    active_students_today: int
    total_chat_sessions: int
    total_tests_taken: int
    average_engagement_score: float

class SchoolAnalytics(BaseModel):
    """School-specific analytics"""
    school_id: int
    school_name: str
    teacher_count: int
    student_count: int
    average_engagement: float
    total_chat_sessions: int
    total_tests_taken: int
    test_success_rate: float

class StudentProgress(BaseModel):
    """Student progress summary"""
    student_id: str
    total_sessions: int
    total_tests: int
    test_success_rate: float
    engagement_score: float
    favorite_subjects: List[str]
    recent_activity: List[dict]
