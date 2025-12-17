"""
Agent Coordinator
Orchestrates multiple specialized agents to work together
"""
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone
from sqlmodel import Session
from .models import Student
from .specialized_agents import (
    TutoringAgent,
    AssessmentAgent,
    SchedulingAgent,
    MotivationAgent,
    ParentConnectAgent
)
from .agent_memory import get_student_memory
from .agent_service import log_agent_action

class AgentCoordinator:
    """
    Coordinates multiple specialized agents to provide comprehensive support
    """
    
    def __init__(self, student: Student, session: Session):
        self.student = student
        self.session = session
        # Ensure student is attached to this session
        self.student = session.merge(student)
        self.memory = get_student_memory(student.id, session)
        
        # Initialize specialized agents
        self.tutoring_agent = TutoringAgent(student, session)
        self.assessment_agent = AssessmentAgent(student, session)
        self.scheduling_agent = SchedulingAgent(student, session)
        self.motivation_agent = MotivationAgent(student, session)
        self.parent_connect_agent = ParentConnectAgent(student, session)
    
    async def handle_student_question(self, question: str, subject: str) -> Dict:
        """
        Coordinate agents to handle a student question
        
        Workflow:
        1. Tutoring Agent analyzes and explains
        2. Assessment Agent decides if quiz needed
        3. Scheduling Agent adds practice if needed
        4. Motivation Agent provides encouragement
        """
        response = {
            "question": question,
            "subject": subject,
            "agents_involved": [],
            "actions_taken": []
        }
        
        # Step 0: Gather Initial Context (Parallel Analysis)
        # We start the Main Response generation IMMEDIATELY for lowest latency
        # Analysis tasks run in parallel to support auxiliary agents (Assessment, Motivation)
        print(f"[COORDINATOR] Starting Parallel Execution (All Agents)...")
        
        # --- QUICK INTENT CHECK (Fast Path) ---
        intent = self.tutoring_agent._detect_message_intent(question)
        special_response = await self.tutoring_agent.handle_special_intent(intent, question)
        
        if special_response:
            print(f"[COORDINATOR] Fast Path triggered for intent: {intent['type']}")
            response["explanation"] = special_response
            response["agents_involved"].append("tutoring_fast_path")
            response["actions_taken"].append(f"handled_{intent['type']}")
            
            # Still log the action
            log_agent_action(
                student_id=self.student.id,
                action_type="fast_path_response",
                action_data={"intent": intent["type"], "response": special_response},
                reasoning=f"Handled special intent: {intent['type']}",
                session=self.session
            )
            return response
            
        # Helper for recent chats
        
        # Helper for recent chats
        from .models import ChatHistory
        from sqlmodel import select
        recent_chats = self.session.exec(
            select(ChatHistory).where(
                ChatHistory.student_id == self.student.id
            ).order_by(ChatHistory.timestamp.desc()).limit(20)
        ).all()
        
        conversation_context = "\n".join([
            f"{'Student' if getattr(msg, 'student_message', None) else 'AI'}: {getattr(msg, 'student_message', getattr(msg, 'ai_response', ''))}"
            for msg in reversed(recent_chats)
        ])

        # --- TIME AWARENESS LOGIC ---
        # Calculate time gap to determine context tags for the AI
        context_tag = "[START OF SESSION]"
        if recent_chats:
            last_msg_time = recent_chats[0].timestamp
            # Ensure timezone awareness
            if last_msg_time.tzinfo is None:
                last_msg_time = last_msg_time.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            delta_minutes = (now - last_msg_time).total_seconds() / 60
            
            # Check if last message was a break request
            last_ai_msg = recent_chats[0].ai_response.lower() if recent_chats[0].ai_response else ""
            was_break = "break" in last_ai_msg or "pause" in last_ai_msg or "rest" in last_ai_msg

            if delta_minutes > 15:
                context_tag = "[STUDENT RETURNED AFTER BREAK]"
            elif 3 < delta_minutes <= 15 and was_break:
                context_tag = "[RETURNED EARLY FROM BREAK]"
            else:
                context_tag = "[CONTINUOUS CONVERSATION]"
        
        conversation_context += f"\n\nSYSTEM_NOTE: {context_tag}"

        # --- CONTINUOUS ASSESSMENT LOGIC ---
        # 1. Random Micro-Assessments (Every ~5 turns)
        # We use the number of recent chats as a proxy for 'turn count' in this session window
        # In a real app, we'd store a persistent 'turns_since_last_quiz' counter
        turn_count = len(recent_chats)
        if turn_count > 0 and turn_count % 5 == 0:
             conversation_context += "\n[MICRO_ASSESSMENT_TRIGGER]: Ask a quick, casual check-up question about the current topic to verify understanding."

        # 2. Test Corrections
        # If student asks for corrections, fetch the last test result
        if "correction" in question.lower() or "wrong" in question.lower() or "mistake" in question.lower():
            from .models import TestResult
            last_test_results = self.session.exec(
                select(TestResult).where(
                    TestResult.student_id == self.student.id
                ).order_by(TestResult.timestamp.desc()).limit(5) # Get last batch
            ).all()
            
            if last_test_results:
                # Group by timestamp to get the single 'quiz' session
                latest_timestamp = last_test_results[0].timestamp
                current_quiz_results = [r for r in last_test_results if r.timestamp == latest_timestamp]
                
                correction_data = "\n".join([
                    f"- Q: {r.question_text} | Student: {r.student_answer} | Correct: {r.correct_answer} | Correct?: {r.is_correct}"
                    for r in current_quiz_results
                ])
                conversation_context += f"\n\n[LAST_QUIZ_CORRECTION_DATA]:\n{correction_data}\nINSTRUCTION: Explain WHY the wrong answers were wrong using this data."

        # DEFINING ALL TASKS
        
        # 1. Analysis Tasks (Background)
        # 1. Analysis Tasks (Background)
        # Wrap in create_task so they can be awaited multiple times safely
        task_sentiment = asyncio.create_task(self.motivation_agent.analyze_sentiment(question))
        task_confusion = asyncio.create_task(self.tutoring_agent.analyze_confusion(question, subject, conversation_context))
        
        # 2. Main Tutor Response (Critical Path - No dependency on Analysis to start)
        # We pass None for confusion_analysis so it self-analyzes or uses defaults to save time
        task_explanation = self.tutoring_agent.generate_explanation({}, subject, question, conversation_context)
        
        # 3. Auxiliary Tasks
        # These need to wait for analysis results, so we wrap them
        async def run_assessment_branch():
             analysis = await task_confusion
             if not analysis:
                 analysis = {}
             # Logic Check for Assessment
             decision = self.assessment_agent.should_assess(subject, {
                "just_finished_tutoring": False,
                "confusion_level": analysis.get("confusion_level"),
                "last_user_message": question
             })
             if decision.get("should_assess"):
                 qs = self.assessment_agent.generate_targeted_questions(
                     subject, decision.get("recommended_difficulty", "medium"), num_questions=3
                 )
                 return {"quiz": {"questions": qs, "difficulty": decision.get("recommended_difficulty"), "reasons": decision.get("reasons")}}
             return None

        async def run_practice_branch():
             analysis = await task_confusion
             if not analysis:
                 analysis = {}
             if analysis.get("confusion_level") in ["medium", "high"]:
                 return self.scheduling_agent.optimize_study_time([subject], 1, [subject])
             return None
            
        async def run_motivation_branch():
             sentiment = await task_sentiment
             # Distress Check (Instant Intervention)
             if sentiment.get("is_distress", False):
                 return {"is_intervention": True, "message": sentiment.get("support_response")}
                 
             engagement = await self.motivation_agent.assess_engagement_level()
             if self.motivation_agent.should_send_encouragement(engagement):
                 msg = await self.motivation_agent.generate_encouragement({
                     "struggle": subject, # Simplified
                     "achievement": "asking great questions"
                 })
                 return {"is_intervention": False, "message": msg}
             return None

        async def run_fatigue_branch():
             # Estimate counts
             today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
             msgs_today_count = self.session.exec(
                 select(ChatHistory).where((ChatHistory.student_id == self.student.id) & (ChatHistory.timestamp >= today_start))
             ).all()
             count = len(msgs_today_count)
             res = self.scheduling_agent.prevent_burnout({
                 "sessions_today": 1, "minutes_today": count * 2, "current_session_minutes": count * 2,
                 "consecutive_days": self.student.login_frequency or 1, "fatigue_signs_detected": len(question) < 5
             })
             if res.get("is_break_needed"):
                 return res.get("recommendations", ["Take a break!"])[0]
             return None
            
        async def run_badge_branch():
            return self.parent_connect_agent.check_new_badges()

        async def run_schedule_branch():
            if self.scheduling_agent.should_proactively_schedule():
                 await asyncio.to_thread(self.scheduling_agent.create_full_schedule)
                 return "\n\n📅 **I've also created a study timetable for you!**"
            return None
            
        # EXECUTE ALL (Optimized gather)
        results = await asyncio.gather(
            task_explanation,
            run_assessment_branch(),
            run_practice_branch(),
            run_motivation_branch(),
            run_fatigue_branch(),
            run_badge_branch(),
            run_schedule_branch(),
            task_confusion, # We need the actual analysis object for logs
            task_sentiment  # We need the actual sentiment object for logs
        )
        
        # Unpack
        (education_text, quiz_data, practice_data, motivation_data, break_msg, new_badges, schedule_msg, confusion_res, sentiment_res) = results
        
        encouragement_msg = None
        if motivation_data:
             if motivation_data.get("is_intervention"):
                 # Override explanation if distress
                 education_text = f"{motivation_data['message']}\n\nDo you want to take a short break?"
                 response["agents_involved"].append("motivation_intervention")
             else:
                 encouragement_msg = motivation_data.get("message")

        # --- DETAILED AGENT LOGS ---
        print("\n" + "="*60)
        print(f"🤖 AGENT WORKSPACE LOG | User: {self.student.full_name}")
        print("="*60)
        print(f"📝 INPUT: \"{question}\"")
        print(f"🧠 CONTEXT: Subject={subject}")
        print("-" * 30)
        
        print(f"⚡ [PARALLEL EXECUTION REPORT]")
        print(f"   > Tutoring Agent:   ✅ Generated Response ({len(education_text)} chars)")
        print(f"   > Analysis Agent:   ✅ Confusion={confusion_res.get('confusion_level')}")
        print(f"   > Sentiment Agent:  ✅ Emotion={sentiment_res.get('emotion')}")
        
        if quiz_data:
            print(f"   > Assessment Agent: 🎯 QUIZ GENERATED")
            print(f"     - Difficulty: {quiz_data['quiz']['difficulty']}")
            print(f"     - Rationale: {quiz_data['quiz']['reasons']}")
        else:
             print(f"   > Assessment Agent: 💤 No quiz needed")
             
        if practice_data:
             print(f"   > Schedule Agent:   📅 PRACTICE SCHEDULED")
        else:
             print(f"   > Schedule Agent:   💤 No practice needed")
             
        if motivation_data:
             print(f"   > Motivation Agent: ❤️ ACTIVE")
             print(f"     - Message: \"{motivation_data.get('message')}\"")
        else:
             print(f"   > Motivation Agent: 💤 Monitoring")
             
        if break_msg:
             print(f"   > Fatigue Monitor:  ⚠️ BREAK ADVISED: \"{break_msg}\"")
        else:
             print(f"   > Fatigue Monitor:  ✅ Energy levels ok")
             
        print("-" * 30)
        print(f"📤 FINAL OUTPUT: \"{education_text[:100]}...\"")
        print("="*60 + "\n")
        # ---------------------------
        
        # Assemble Response (Standard logic)
        response["explanation"] = education_text
        response["confusion_analysis"] = confusion_res
        response["agents_involved"].append("tutoring")
        response["actions_taken"].append("provided_explanation")
        
        if quiz_data:
            response["quiz"] = quiz_data["quiz"]
            response["agents_involved"].append("assessment")
        
        if practice_data:
            response["practice_schedule"] = practice_data
            response["agents_involved"].append("scheduling")
            
        if encouragement_msg and not motivation_data.get("is_intervention"):
            if schedule_msg:
                encouragement_msg += schedule_msg
                schedule_msg = None
            response["encouragement"] = encouragement_msg
            response["agents_involved"].append("motivation")
            
        if break_msg:
            response["break_suggestion"] = break_msg
            response["agents_involved"].append("scheduling_fatigue_monitor")
            
        if new_badges:
            response["new_badges"] = new_badges
            response["agents_involved"].append("parent_connect")
            
        if schedule_msg:
             response["explanation"] += schedule_msg
             response["agents_involved"].append("scheduling_proactive")

        # Log coordination
        log_agent_action(
            student_id=self.student.id,
            action_type="multi_agent_coordination",
            action_data={
                "agents_involved": response["agents_involved"],
                "actions_taken": response["actions_taken"],
                "subject": subject
            },
            reasoning=f"Optimized Parallel Execution for {subject}",
            session=self.session
        )
        
        return response
    
    async def handle_student_question_stream(self, question: str, subject: str):
        """
        Stream coordinator response to reduce latency.
        Yields chunks:
        1. {"type": "response", "content": "..."} (Streaming text) - NOT YET IMPLEMENTED FULL STREAMING TEXT, just yielding full response early
        2. {"type": "control", "data": {...}} (Quiz, Schedule, Badge updates)
        """
        try:
            # Step 0: Gather Initial Context
            print(f"[COORDINATOR] Starting Streaming Execution...")
        
            # --- QUICK INTENT CHECK (Fast Path for Streaming) ---
            intent = self.tutoring_agent._detect_message_intent(question)
            special_response = await self.tutoring_agent.handle_special_intent(intent, question)
        
            if special_response:
                 print(f"[COORDINATOR] Streaming Fast Path for intent: {intent['type']}")
                 # Yield response immediately
                 yield json.dumps({
                    "type": "response",
                    "content": special_response
                 }) + "\n"
             
                 # Yield control (empty)
                 yield json.dumps({
                    "type": "control",
                    "data": {"agents_involved": ["tutoring_fast_path"]}
                 }) + "\n"
                 return
        
            # ... (Same context gathering logic as handle_student_question) ...
            # For DRY, we should refactor, but for now we'll duplicate the critical context logic for speed
        
            from .models import ChatHistory
            from sqlmodel import select
            recent_chats = self.session.exec(
                select(ChatHistory).where(
                    ChatHistory.student_id == self.student.id
                ).order_by(ChatHistory.timestamp.desc()).limit(20)
            ).all()
        
            conversation_context = "\n".join([
                f"{'Student' if getattr(msg, 'student_message', None) else 'AI'}: {getattr(msg, 'student_message', getattr(msg, 'ai_response', ''))}"
                for msg in reversed(recent_chats)
            ])
        
            # --- TIME AWARENESS LOGIC (Simplified) ---
            context_tag = "[START OF SESSION]"
            if recent_chats:
                 last_msg_time = recent_chats[0].timestamp
                 if last_msg_time.tzinfo is None:
                     last_msg_time = last_msg_time.replace(tzinfo=timezone.utc)
                 now = datetime.now(timezone.utc)
                 delta_minutes = (now - last_msg_time).total_seconds() / 60
                 if delta_minutes > 15: context_tag = "[STUDENT RETURNED AFTER BREAK]"
                 else: context_tag = "[CONTINUOUS CONVERSATION]"
            conversation_context += f"\n\nSYSTEM_NOTE: {context_tag}"

            # 1. Start Analysis Tasks (Background)
            task_sentiment = asyncio.create_task(self.motivation_agent.analyze_sentiment(question))
            task_confusion = asyncio.create_task(self.tutoring_agent.analyze_confusion(question, subject, conversation_context))
        
            # 2. Main Tutor Response (Blocking but yielded first)
            # We await this first so we can send audio ASAP
            education_text = await self.tutoring_agent.generate_explanation({}, subject, question, conversation_context)
        
            # YIELD 1: The spoken response
            yield json.dumps({
                "type": "response",
                "content": education_text
            }) + "\n"
        
            # 3. Auxiliary Tasks (Parallel)
            # These run while the user is listening to the first part
        
            async def run_assessment_branch():
                 analysis = await task_confusion
                 if not analysis: analysis = {}
                 decision = self.assessment_agent.should_assess(subject, {
                    "just_finished_tutoring": False, # Prevent aggressive quiz
                    "confusion_level": analysis.get("confusion_level"),
                    "last_user_message": question
                 })
                 if decision.get("should_assess"):
                     qs = self.assessment_agent.generate_targeted_questions(
                         subject, decision.get("recommended_difficulty", "medium"), num_questions=3
                     )
                     return {"quiz": {"questions": qs, "difficulty": decision.get("recommended_difficulty"), "reasons": decision.get("reasons")}}
                 return None

            async def run_practice_branch():
                 analysis = await task_confusion
                 if not analysis: analysis = {}
                 if analysis.get("confusion_level") in ["medium", "high"]:
                     return self.scheduling_agent.optimize_study_time([subject], 1, [subject])
                 return None
            
            async def run_motivation_branch():
                 sentiment = await task_sentiment
                 if sentiment.get("is_distress", False):
                     return {"is_intervention": True, "message": sentiment.get("support_response")}
                 engagement = await self.motivation_agent.assess_engagement_level()
                 if self.motivation_agent.should_send_encouragement(engagement):
                     msg = await self.motivation_agent.generate_encouragement({"struggle": subject, "achievement": "asking great questions"})
                     return {"is_intervention": False, "message": msg}
                 return None

            async def run_fatigue_branch():
                 # ... (Simplified fatigue) ...
                 return None
            
            async def run_badge_branch():
                return self.parent_connect_agent.check_new_badges()

            async def run_schedule_branch():
                if self.scheduling_agent.should_proactively_schedule():
                     self.scheduling_agent.create_full_schedule()
                     return "\n\n📅 **I've also created a study timetable for you!**"
                return None
            
            # EXECUTE ALL AUXILIARY
            results = await asyncio.gather(
                run_assessment_branch(),
                run_practice_branch(),
                run_motivation_branch(),
                run_fatigue_branch(),
                run_badge_branch(),
                run_schedule_branch(),
                task_confusion,
                task_sentiment
            )
        
            (quiz_data, practice_data, motivation_data, break_msg, new_badges, schedule_msg, confusion_res, sentiment_res) = results

            # Assemble Control Data
            control_data = {
                "agents_involved": ["tutoring"],
                "actions_taken": ["provided_explanation"]
            }
        
            if quiz_data:
                control_data["quiz"] = quiz_data["quiz"]
                control_data["agents_involved"].append("assessment")
        
            if practice_data:
                control_data["practice_schedule"] = practice_data
                control_data["agents_involved"].append("scheduling")
            
            if motivation_data and not motivation_data.get("is_intervention"):
                 control_data["encouragement"] = motivation_data.get("message")
                 control_data["agents_involved"].append("motivation")
             
            if new_badges:
                control_data["new_badges"] = new_badges
                control_data["agents_involved"].append("parent_connect")

            if schedule_msg:
                 control_data["schedule_msg"] = schedule_msg
             
            # YIELD 2: Control Data
            yield json.dumps({
                "type": "control",
                "data": control_data
            }) + "\n"
        
            # Log coordination (Background)
            log_agent_action(
                student_id=self.student.id,
                action_type="multi_agent_stream",
                action_data=control_data,
                reasoning=f"Streamed execution for {subject}",
                session=self.session
            )

        except Exception as e:
            print(f"CRITICAL STREAM ERROR: {e}")
            import traceback
            traceback.print_exc()
            yield json.dumps({
                "type": "response",
                "content": f"I encountered a system error: {str(e)}"
            }) + "\n"
    
    def handle_exam_preparation(
        self,
        exam_date: datetime,
        subjects: List[str]
    ) -> Dict:
        """
        Coordinate agents for comprehensive exam preparation
        """
        response = {
            "exam_date": exam_date.isoformat(),
            "subjects": subjects,
            "preparation_plan": {},
            "agents_involved": []
        }
        
        # Step 1: Assessment Agent evaluates current knowledge
        print(f"[COORDINATOR] Assessment Agent evaluating current knowledge...")
        knowledge_assessment = {}
        for subject in subjects:
            from .models import TestResult
            from sqlmodel import select
            from datetime import timedelta
            
            recent_tests = self.session.exec(
                select(TestResult).where(
                    (TestResult.student_id == self.student.id) &
                    (TestResult.subject == subject) &
                    (TestResult.timestamp >= datetime.utcnow() - timedelta(days=30))
                )
            ).all()
            
            mastery = self.assessment_agent.evaluate_mastery(subject, recent_tests)
            knowledge_assessment[subject] = mastery
        
        response["knowledge_assessment"] = knowledge_assessment
        response["agents_involved"].append("assessment")
        
        # Step 2: Scheduling Agent creates study plan
        print(f"[COORDINATOR] Scheduling Agent creating study plan...")
        days_until_exam = (exam_date - datetime.utcnow()).days
        
        # Prioritize weak subjects
        weak_subjects = [
            subj for subj, data in knowledge_assessment.items()
            if data.get("mastery_level", 0) < 0.6
        ]
        
        time_allocation = self.scheduling_agent.optimize_study_time(
            subjects=subjects,
            available_hours_per_day=3,  # More time for exam prep
            priority_subjects=weak_subjects
        )
        
        response["study_schedule"] = time_allocation
        response["weak_subjects"] = weak_subjects
        response["agents_involved"].append("scheduling")
        
        # Step 3: Tutoring Agent creates topic breakdown
        print(f"[COORDINATOR] Tutoring Agent planning topics...")
        topic_recommendations = {}
        for subject in subjects:
            mastery_level = knowledge_assessment[subject].get("mastery_level", 0.5)
            next_topic = self.tutoring_agent.recommend_next_topic(subject, mastery_level)
            topic_recommendations[subject] = next_topic
        
        response["topic_recommendations"] = topic_recommendations
        response["agents_involved"].append("tutoring")
        
        # Step 4: Motivation Agent sets milestones
        print(f"[COORDINATOR] Motivation Agent setting milestones...")
        milestone_message = self.motivation_agent.celebrate_milestone(
            f"Started {days_until_exam}-day exam preparation",
            {"subjects": subjects, "exam_date": exam_date.isoformat()}
        )
        
        response["motivation"] = {
            "milestone_message": milestone_message,
            "daily_encouragement_scheduled": True
        }
        response["agents_involved"].append("motivation")
        
        # Log coordination
        log_agent_action(
            student_id=self.student.id,
            action_type="exam_prep_coordination",
            action_data={
                "agents_involved": response["agents_involved"],
                "subjects": subjects,
                "days_until_exam": days_until_exam
            },
            reasoning=f"Coordinated {len(response['agents_involved'])} agents for exam preparation",
            session=self.session
        )
        
        return response
    
    def handle_low_engagement(self) -> Dict:
        """
        Coordinate agents to re-engage inactive student
        """
        response = {
            "intervention_type": "low_engagement",
            "agents_involved": [],
            "actions": []
        }
        
        # Step 1: Motivation Agent assesses engagement
        print(f"[COORDINATOR] Motivation Agent assessing engagement...")
        engagement = self.motivation_agent.assess_engagement_level()
        response["engagement_assessment"] = engagement
        response["agents_involved"].append("motivation")
        
        if engagement.get("engagement_level") == "low":
            # Step 2: Motivation Agent sends encouragement
            print(f"[COORDINATOR] Motivation Agent sending encouragement...")
            encouragement = self.motivation_agent.generate_encouragement({
                "struggle": "staying engaged",
                "achievement": None
            })
            response["encouragement"] = encouragement
            response["actions"].append("sent_encouragement")
            
            # Step 3: Scheduling Agent suggests lighter schedule
            print(f"[COORDINATOR] Scheduling Agent adjusting schedule...")
            burnout_check = self.scheduling_agent.prevent_burnout({
                "sessions_today": 0,
                "hours_today": 0,
                "consecutive_days": 0
            })
            response["schedule_adjustment"] = burnout_check
            response["agents_involved"].append("scheduling")
            response["actions"].append("adjusted_schedule")
            
            # Step 4: Tutoring Agent suggests fun topic
            print(f"[COORDINATOR] Tutoring Agent suggesting engaging topic...")
            # Suggest topic related to student's hobby
            fun_topic = f"Explore how {self.student.hobby} relates to learning"
            response["fun_topic_suggestion"] = fun_topic
            response["agents_involved"].append("tutoring")
            response["actions"].append("suggested_fun_topic")
        
        # Log coordination
        log_agent_action(
            student_id=self.student.id,
            action_type="low_engagement_intervention",
            action_data={
                "agents_involved": response["agents_involved"],
                "engagement_level": engagement.get("engagement_level"),
                "actions": response["actions"]
            },
            reasoning=f"Coordinated {len(response['agents_involved'])} agents to address low engagement",
            session=self.session
        )
        
        return response
    
    def daily_check_in(self) -> Dict:
        """
        Daily coordination of all agents for student wellness
        """
        response = {
            "check_in_type": "daily",
            "timestamp": datetime.utcnow().isoformat(),
            "agent_reports": {}
        }
        
        # Get report from each agent
        print(f"[COORDINATOR] Running daily check-in for {self.student.full_name}...")
        
        # Motivation Agent: Engagement check
        engagement = self.motivation_agent.assess_engagement_level()
        response["agent_reports"]["motivation"] = {
            "engagement_level": engagement.get("engagement_level"),
            "recommendation": "Send encouragement" if engagement.get("engagement_level") == "low" else "Continue monitoring"
        }
        
        # Scheduling Agent: Burnout check
        burnout = self.scheduling_agent.prevent_burnout({
            "sessions_today": 0,  # Would be calculated from actual data
            "hours_today": 0,
            "consecutive_days": 0
        })
        response["agent_reports"]["scheduling"] = {
            "burnout_risk": burnout.get("burnout_risk"),
            "recommendations": burnout.get("recommendations", [])
        }
        
        # Assessment Agent: Check if assessment needed
        # (Would check across all subjects)
        response["agent_reports"]["assessment"] = {
            "assessments_pending": 0,
            "recommendation": "Monitor activity"
        }
        
        # Tutoring Agent: Check for topics to revisit
        topics_to_revisit = self.memory.get_topics_to_revisit()
        response["agent_reports"]["tutoring"] = {
            "recommendation": f"Review {len(topics_to_revisit)} topics" if topics_to_revisit else "No review needed"
        }
        
        # Parent Connect Agent: Send daily summary if appropriate
        # (e.g., if there's activity or if it's Friday)
        # For this hackathon, we'll try to send it if there's any activity
        print(f"[COORDINATOR] Parent Connect Agent checking activity...")
        
        # Mock activity report (in real system, this comes from an analytics service)
        activity_report = {
            "total_actions": 5, # Mock: assuming some activity
            "completed_tasks": 1,
            "subjects_studied": "General",
            "average_quiz_score": "85%"
        }
        
        parent_notification = self.parent_connect_agent.notify_daily_summary(activity_report)
        response["agent_reports"]["parent_connect"] = parent_notification
        
        return response


def coordinate_all_students(session: Session) -> Dict:
    """
    Run daily coordination for all active students
    Background task
    """
    from .models import Student
    from sqlmodel import select
    
    students = session.exec(
        select(Student).where(Student.is_active == True)
    ).all()
    
    results = {
        "students_checked": len(students),
        "interventions": [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    for student in students:
        coordinator = AgentCoordinator(student, session)
        
        # Run daily check-in
        check_in = coordinator.daily_check_in()
        
        # Take action if needed
        engagement_level = check_in["agent_reports"]["motivation"]["engagement_level"]
        if engagement_level == "low":
            intervention = coordinator.handle_low_engagement()
            results["interventions"].append({
                "student_id": student.id,
                "student_name": student.full_name,
                "intervention": intervention
            })
    
    return results
