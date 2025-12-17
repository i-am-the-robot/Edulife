"""
Agent Tools System
Tools that the AI agent can use autonomously to help students
"""
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from sqlmodel import Session, select
from .models import Student, ChatHistory, TestResult, Tutorial, Task
from .agent_memory import get_student_memory
from .autonomous_quiz_agent import QuizGenerationAgent
from .task_planning_agent import TaskPlanningAgent

class AgentTools:
    """
    Collection of tools the AI agent can use autonomously
    """
    
    def __init__(self, student: Student, session: Session):
        self.student = student
        self.session = session
        self.memory = get_student_memory(student.id, session)
        
        # Register available tools
        self.tools = {
            "analyze_performance": self.analyze_performance,
            "suggest_topics": self.suggest_topics,
            "generate_quiz": self.generate_quiz,
            "create_study_plan": self.create_study_plan,
            "find_weak_areas": self.find_weak_areas,
            "get_learning_recommendations": self.get_learning_recommendations,
            "track_progress": self.track_progress
        }
    
    def use_tool(self, tool_name: str, **kwargs) -> Dict:
        """
        Execute a tool by name
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.tools.keys())
            }
        
        try:
            result = self.tools[tool_name](**kwargs)
            return {
                "success": True,
                "tool": tool_name,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
    
    def analyze_performance(self, subject: Optional[str] = None, days: int = 30) -> Dict:
        """
        Analyze student's performance over time
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(TestResult).where(
            (TestResult.student_id == self.student.id) &
            (TestResult.timestamp >= cutoff_date)
        )
        
        if subject:
            query = query.where(TestResult.subject == subject)
        
        results = self.session.exec(query).all()
        
        if not results:
            return {
                "message": "No test data available",
                "total_tests": 0
            }
        
        # Calculate metrics
        total_tests = len(results)
        correct = sum(1 for r in results if r.is_correct)
        accuracy = (correct / total_tests * 100) if total_tests > 0 else 0
        
        # Group by subject
        by_subject = {}
        for result in results:
            subj = result.subject or "General"
            if subj not in by_subject:
                by_subject[subj] = {"correct": 0, "total": 0}
            by_subject[subj]["total"] += 1
            if result.is_correct:
                by_subject[subj]["correct"] += 1
        
        # Calculate subject accuracies
        subject_performance = {
            subj: {
                "accuracy": (data["correct"] / data["total"] * 100),
                "tests_taken": data["total"]
            }
            for subj, data in by_subject.items()
        }
        
        return {
            "period_days": days,
            "total_tests": total_tests,
            "overall_accuracy": round(accuracy, 1),
            "correct_answers": correct,
            "by_subject": subject_performance,
            "trend": "improving" if accuracy > 70 else "needs_attention"
        }
    
    def suggest_topics(self, subject: str, count: int = 3) -> Dict:
        """
        Suggest topics to study based on performance and curriculum
        """
        # Get weak areas
        weak_areas = self.find_weak_areas(subject=subject)
        
        # Get topics to revisit from memory
        topics_to_revisit = self.memory.get_topics_to_revisit()
        subject_topics = [
            t for t in topics_to_revisit 
            if subject.lower() in t.get("topic", "").lower()
        ]
        
        # Get class-level curriculum topics
        from .schedule_service import get_class_level_topics
        class_topics = get_class_level_topics(self.student.student_class, "")
        subject_curriculum = class_topics.get(subject, [])
        
        suggestions = []
        
        # Priority 1: Weak areas
        for area in weak_areas.get("weak_subjects", [])[:count]:
            suggestions.append({
                "topic": area,
                "reason": "Needs improvement (low performance)",
                "priority": "high"
            })
        
        # Priority 2: Topics to revisit
        for topic in subject_topics[:count - len(suggestions)]:
            suggestions.append({
                "topic": topic.get("topic"),
                "reason": topic.get("reason", "Scheduled for review"),
                "priority": "medium"
            })
        
        # Priority 3: New curriculum topics
        mastered = [t.get("topic") for t in self.memory.get_mastered_topics()]
        for topic in subject_curriculum:
            if len(suggestions) >= count:
                break
            if topic not in mastered and topic not in [s["topic"] for s in suggestions]:
                suggestions.append({
                    "topic": topic,
                    "reason": "Next in curriculum",
                    "priority": "low"
                })
        
        return {
            "subject": subject,
            "suggestions": suggestions[:count],
            "total_available": len(subject_curriculum)
        }
    
    def generate_quiz(self, subject: str, difficulty: Optional[str] = None) -> Dict:
        """
        Generate a quiz for the student
        """
        agent = QuizGenerationAgent(self.student, self.session)
        quiz = agent.generate_adaptive_quiz(subject, difficulty=difficulty)
        
        return {
            "quiz_generated": True,
            "subject": subject,
            "difficulty": quiz.get("difficulty"),
            "questions": quiz.get("questions"),
            "action_id": quiz.get("action_id")
        }
    
    def create_study_plan(
        self,
        goal_type: str,
        target_date: Optional[str] = None,
        subjects: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a study plan for the student
        """
        planner = TaskPlanningAgent(self.student, self.session)
        
        if target_date:
            target = datetime.fromisoformat(target_date)
        else:
            target = datetime.utcnow() + timedelta(days=14)
        
        if goal_type == "exam_prep" and subjects:
            plan = planner.create_exam_preparation_plan(target, subjects)
        elif goal_type == "skill_mastery" and subjects:
            plan = planner.create_skill_mastery_plan(subjects[0], subjects[0], target)
        else:
            return {
                "success": False,
                "error": "Invalid goal_type or missing subjects"
            }
        
        return {
            "plan_created": True,
            "plan_id": plan.id,
            "goal": plan.goal,
            "deadline": plan.deadline.isoformat(),
            "total_steps": len(json.loads(plan.steps))
        }
    
    def find_weak_areas(self, subject: Optional[str] = None) -> Dict:
        """
        Identify areas where student needs improvement
        """
        performance = self.analyze_performance(subject=subject, days=30)
        
        weak_subjects = []
        for subj, data in performance.get("by_subject", {}).items():
            if data["accuracy"] < 60:
                weak_subjects.append({
                    "subject": subj,
                    "accuracy": data["accuracy"],
                    "tests_taken": data["tests_taken"]
                })
        
        # Sort by accuracy (worst first)
        weak_subjects.sort(key=lambda x: x["accuracy"])
        
        return {
            "weak_subjects": [s["subject"] for s in weak_subjects],
            "details": weak_subjects,
            "recommendation": "Focus on these subjects" if weak_subjects else "Keep up the good work!"
        }
    
    def get_learning_recommendations(self) -> Dict:
        """
        Get personalized learning recommendations
        """
        # Analyze overall performance
        performance = self.analyze_performance(days=30)
        
        # Get effective strategies
        effective_strategies = self.memory.get_effective_strategies()
        
        # Get active goals
        active_goals = self.memory.get_active_goals()
        
        recommendations = []
        
        # Based on performance
        if performance.get("overall_accuracy", 0) < 60:
            recommendations.append({
                "type": "performance",
                "message": "Focus on foundational concepts before advancing",
                "action": "Review basic topics"
            })
        elif performance.get("overall_accuracy", 0) > 80:
            recommendations.append({
                "type": "performance",
                "message": "Great progress! Ready for advanced topics",
                "action": "Try challenging problems"
            })
        
        # Based on effective strategies
        if effective_strategies:
            top_strategy = max(effective_strategies, key=lambda x: x.get("success_count", 0))
            recommendations.append({
                "type": "strategy",
                "message": f"Continue using: {top_strategy.get('strategy')}",
                "action": "Apply this strategy to new topics"
            })
        
        # Based on goals
        if not active_goals:
            recommendations.append({
                "type": "goal",
                "message": "Set a learning goal to stay motivated",
                "action": "Create a study plan"
            })
        
        return {
            "recommendations": recommendations,
            "learning_style": self.memory.memory.learning_style,
            "optimal_session_length": self.memory.memory.optimal_session_length
        }
    
    def track_progress(self, metric: str = "overall") -> Dict:
        """
        Track student's learning progress
        """
        # Get historical performance
        last_30_days = self.analyze_performance(days=30)
        last_7_days = self.analyze_performance(days=7)
        
        # Calculate improvement
        improvement = (
            last_7_days.get("overall_accuracy", 0) - 
            last_30_days.get("overall_accuracy", 0)
        )
        
        # Get milestones
        milestones = json.loads(self.memory.memory.progress_milestones or "[]")
        recent_milestones = milestones[-5:] if milestones else []
        
        return {
            "current_accuracy": last_7_days.get("overall_accuracy", 0),
            "30_day_accuracy": last_30_days.get("overall_accuracy", 0),
            "improvement": round(improvement, 1),
            "trend": "improving" if improvement > 0 else "declining" if improvement < 0 else "stable",
            "recent_milestones": recent_milestones,
            "total_tests": last_30_days.get("total_tests", 0)
        }


def decide_which_tool_to_use(student: Student, context: str, session: Session) -> Optional[str]:
    """
    AI decides which tool to use based on context
    Simple rule-based for now, can be enhanced with LLM
    """
    context_lower = context.lower()
    
    # Rule-based decision
    if "performance" in context_lower or "how am i doing" in context_lower:
        return "analyze_performance"
    
    if "quiz" in context_lower or "test" in context_lower:
        return "generate_quiz"
    
    if "what should i study" in context_lower or "suggest" in context_lower:
        return "suggest_topics"
    
    if "plan" in context_lower or "exam" in context_lower:
        return "create_study_plan"
    
    if "weak" in context_lower or "struggling" in context_lower:
        return "find_weak_areas"
    
    if "recommend" in context_lower or "advice" in context_lower:
        return "get_learning_recommendations"
    
    if "progress" in context_lower or "improvement" in context_lower:
        return "track_progress"
    
    return None
