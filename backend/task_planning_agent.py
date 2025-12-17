"""
Task Planning Agent
Creates and manages multi-step plans for complex learning goals
Examples: Exam preparation, skill mastery, assignment completion
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlmodel import Session, select
from .models import Student, TaskPlan, ChatHistory, TestResult, Task
from .agent_memory import get_student_memory
from .agent_service import log_agent_action
from .ai_service import groq_client
import os

class TaskPlanningAgent:
    """
    Agent that creates and manages multi-step learning plans
    """
    
    def __init__(self, student: Student, session: Session):
        self.student = student
        self.session = session
        self.memory = get_student_memory(student.id, session)
    
    def create_exam_preparation_plan(
        self,
        exam_date: datetime,
        subjects: List[str],
        current_knowledge: Optional[Dict] = None
    ) -> TaskPlan:
        """
        Create a comprehensive exam preparation plan
        """
        days_until_exam = (exam_date - datetime.utcnow()).days
        
        if days_until_exam < 1:
            raise ValueError("Exam date must be in the future")
        
        # Assess current knowledge if not provided
        if not current_knowledge:
            current_knowledge = self._assess_current_knowledge(subjects)
        
        # Generate plan steps using AI
        steps = self._generate_exam_prep_steps(
            subjects,
            days_until_exam,
            current_knowledge
        )
        
        # Create task plan
        plan = TaskPlan(
            student_id=self.student.id,
            goal=f"Prepare for exam on {exam_date.strftime('%Y-%m-%d')}",
            plan_type="exam_prep",
            steps=json.dumps(steps),
            deadline=exam_date,
            status="active"
        )
        
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)
        
        # Log action
        log_agent_action(
            student_id=self.student.id,
            action_type="plan_created",
            action_data={
                "plan_id": plan.id,
                "plan_type": "exam_prep",
                "subjects": subjects,
                "days_until_exam": days_until_exam,
                "num_steps": len(steps)
            },
            reasoning=f"Created {days_until_exam}-day exam prep plan for {', '.join(subjects)}",
            session=self.session
        )
        
        # Add goal to agent memory
        self.memory.add_goal(f"Complete exam preparation plan for {', '.join(subjects)}")
        
        return plan
    
    def _assess_current_knowledge(self, subjects: List[str]) -> Dict:
        """
        Assess student's current knowledge level in subjects
        """
        knowledge = {}
        
        for subject in subjects:
            # Get recent test results
            results = self.session.exec(
                select(TestResult).where(
                    (TestResult.student_id == self.student.id) &
                    (TestResult.subject == subject) &
                    (TestResult.timestamp >= datetime.utcnow() - timedelta(days=30))
                )
            ).all()
            
            if results:
                correct = sum(1 for r in results if r.is_correct)
                performance = (correct / len(results)) * 100
            else:
                performance = 50  # Default assumption
            
            # Categorize knowledge level
            if performance >= 80:
                level = "strong"
            elif performance >= 60:
                level = "moderate"
            elif performance >= 40:
                level = "weak"
            else:
                level = "needs_foundation"
            
            knowledge[subject] = {
                "performance": performance,
                "level": level,
                "tests_taken": len(results)
            }
        
        return knowledge
    
    def _generate_exam_prep_steps(
        self,
        subjects: List[str],
        days_available: int,
        current_knowledge: Dict
    ) -> List[Dict]:
        """
        Generate detailed exam preparation steps using AI
        """
        if not groq_client:
            return self._generate_default_steps(subjects, days_available)
        
        # Build knowledge summary
        knowledge_summary = "\n".join([
            f"- {subject}: {data['level']} ({data['performance']:.0f}%)"
            for subject, data in current_knowledge.items()
        ])
        
        prompt = f"""Create a detailed {days_available}-day exam preparation plan for {self.student.full_name}, a {self.student.age}-year-old {self.student.student_class} student.

SUBJECTS TO PREPARE:
{', '.join(subjects)}

CURRENT KNOWLEDGE LEVELS:
{knowledge_summary}

STUDENT PROFILE:
- Personality: {self.student.personality.value}
- Learning style: {self.memory.memory.learning_style or 'Not determined'}
- Optimal session length: {self.memory.memory.optimal_session_length or 30} minutes

