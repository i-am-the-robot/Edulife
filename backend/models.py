"""
Database models for EduLife v2.0
Complete schema with all relationships
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    """User roles"""
    ADMIN = "Admin"
    HEAD_TEACHER = "HeadTeacher"
    TEACHER = "Teacher"

class LearningProfile(str, Enum):
    """Learning profile types - NEVER shown to student"""
    STANDARD = "Standard"
    PERSONALIZED = "Personalized"

class SupportType(str, Enum):
    """Support types - NEVER shown to student, used for AI adaptation"""
    NONE = "None"
    DYSLEXIA = "Dyslexia"
    DOWN_SYNDROME = "DownSyndrome"
    AUTISM = "Autism"

class PersonalityType(str, Enum):
    """Personality types"""
    INTROVERT = "Introvert"
    EXTROVERT = "Extrovert"

class TutorialStatus(str, Enum):
    """Tutorial status"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# ============================================================================
# MODELS
# ============================================================================

class Admin(SQLModel, table=True):
    """System administrator model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    phone: Optional[str] = None
    school_id: Optional[int] = Field(default=None, foreign_key="school.id")  # None = Super Admin, else School Admin
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class School(SQLModel, table=True):
    """School/Institution model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    app_key: str = Field(unique=True, index=True)  # Auto-generated unique key
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    logo_url: Optional[str] = None
    grade_levels: Optional[str] = None  # JSON list: ["K-5", "6-8", "9-12"]
    syllabus_text: Optional[str] = None  # For RAG system
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    users: List["User"] = Relationship(back_populates="school")
    students: List["Student"] = Relationship(back_populates="school")

