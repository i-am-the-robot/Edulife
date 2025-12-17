"""
Agent Integration with Notifications
Updates existing agents to send notifications when they take actions
"""

# Add these imports to autonomous_quiz_agent.py
from .notification_service import NotificationService

# In QuizGenerationAgent.generate_adaptive_quiz(), after generating quiz, add:
"""
# Send notification to student
NotificationService.send_quiz_ready_notification(
    student_id=self.student.id,
    subject=subject,
    num_questions=len(questions),
    difficulty=difficulty,
    session=self.session
)
"""

# Add these imports to agent_service.py
from .notification_service import NotificationService

# In perform_proactive_check_ins(), after generating message, add:
"""
# Send notification
NotificationService.send_check_in_notification(
    student_id=student.id,
    message=message,
    days_inactive=student_data["days_inactive"],
    session=session
)
"""

# Add these imports to task_planning_agent.py
from .notification_service import NotificationService

# In create_exam_preparation_plan(), after creating plan, add:
"""
# Send notification
NotificationService.send_plan_update_notification(
    student_id=self.student.id,
    plan_goal=plan.goal,
    update_message=f"Your {days_until_exam}-day exam prep plan is ready!",
    plan_id=plan.id,
    session=self.session
)
"""

# In complete_step(), when plan is completed, add:
"""
# Send achievement notification
NotificationService.send_achievement_notification(
    student_id=self.student.id,
    achievement=f"Completed: {plan.goal}",
    description=f"Congratulations! You've completed all {len(steps)} steps of your study plan!",
    session=self.session
)
"""

# Add these imports to specialized_agents.py (MotivationAgent)
from .notification_service import NotificationService

# In MotivationAgent.celebrate_milestone(), add:
"""
# Send achievement notification
NotificationService.send_achievement_notification(
    student_id=self.student.id,
    achievement=milestone,
    description=celebration,
    session=self.session
)
"""