REQUIREMENTS:
1. Create a step-by-step plan with {days_available} days
2. Prioritize weak subjects (needs_foundation, weak)
3. Include review sessions for strong subjects
4. Schedule practice tests before exam
5. Include breaks and rest days
6. Each step should have:
   - day_number (1 to {days_available})
   - title (brief description)
   - subject
   - activity_type (study/practice/review/test/rest)
   - duration_minutes
   - topics (list of specific topics)
   - priority (high/medium/low)

Generate a JSON array of steps. Return ONLY the JSON array, no additional text.

Example format:
[
  {{
    "day_number": 1,
    "title": "Mathematics Foundation Review",
    "subject": "Mathematics",
    "activity_type": "study",
    "duration_minutes": 60,
    "topics": ["Algebra basics", "Equations"],
    "priority": "high"
  }},
  ...
]"""
        
        try:
            response = groq_client.chat.completions.create(
                model=os.getenv("GROQ_MODEL"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            steps_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in steps_text:
                steps_text = steps_text.split("```json")[1].split("```")[0].strip()
            elif "```" in steps_text:
                steps_text = steps_text.split("```")[1].split("```")[0].strip()
            
            steps = json.loads(steps_text)
            return steps
            
        except Exception as e:
            print(f"Error generating exam prep steps: {e}")
            return self._generate_default_steps(subjects, days_available)
    
    def _generate_default_steps(self, subjects: List[str], days: int) -> List[Dict]:
        """
        Generate default exam prep steps if AI fails
        """
        steps = []
        days_per_subject = max(1, days // len(subjects))
        
        for i, subject in enumerate(subjects):
            start_day = i * days_per_subject + 1
            
            # Study phase
            steps.append({
                "day_number": start_day,
                "title": f"{subject} - Core Concepts",
                "subject": subject,
                "activity_type": "study",
                "duration_minutes": 60,
                "topics": ["Core concepts", "Key formulas"],
                "priority": "high"
            })
            
            # Practice phase
            if start_day + 1 <= days:
                steps.append({
                    "day_number": start_day + 1,
                    "title": f"{subject} - Practice Problems",
                    "subject": subject,
                    "activity_type": "practice",
                    "duration_minutes": 45,
                    "topics": ["Practice exercises"],
                    "priority": "medium"
                })
        
        # Final review
        if days > 2:
            steps.append({
                "day_number": days - 1,
                "title": "Final Review - All Subjects",
                "subject": "All",
                "activity_type": "review",
                "duration_minutes": 90,
                "topics": ["Quick review", "Key points"],
                "priority": "high"
            })
        
        return steps
    
    def create_skill_mastery_plan(
        self,
        skill: str,
        subject: str,
        target_date: Optional[datetime] = None
    ) -> TaskPlan:
        """
        Create a plan to master a specific skill
        """
        if not target_date:
            target_date = datetime.utcnow() + timedelta(days=14)  # Default 2 weeks
        
        days_available = (target_date - datetime.utcnow()).days
        
        # Generate progressive steps
        steps = [
            {
                "day_number": 1,
                "title": f"Introduction to {skill}",
                "subject": subject,
                "activity_type": "study",
                "duration_minutes": 30,
                "topics": [f"{skill} basics", "Fundamentals"],
                "priority": "high"
            },
            {
                "day_number": 3,
                "title": f"{skill} - Practice Exercises",
                "subject": subject,
                "activity_type": "practice",
                "duration_minutes": 45,
                "topics": ["Beginner exercises"],
                "priority": "high"
            },
            {
                "day_number": 7,
                "title": f"{skill} - Intermediate Level",
                "subject": subject,
                "activity_type": "study",
                "duration_minutes": 60,
                "topics": ["Advanced concepts", "Applications"],
                "priority": "medium"
            },
            {
                "day_number": 10,
                "title": f"{skill} - Advanced Practice",
                "subject": subject,
                "activity_type": "practice",
                "duration_minutes": 60,
                "topics": ["Complex problems"],
                "priority": "medium"
            },
            {
                "day_number": days_available - 1,
                "title": f"{skill} - Mastery Test",
                "subject": subject,
                "activity_type": "test",
                "duration_minutes": 45,
                "topics": ["Comprehensive assessment"],
                "priority": "high"
            }
        ]
        
        plan = TaskPlan(
            student_id=self.student.id,
            goal=f"Master {skill} in {subject}",
            plan_type="skill_mastery",
            steps=json.dumps(steps),
            deadline=target_date,
            status="active"
        )
        
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)
        
        # Log action
        log_agent_action(
            student_id=self.student.id,
            action_type="plan_created",
            action_data={
                "plan_id": plan.id,
                "plan_type": "skill_mastery",
                "skill": skill,
                "subject": subject
            },
            reasoning=f"Created skill mastery plan for {skill}",
            session=self.session
        )
        
        return plan
    
    def monitor_plan_progress(self, plan_id: int) -> Dict:
        """
        Monitor progress on a task plan and provide recommendations
        """
        plan = self.session.get(TaskPlan, plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        steps = json.loads(plan.steps)
        completed_steps = json.loads(plan.completed_steps or "[]")
        
        # Calculate progress
        total_steps = len(steps)
        completed_count = len(completed_steps)
        progress_percentage = (completed_count / total_steps * 100) if total_steps > 0 else 0
        
        # Check if on track
        days_elapsed = (datetime.utcnow() - plan.created_at).days
        days_total = (plan.deadline - plan.created_at).days if plan.deadline else 14
        expected_progress = (days_elapsed / days_total * 100) if days_total > 0 else 0
        
        on_track = progress_percentage >= expected_progress - 10  # 10% tolerance
        
        # Get next step
        next_step = None
        for step in steps:
            if step.get("day_number", 0) not in completed_steps:
                next_step = step
                break
        
        # Recommendations
        recommendations = []
        if not on_track:
            recommendations.append("You're falling behind schedule. Consider dedicating more time today.")
        if next_step and next_step.get("priority") == "high":
            recommendations.append(f"High priority: {next_step.get('title')}")
        if plan.deadline and (plan.deadline - datetime.utcnow()).days <= 2:
            recommendations.append("Exam is approaching! Focus on final review.")
        
        return {
            "plan_id": plan_id,
            "goal": plan.goal,
            "status": plan.status,
            "progress_percentage": round(progress_percentage, 1),
            "completed_steps": completed_count,
            "total_steps": total_steps,
            "on_track": on_track,
            "next_step": next_step,
            "recommendations": recommendations,
            "days_remaining": (plan.deadline - datetime.utcnow()).days if plan.deadline else None
        }
    
    def complete_step(self, plan_id: int, step_day_number: int):
        """
        Mark a step as completed
        """
        plan = self.session.get(TaskPlan, plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        completed_steps = json.loads(plan.completed_steps or "[]")
        
        if step_day_number not in completed_steps:
            completed_steps.append(step_day_number)
            plan.completed_steps = json.dumps(completed_steps)
            plan.current_step = step_day_number
            
            # Check if plan is complete
            steps = json.loads(plan.steps)
            if len(completed_steps) >= len(steps):
                plan.status = "completed"
                plan.completed_at = datetime.utcnow()
                plan.success_rate = 1.0
                
                # Complete goal in memory
                self.memory.complete_goal(plan.goal)
                self.memory.add_milestone(
                    f"Completed: {plan.goal}",
                    {"plan_id": plan_id, "steps_completed": len(completed_steps)}
                )
            
            self.session.add(plan)
            self.session.commit()
    
    def adjust_plan(self, plan_id: int, reason: str, new_deadline: Optional[datetime] = None):
        """
        Adjust a plan based on student progress
        """
        plan = self.session.get(TaskPlan, plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        adjustments = json.loads(plan.adjustments_made or "[]")
        adjustments.append({
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "old_deadline": plan.deadline.isoformat() if plan.deadline else None,
            "new_deadline": new_deadline.isoformat() if new_deadline else None
        })
        
        plan.adjustments_made = json.dumps(adjustments)
        if new_deadline:
            plan.deadline = new_deadline
        
        self.session.add(plan)
        self.session.commit()


def get_active_plans(student_id: str, session: Session) -> List[Dict]:
    """
    Get all active plans for a student
    """
    plans = session.exec(
        select(TaskPlan).where(
            (TaskPlan.student_id == student_id) &
            (TaskPlan.status == "active")
        ).order_by(TaskPlan.deadline)
    ).all()
    
    return [
        {
            "id": p.id,
            "goal": p.goal,
            "plan_type": p.plan_type,
            "created_at": p.created_at.isoformat(),
            "deadline": p.deadline.isoformat() if p.deadline else None,
            "current_step": p.current_step,
            "total_steps": len(json.loads(p.steps))
        }
        for p in plans
    ]
