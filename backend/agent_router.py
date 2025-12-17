"""
Agent Router
API endpoints for agentic AI features
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Dict, Optional, List
from datetime import datetime
import json

from .database import get_db_session
from .models import Student, AgentMemory, AgentAction, TaskPlan
from .auth import oauth2_scheme
from .agent_memory import get_student_memory
from .agent_service import (
    check_inactive_students,
    generate_check_in_message,
    perform_proactive_check_ins,
    get_agent_effectiveness_stats
)
from .autonomous_quiz_agent import QuizGenerationAgent, check_and_generate_quizzes

router = APIRouter(prefix="/api/agent", tags=["Agent"])

# Helper to get current student
async def get_current_student(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session)
) -> Student:
    """Get current authenticated student"""
    from .auth import decode_token
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
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
    if student is None or not student.is_active:
        raise credentials_exception
    
    return student


# ============================================================================
# AGENT MEMORY ENDPOINTS
# ============================================================================

@router.get("/memory/{student_id}", response_model=Dict)
async def get_agent_memory(
    student_id: str,
    session: Session = Depends(get_db_session)
):
    """Get agent memory for a student"""
    memory = get_student_memory(student_id, session)
    return memory.get_memory_summary()


@router.get("/memory/me", response_model=Dict)
async def get_my_agent_memory(
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Get my agent memory"""
    memory = get_student_memory(current_student.id, session)
    
    return {
        **memory.get_memory_summary(),
        "effective_strategies": memory.get_effective_strategies(),
        "topics_to_revisit": memory.get_topics_to_revisit(),
        "mastered_topics": memory.get_mastered_topics(),
        "active_goals": memory.get_active_goals()
    }


# ============================================================================
# PROACTIVE CHECK-INS
# ============================================================================

@router.post("/check-in/{student_id}", response_model=Dict)
async def trigger_check_in(
    student_id: str,
    session: Session = Depends(get_db_session)
):
    """Manually trigger a proactive check-in for a student"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Calculate days inactive
    from .models import ChatHistory
    from sqlmodel import select
    
    last_chat = session.exec(
        select(ChatHistory).where(
            ChatHistory.student_id == student_id
        ).order_by(ChatHistory.timestamp.desc()).limit(1)
    ).first()
    
    days_inactive = (datetime.utcnow() - last_chat.timestamp).days if last_chat else 999
    
    # Generate message
    message = generate_check_in_message(student, days_inactive, session)
    
    # Log action
    from .agent_service import log_agent_action
    action = log_agent_action(
        student_id=student_id,
        action_type="check_in",
        action_data={"message": message, "days_inactive": days_inactive},
        reasoning=f"Manual check-in triggered for {student.full_name}",
        session=session
    )
    
    return {
        "student_id": student_id,
        "student_name": student.full_name,
        "message": message,
        "days_inactive": days_inactive,
        "action_id": action.id
    }


@router.post("/check-ins/run-all", response_model=Dict)
async def run_all_check_ins(
    session: Session = Depends(get_db_session)
):
    """Run proactive check-ins for all inactive students"""
    results = perform_proactive_check_ins(session)
    return results


# ============================================================================
# AUTONOMOUS QUIZ GENERATION
# ============================================================================

@router.post("/quiz/generate/{student_id}", response_model=Dict)
async def generate_autonomous_quiz(
    student_id: str,
    subject: Optional[str] = None,
    session: Session = Depends(get_db_session)
):
    """Generate an autonomous quiz for a student"""
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    agent = QuizGenerationAgent(student, session)
    
    # Check if quiz should be generated
    decision = agent.should_generate_quiz(subject)
    
    if not decision["should_generate"]:
        return {
            "quiz_generated": False,
            "reasoning": decision["reasoning"],
            "suggestion": "Continue learning, quiz not needed yet"
        }
    
    # Determine subject if not provided
    if not subject:
        from sqlmodel import select, func
        from .models import ChatHistory
        
        most_active = session.exec(
            select(ChatHistory.subject).where(
                (ChatHistory.student_id == student_id) &
                (ChatHistory.subject.isnot(None))
            ).group_by(ChatHistory.subject)
            .order_by(func.count(ChatHistory.id).desc())
            .limit(1)
        ).first()
        
        subject = most_active if most_active else "General"
    
    # Generate quiz
    quiz = agent.generate_adaptive_quiz(subject)
    
    return {
        "quiz_generated": True,
        **quiz,
        "decision": decision
    }


@router.post("/quiz/run-all", response_model=Dict)
async def run_all_quiz_generation(
    session: Session = Depends(get_db_session)
):
    """Run autonomous quiz generation for all students"""
    results = check_and_generate_quizzes(session)
    return results


# ============================================================================
# AGENT EFFECTIVENESS
# ============================================================================

@router.get("/effectiveness/{student_id}", response_model=Dict)
async def get_effectiveness(
    student_id: str,
    session: Session = Depends(get_db_session)
):
    """Get agent effectiveness statistics for a student"""
    stats = get_agent_effectiveness_stats(student_id, session)
    return stats


@router.get("/actions/{student_id}", response_model=list)
async def get_agent_actions(
    student_id: str,
    limit: int = 20,
    session: Session = Depends(get_db_session)
):
    """Get recent agent actions for a student"""
    from sqlmodel import select
    
    actions = session.exec(
        select(AgentAction).where(
            AgentAction.student_id == student_id
        ).order_by(AgentAction.timestamp.desc()).limit(limit)
    ).all()
    
    return [
        {
            "id": a.id,
            "action_type": a.action_type,
            "reasoning": a.reasoning,
            "outcome": a.outcome,
            "effectiveness_score": a.effectiveness_score,
            "timestamp": a.timestamp.isoformat()
        }
        for a in actions
    ]


# ============================================================================
# PHASE 2: TASK PLANNING
# ============================================================================

@router.post("/plan/exam-prep", response_model=Dict)
async def create_exam_prep_plan(
    exam_date: str,
    subjects: List[str],
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Create an exam preparation plan"""
    from .task_planning_agent import TaskPlanningAgent
    from datetime import datetime
    
    planner = TaskPlanningAgent(current_student, session)
    target_date = datetime.fromisoformat(exam_date)
    
    plan = planner.create_exam_preparation_plan(target_date, subjects)
    
    return {
        "plan_id": plan.id,
        "goal": plan.goal,
        "plan_type": plan.plan_type,
        "deadline": plan.deadline.isoformat(),
        "steps": json.loads(plan.steps),
        "total_steps": len(json.loads(plan.steps))
    }