class User(SQLModel, table=True):
    """Teacher/User model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    address: str
    phone: Optional[str] = None
    role: UserRole = Field(default=UserRole.TEACHER)
    school_id: Optional[int] = Field(default=None, foreign_key="school.id")
    
    # Teacher-specific fields
    subjects: Optional[str] = None  # JSON list: ["Math", "Science"]
    years_experience: Optional[int] = None
    specializations: Optional[str] = None  # JSON list
    profile_photo_url: Optional[str] = None
    
    # Metadata
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Relationships
    school: Optional[School] = Relationship(back_populates="users")
    students_created: List["Student"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "[Student.created_by_user_id]"}
    )
    students_assigned: List["Student"] = Relationship(
        back_populates="assigned_teacher",
        sa_relationship_kwargs={"foreign_keys": "[Student.assigned_teacher_id]"}
    )
    tutorials: List["Tutorial"] = Relationship(back_populates="teacher")
    tasks_created: List["Task"] = Relationship(back_populates="teacher")
    notifications: List["TeacherNotification"] = Relationship(back_populates="teacher")

class Student(SQLModel, table=True):
    """Student model"""
    id: str = Field(primary_key=True)  # Custom format: {school_id}_student_{timestamp}
    full_name: str
    age: int
    student_class: str  # Grade/Class
    hobby: str
    personality: PersonalityType
    pin: str = Field(default="0000")  # 4-digit PIN for login
    
    # Learning profile - NEVER shown to student
    learning_profile: LearningProfile = Field(default=LearningProfile.STANDARD)
    support_type: SupportType = Field(default=SupportType.NONE)  # For AI adaptation only
    learning_preferences: Optional[str] = None  # JSON: {"visual": 40, "auditory": 30, "kinesthetic": 30}
    
    # School and creator
    school_id: Optional[int] = Field(default=None, foreign_key="school.id")
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")  # Who registered the student
    assigned_teacher_id: Optional[int] = Field(default=None, foreign_key="user.id")  # Teacher assigned to manage student
    
    # Progress tracking
    enrollment_date: datetime = Field(default_factory=datetime.utcnow)
    engagement_score: Optional[float] = Field(default=0.0)  # 0-100, calculated from activities
    login_frequency: Optional[int] = None  # Logins per week
    last_active: Optional[datetime] = None
    favorite_subjects: Optional[str] = None  # JSON list
    is_active: bool = Field(default=True)
    
    # Parent contact for WhatsApp notifications
    parent_whatsapp: Optional[str] = None  # Parent's WhatsApp number (format: +234XXXXXXXXXX)
    
    # Streak mechanics for engagement
    current_streak: int = Field(default=0)  # Days in a row
    longest_streak: int = Field(default=0)  # Best streak ever
    last_activity_date: Optional[datetime] = None  # For streak calculation
    streak_freeze_count: int = Field(default=0)  # Earned "skip day" rewards
    
    # Relationships
    school: Optional[School] = Relationship(back_populates="students")
    created_by_user: Optional[User] = Relationship(
        back_populates="students_created",
        sa_relationship_kwargs={"foreign_keys": "Student.created_by_user_id"}
    )
    assigned_teacher: Optional[User] = Relationship(
        back_populates="students_assigned",
        sa_relationship_kwargs={"foreign_keys": "Student.assigned_teacher_id"}
    )
    chat_history: List["ChatHistory"] = Relationship(back_populates="student")
    test_results: List["TestResult"] = Relationship(back_populates="student")
    conversation_answers: List["ConversationAnswer"] = Relationship(back_populates="student")
    tutorials: List["Tutorial"] = Relationship(back_populates="student")
    tasks: List["Task"] = Relationship(back_populates="student")
    timetable: List["Timetable"] = Relationship(back_populates="student")


class ChatHistory(SQLModel, table=True):
    """Chat conversation history"""
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    session_id: str = Field(index=True)  # Groups related messages
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    subject: Optional[str] = None
    topic: Optional[str] = None
    student_message: str
    ai_response: str
    is_favorite: bool = Field(default=False)
    
    # Relationship
    student: Optional[Student] = Relationship(back_populates="chat_history")
    test_results: List["TestResult"] = Relationship(back_populates="chat_history")
    conversation_answers: List["ConversationAnswer"] = Relationship(back_populates="chat_history")

class TestResult(SQLModel, table=True):
    """Interactive test results from AI conversations"""
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    chat_history_id: int = Field(foreign_key="chathistory.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    subject: str
    topic: str
    question: str
    student_answer: str
    correct_answer: str
    is_correct: bool
    attempt_number: int = Field(default=1)
    time_spent_seconds: Optional[int] = None
    ai_feedback: str  # Encouraging feedback given
    
    # Relationships
    student: Optional[Student] = Relationship(back_populates="test_results")
    chat_history: Optional[ChatHistory] = Relationship(back_populates="test_results")

class ConversationAnswer(SQLModel, table=True):
    """Tracks correct answers given during regular AI conversations"""
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    chat_history_id: int = Field(foreign_key="chathistory.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    question: str  # The question AI asked
    student_answer: str  # Student's response
    is_correct: bool
    points_awarded: float = Field(default=0.1)
    subject: Optional[str] = None
    topic: Optional[str] = None
    
    # Relationship
    student: Optional[Student] = Relationship(back_populates="conversation_answers")
    chat_history: Optional[ChatHistory] = Relationship(back_populates="conversation_answers")

class Tutorial(SQLModel, table=True):
    """Scheduled tutorials between teacher and student"""
    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: int = Field(foreign_key="user.id")
    student_id: str = Field(foreign_key="student.id")
    scheduled_time: datetime
    duration_minutes: int
    subject: Optional[str] = None
    notes: Optional[str] = None
    status: TutorialStatus = Field(default=TutorialStatus.SCHEDULED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    teacher: Optional[User] = Relationship(back_populates="tutorials")
    student: Optional[Student] = Relationship(back_populates="tutorials")

class Task(SQLModel, table=True):
    """Tasks/Assignments given to students"""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    due_date: datetime
    teacher_id: int = Field(foreign_key="user.id")
    student_id: Optional[str] = Field(default=None, foreign_key="student.id")  # If None, it might be a class-wide task concept, but for now we'll link to student directly or handle logic in router
    status: str = Field(default="pending")  # pending, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    teacher: Optional[User] = Relationship(back_populates="tasks_created")
    student: Optional[Student] = Relationship(back_populates="tasks")

# ============================================================================
# ENGAGEMENT & GAMIFICATION MODELS
# ============================================================================

class Achievement(SQLModel, table=True):
    """Achievements that students can unlock"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # "First Steps", "Streak Master", etc.
    description: str
    icon: str  # Emoji or icon name
    unlock_condition: str  # JSON criteria: {"type": "streak", "value": 7}
    rarity: str = Field(default="common")  # common, rare, epic, legendary
    points: int = Field(default=10)  # Engagement points awarded
    
    # Relationships
    student_achievements: List["StudentAchievement"] = Relationship(back_populates="achievement")

