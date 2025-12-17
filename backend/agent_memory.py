"""
Agent Memory Service
Manages persistent memory for each student's AI agent
Tracks learning patterns, effective strategies, and agent state
"""
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict
from sqlmodel import Session, select
from .models import AgentMemory, Student
from .database import get_db_session

class StudentAgentMemory:
    """
    Persistent memory manager for student AI agents
    """
    
    def __init__(self, student_id: str, session: Session):
        self.student_id = student_id
        self.session = session
        self.memory = self._load_or_create_memory()
    
    def _load_or_create_memory(self) -> AgentMemory:
        """Load existing memory or create new one"""
        memory = self.session.exec(
            select(AgentMemory).where(AgentMemory.student_id == self.student_id)
        ).first()
        
        if not memory:
            memory = AgentMemory(
                student_id=self.student_id,
                effective_strategies=json.dumps([]),
                ineffective_strategies=json.dumps([]),
                topics_to_revisit=json.dumps([]),
                mastered_topics=json.dumps([]),
                current_focus_topics=json.dumps([]),
                agent_goals=json.dumps([]),
                agent_goals=json.dumps([]),
                progress_milestones=json.dumps([]),
                preferred_examples=json.dumps([]),
                user_facts=json.dumps([])
            )
            self.session.add(memory)
            self.session.commit()
            self.session.refresh(memory)
        
        return memory
    
    def update_interaction(self):
        """Update last interaction time and count"""
        self.memory.last_interaction = datetime.now(timezone.utc)
        self.memory.interaction_count += 1
        self.memory.updated_at = datetime.now(timezone.utc)
        self.session.add(self.memory)
        self.session.commit()
    
    def add_effective_strategy(self, strategy: str):
        """Add a strategy that worked well"""
        strategies = json.loads(self.memory.effective_strategies or "[]")
        if strategy not in strategies:
            strategies.append({
                "strategy": strategy,
                "added_at": datetime.now(timezone.utc).isoformat(),
                "success_count": 1
            })
        else:
            # Increment success count
            for s in strategies:
                if s["strategy"] == strategy:
                    s["success_count"] = s.get("success_count", 1) + 1
        
        self.memory.effective_strategies = json.dumps(strategies)
        self.memory.updated_at = datetime.now(timezone.utc)
        self.session.add(self.memory)
        self.session.commit()
    
    def add_ineffective_strategy(self, strategy: str):
        """Add a strategy that didn't work"""
        strategies = json.loads(self.memory.ineffective_strategies or "[]")
        if strategy not in strategies:
            strategies.append({
                "strategy": strategy,
                "added_at": datetime.now(timezone.utc).isoformat()
            })
        
        self.memory.ineffective_strategies = json.dumps(strategies)
        self.memory.updated_at = datetime.now(timezone.utc)
        self.session.add(self.memory)
        self.session.commit()
    
    def add_topic_to_revisit(self, topic: str, reason: str = ""):
        """Mark a topic for review"""
        topics = json.loads(self.memory.topics_to_revisit or "[]")
        topics.append({
            "topic": topic,
            "reason": reason,
            "added_at": datetime.now(timezone.utc).isoformat()
        })
        
        self.memory.topics_to_revisit = json.dumps(topics)
        self.memory.updated_at = datetime.now(timezone.utc)
        self.session.add(self.memory)
        self.session.commit()
    
    def mark_topic_mastered(self, topic: str):
        """Mark a topic as mastered"""
        mastered = json.loads(self.memory.mastered_topics or "[]")
        if topic not in mastered:
            mastered.append({
                "topic": topic,
                "mastered_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Remove from topics to revisit
        to_revisit = json.loads(self.memory.topics_to_revisit or "[]")
        to_revisit = [t for t in to_revisit if t.get("topic") != topic]
        
        self.memory.mastered_topics = json.dumps(mastered)
        self.memory.topics_to_revisit = json.dumps(to_revisit)
        self.memory.updated_at = datetime.now(timezone.utc)
        self.session.add(self.memory)
        self.session.commit()
    
    def set_learning_style(self, style: str):
        """Set the student's learning style"""
        valid_styles = ["visual", "auditory", "kinesthetic", "reading"]
        if style.lower() in valid_styles:
            self.memory.learning_style = style.lower()
            self.memory.updated_at = datetime.now(timezone.utc)
            self.session.add(self.memory)
            self.session.commit()
    
    def add_goal(self, goal: str):
        """Add an agent goal"""
        goals = json.loads(self.memory.agent_goals or "[]")
        goals.append({
            "goal": goal,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        })
        
        self.memory.agent_goals = json.dumps(goals)
        self.memory.updated_at = datetime.now(timezone.utc)
        self.session.add(self.memory)
        self.session.commit()
    
    def complete_goal(self, goal: str):
        """Mark a goal as completed"""
        goals = json.loads(self.memory.agent_goals or "[]")
        for g in goals:
            if g["goal"] == goal:
                g["status"] = "completed"
                g["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        self.memory.agent_goals = json.dumps(goals)
        self.memory.updated_at = datetime.now(timezone.utc)
        self.session.add(self.memory)
        self.session.commit()
    
    def add_milestone(self, milestone: str, data: dict = None):
        """Add a progress milestone"""
        milestones = json.loads(self.memory.progress_milestones or "[]")
        milestones.append({
            "milestone": milestone,
            "achieved_at": datetime.now(timezone.utc).isoformat(),
            "data": data or {}
        })
        
        self.memory.progress_milestones = json.dumps(milestones)
        self.memory.updated_at = datetime.now(timezone.utc)
        self.session.add(self.memory)
        self.session.add(self.memory)
        self.session.commit()
        
    def add_fact(self, category: str, fact: str):
        """Add a permanent fact about the user"""
        facts = json.loads(self.memory.user_facts or "[]")
        
        # Check duplicates
        for f in facts:
            if f["fact"] == fact:
                return
                
        facts.append({
            "category": category, # e.g., 'hobby', 'pet', 'goal'
            "fact": fact,
            "added_at": datetime.now(timezone.utc).isoformat()
        })
        
        self.memory.user_facts = json.dumps(facts)
        self.memory.updated_at = datetime.now(timezone.utc)
        self.session.add(self.memory)
        self.session.commit()
        
    def get_all_facts(self) -> List[Dict]:
        """Get all stored user facts"""
        return json.loads(self.memory.user_facts or "[]")
    
    def get_effective_strategies(self) -> List[Dict]:
        """Get list of effective strategies"""
        return json.loads(self.memory.effective_strategies or "[]")
    
    def get_topics_to_revisit(self) -> List[Dict]:
        """Get topics that need review"""
        return json.loads(self.memory.topics_to_revisit or "[]")
    
    def get_mastered_topics(self) -> List[Dict]:
        """Get mastered topics"""
        return json.loads(self.memory.mastered_topics or "[]")
    
    def get_active_goals(self) -> List[Dict]:
        """Get active goals"""
        goals = json.loads(self.memory.agent_goals or "[]")
        return [g for g in goals if g.get("status") == "active"]
    
    def get_memory_summary(self) -> Dict:
        """Get a summary of agent memory"""
        return {
            "student_id": self.student_id,
            "learning_style": self.memory.learning_style,
            "interaction_count": self.memory.interaction_count,
            "last_interaction": self.memory.last_interaction.isoformat() if self.memory.last_interaction else None,
            "effective_strategies_count": len(self.get_effective_strategies()),
            "topics_to_revisit_count": len(self.get_topics_to_revisit()),
            "mastered_topics_count": len(self.get_mastered_topics()),
            "active_goals_count": len(self.get_active_goals()),
            "user_facts_count": len(self.get_all_facts()),
            "optimal_session_length": self.memory.optimal_session_length,
            "best_time_of_day": self.memory.best_time_of_day
        }


def get_student_memory(student_id: str, session: Session) -> StudentAgentMemory:
    """Get or create agent memory for a student"""
    return StudentAgentMemory(student_id, session)