@router.post("/plan/skill-mastery", response_model=Dict)
async def create_skill_mastery_plan(
    skill: str,
    subject: str,
    target_date: Optional[str] = None,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Create a skill mastery plan"""
    from .task_planning_agent import TaskPlanningAgent
    from datetime import datetime
    
    planner = TaskPlanningAgent(current_student, session)
    target = datetime.fromisoformat(target_date) if target_date else None
    
    plan = planner.create_skill_mastery_plan(skill, subject, target)
    
    return {
        "plan_id": plan.id,
        "goal": plan.goal,
        "steps": json.loads(plan.steps)
    }


@router.get("/plan/{plan_id}/progress", response_model=Dict)
async def get_plan_progress(
    plan_id: int,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Get progress on a task plan"""
    from .task_planning_agent import TaskPlanningAgent
    
    planner = TaskPlanningAgent(current_student, session)
    progress = planner.monitor_plan_progress(plan_id)
    
    return progress


@router.post("/plan/{plan_id}/complete-step", response_model=Dict)
async def complete_plan_step(
    plan_id: int,
    step_day_number: int,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Mark a plan step as completed"""
    from .task_planning_agent import TaskPlanningAgent
    
    planner = TaskPlanningAgent(current_student, session)
    planner.complete_step(plan_id, step_day_number)
    
    return {"success": True, "step_completed": step_day_number}


@router.get("/plans/active", response_model=list)
async def get_active_plans(
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Get all active plans for current student"""
    from .task_planning_agent import get_active_plans
    
    plans = get_active_plans(current_student.id, session)
    return plans


# ============================================================================
# PHASE 2: TOOL USE
# ============================================================================

@router.post("/tool/use", response_model=Dict)
async def use_agent_tool(
    tool_name: str,
    tool_params: Optional[Dict] = None,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Use an agent tool"""
    from .agent_tools import AgentTools
    
    tools = AgentTools(current_student, session)
    result = tools.use_tool(tool_name, **(tool_params or {}))
    
    return result


@router.get("/tools/available", response_model=Dict)
async def get_available_tools(
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Get list of available agent tools"""
    from .agent_tools import AgentTools
    
    tools = AgentTools(current_student, session)
    
    return {
        "available_tools": list(tools.tools.keys()),
        "descriptions": {
            "analyze_performance": "Analyze your test performance over time",
            "suggest_topics": "Get topic suggestions based on your progress",
            "generate_quiz": "Generate a quiz for practice",
            "create_study_plan": "Create a personalized study plan",
            "find_weak_areas": "Identify areas needing improvement",
            "get_learning_recommendations": "Get personalized learning recommendations",
            "track_progress": "Track your learning progress"
        }
    }


# ============================================================================
# PHASE 2: SELF-REFLECTION
# ============================================================================

@router.post("/reflect/{student_id}", response_model=Dict)
async def run_agent_reflection(
    student_id: str,
    session: Session = Depends(get_db_session)
):
    """Run self-reflection for a student's agent"""
    from .agent_reflection import AgentReflection
    
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    reflection = AgentReflection(student, session)
    result = reflection.run_self_reflection()
    
    return result


@router.get("/reflect/evaluate/{student_id}", response_model=Dict)
async def evaluate_teaching_effectiveness(
    student_id: str,
    days: int = 30,
    session: Session = Depends(get_db_session)
):
    """Evaluate teaching effectiveness for a student"""
    from .agent_reflection import AgentReflection
    
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    reflection = AgentReflection(student, session)
    evaluation = reflection.evaluate_teaching_effectiveness(days)
    
    return evaluation


@router.post("/reflect/run-all", response_model=Dict)
async def run_all_reflections(
    session: Session = Depends(get_db_session)
):
    """Run self-reflection for all students"""
    from .agent_reflection import run_reflection_for_all_students
    
    results = run_reflection_for_all_students(session)
    return results


# ============================================================================
# PHASE 3: MULTI-AGENT SYSTEM
# ============================================================================

@router.post("/multi-agent/handle-question", response_model=Dict)
async def handle_question_multi_agent(
    question: str,
    subject: str,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """
    Handle student question using multi-agent coordination
    Involves: Tutoring, Assessment, Scheduling, Motivation agents
    """
    from .agent_coordinator import AgentCoordinator
    
    coordinator = AgentCoordinator(current_student, session)
    result = coordinator.handle_student_question(question, subject)
    
    return result


@router.post("/multi-agent/exam-prep", response_model=Dict)
async def prepare_for_exam_multi_agent(
    exam_date: str,
    subjects: List[str],
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """
    Coordinate all agents for comprehensive exam preparation
    """
    from .agent_coordinator import AgentCoordinator
    from datetime import datetime
    
    coordinator = AgentCoordinator(current_student, session)
    target_date = datetime.fromisoformat(exam_date)
    
    result = coordinator.handle_exam_preparation(target_date, subjects)
    
    return result


@router.post("/multi-agent/engagement-intervention", response_model=Dict)
async def handle_low_engagement_multi_agent(
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """
    Coordinate agents to re-engage inactive student
    """
    from .agent_coordinator import AgentCoordinator
    
    coordinator = AgentCoordinator(current_student, session)
    result = coordinator.handle_low_engagement()
    
    return result


@router.get("/multi-agent/daily-check-in", response_model=Dict)
async def daily_check_in_multi_agent(
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """
    Run daily check-in with all agents
    """
    from .agent_coordinator import AgentCoordinator
    
    coordinator = AgentCoordinator(current_student, session)
    result = coordinator.daily_check_in()
    
    return result


@router.post("/multi-agent/coordinate-all", response_model=Dict)
async def coordinate_all_students_multi_agent(
    session: Session = Depends(get_db_session)
):
    """
    Run daily coordination for all active students
    Background task endpoint
    """
    from .agent_coordinator import coordinate_all_students
    
    results = coordinate_all_students(session)
    return results


# ============================================================================
# SPECIALIZED AGENT ENDPOINTS
# ============================================================================

@router.post("/agent/tutoring/explain", response_model=Dict)
async def tutoring_agent_explain(
    topic: str,
    question: str,
    subject: str,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Use Tutoring Agent to explain a concept"""
    from .specialized_agents import TutoringAgent
    
    agent = TutoringAgent(current_student, session)
    confusion = agent.analyze_confusion(question, subject)
    explanation = agent.generate_explanation(topic, confusion)
    
    return {
        "topic": topic,
        "explanation": explanation,
        "confusion_analysis": confusion
    }


@router.post("/agent/assessment/evaluate", response_model=Dict)
async def assessment_agent_evaluate(
    topic: str,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Use Assessment Agent to evaluate mastery"""
    from .specialized_agents import AssessmentAgent
    from .models import TestResult
    from sqlmodel import select
    from datetime import timedelta
    
    agent = AssessmentAgent(current_student, session)
    
    # Get recent results
    recent_tests = session.exec(
        select(TestResult).where(
            (TestResult.student_id == current_student.id) &
            (TestResult.subject == topic) &
            (TestResult.timestamp >= datetime.utcnow() - timedelta(days=30))
        )
    ).all()
    
    mastery = agent.evaluate_mastery(topic, recent_tests)
    
    return mastery


@router.post("/agent/scheduling/optimize", response_model=Dict)
async def scheduling_agent_optimize(
    subjects: List[str],
    hours_per_day: int = 2,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Use Scheduling Agent to optimize study time"""
    from .specialized_agents import SchedulingAgent
    
    agent = SchedulingAgent(current_student, session)
    schedule = agent.optimize_study_time(subjects, hours_per_day)
    
    return schedule


@router.get("/agent/motivation/engagement", response_model=Dict)
async def motivation_agent_check_engagement(
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Use Motivation Agent to check engagement"""
    from .specialized_agents import MotivationAgent
    
    agent = MotivationAgent(current_student, session)
    engagement = agent.assess_engagement_level()
    
    # Generate encouragement if needed
    if agent.should_send_encouragement(engagement):
        encouragement = agent.generate_encouragement({"achievement": "staying engaged"})
        engagement["encouragement"] = encouragement
    
    return engagement