class StudentAchievement(SQLModel, table=True):
    """Tracks which achievements each student has unlocked"""
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    achievement_id: int = Field(foreign_key="achievement.id")
    unlocked_at: datetime = Field(default_factory=datetime.utcnow)
    is_new: bool = Field(default=True)  # Show "NEW!" badge in UI
    
    # Relationships
    achievement: Optional[Achievement] = Relationship(back_populates="student_achievements")

class PowerUp(SQLModel, table=True):
    """Power-ups students can earn and use"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # "Hint Helper", "Curiosity Boost", "Time Freeze"
    description: str
    effect: str  # JSON describing what it does
    duration: int = Field(default=3)  # How many questions it lasts
    icon: str  # Emoji or icon name

class StudentPowerUp(SQLModel, table=True):
    """Tracks power-ups owned by students"""
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    power_up_id: int = Field(foreign_key="powerup.id")
    quantity: int = Field(default=1)
    earned_at: datetime = Field(default_factory=datetime.utcnow)

class SessionMetrics(SQLModel, table=True):
    """Invisible metrics for tracking engagement and flow state"""
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    session_id: str = Field(index=True)
    session_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Metrics
    duration_seconds: int
    questions_answered: int = Field(default=0)
    correct_answers: int = Field(default=0)
    success_rate: float = Field(default=0.0)  # Percentage
    avg_response_time: float = Field(default=0.0)  # Seconds
    self_initiated_questions: int = Field(default=0)  # Student asked "why?", "how?"
    
    # Flow state indicators
    peak_flow_duration: int = Field(default=0)  # Seconds in optimal challenge zone
    difficulty_adjustments: int = Field(default=0)  # How many times difficulty changed
    
    # Engagement points earned this session
    engagement_points: int = Field(default=0)

class AssignmentStudySession(SQLModel, table=True):
    """Tracks student study sessions for assignments with quizzes"""
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    student_id: str = Field(foreign_key="student.id")
    chat_session_id: str  # Links to ChatHistory.session_id
    status: str = Field(default="in_progress")  # 'in_progress', 'quiz_pending', 'completed'
    conversation_count: int = Field(default=0)
    last_quiz_at: int = Field(default=0)  # Conversation count when last quiz was given
    quiz_questions: Optional[str] = None  # JSON array of periodic quiz questions
    quiz_answers: Optional[str] = None  # JSON array of student answers
    final_questions: Optional[str] = None  # JSON array of final assessment questions
    final_answers: Optional[str] = None  # JSON array of final assessment answers
    quiz_score: Optional[float] = None
    final_score: Optional[float] = None
    summary: Optional[str] = None  # AI-generated summary for teacher
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    submitted_to_teacher: bool = Field(default=False)
    viewed_by_teacher: bool = Field(default=False)  # Track if teacher has viewed this submission
    viewed_at: Optional[datetime] = None  # When teacher viewed the submission

# ============================================================================
# AGENTIC AI MODELS
# ============================================================================

class AgentMemory(SQLModel, table=True):
    """
    Persistent memory for each student's AI agent
    Tracks learning patterns, effective strategies, and agent state
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    
    # Learning patterns
    learning_style: Optional[str] = None  # 'visual', 'auditory', 'kinesthetic', 'reading'
    effective_strategies: Optional[str] = None  # JSON array of strategies that work
    ineffective_strategies: Optional[str] = None  # JSON array of strategies that don't work
    
    # Topics tracking
    topics_to_revisit: Optional[str] = None  # JSON array of topics needing review
    mastered_topics: Optional[str] = None  # JSON array of mastered topics
    current_focus_topics: Optional[str] = None  # JSON array of current learning focus
    
    # Agent state
    last_interaction: Optional[datetime] = None
    interaction_count: int = Field(default=0)
    agent_goals: Optional[str] = None  # JSON array of current objectives
    progress_milestones: Optional[str] = None  # JSON array of achievements
    
    # Personalization
    preferred_examples: Optional[str] = None  # Types of examples student responds to
    optimal_session_length: Optional[int] = None  # Minutes
    best_time_of_day: Optional[str] = None  # 'morning', 'afternoon', 'evening'
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentAction(SQLModel, table=True):
    """
    Log of autonomous actions taken by the AI agent
    Enables tracking and learning from agent behavior
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    
    # Action details
    action_type: str  # 'check_in', 'quiz_generated', 'plan_created', 'strategy_adjusted'
    action_data: Optional[str] = None  # JSON data about the action
    reasoning: Optional[str] = None  # Why the agent took this action
    
    # Outcome tracking
    outcome: Optional[str] = None  # 'successful', 'failed', 'pending'
    student_response: Optional[str] = None  # How student responded
    effectiveness_score: Optional[float] = None  # 0-1 score of how effective the action was
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Optional[str] = None  # JSON context at time of action


class TaskPlan(SQLModel, table=True):
    """
    Multi-step plans created by the AI agent
    Example: Exam preparation plan, skill mastery plan
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    
    # Plan details
    goal: str  # "Prepare for Math exam", "Master Algebra"
    plan_type: str  # 'exam_prep', 'skill_mastery', 'assignment_completion'
    steps: str  # JSON array of plan steps
    
    # Progress tracking
    current_step: int = Field(default=0)
    completed_steps: Optional[str] = None  # JSON array of completed step IDs
    status: str = Field(default="active")  # 'active', 'completed', 'abandoned', 'paused'
    
    # Timeline
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Adaptation
    adjustments_made: Optional[str] = None  # JSON log of plan adjustments
    success_rate: Optional[float] = None  # How well the plan is working


