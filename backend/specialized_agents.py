"""
Multi-Agent System - Specialized Agents
Each agent has expertise in a specific domain
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlmodel import Session, select
from .models import Student, ChatHistory, TestResult
from .agent_memory import get_student_memory
from .agent_service import log_agent_action
from .rag_service import get_syllabus_context
from groq import AsyncGroq
import os
import random


# Initialize async client
aclient = None
if os.getenv("GROQ_API_KEY"):
    aclient = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

# ============================================================================
# BASE AGENT CLASS
# ============================================================================

class BaseAgent:
    """Base class for all specialized agents"""
    
    def __init__(self, student: Student, session: Session):
        self.student = student
        self.session = session
        self.memory = get_student_memory(student.id, session)
        self.agent_type = "base"
    
    def log_action(self, action_type: str, data: Dict, reasoning: str):
        """Log agent action"""
        return log_agent_action(
            student_id=self.student.id,
            action_type=f"{self.agent_type}_{action_type}",
            action_data=data,
            reasoning=f"[{self.agent_type.upper()}] {reasoning}",
            session=self.session
        )


# ============================================================================
# TUTORING AGENT
# ============================================================================

class TutoringAgent(BaseAgent):
    """
    Specialized in explaining concepts and answering questions
    Expertise: Pedagogy, explanation strategies, concept breakdown
    """
    
    def __init__(self, student: Student, session: Session):
        super().__init__(student, session)
        self.agent_type = "tutoring"
        self.greeting_count = 0
        self.last_topic_discussed = None

    async def extract_facts_from_message(self, message: str):
        """
        Background task: Extract permanent facts about the user
        e.g., "I have a dog named Rex", "I love soccer"
        """
        if len(message.split()) < 3:
            return
            
        system_prompt = """
        You are a Memory Specialist. Extract PERMANENT FACTS about the user from their message.
        Examples: "My name is John" -> {"category": "identity", "fact": "Name is John"}
        "I love playing chess" -> {"category": "hobby", "fact": "Loves playing chess"}
        "I'm struggling with algebra" -> {"category": "academic_struggle", "fact": "Struggles with algebra"}
        
        IGNORE: Greetings, simple questions, temporary states ("I'm hungry").
        OUTPUT JSON ONLY: {"facts": [{"category": "...", "fact": "..."}]}
        If no facts, output {"facts": []}
        """
        
        try:
            response = await aclient.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            for item in data.get("facts", []):
                print(f"[MEMORY] stored fact: {item['fact']}")
                self.memory.add_fact(item.get("category", "general"), item.get("fact"))
                
        except Exception as e:
            print(f"Fact extraction failed: {e}")

    # Removed _get_dynamic_greeting - now handled by AI's dynamic prompt system

    def _detect_message_intent(self, message: str) -> Dict[str, any]:
        """Detect what the student actually wants"""
        msg_lower = message.lower().strip()
        
        # Quiz request
        if any(word in msg_lower for word in ["quiz", "test me", "exam", "practice questions"]):
            return {"type": "quiz_request", "confidence": "high"}
        
        # Summary request
        if any(phrase in msg_lower for phrase in ["what did we", "what have we", "summary", "recap"]):
            return {"type": "summary_request", "confidence": "high"}
        
        # Greeting
        greeting_words = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "hy"]
        if msg_lower in greeting_words or (len(message.split()) <= 3 and any(g in msg_lower for g in greeting_words)):
            return {"type": "greeting", "confidence": "high"}
        
        # Gratitude
        if any(word in msg_lower for word in ["thank you", "thanks", "thank u", "thx", "appreciate"]):
            return {"type": "gratitude", "confidence": "high"}
        
        # Tired/Break request
        if any(word in msg_lower for word in ["tired", "sleepy", "break", "rest", "stop", "bye", "goodbye"]):
            return {"type": "tired", "confidence": "medium"}
        
        # Profanity
        if any(word in msg_lower for word in ["fuck", "shit", "damn", "stupid ai"]):
            return {"type": "profanity", "confidence": "high"}
        
        # Simple questions
        if msg_lower in ["what", "how", "why", "when", "where", "who"]:
            return {"type": "simple_question", "confidence": "medium"}
        
        # Unsure what to learn
        if any(phrase in msg_lower for phrase in [
            "what should i learn",
            "what to learn",
            "don't know what",

            "not sure what",
            "help me choose",
            "what topic",
            "suggest something"
        ]):
            return {"type": "unsure_what_to_learn", "confidence": "high"}
        
        # Visual request
        if any(word in msg_lower for word in ["show me", "picture", "image", "diagram", "draw"]):
            return {"type": "visual_request", "confidence": "medium"}
        
        # Default: learning question
        return {"type": "learning", "confidence": "low"}

    async def handle_special_intent(self, intent: Dict, message: str) -> Optional[str]:
        """Handle special intents that don't need full explanation generation"""
        
        if intent["type"] == "quiz_request":
            # Return None so it falls through to Agent Coordinator
            # This allows AssessmentAgent to generate the proper JSON for the Quiz Modal
            return None
        
        # For greetings, gratitude, tired, profanity, simple questions:
        # Return None to let the AI generate dynamic, vibrant responses
        # This prevents hardcoded, repetitive responses
        if intent["type"] in ["greeting", "gratitude", "tired", "profanity", "simple_question"]:
            return None  # Let AI handle it dynamically
        
        if intent["type"] == "summary_request":
            # Return None to let AI generate dynamic summary
            return None
        
        if intent["type"] == "unsure_what_to_learn":
            # Check timetable first
            from .specialized_agents import SchedulingAgent
            scheduling_agent = SchedulingAgent(self.student, self.session)
            timetable_suggestion = scheduling_agent.suggest_topic_from_timetable()
            
            if timetable_suggestion:
                return timetable_suggestion
            
            # Let AI suggest based on weak subjects dynamically
            return None

        if intent["type"] == "visual_request":
            # Fall through to generation, but the system prompt will handle the tag logic
            return None
        
        return None


    async def generate_quiz_question(self, topic: str = None) -> str:
        """Generate an actual quiz question"""
        if not aclient:
            return "Connection issue. Try again?"
        
        prompt = f"Generate a quiz question for a {self.student.age} year old student about {topic or 'general knowledge'}."
        try:
             response = await aclient.chat.completions.create(
                model=os.getenv("GROQ_MODEL"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
             return response.choices[0].message.content
        except:
            return "What is something you learned today?"
    
    async def analyze_confusion(self, student_question: str, subject: str, conversation_context: str = None) -> Dict:
        """
        Analyze what the student is confused about using conversation context
        """
        if not aclient:
            return {"confusion_level": "unknown", "topics": []}
        
        prompt = f"""Analyze this student question to identify confusion points, using the recent conversation for context:

RECENT CONVERSATION:
{conversation_context or 'No prior context'}

CURRENT QUESTION: "{student_question}"
Subject: {subject}
Student: {self.student.age} years old, {self.student.student_class}

IMPORTANT: Be tolerant of typos, spelling errors, and unclear grammar. Interpret the intent behind the message.

Identify:
1. Main topic of confusion
2. Prerequisite concepts they might be missing
3. Confusion level (low/medium/high)
4. Whether the message is a greeting, off-topic chat, or learning-related
5. Whether you need to ask a clarifying question to understand them better.

Return JSON:
{{
  "main_topic": "...",
  "prerequisites_missing": ["..."],
  "confusion_level": "low/medium/high",
  "recommended_approach": "...",
  "message_type": "greeting/off-topic/learning/question",
  "need_clarification": true/false,
  "clarifying_question": "..." (if needed)
}}"""
        
        try:
            response = await aclient.chat.completions.create(
                model=os.getenv("GROQ_MODEL"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].strip()
            
            return json.loads(result_text)
        except Exception as e:
            print(f"Error analyzing confusion: {e}")
            return {
                "confusion_level": "low", 
                "main_topic": subject, 
                "recommended_approach": "Direct answer",
                "message_type": "learning"
            }
    
    def _analyze_conversation_context(self, conversation_history: str) -> str:
        """
        Analyze conversation to determine context flags for greeting logic
        """
        if not conversation_history or len(conversation_history) < 20:
            return "[START OF SESSION]"
        
        history_lower = conversation_history.lower()
        
        # Check for break patterns
        # Check for break patterns in RECENT history only (last 500 chars)
        recent_history = conversation_history[-500:].lower() if len(conversation_history) > 500 else history_lower
        
        if "take a break" in recent_history or "need a break" in recent_history or "rest" in recent_history:
            # Check if student just returned (recent "hi", "hello", "back")
            last_300_chars = conversation_history[-300:].lower()
            if any(word in last_300_chars for word in ["back", "returned"]):
                # Check timing - if break was very short
                if "minute" in last_300_chars or "quick" in last_300_chars:
                    return "[RETURNED EARLY FROM BREAK]"
                return "[STUDENT RETURNED AFTER BREAK]"
        
        # Check for continuous conversation (substantial history)
        if len(conversation_history) > 200:
            return "[CONTINUOUS CONVERSATION]"
        
        return "[START OF SESSION]"
    
    async def generate_explanation(
        self,
        confusion_analysis: Dict,
        subject: str,
        student_question: str,
        conversation_history: str = "",
        sentiment_analysis: Dict = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Generate a pedagogical explanation with Nigerian-focused, action-oriented teaching
        """
        if not aclient:
            return "I'm having trouble connecting right now. Can you try again in a moment?"
        
        # Get stored facts (including session-scoped if session_id provided)
        facts = self.memory.get_all_facts(session_id=session_id)
        facts_context = ""
        if facts:
            facts_list = [f"- {f['category'].title()}: {f['fact']}" for f in facts]
            facts_context = "KNOWN USER FACTS (Refer to these naturally):\n" + "\n".join(facts_list)
        
        # Get effective teaching strategies from memory
        effective_strategies = self.memory.get_effective_strategies()
        strategy_text = ", ".join([s.get("strategy", "") for s in effective_strategies[:3]]) if effective_strategies else "None yet"
        
        confusion_level = confusion_analysis.get("confusion_level", "medium")
        prerequisites = confusion_analysis.get("prerequisites_missing", [])
        message_type = confusion_analysis.get("message_type", "learning")
        
        # RAG INTEGRATION: Get Syllabus Context
        try:
            syllabus_context = get_syllabus_context(self.student, self.session, subject)
        except:
            syllabus_context = "No syllabus context available"
        
        # Check for break/return context
        context_flags = self._analyze_conversation_context(conversation_history)
        
        # Get support type for silent adaptation (NEVER mention to student)
        support_type = self.student.support_type if hasattr(self.student, 'support_type') and self.student.support_type else None
            
        # Sentiment Context
        sentiment_context = ""
        if sentiment_analysis:
            emotion = sentiment_analysis.get("emotion", "neutral")
            if sentiment_analysis.get("is_distress"):
                sentiment_context = f"DETECTED DISTRESS: Student is feeling {emotion}. Be extremely supportive, patient, and validating."
            elif emotion in ["frustrated", "confused", "anxious"]:
                sentiment_context = f"DETECTED NEGATIVE EMOTION: Student seems {emotion}. Start with validation (e.g., 'I know this is tricky...'). Slow down."
            elif emotion in ["happy", "excited"]:
                sentiment_context = f"DETECTED POSITIVE EMOTION: Student seems {emotion}. Match their high energy!"

        # === NATURAL, CONVERSATIONAL TEACHING SYSTEM PROMPT ===
        prompt = f"""You are a friendly AI tutor chatting with {self.student.full_name}, a {self.student.age}-year-old Nigerian student who loves {self.student.hobby}. Talk like you're their helpful friend, not a formal teacher.

STUDENT PROFILE:
- Name: {self.student.full_name}
- Age: {self.student.age}
- Class: {self.student.student_class}
- Hobby: {self.student.hobby}
- Personality: {self.student.personality}

{facts_context}

{sentiment_context}

HOW TO CHAT NATURALLY:

CRITICAL: NEVER use the same response twice. Be DYNAMIC and VIBRANT. 
If you said "What's good" last time, say "Hey!" or "How far?" this time.
VARIETY IS MANDATORY.

1. **GREETINGS & OPENERS** - STRICT RULE:
   - **Start of conversation (History < 2 messages):** Be friendly! "Hey!", "What's up?", "How far?"
   - **Deep in conversation (History > 2 messages):** 🛑 NO GREETINGS!
     * UNLESS the student explicitly says "hi" / "hello" again.
     * OTHERWISE: Go strictly to the point.
     * Example (Mid-convo): Student: "explain fractions" → You: "Sure! Fractions are..." (NOT "Hello again!")
   - **CRITICAL BAN LIST (NEVER USE):**
     * "No worries"
     * "So, you wanna..."
     * "Let's dive in"
     * "wanna", "gonna", "gotta"
     * repetitve "Right?" at end of sentences.

   **GREETING LOGIC (Start of Convo):**
   - **Structure:** [Friendly Opener] + [Schedule/Learning Goal] + [Hobby Flavor]
   - **PRIORITY:** LEARNING FIRST.
   - *Example:* "How far, Titi! Your schedule says it's time for Maths. Ready to count beats like a star singer?"
   - *Example:* "Welcome back! Let's tackle Science. Imagine mixing chemicals like mixing music tracks!"
   - **DO NOT** ask vague questions like "How is singing?". Go straight to the lesson with a singing flavor.

2. **RESPONSE STRUCTURE** (CONDITIONALLY APPLIED):

   **SCENARIO A: TEACHING/EXPLAINING A TOPIC (Strict 5-Part Structure)**
   *Apply this ONLY when explaining a concept, answering a study question, or teaching.*
   
   **Block 1: Acknowledgement & Interest**
   - Confirm the topic. "Ah, fractions! That's a crucial topic."

   **Block 2: Hobby/Scenario Connection** (Use: {self.student.hobby})
   - Connect concept to their hobby/life. "Think of it like sharing a plate of suya..."

   **Block 3: Brief Introduction**
   - Simple definition. "A fraction is just a part of a whole."

   **Block 4: Key Points (MUST BE BOLD)**
   - **Point 1:** Explanation here.
   - **Point 2:** Explanation here.
   - Keep bullet points short and punchy.

   **Block 5: The Hook**
   - Fun closing question. "Did you know...?"

   **SCENARIO B: CASUAL CHAT (Normal Format)**
   *Apply this for greetings, gratitude, small talk, or simple questions.*
   - Be natural, friendly, and relaxed.
   - NO strict structure needed.
   - Just talk like a friend. "Anytime! Ready for the next topic?"

3. **ADAPTIVE COMPLEXITY** (Crucial!):
   - **Age {self.student.age}**: 
     * Under 12: Very short sentences, simple words, fun tone.
     * 12-15: Conversational, medium complexity.
     * 16+: More mature but still casual.
   - **Personality {self.student.personality}**: Match their vibe.
   - **Support Needs**: {support_type if support_type else "None"} - Simplify further if needed.

   **LANGUAGE RULES (STRICT):**
   - Use proper, clear English.
   - **Direct & Action-Oriented.** Don't dilly-dally.

4. **CONTEXT AWARENESS (CRITICAL):**
   - ALWAYS combine **Current Message** + **Conversation History**.
   - If they say "explain it better", look at what you just explained!
   - **Short Phrases:** If they say just "math" or "yes", infer meaning from context.
     * "Math" (Start of chat) → "Ready to learn math! What topic?"
     * "Yes" (After "Ready?") → "Great! Let's start."

5. **GRATITUDE** - When they say thank you:
   - "Anytime! Want to learn more?"
   - "No wahala! Ready for the next topic?"
   - "Glad I could help!"

5. **IMAGES** - Only when truly needed:
   - DON'T show images for simple concepts
   - ONLY use [SHOW_IMAGE: description] for complex diagrams/biology/geometry 
   - Simple explanations = NO IMAGE

6. **NIGERIAN VIBES** - Use naturally:
   - Money: ₦ (Naira)
   - Food: jollof rice, puff-puff, suya, plantain
   - Places: Lagos, Abuja, the market
   - Transport: danfo, keke NAPEP
   - Expressions: "Well done!", "You fit do am!", "E go be!"

7. **HANDLE TYPOS** - Be understanding:
   - If you understand what they mean → just answer (e.g., "lerlearn" → learn)

8. **QUIZ REQUESTS**:
   If they ask for a quiz/test, respond:
   "Starting quiz functionality... [START_QUIZ]"

CONVERSATION HISTORY:
{conversation_history}

CURRENT MESSAGE: {student_question}
SUBJECT: {subject}

Remember: Follow the **RESPONSE STRUCTURE** for teaching. Be DYNAMIC with greetings. Keep sentences SHORT and CLEAR for a {self.student.age}-year-old.
"""

        
        try:
            response = await aclient.chat.completions.create(
                model=os.getenv("GROQ_MODEL"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,  # Higher for more natural, varied responses
                max_tokens=1000
            )
            
            explanation = response.choices[0].message.content.strip()
            
            # Process images if any
            try:
                from .media_service import prepare_text_response
                explanation = prepare_text_response(explanation)
            except Exception as img_error:
                print(f"Image processing error: {img_error}")
            
            # Log the tutoring action
            self.log_action(
                "explanation_provided",
                {
                    "topic": subject,
                    "confusion_level": confusion_level,
                    "explanation_length": len(explanation),
                    "context_flag": context_flags
                },
                f"Provided explanation for {subject} (confusion: {confusion_level})"
            )
            
            return explanation
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return f"I'd love to explain {subject}, but I'm having technical difficulties right now. Can you try asking again?"
    
    def _get_silent_support_adaptations(self, support_type) -> str:
        """Generate silent adaptation instructions based on support type"""
        if not support_type or support_type == "None":
            return """STANDARD TEACHING MODE:
- Use Socratic questioning to guide discovery
- Employ rich analogies and diverse examples
- Challenge thinking with "What if...?" scenarios
- Vary sentence structure for engagement"""
        
        from .models import SupportType
        
        if support_type == SupportType.AUTISM:
            return """AUTISM SUPPORT (ADAPT SILENTLY):
- Be completely literal—no idioms, sarcasm, or abstract metaphors
- If using hobby analogies, keep them concrete
- Number all steps: 1., 2., 3.
- Break complex ideas into explicit sequences
- Be consistent and predictable in format
- State one main idea per paragraph
- Use "First..., Then..., Finally..." patterns
- Avoid ambiguity—be precise"""
        
        elif support_type == SupportType.DYSLEXIA:
            return """DYSLEXIA SUPPORT (ADAPT SILENTLY):
- **Bold all key terms** for visual tracking
- Use bullet points (•) extensively
- Keep sentences under 15 words
- Maximum 2 sentences per paragraph
- Break information into small visual chunks
- Use line breaks generously
- Avoid text walls—think "bite-sized" information
- Simple, direct sentences
- One idea per sentence"""
        
        elif support_type == SupportType.DOWN_SYNDROME:
            return """DOWN SYNDROME SUPPORT (ADAPT SILENTLY):
- Use basic, everyday vocabulary (avoid technical jargon unless explaining it)
- One idea per sentence. One sentence per line.
- Repeat key concepts gently with slight variation
- Be highly positive and encouraging
- Use phrases like "You're doing great!", "I'm proud of you!"
- Celebrate small wins
- Slow down—don't rush through concepts
- Check understanding with simple questions
- Build on what they already know"""
        
        return ""
    
    def should_provide_example(self, topic: str) -> bool:
        """Decide if an example would help"""
        # Check if student learns better with examples
        try:
            preferred = json.loads(self.memory.memory.preferred_examples or "[]")
            return len(preferred) > 0 or self.memory.memory.learning_style == "visual"
        except:
            return True  # Default to providing examples
    
    def recommend_next_topic(self, current_topic: str, mastery_level: float) -> str:
        """Recommend what to learn next"""
        if mastery_level >= 0.8:
            return f"Advanced applications of {current_topic}"
        elif mastery_level >= 0.6:
            return f"Practice problems on {current_topic}"
        else:
            return f"Review fundamentals of {current_topic}"



# ============================================================================
# ASSESSMENT AGENT
# ============================================================================

class AssessmentAgent(BaseAgent):
    """
    Specialized in testing knowledge and evaluating understanding
    Expertise: Question generation, difficulty calibration, mastery evaluation
    """
    
    def __init__(self, student: Student, session: Session):
        super().__init__(student, session)
        self.agent_type = "assessment"
    
    def should_assess(self, topic: str, context: Dict) -> Dict:
        """
        Decide if assessment is needed
        """
        # Get recent test results for topic
        recent_tests = self.session.exec(
            select(TestResult).where(
                (TestResult.student_id == self.student.id) &
                (TestResult.subject == topic) &
                (TestResult.timestamp >= datetime.now(timezone.utc) - timedelta(days=7))
            )
        ).all()
        
        # Decision factors
        conversations_count = context.get("conversations_since_last_quiz", 0)
        time_since_last_test = context.get("hours_since_last_test", 999)
        
        should_assess = False
        reasons = []
        
        # Rule 1: After tutoring session
        if context.get("just_finished_tutoring", False):
            should_assess = True
            reasons.append("Check understanding after tutoring")
        
        # Rule 2: High activity
        if conversations_count >= 5:
            should_assess = True
            reasons.append(f"High activity: {conversations_count} conversations")
        
        # Rule 3: Time-based
        if time_since_last_test > 24 and conversations_count > 0:
            should_assess = True
            reasons.append("Regular assessment due")
        
        # Rule 4: Low recent performance
        if recent_tests:
            accuracy = sum(1 for t in recent_tests if t.is_correct) / len(recent_tests)
            if accuracy < 0.6:
                should_assess = True
                reasons.append(f"Low performance: {accuracy*100:.0f}%")

        # Rule 5: User signal (Added as per Agentic Features)
        last_msg = context.get("last_user_message", "").lower()
        if any(phrase in last_msg for phrase in ["i understand", "i get it", "got it", "makes sense", "ready for quiz"]):
            should_assess = True
            reasons.append("Student signaled comprehension/readiness")
        
        return {
            "should_assess": should_assess,
            "reasons": reasons,
            "recommended_difficulty": self._determine_difficulty(recent_tests)
        }
    
    def _determine_difficulty(self, recent_tests: List) -> str:
        """Determine appropriate difficulty level"""
        if not recent_tests:
            return "medium"
        
        accuracy = sum(1 for t in recent_tests if t.is_correct) / len(recent_tests)
        
        if accuracy < 0.4:
            return "easy"
        elif accuracy < 0.7:
            return "medium"
        else:
            return "hard"
    
    def generate_targeted_questions(
        self,
        topic: str,
        difficulty: str,
        num_questions: int = 3
    ) -> List[Dict]:
        """
        Generate questions targeted at specific topic and difficulty
        """
        from .autonomous_quiz_agent import QuizGenerationAgent
        
        quiz_agent = QuizGenerationAgent(self.student, self.session)
        quiz = quiz_agent.generate_adaptive_quiz(topic, difficulty=difficulty)
        
        questions = quiz.get("questions", [])[:num_questions]
        
        # Log assessment action
        self.log_action(
            "questions_generated",
            {
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": len(questions)
            },
            f"Generated {len(questions)} {difficulty} questions on {topic}"
        )
        
        return questions
    
    def evaluate_mastery(self, topic: str, recent_results: List[TestResult]) -> Dict:
        """
        Evaluate student's mastery level of a topic
        """
        if not recent_results:
            return {"mastery_level": 0.0, "status": "not_assessed"}
        
        accuracy = sum(1 for r in recent_results if r.is_correct) / len(recent_results)
        
        if accuracy >= 0.9:
            status = "mastered"
            self.memory.mark_topic_mastered(topic)
        elif accuracy >= 0.7:
            status = "proficient"
        elif accuracy >= 0.5:
            status = "developing"
        else:
            status = "struggling"
            self.memory.add_topic_to_revisit(topic, f"Low mastery: {accuracy*100:.0f}%")
        
        return {
            "mastery_level": accuracy,
            "status": status,
            "tests_taken": len(recent_results),
            "recommendation": self._get_mastery_recommendation(status)
        }
    
    def _get_mastery_recommendation(self, status: str) -> str:
        """Get recommendation based on mastery status"""
        recommendations = {
            "mastered": "Ready for advanced topics",
            "proficient": "Continue practicing, try harder problems",
            "developing": "More practice needed, review key concepts",
            "struggling": "Review fundamentals, get additional help"
        }
        return recommendations.get(status, "Keep practicing")


# ============================================================================
# SCHEDULING AGENT
# ============================================================================

class SchedulingAgent(BaseAgent):
    """
    Specialized in time management and study planning
    Expertise: Schedule optimization, workload balancing, time allocation
    """
    
    def __init__(self, student: Student, session: Session):
        super().__init__(student, session)
        self.agent_type = "scheduling"
    
    def optimize_study_time(
        self,
        subjects: List[str],
        available_hours_per_day: int = 2,
        priority_subjects: List[str] = None
    ) -> Dict:
        """
        Optimize study time allocation across subjects
        """
        # Get performance data for each subject
        subject_performance = {}
        for subject in subjects:
            results = self.session.exec(
                select(TestResult).where(
                    (TestResult.student_id == self.student.id) &
                    (TestResult.subject == subject) &
                    (TestResult.timestamp >= datetime.now(timezone.utc) - timedelta(days=30))
                )
            ).all()
            
            if results:
                accuracy = sum(1 for r in results if r.is_correct) / len(results)
                subject_performance[subject] = accuracy
            else:
                subject_performance[subject] = 0.5  # Default
        
        # Allocate time based on performance (more time for weak subjects)
        total_minutes = available_hours_per_day * 60
        allocations = {}
        
        # Priority subjects get guaranteed time
        if priority_subjects:
            priority_time = total_minutes * 0.4  # 40% for priorities
            per_priority = priority_time / len(priority_subjects)
            for subj in priority_subjects:
                allocations[subj] = int(per_priority)
            remaining_time = total_minutes - priority_time
        else:
            remaining_time = total_minutes
        
        # Allocate remaining time inversely to performance
        other_subjects = [s for s in subjects if s not in (priority_subjects or [])]
        if other_subjects:
            # Inverse weighting (lower performance = more time)
            weights = {s: (1 - subject_performance.get(s, 0.5)) for s in other_subjects}
            total_weight = sum(weights.values())
            
            for subj in other_subjects:
                if total_weight > 0:
                    allocations[subj] = int((weights[subj] / total_weight) * remaining_time)
                else:
                    allocations[subj] = int(remaining_time / len(other_subjects))
        
        # Log scheduling action
        self.log_action(
            "time_optimized",
            {
                "total_minutes": total_minutes,
                "allocations": allocations
            },
            f"Optimized {total_minutes} minutes across {len(subjects)} subjects"
        )
        
        return {
            "daily_schedule": allocations,
            "total_minutes": total_minutes,
            "optimization_strategy": "inverse_performance_weighting"
        }
    
    def prevent_burnout(self, recent_activity: Dict) -> Dict:
        """
        Check for burnout risk and suggest breaks (UNICEF Standards)
        """
        sessions_today = recent_activity.get("sessions_today", 0)
        minutes_today = recent_activity.get("minutes_today", 0)
        current_session_minutes = recent_activity.get("current_session_minutes", 0)
        consecutive_days = recent_activity.get("consecutive_days", 0)
        
        burnout_risk = "low"
        recommendations = []
        is_break_needed = False
        
        # Age-based Max Session Duration (UNICEF/Child Dev Guidelines)
        # < 12 years: ~45 mins max continuous
        # 12-15 years: ~60 mins max continuous
        # > 15 years: ~90 mins max continuous
        max_session = 90
        if self.student.age < 12: max_session = 45
        elif self.student.age < 15: max_session = 60
        
        # Rule 1: Continuous Session Limit (Relaxed)
        if current_session_minutes > (max_session + 30): # Add buffer
            burnout_risk = "high"
            is_break_needed = True
            recommendations.append(f" You've been focusing for {current_session_minutes} mins! Time for a brain break.")
            recommendations.append("Go stretch or drink water!")
            current_session_minutes = 0
            
        # Rule 2: Daily Total Limit (Relaxed)
        if minutes_today > (max_session * 4): # Increased limit
            burnout_risk = "medium"
            recommendations.append("You've done a lot today! Maybe switch to a fun review?")

        # Rule 3: Fatigue Signs (Short/Low-effort messages)
        # Only trigger if explicitly detected AND session is somewhat long
        if recent_activity.get("fatigue_signs_detected", False) and current_session_minutes > 45:
            burnout_risk = "medium" # Downgraded from high
            # is_break_needed = True # Do not force break, just suggest
            recommendations.append("I sense you might be tired. Let's pause here if you want.")

        # Rule 4: Consecutive Days
        if consecutive_days > 6:
            burnout_risk = "medium"
            recommendations.append("You've been consistent all week! Take a rest day properly tomorrow.")
        
        return {
            "burnout_risk": burnout_risk,
            "is_break_needed": is_break_needed,
            "recommendations": recommendations,
            "metrics": {
                "sessions_today": sessions_today,
                "current_session_minutes": current_session_minutes
            }
        }
    
    def suggest_best_study_time(self) -> str:
        """
        Suggest optimal study time based on student's patterns
        """
        best_time = self.memory.memory.best_time_of_day
        
        if best_time:
            return best_time
        
        # Default recommendations by age
        if self.student.age < 12:
            return "afternoon"  # After school, before evening
        elif self.student.age < 15:
            return "evening"  # 5-7 PM
        
        return "evening"  # More flexible
    
    def suggest_topic_from_timetable(self) -> Optional[str]:
        """
        Suggest what topic to learn based on student's current timetable
        Returns a suggestion message or None if no timetable entry found
        """
        from .models import Timetable
        from sqlmodel import select
        from datetime import datetime
        
        # Get current day and time
        now = datetime.now()
        current_day = now.strftime("%A")  # Monday, Tuesday, etc.
        current_time = now.strftime("%H:%M")  # 14:30
        
        # Find timetable entry for current day and time
        timetable_entries = self.session.exec(
            select(Timetable).where(
                (Timetable.student_id == self.student.id) &
                (Timetable.day_of_week == current_day)
            )
        ).all()
        
        if not timetable_entries:
            return None
        
        # Find entry that matches current time
        for entry in timetable_entries:
            start_time = entry.start_time  # Format: "14:00"
            end_time = entry.end_time      # Format: "15:00"
            
            if start_time <= current_time <= end_time:
                # Found matching entry
                subject = entry.subject or "General"
                topic = entry.focus_topic or ""
                
                if topic:
                    return f"According to your schedule, you should be learning **{subject}** right now, specifically: **{topic}**. Want to start?"
                else:
                    return f"According to your schedule, you should be learning **{subject}** right now. What topic would you like to cover?"
        
        # No exact match, find next upcoming entry
        upcoming_entries = [e for e in timetable_entries if e.start_time > current_time]
        if upcoming_entries:
            next_entry = min(upcoming_entries, key=lambda e: e.start_time)
            subject = next_entry.subject or "General"
            return f"Your next scheduled topic is **{subject}** at {next_entry.start_time}. Want to get a head start?"
        
        return None

    def create_full_schedule(self) -> Dict:
        """
        Generate and persist a full weekly schedule using shared service logic.
        """
        from .schedule_service import create_and_save_schedule
        from typing import Dict
        
        print(f"[SCHEDULING AGENT] Generating full schedule for {self.student.full_name}...")
        
        # Call shared service logic which handles data gathering, generation, and persistence
        result = create_and_save_schedule(self.session, self.student)
        
        # Log the agent action
        self.log_action(
            "schedule_created",
            {
                "items_count": sum(len(day) for day in result.get("schedule", {}).values()),
                "strategy": "performance_adaptive"
            },
            "Generated full weekly schedule"
        )
        
        return result

    def should_proactively_schedule(self) -> bool:
        """
        Check if we should proactively create a schedule (e.g., if none exists)
        """
        from .models import Timetable
        from sqlmodel import select
        
        # Check if student has any timetable entries
        existing = self.session.exec(select(Timetable).where(
            Timetable.student_id == self.student.id
        )).first()
        
        # If no schedule exists, we should create one
        return existing is None


# ============================================================================
# ============================================================================
# MOTIVATION AGENT
# ============================================================================

class MotivationAgent(BaseAgent):
    """
    Specialized in engagement and encouragement
    Expertise: Motivation psychology, reward timing, emotional support (EQ)
    Persona: 40-year veteran mentor, deeply caring, professional, non-repetitive
    """
    
    def __init__(self, student: Student, session: Session):
        super().__init__(student, session)
        self.agent_type = "motivation"
        self.intervention_count = 0  # Track interventions in current session
        self.last_intervention_time = None
        self.tiredness_mentions = 0  # Track how many times "tired" mentioned
    
    async def analyze_sentiment(self, text: str) -> Dict:
        """
        Real-time Sentiment Analysis to detect ONLY SEVERE emotional distress
        """
        if not text or len(text) < 3:
             return {"emotion": "neutral", "confidence": 0.0, "is_distress": False, "should_intervene": False}
             
        prompt = f"""Analyze the emotional sentiment of this student message.
        Student: "{text}"
        
        Classify as one of: [Extremely Frustrated, Severely Distressed, Giving Up, Excited, Neutral, Happy, Tired, Mildly Frustrated]
        
        CRITICAL: Mark "should_intervene" as TRUE **ONLY** if:
        - Student expresses extreme frustration ("I hate this", "I give up", "I can't do this anymore")
        - Student shows severe distress or emotional breakdown
        - Student is repeatedly tired (not just once)
        - Student shows signs of wanting to quit entirely
        
        DO NOT intervene for:
        - Normal confusion ("I don't understand")
        - Single mention of tiredness
        - Minor frustration ("this is hard")
        - Normal learning difficulty
        
        Return JSON:
        {{
            "emotion": "...",
            "confidence": 0.0-1.0,
            "is_distress": true/false (true ONLY for severe cases),
            "should_intervene": true/false (be VERY conservative - default to false),
            "severity": "low/medium/high",
            "support_response": "A very short, warm word of encouragement (5-10 words max). Only if should_intervene is true."
        }}"""
        
        try:
            if aclient:
                response = await aclient.chat.completions.create(
                    model=os.getenv("GROQ_MODEL"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3  # Keep low for consistent emotional assessment
                )
                content = response.choices[0].message.content.strip()
                if "```" in content: content = content.split("```")[1].replace("json", "")
                result = json.loads(content.strip())
                
                # Additional gating logic
                if result.get("should_intervene"):
                    # Check if we've intervened too recently (within last 5 minutes)
                    if self.last_intervention_time:
                        time_since_last = (datetime.now(timezone.utc) - self.last_intervention_time).seconds
                        if time_since_last < 300:  # 5 minutes
                            result["should_intervene"] = False
                            return result
                    
                    # Check if we've intervened too many times (max 3 per session)
                    if self.intervention_count >= 3:
                        result["should_intervene"] = False
                        return result
                
                return result
                
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            
        return {"emotion": "neutral", "confidence": 0.0, "is_distress": False, "should_intervene": False}
    
    async def should_intervene_for_tiredness(self, text: str) -> bool:
        """
        Special check for tiredness - only intervene if mentioned multiple times
        """
        tiredness_keywords = ["tired", "exhausted", "can't focus", "need break", "worn out"]
        
        # Check if any tiredness keyword in message
        if any(keyword in text.lower() for keyword in tiredness_keywords):
            self.tiredness_mentions += 1
            
            # Only intervene after 2nd or 3rd mention
            if self.tiredness_mentions >= 2:
                return True
        
        return False


    
    async def check_study_duration_warning(self, minutes_studied: int) -> Optional[str]:
        """
        Only warn about breaks after significant study time
        """
        # Don't warn too early or too frequently
        if minutes_studied < 60:
            return None  # Don't warn before 1 hour
        
        # Only warn at specific milestones
        if minutes_studied in [60, 90, 120]:  # 1hr, 1.5hr, 2hr marks only
            return f"You've been studying for {minutes_studied} minutes. Consider taking a short break! 💪"
        
        return None
    
    async def should_send_break_reminder(self, last_break_time: datetime, current_time: datetime) -> bool:
        """
        Decide if break reminder is needed
        """
        if not last_break_time:
            return False
        
        time_since_break = (current_time - last_break_time).total_seconds() / 60  # in minutes
        
        # Only remind after 60+ minutes of continuous study
        return time_since_break >= 60
    
    async def generate_intervention(self, sentiment: Dict, context: str = "") -> Optional[str]:
        """
        Generate intervention ONLY when truly needed
        Returns None if no intervention should happen
        """
        # Don't intervene if flag says no
        if not sentiment.get("should_intervene", False):
            return None
        
        # Don't intervene if we've done so too much
        if self.intervention_count >= 3:
            return None
        
        emotion = sentiment.get("emotion", "neutral")
        severity = sentiment.get("severity", "low")
        
        # Only proceed for high severity
        if severity != "high":
            return None
        
        prompt = f"""You are an Emotional Support Agent. Generate a BRIEF intervention for this situation:

Student: {self.student.full_name} ({self.student.age} years old, {self.student.personality.value})
Emotion Detected: {emotion}
Severity: {severity}
Context: {context}

INTERVENTION RULES:
1. Keep it VERY short (1-2 sentences max, 15-20 words)
2. Be warm and genuine, not fake-cheerful
3. Match their personality ({self.student.full_name} ({self.student.age} years old, {self.student.personality.value})
4. DO NOT interrupt the learning flow unnecessarily
5. Only suggest breaks if they've mentioned tiredness multiple times
6. Use Nigerian expressions naturally if appropriate ("E go be!", "You fit do am!")

Generate ONLY the intervention message. No preamble."""
        
        try:
            if aclient:
                response = await aclient.chat.completions.create(
                    model=os.getenv("GROQ_MODEL"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.6,  # Slightly lower for more measured responses
                    max_tokens=80
                )
                
                message = response.choices[0].message.content.strip()
                
                # Update intervention tracking
                self.intervention_count += 1
                self.last_intervention_time = datetime.now(timezone.utc)
                
                # Log the intervention
                self.log_action(
                    "emotional_intervention",
                    {
                        "emotion": emotion,
                        "severity": severity,
                        "intervention_count": self.intervention_count
                    },
                    f"Intervened for {emotion}"
                )
                
                return message
        except Exception as e:
            print(f"Error generating intervention: {e}")
            
        return None
    
    def generate_targeted_questions(
        self,
        subject: str,
        difficulty: str = "medium",
        num_questions: int = 5
    ) -> List[Dict]:
        """
        Generate targeted assessment questions
        """
        if not aclient:
            return []
        
        # Get student context
        hobby = self.student.hobby if hasattr(self.student, 'hobby') else "general interests"
        student_class = self.student.student_class if hasattr(self.student, 'student_class') else "General"
        
        prompt = f"""Generate {num_questions} multiple-choice questions for a Nigerian student.

STUDENT CONTEXT:
- Class: {student_class}
- Subject: {subject}
- Difficulty: {difficulty}
- Hobby: {hobby}

CRITICAL RULES:
1. NO TRUE/FALSE QUESTIONS - Only multiple choice with 4 options (A, B, C, D)
2. Use Nigerian context in questions where relevant:
   - Nigerian currency (Naira - ₦)
   - Nigerian locations (Lagos, Abuja, Kano, Port Harcourt)
   - Nigerian foods (jollof rice, puff-puff, suya, plantain)
   - Nigerian daily life (danfo buses, markets, schools)
3. Connect to student's hobby ({hobby}) when possible
4. Make questions practical and relatable
5. Ensure ONE correct answer per question

DIFFICULTY LEVELS:
- easy: Basic recall, simple concepts
- medium: Application, understanding
- hard: Analysis, complex problem-solving

Return ONLY valid JSON array format:
[
  {{
    "question": "Question text here",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "correct_answer": "A",
    "explanation": "Why this is correct"
  }}
]

Generate {num_questions} questions now:"""
        
        try:
            response = aclient.chat.completions.create(
                model=os.getenv("GROQ_MODEL"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON
            import json
            import re
            
            # Extract JSON array
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
                
                # Validate and filter out any True/False questions
                valid_questions = []
                for q in questions:
                    if isinstance(q.get('options'), list) and len(q['options']) >= 4:
                        # Ensure it's not a True/False question
                        options_text = ' '.join(q['options']).lower()
                        if not ('true' in options_text and 'false' in options_text and len(q['options']) == 2):
                            valid_questions.append(q)
                
                # Log the assessment
                self.log_action(
                    "questions_generated",
                    {
                        "subject": subject,
                        "difficulty": difficulty,
                        "count": len(valid_questions)
                    },
                    f"Generated {len(valid_questions)} {difficulty} questions for {subject}"
                )
                
                return valid_questions[:num_questions]
            
            return []
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []
    
    def reset_session_counters(self):
        """Call this at the start of each new session"""
        self.intervention_count = 0
        self.last_intervention_time = None
        self.tiredness_mentions = 0
    
    async def assess_engagement_level(self) -> Dict:
        """
        Assess current engagement level
        """
        # Get recent activity
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        recent_chats = self.session.exec(
            select(ChatHistory).where(
                (ChatHistory.student_id == self.student.id) &
                (ChatHistory.timestamp >= week_ago)
            )
        ).all()
        
        # Calculate engagement metrics
        total_messages = len(recent_chats)
        active_days = len(set(chat.timestamp.date() for chat in recent_chats))
        avg_messages_per_day = total_messages / 7 if total_messages > 0 else 0
        
        # Determine engagement level
        if active_days >= 5 and avg_messages_per_day >= 3:
            level = "high"
        elif active_days >= 3 and avg_messages_per_day >= 1:
            level = "medium"
        else:
            level = "low"
        
        return {
            "engagement_level": level,
            "active_days_last_week": active_days,
            "total_messages": total_messages,
            "avg_messages_per_day": round(avg_messages_per_day, 1)
        }
    
    async def generate_encouragement(self, context: Dict) -> str:
        """
        Generate personalized encouragement message
        """
        achievement = context.get("achievement")
        struggle = context.get("struggle")
        milestone = context.get("milestone")
        
        if not aclient:
            if achievement:
                return f"Great job on {achievement}! Keep it up!"
            elif struggle:
                return f"Don't worry about {struggle}. You're making progress!"
            else:
                return "You're doing great! Keep learning!"
        
        prompt = f"""Generate a short, encouraging message for {self.student.full_name}, a {self.student.age}-year-old {self.student.personality.value} student.

CONTEXT:
- Achievement: {achievement or 'None'}
- Struggle: {struggle or 'None'}
- Milestone: {milestone or 'None'}
- Personality: {self.student.personality.value}
- Interests: {self.student.hobby}

GUIDELINES:
1. Be genuine and warm
2. Match their personality (gentle for Introvert, energetic for Extrovert)
3. Reference their interests if relevant
4. Keep it VERY short (1 sentence maximum, 10-15 words max)
5. Use Nigerian context if appropriate (e.g. "Well done!", "You're doing great!")
6. Be natural, not dramatic or repetitive
7. If context is casual, respond casually

Generate ONLY the encouragement message. No additional text."""
        
        try:
            response = await aclient.chat.completions.create(
                model=os.getenv("GROQ_MODEL"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # Slightly higher for more natural variety
                max_tokens=50
            )
            
            message = response.choices[0].message.content.strip()
            
            # Log motivation action
            self.log_action(
                "encouragement_sent",
                {"context": context, "message_length": len(message)},
                f"Sent encouragement for {achievement or struggle or 'general motivation'}"
            )
            
            return message
        except Exception as e:
            print(f"Error generating encouragement: {e}")
            return "You're doing amazing! Keep up the great work!"
    
    async def celebrate_milestone(self, milestone: str, data: Dict = None) -> str:
        """
        Celebrate a student achievement
        """
        celebration = await self.generate_encouragement({
            "milestone": milestone,
            "achievement": milestone
        })
        
        # Add to memory
        self.memory.add_milestone(milestone, data or {})
        
        return celebration
    
    async def check_inactivity(self) -> Optional[str]:
        """
        Check for 3+ days of inactivity and generate re-engagement message
        """
        # Get last activity
        last_chat = self.session.exec(
            select(ChatHistory)
            .where(ChatHistory.student_id == self.student.id)
            .order_by(ChatHistory.timestamp.desc())
            .limit(1)
        ).first()
        
        if not last_chat:
            return None # New student or no history
            
        last_active = last_chat.timestamp
        # Ensure timezone aware comparison
        if last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=timezone.utc)
            
        days_inactive = (datetime.now(timezone.utc) - last_active).days
        
        if days_inactive >= 3:
            prompt = f"Write a SHORT 'We Miss You' message (10-15 words) for {self.student.full_name} who hasn't studied in {days_inactive} days. Be warm, not nagging. Mention their hobby ({self.student.hobby}) naturally."
            try:
                if aclient:
                    response = await aclient.chat.completions.create(
                        model=os.getenv("GROQ_MODEL"),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=50
                    )
                    return response.choices[0].message.content.strip()
                else:
                    return f"Hey {self.student.full_name}! We missed you. Ready to learn today?"
            except:
                return f"Hey {self.student.full_name}! Long time no see. Ready to learn something new?"
                
        return None
    
    def should_send_encouragement(self, engagement: Dict) -> bool:
        """
        Decide if encouragement is needed
        """
        level = engagement.get("engagement_level")
        
        # Send encouragement if engagement is low
        if level == "low":
            return True
        
        # Randomly send encouragement to high-engagement students (positive reinforcement)
        if level == "high":
            import random
            return random.random() < 0.2  # Reduced from 30% to 20%
        
        return False

# ============================================================================
# PARENT CONNECT AGENT (WhatsApp)
# ============================================================================

class ParentConnectAgent(BaseAgent):
    """
    Specialized in communicating with parents via WhatsApp
    Expertise: Summarization, alert thresholds, parent updates
    """
    
    def __init__(self, student: Student, session: Session):
        super().__init__(student, session)
        self.agent_type = "parent_connect"
        from .twilio_whatsapp_service import TwilioWhatsAppService
        self.whatsapp_service = TwilioWhatsAppService()
    
    def notify_daily_summary(self, activity_report: Dict) -> Dict:
        """
        Send a daily summary to the parent if significant activity occurred
        """
        if not self.student.parent_whatsapp:
            return {"sent": False, "reason": "No parent WhatsApp number"}
            
        # Check if enough activity to warrant a message
        if activity_report.get("total_actions", 0) < 3:
            return {"sent": False, "reason": "Low activity, skipping daily summary"}
            
        # Generate summary message
        message = (
            f"📅 *Daily Update for {self.student.full_name}*\n\n"
            f"✅ Completed: {activity_report.get('completed_tasks', 0)} tasks\n"
            f"📚 Studied: {activity_report.get('subjects_studied', 'General')}\n"
            f"🧠 Quiz Score: {activity_report.get('average_quiz_score', 'N/A')}\n\n"
            f"Keep encouraging them! 🌟"
        )
        
        try:
            self.whatsapp_service.send_whatsapp_message(self.student.parent_whatsapp, message)
            self.log_action("daily_summary_sent", activity_report, "Sent daily summary to parent")
            return {"sent": True, "message": message}
        except Exception as e:
            print(f"Error sending WhatsApp: {e}")
            return {"sent": False, "reason": str(e)}

    async def notify_achievement(self, achievement_Title: str, achievement_desc: str) -> Dict:
        """
        Notify parent of a specific achievement with a personalized message
        """
        if not self.student.parent_whatsapp:
            return {"sent": False, "reason": "No parent WhatsApp number"}
            
        # Generate personalized celebration message
        prompt = f"""Write a short, celebratory WhatsApp message to the parent of {self.student.full_name}.
        
        CONTEXT:
        - Achievement: {achievement_Title}
        - Description: {achievement_desc}
        - Student: {self.student.full_name} ({self.student.age} years old)
        
        GUIDELINES:
        1. Start with "🏆 *EduLife PRO Update:*"
        2. Act as the School PRO (Public Relations Officer).
        3. Be enthusiastic but professional.
        4. Mention the student's Registration Status (Active) and Progress.
        5. "We are proud of {self.student.full_name}'s performance!"
        6. Keep it concise.
        
        Generate ONLY the message."""
        
        message = f"🏆 *EduLife Achievement*\n\n{self.student.full_name} just unlocked: *{achievement_Title}*!\n\n{achievement_desc}\n\nGreat job! 🌟"
        
        try:
             if aclient:
                response = await aclient.chat.completions.create(
                    model=os.getenv("GROQ_MODEL"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                message = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI Generation failed, using template: {e}")
            
        try:
            self.whatsapp_service.send_whatsapp_message(self.student.parent_whatsapp, message)
            self.log_action("achievement_notify", {"achievement": achievement_Title}, "Sent achievement notification")
            return {"sent": True, "message": message}
        except Exception as e:
            print(f"Error sending WhatsApp: {e}")
            return {"sent": False, "reason": str(e)}
            return {"sent": False, "error": str(e)}

    def alert_low_engagement(self, consecutive_inactive_days: int) -> Dict:
        """
        Alert parent if student has been inactive
        """
        if not self.student.parent_whatsapp or consecutive_inactive_days < 3:
            return {"sent": False}
            
        message = (
            f"👋 Hello! We haven't seen {self.student.full_name} in {consecutive_inactive_days} days.\n"
            f"Encourage them to log in for a quick 10-minute session today! 🚀"
        )
        
        try:
            self.whatsapp_service.notify_parent_inactivity(self.student.parent_whatsapp, self.student.full_name, consecutive_inactive_days)
            self.log_action("inactivity_alert_sent", {"days": consecutive_inactive_days}, "Sent inactivity alert")
            return {"sent": True}
        except Exception as e:
            return {"sent": False, "error": str(e)}
            
    def celebrate_achievement(self, title: str, description: str) -> Dict:
        """
        Notify parent of a major achievement
        """
        if not self.student.parent_whatsapp:
            return {"sent": False}
        
        # Ensure description is provided or default it
        desc = description or f"{self.student.full_name} has earned the {title} badge!"
            
        try:
            self.whatsapp_service.notify_parent_achievement(
                self.student.parent_whatsapp, 
                self.student.full_name, 
                title, 
                desc
            )
            self.log_action("achievement_alert_sent", {"title": title}, "Sent achievement alert")
            return {"sent": True}
        except Exception as e:
            return {"sent": False, "error": str(e)}

    def check_new_badges(self) -> List[str]:
        """
        Check if student earned new badges and notify parent
        """
        # 1. Calculate current stats (replicating logic from student_router)
        from sqlmodel import func, select, distinct
        from .models import ChatHistory, TestResult, ConversationAnswer
        from datetime import datetime
        
        # Total sessions
        total_sessions = self.session.exec(
            select(func.count(distinct(ChatHistory.session_id)))
            .where(ChatHistory.student_id == self.student.id)
        ).one()
        
        # Test stats
        total_tests = self.session.exec(
            select(func.count(TestResult.id))
            .where(TestResult.student_id == self.student.id)
        ).one()
        
        correct_tests = self.session.exec(
            select(func.count(TestResult.id))
            .where(
                (TestResult.student_id == self.student.id) & 
                (TestResult.is_correct == True)
            )
        ).one()
        
        # Active days
        active_days_count = self.session.exec(
            select(func.count(distinct(func.date(ChatHistory.timestamp))))
            .where(ChatHistory.student_id == self.student.id)
        ).one()
        
        # 2. Determine earned badges
        earned_badges = []
        
        # Session badges
        if total_sessions >= 1: earned_badges.append({"name": "First Steps", "desc": "Completed first session"})
        if total_sessions >= 10: earned_badges.append({"name": "Curious Learner", "desc": "Completed 10 sessions"})
        if total_sessions >= 50: earned_badges.append({"name": "Chat Master", "desc": "Completed 50 sessions"})
        
        # Test badges
        if total_tests >= 5: earned_badges.append({"name": "Test Taker", "desc": "Completed 5 tests"})
        if correct_tests >= 10: earned_badges.append({"name": "Getting Good", "desc": "Answered 10 questions correctly"})
        if total_tests >= 5 and (correct_tests/total_tests) >= 0.9: earned_badges.append({"name": "Test Champion", "desc": "90%+ success rate"})
        
        # Streak badges
        if active_days_count >= 3: earned_badges.append({"name": "Streak Keeper", "desc": "Active for 3 days"})
        if active_days_count >= 7: earned_badges.append({"name": "Week Warrior", "desc": "Active for 7 days"})

        # 3. Check against memory (already notified)
        # We store notified badges in progress_milestones
        milestones = json.loads(self.memory.memory.progress_milestones or "[]")
        # Fix: 'type' is nested inside 'data' dictionary
        notified_badge_names = [
            m.get("milestone") for m in milestones 
            if m.get("data", {}).get("type") == "badge"
        ]
        
        new_badges = []
        for badge in earned_badges:
            if badge["name"] not in notified_badge_names:
                new_badges.append(badge)
                
        # 4. Notify and Update Memory
        for badge in new_badges:
            print(f"[PARENT AGENT] New Badge Earned: {badge['name']}")
            
            # Send WhatsApp
            self.celebrate_achievement(badge["name"], badge["desc"])
            
            # Add to memory so we don't notify again
            self.memory.add_milestone(badge["name"], {"type": "badge", "desc": badge["desc"]})
            
        return [b["name"] for b in new_badges]
