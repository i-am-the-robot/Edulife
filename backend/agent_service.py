"""
Agent Service
Autonomous actions and proactive student engagement
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlmodel import Session, select, func
from .models import Student, ChatHistory, AgentAction, AgentMemory
from .agent_memory import get_student_memory
from .ai_service import groq_client, GROQ_MODEL

def check_inactive_students(session: Session, days_threshold: int = 3) -> List[Dict]:
    """
    Find students who haven't been active recently
    Returns list of inactive students with suggested actions
    """
    threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
    
    # Get all active students
    students = session.exec(
        select(Student).where(Student.is_active == True)
    ).all()
    
    inactive_students = []
    
    for student in students:
        # Check last activity
        last_chat = session.exec(
            select(ChatHistory).where(
                ChatHistory.student_id == student.id
            ).order_by(ChatHistory.timestamp.desc()).limit(1)
        ).first()
        
        if not last_chat or last_chat.timestamp < threshold_date:
            days_inactive = (datetime.utcnow() - last_chat.timestamp).days if last_chat else 999
            
            inactive_students.append({
                "student_id": student.id,
                "student_name": student.full_name,
                "days_inactive": days_inactive,
                "last_active": last_chat.timestamp if last_chat else None,
                "personality": student.personality.value,
                "hobby": student.hobby
            })
    
    return inactive_students


def generate_check_in_message(student: Student, days_inactive: int, session: Session) -> str:
    """
    Generate personalized check-in message for inactive student
    """
    if not groq_client:
        return f"Hi {student.full_name}! We haven't seen you in {days_inactive} days. How are you doing?"
    
    # Get agent memory for personalization
    memory = get_student_memory(student.id, session)
    mastered_topics = memory.get_mastered_topics()
    topics_to_revisit = memory.get_topics_to_revisit()
    
    prompt = f"""Generate a warm, encouraging check-in message for {student.full_name}, a {student.age}-year-old {student.personality.value} student who hasn't been active for {days_inactive} days.

STUDENT CONTEXT:
- Personality: {student.personality.value}
- Interests: {student.hobby}
- Class: {student.student_class}
- Recently mastered: {', '.join([t['topic'] for t in mastered_topics[-3:]]) if mastered_topics else 'None yet'}
- Needs review: {', '.join([t['topic'] for t in topics_to_revisit[:2]]) if topics_to_revisit else 'None'}

GUIDELINES:
1. Be warm and encouraging, not pushy
2. Reference their interests or recent achievements
3. Suggest a specific topic they might enjoy
4. Keep it short (2-3 sentences)
5. Use Nigerian context if appropriate
6. Match their personality (gentle for Introvert, energetic for Extrovert)
7. Don't use any profane language or explicit language.
8. Systematically avoid discussing adult content or topics

Generate ONLY the message, no additional text."""
    
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating check-in message: {e}")
        return f"Hi {student.full_name}! We miss you! Ready to continue learning?"


def log_agent_action(
    student_id: str,
    action_type: str,
    action_data: Dict,
    reasoning: str,
    session: Session
) -> AgentAction:
    """
    Log an autonomous action taken by the agent
    """
    action = AgentAction(
        student_id=student_id,
        action_type=action_type,
        action_data=json.dumps(action_data),
        reasoning=reasoning,
        outcome="pending"
    )
    
    session.add(action)
    session.commit()
    session.refresh(action)
    
    return action


def update_action_outcome(
    action_id: int,
    outcome: str,
    student_response: Optional[str],
    effectiveness_score: Optional[float],
    session: Session
):
    """
    Update the outcome of an agent action
    """
    action = session.get(AgentAction, action_id)
    if action:
        action.outcome = outcome
        action.student_response = student_response
        action.effectiveness_score = effectiveness_score
        
        session.add(action)
        session.commit()


def perform_proactive_check_ins(session: Session) -> Dict:
    """
    Main function to perform proactive check-ins
    Called by background scheduler
    """
    inactive_students = check_inactive_students(session, days_threshold=3)
    
    results = {
        "total_checked": len(inactive_students),
        "messages_generated": 0,
        "actions_logged": []
    }
    
    for student_data in inactive_students:
        student = session.get(Student, student_data["student_id"])
        if not student:
            continue
        
        # Generate personalized message
        message = generate_check_in_message(
            student,
            student_data["days_inactive"],
            session
        )
        
        # Log the action
        action = log_agent_action(
            student_id=student.id,
            action_type="check_in",
            action_data={
                "message": message,
                "days_inactive": student_data["days_inactive"],
                "trigger": "proactive_engagement"
            },
            reasoning=f"Student inactive for {student_data['days_inactive']} days",
            session=session
        )
        
        results["messages_generated"] += 1
        results["actions_logged"].append({
            "action_id": action.id,
            "student_id": student.id,
            "student_name": student.full_name,
            "message": message
        })
    
    return results


def get_agent_effectiveness_stats(student_id: str, session: Session) -> Dict:
    """
    Get statistics on agent effectiveness for a student
    """
    actions = session.exec(
        select(AgentAction).where(
            (AgentAction.student_id == student_id) &
            (AgentAction.effectiveness_score.isnot(None))
        )
    ).all()
    
    if not actions:
        return {
            "total_actions": 0,
            "average_effectiveness": 0.0,
            "most_effective_action_type": None
        }
    
    # Calculate stats
    total_actions = len(actions)
    avg_effectiveness = sum(a.effectiveness_score for a in actions) / total_actions
    
    # Group by action type
    by_type = {}
    for action in actions:
        if action.action_type not in by_type:
            by_type[action.action_type] = []
        by_type[action.action_type].append(action.effectiveness_score)
    
    # Find most effective type
    most_effective = max(
        by_type.items(),
        key=lambda x: sum(x[1]) / len(x[1])
    ) if by_type else (None, [])
    
    return {
        "total_actions": total_actions,
        "average_effectiveness": round(avg_effectiveness, 2),
        "most_effective_action_type": most_effective[0],
        "by_action_type": {
            k: round(sum(v) / len(v), 2)
            for k, v in by_type.items()
        }
    }