class AgentNotification(SQLModel, table=True):
    """
    Notifications sent by agents to students
    For new activities, quizzes, check-ins, reminders, achievements
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    
    # Notification details
    notification_type: str  # 'quiz_ready', 'check_in', 'study_reminder', 'achievement', 'plan_update'
    agent_type: str  # 'tutoring', 'assessment', 'scheduling', 'motivation', 'coordinator'
    title: str  # Short title
    message: str  # Full message content
    
    # Action data
    action_url: Optional[str] = None  # URL to navigate to (e.g., /quiz/123)
    action_data: Optional[str] = None  # JSON data for the action
    
    # Status
    is_read: bool = Field(default=False)
    read_at: Optional[datetime] = None
    priority: str = Field(default="normal")  # 'low', 'normal', 'high', 'urgent'
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # When notification becomes irrelevant


class TeacherNotification(SQLModel, table=True):
    """
    Notifications for teachers regarding student activity
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    teacher_id: int = Field(foreign_key="user.id", index=True)
    student_id: Optional[str] = Field(default=None, foreign_key="student.id")
    
    # Notification details
    type: str  # 'alert', 'info', 'success', 'warning'
    title: str
    message: str
    category: str = Field(default="general") # 'engagement', 'academic', 'system'
    
    # Status
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    teacher: "User" = Relationship(back_populates="notifications")
    student: Optional["Student"] = Relationship()


class Timetable(SQLModel, table=True):
    """Student study schedule"""
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="student.id", index=True)
    day_of_week: str  # Monday, Tuesday...
    start_time: str   # "16:00"
    end_time: str     # "17:00"
    subject: Optional[str] = None
    focus_topic: Optional[str] = None
    description: Optional[str] = None
    activity_type: str = Field(default="study")  # study, quiz, break
    is_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    student: Optional["Student"] = Relationship(back_populates="timetable")



