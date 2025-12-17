"""
Agent Self-Reflection
Agent evaluates its own performance and adapts strategies
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlmodel import Session, select, func
from .models import Student, AgentAction, TestResult, ChatHistory
from .agent_memory import get_student_memory
from .agent_service import log_agent_action

class AgentReflection:
    """
    Self-reflection mechanism for the AI agent
    Evaluates effectiveness and adapts strategies
    """
    
    def __init__(self, student: Student, session: Session):
        self.student = student
        self.session = session
        self.memory = get_student_memory(student.id, session)
    
    def evaluate_teaching_effectiveness(self, time_period_days: int = 30) -> Dict:
        """
        Evaluate how effective the agent's teaching has been
        """
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        
        # Get student's test performance over time
        results = self.session.exec(
            select(TestResult).where(
                (TestResult.student_id == self.student.id) &
                (TestResult.timestamp >= cutoff_date)
            ).order_by(TestResult.timestamp)
        ).all()
        
        if len(results) < 5:
            return {
                "evaluation": "insufficient_data",
                "message": "Need more test data to evaluate effectiveness",
                "tests_taken": len(results)
            }
        
        # Calculate improvement rate
        first_half = results[:len(results)//2]
        second_half = results[len(results)//2:]
        
        first_accuracy = sum(1 for r in first_half if r.is_correct) / len(first_half) * 100
        second_accuracy = sum(1 for r in second_half if r.is_correct) / len(second_half) * 100
        
        improvement_rate = second_accuracy - first_accuracy
        
        # Get engagement metrics
        chat_count = self.session.exec(
            select(func.count(ChatHistory.id)).where(
                (ChatHistory.student_id == self.student.id) &
                (ChatHistory.timestamp >= cutoff_date)
            )
        ).one()
        
        # Get agent actions and their effectiveness
        actions = self.session.exec(
            select(AgentAction).where(
                (AgentAction.student_id == self.student.id) &
                (AgentAction.timestamp >= cutoff_date) &
                (AgentAction.effectiveness_score.isnot(None))
            )
        ).all()
        
        avg_action_effectiveness = (
            sum(a.effectiveness_score for a in actions) / len(actions)
            if actions else 0.5
        )
        
        # Overall effectiveness score
        effectiveness_score = (
            (second_accuracy / 100) * 0.4 +  # Current performance (40%)
            (max(0, improvement_rate / 50)) * 0.3 +  # Improvement (30%)
            avg_action_effectiveness * 0.3  # Action effectiveness (30%)
        )
        
        # Determine effectiveness level
        if effectiveness_score >= 0.8:
            level = "highly_effective"
            recommendation = "Continue current approach"
        elif effectiveness_score >= 0.6:
            level = "effective"
            recommendation = "Minor adjustments may help"
        elif effectiveness_score >= 0.4:
            level = "moderately_effective"
            recommendation = "Consider changing teaching strategies"
        else:
            level = "needs_improvement"
            recommendation = "Significant strategy changes needed"
        
        return {
            "evaluation": level,
            "effectiveness_score": round(effectiveness_score, 2),
            "metrics": {
                "first_half_accuracy": round(first_accuracy, 1),
                "second_half_accuracy": round(second_accuracy, 1),
                "improvement_rate": round(improvement_rate, 1),
                "engagement_level": chat_count,
                "action_effectiveness": round(avg_action_effectiveness, 2)
            },
            "recommendation": recommendation,
            "period_days": time_period_days
        }
    
    def identify_ineffective_strategies(self) -> List[Dict]:
        """
        Identify strategies that aren't working
        """
        # Get actions with low effectiveness
        ineffective_actions = self.session.exec(
            select(AgentAction).where(
                (AgentAction.student_id == self.student.id) &
                (AgentAction.effectiveness_score.isnot(None)) &
                (AgentAction.effectiveness_score < 0.5)
            ).order_by(AgentAction.timestamp.desc()).limit(10)
        ).all()
        
        # Group by action type
        ineffective_by_type = {}
        for action in ineffective_actions:
            action_type = action.action_type
            if action_type not in ineffective_by_type:
                ineffective_by_type[action_type] = []
            ineffective_by_type[action_type].append({
                "action_id": action.id,
                "effectiveness": action.effectiveness_score,
                "reasoning": action.reasoning,
                "timestamp": action.timestamp.isoformat()
            })
        
        # Get ineffective strategies from memory
        memory_ineffective = self.memory.memory.ineffective_strategies
        if memory_ineffective:
            memory_strategies = json.loads(memory_ineffective)
        else:
            memory_strategies = []
        
        return {
            "ineffective_actions": ineffective_by_type,
            "known_ineffective_strategies": memory_strategies,
            "total_ineffective": len(ineffective_actions)
        }
    
    def suggest_strategy_adjustments(self, evaluation: Dict) -> List[Dict]:
        """
        Suggest specific strategy adjustments based on evaluation
        """
        suggestions = []
        
        effectiveness_score = evaluation.get("effectiveness_score", 0.5)
        metrics = evaluation.get("metrics", {})
        
        # Based on improvement rate
        improvement = metrics.get("improvement_rate", 0)
        if improvement < 0:
            suggestions.append({
                "area": "teaching_approach",
                "issue": "Student performance is declining",
                "suggestion": "Try more interactive, hands-on learning",
                "priority": "high"
            })
        
        # Based on engagement
        engagement = metrics.get("engagement_level", 0)
        if engagement < 10:  # Less than 10 chats in 30 days
            suggestions.append({
                "area": "engagement",
                "issue": "Low student engagement",
                "suggestion": "Use more gamification and rewards",
                "priority": "high"
            })
        
        # Based on action effectiveness
        action_eff = metrics.get("action_effectiveness", 0.5)
        if action_eff < 0.5:
            suggestions.append({
                "area": "autonomous_actions",
                "issue": "Agent actions not effective",
                "suggestion": "Reduce frequency of check-ins, focus on quality",
                "priority": "medium"
            })
        
        # Based on current accuracy
        current_acc = metrics.get("second_half_accuracy", 50)
        if current_acc < 60:
            suggestions.append({
                "area": "difficulty_level",
                "issue": "Student struggling with current difficulty",
                "suggestion": "Reduce difficulty, focus on fundamentals",
                "priority": "high"
            })
        elif current_acc > 90:
            suggestions.append({
                "area": "difficulty_level",
                "issue": "Content may be too easy",
                "suggestion": "Increase difficulty, introduce advanced topics",
                "priority": "medium"
            })
        
        # Based on personality
        if self.student.personality.value == "Introvert" and engagement < 15:
            suggestions.append({
                "area": "personalization",
                "issue": "Introvert student needs different approach",
                "suggestion": "Use more self-paced learning, less pressure",
                "priority": "medium"
            })
        
        return suggestions
    
    def adjust_strategy(self, evaluation: Dict):
        """
        Automatically adjust teaching strategy based on evaluation
        """
        suggestions = self.suggest_strategy_adjustments(evaluation)
        
        adjustments_made = []
        
        for suggestion in suggestions:
            if suggestion["priority"] == "high":
                # Apply high-priority adjustments
                area = suggestion["area"]
                
                if area == "difficulty_level":
                    # Adjust difficulty in memory
                    if "too easy" in suggestion["suggestion"]:
                        self.memory.add_effective_strategy("increase_difficulty")
                    else:
                        self.memory.add_effective_strategy("simplify_content")
                    
                    adjustments_made.append({
                        "adjustment": suggestion["suggestion"],
                        "applied": True
                    })
                
                elif area == "teaching_approach":
                    # Change teaching approach
                    self.memory.add_ineffective_strategy("current_approach")
                    self.memory.add_goal("Try interactive learning methods")
                    
                    adjustments_made.append({
                        "adjustment": "Switch to interactive learning",
                        "applied": True
                    })
                
                elif area == "engagement":
                    # Increase engagement tactics
                    self.memory.add_goal("Increase student engagement")
                    
                    adjustments_made.append({
                        "adjustment": "Focus on gamification",
                        "applied": True
                    })
        
        # Log the reflection and adjustment
        log_agent_action(
            student_id=self.student.id,
            action_type="strategy_adjusted",
            action_data={
                "evaluation": evaluation,
                "suggestions": suggestions,
                "adjustments_made": adjustments_made
            },
            reasoning=f"Self-reflection: {evaluation.get('evaluation')} - {evaluation.get('recommendation')}",
            session=self.session
        )
        
        return {
            "reflection_complete": True,
            "evaluation": evaluation.get("evaluation"),
            "adjustments_made": adjustments_made,
            "suggestions": suggestions
        }
    
    def run_self_reflection(self) -> Dict:
        """
        Complete self-reflection cycle
        """
        # Evaluate effectiveness
        evaluation = self.evaluate_teaching_effectiveness(time_period_days=30)
        
        if evaluation.get("evaluation") == "insufficient_data":
            return evaluation
        
        # Identify ineffective strategies
        ineffective = self.identify_ineffective_strategies()
        
        # Adjust strategy if needed
        if evaluation.get("effectiveness_score", 1.0) < 0.7:
            adjustments = self.adjust_strategy(evaluation)
        else:
            adjustments = {
                "message": "Current strategies are effective, no changes needed"
            }
        
        return {
            "reflection_timestamp": datetime.utcnow().isoformat(),
            "evaluation": evaluation,
            "ineffective_strategies": ineffective,
            "adjustments": adjustments
        }


def run_reflection_for_all_students(session: Session) -> Dict:
    """
    Run self-reflection for all active students
    Background task to be run periodically
    """
    from .models import Student
    
    students = session.exec(
        select(Student).where(Student.is_active == True)
    ).all()
    
    results = {
        "students_evaluated": 0,
        "adjustments_made": 0,
        "evaluations": []
    }
    
    for student in students:
        reflection = AgentReflection(student, session)
        result = reflection.run_self_reflection()
        
        if result.get("evaluation", {}).get("evaluation") != "insufficient_data":
            results["students_evaluated"] += 1
            
            if result.get("adjustments", {}).get("adjustments_made"):
                results["adjustments_made"] += 1
            
            results["evaluations"].append({
                "student_id": student.id,
                "student_name": student.full_name,
                "effectiveness": result.get("evaluation", {}).get("effectiveness_score"),
                "adjustments": len(result.get("adjustments", {}).get("adjustments_made", []))
            })
    
    return results
