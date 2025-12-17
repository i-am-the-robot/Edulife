"""
AI Service
Handles Groq API integration for adaptive, inclusive AI chat
Refactored to Class-based structure for compatibility with Router
OPTIMIZED PROMPTS - December 2024
"""
import os
import json
import re
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import AsyncGroq # Use Async client
from duckduckgo_search import DDGS # For image search
import wikipedia # Fallback/Alternative image search

from .models import Student, SupportType, LearningProfile, School

load_dotenv()

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL")
        self.client = None
        
        if self.api_key and self.api_key != "your_groq_api_key_here":
            self.client = AsyncGroq(api_key=self.api_key)
        else:
            print("⚠️ GROQ_API_KEY not found. AI features will be disabled.")

    # ============================================================================
    # PUBLIC METHODS (Called by Router)
    # ============================================================================

    async def chat(self, student_id: str, message: str, session=None, session_id: str = None) -> str:
        """
        Main entry point for Chat/Voice Router.
        Retrieves student context and generates response.
        """
        if not self.client:
            return "I'm currently offline (API Key missing). Please tell my admin!"

        # We need the Student object for the prompt.
        from sqlmodel import select
        from .models import Student, ChatHistory
        
        try:
            student = session.get(Student, student_id)
            if not student:
                return "Error: Student profile not found."

            # Get Conversation History (Last 6 messages)
            # Filter by session_id if provided to keep context tight
            query = select(ChatHistory).where(ChatHistory.student_id == student_id)
            
            if session_id:
                query = query.where(ChatHistory.session_id == session_id)
                
            history_stmt = query.order_by(ChatHistory.timestamp.desc()).limit(12)
            recent_chats = session.exec(history_stmt).all()
            
            conversation_history = []
            for chat in reversed(recent_chats):
                u_msg = getattr(chat, 'student_message', getattr(chat, 'message', ''))
                a_msg = getattr(chat, 'ai_response', getattr(chat, 'response', ''))
                
                conversation_history.append({"role": "user", "content": u_msg})
                conversation_history.append({"role": "assistant", "content": a_msg})

            return await self.generate_ai_response(student, message, conversation_history, subject=None, session=session)

        except Exception as e:
            print(f"Chat error: {e}")
            return "Sorry, I'm having a little trouble thinking right now."

    def _adapt_content_for_support(self, text: str, support_type: SupportType) -> str:
        """
        Invisible Content Adaptation Layer (RAG Pre-processing)
        Adapts syllabus/knowledge text BEFORE it reaches the AI context window.
        """
        if not text: return ""
        
        adapted_text = text
        
        if support_type == SupportType.AUTISM:
            # 1. Structure: Force numbered lists for sequences
            # (Simple heuristic: replace bullets with numbers if likely a list)
            if "•" in adapted_text or "-" in adapted_text:
               adapted_text = adapted_text.replace("•", "1.").replace("- ", "1. ")
            # 2. Literalness: (AI Prompt handles the generation, but we can simplify input text if it's too flowery)
            pass 

        elif support_type == SupportType.DYSLEXIA:
            # 1. Visual Chunking: Break long paragraphs
            # (Heuristic: double newline after every period)
            adapted_text = adapted_text.replace(". ", ".\n\n")
            
        elif support_type == SupportType.DOWN_SYNDROME:
            # 1. Simplification Level (Concept Extraction could happen here)
            # For now, we rely on the Prompt to do the heavy lifting, 
            # but we can reduce volume of text fed to context to prevent overwhelm.
            # Truncation or summarization could go here.
            pass
            
        return adapted_text

    async def generate_ai_response(
        self,
        student: Student,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        subject: Optional[str] = None,
        session = None
    ) -> str:
        """
        Generate AI response using Groq with adaptive prompting
        """
        if not self.client:
            return "⚠️ AI service is not configured."

        system_prompt = self._get_adaptive_system_prompt(student)
        
        # RAG: Syllabus Integration
        if session and student.school_id:
            msg_subject = subject or "General"
            # Fetch School Syllabus
            school = session.get(School, student.school_id)
            if school and school.syllabus_text:
                # OPTIONAL: Filter syllabus by subject if stored structurally, 
                # but currently it's a blob, so we pass relevant chunks or full text.
                # Here we adapt it first:
                raw_syllabus = school.syllabus_text
                adapted_syllabus = self._adapt_content_for_support(raw_syllabus, student.support_type)
                
                system_prompt += f"\n\nSYLLABUS CONTEXT ({msg_subject}):\nUse this as ground truth:\n{adapted_syllabus}\n"

        # Subject Context
        if subject and subject != "General":
            system_prompt += f"\n\nCURRENT SUBJECT: {subject}\nFocus your responses on {subject}."

        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=600 # Slightly longer for good explanations
            )
            
            ai_response = response.choices[0].message.content
            
            # PROCESS IMAGE TAGS
            if "[SHOW_IMAGE:" in ai_response:
                try:
                    from .media_service import process_image_tags
                    ai_response = process_image_tags(ai_response)
                except Exception as img_err:
                    print(f"Image processing error: {img_err}")

            return convert_markdown_to_html(ai_response)
            
        except Exception as e:
            print(f"Groq generation error: {e}")
            return "I'm having trouble connecting to my brain! Let's try again."

    def _get_adaptive_system_prompt(self, student: Student) -> str:
        """
        OPTIMIZED: Generate adaptive persona prompt with improved clarity,
        reduced cognitive load, and better instruction hierarchy.
        """
        personality_val = student.personality.value if hasattr(student.personality, 'value') else str(student.personality)
        support_val = student.support_type.value if student.support_type and hasattr(student.support_type, 'value') else str(student.support_type or "General")

        # ==================================================================
        # CORE IDENTITY & MISSION (Simplified & Strengthened)
        # ==================================================================
        base_prompt = f"""You are EduBuddy, an expert Nigerian teacher specializing in inclusive education.

STUDENT: {student.full_name} | Age: {student.age} | Class: {student.student_class}
INTEREST: {student.hobby}
PERSONALITY: {personality_val}

YOUR MISSION:
Teach {student.full_name} effectively using their interest in {student.hobby} as a learning bridge.

# CORE TEACHING PRINCIPLES

## 1. COMMUNICATION STYLE
- Be helpful, warm, and engaging.
- You can use natural conversation starters, but don't waste too much time before getting to the point.
- Answer questions clearly.

## 2. CULTURAL RELEVANCE
- Use Nigerian context: Naira currency, Lagos landmarks, local markets, Nigerian foods
- Reference familiar African examples when possible
- Make learning relatable to {student.full_name}'s environment

## 3. HOBBY INTEGRATION
- Use {student.hobby} for analogies and metaphors in ~50% of explanations
- Keep it natural: "Think of this like [hobby concept]..."
- Don't force it—use when it genuinely helps understanding

## 4. POSITIVE REINFORCEMENT
- Encourage the student.
- Use constructive feedback: "Good thinking, but...", "You're close! Let me clarify...", "Let's look at this differently..."

## 5. PROACTIVE VISUAL AIDS (MANDATORY)
IF the student uses words like: "Show me", "Picture", "Image", "Graph", "Diagram", "See", "Look at"
→ You MUST generate an image tag immediately: [SHOW_IMAGE: specific descriptive query]
Example:
Student: "Show me a lion"
You: "Here is a majestic lion for you! [SHOW_IMAGE: male lion with mane in savannah]"

Don't ask permission. Just include it naturally.

"""

        # ==================================================================
        # ACCESSIBILITY ADAPTATIONS (Streamlined by Support Type)
        # ==================================================================
        if student.support_type == SupportType.AUTISM:
            base_prompt += """
# AUTISM SUPPORT ADAPTATIONS

LANGUAGE:
- Be completely literal—no idioms, sarcasm, or abstract metaphors
- If using hobby analogies, keep them concrete: "A goalkeeper blocks the ball. A cell membrane blocks molecules."

STRUCTURE:
- Number all steps: 1., 2., 3.
- Break complex ideas into explicit sequences
- Be consistent and predictable in your format

CLARITY:
- State one main idea per paragraph
- Use "First..., Then..., Finally..." patterns
- Avoid ambiguity—be precise

"""
        elif student.support_type == SupportType.DYSLEXIA:
            base_prompt += """
# DYSLEXIA SUPPORT ADAPTATIONS

FORMATTING:
- **Bold all key terms** for visual tracking
- Use bullet points (•) extensively
- Keep sentences under 15 words
- Maximum 2 sentences per paragraph

STRUCTURE:
- Break information into small visual chunks
- Use line breaks generously
- Avoid text walls—think "bite-sized" information

LANGUAGE:
- Simple, direct sentences
- Avoid complex compound structures
- One idea per sentence

"""
        elif student.support_type == SupportType.DOWN_SYNDROME:
            base_prompt += """
# DOWN SYNDROME SUPPORT ADAPTATIONS

SIMPLICITY:
- Use basic, everyday vocabulary (avoid technical jargon unless explaining it)
- One idea per sentence. One sentence per line.
- Repeat key concepts gently with slight variation

ENCOURAGEMENT:
- Be highly positive and encouraging
- Use phrases like "You're doing great!", "I'm proud of you!"
- Celebrate small wins

PACE:
- Slow down—don't rush through concepts
- Check understanding with simple questions
- Build on what they already know

"""
        else:
            base_prompt += """
# STANDARD TEACHING MODE

APPROACH:
- Use Socratic questioning to guide discovery
- Employ rich analogies and diverse examples
- Challenge thinking with "What if...?" scenarios
- Vary sentence structure for engagement

"""

        # ==================================================================
        # UNIVERSAL OUTPUT STANDARDS (Applies to ALL)
        # ==================================================================
        base_prompt += """
# OUTPUT FORMATTING RULES

READABILITY:
- Short sentences: Aim for 12-15 words maximum
- Short paragraphs: 2-3 lines each
- Double line breaks between ideas

LISTS & ORGANIZATION:
- Use bullets (•) for related items
- Use numbers (1., 2., 3.) for sequences or steps
- Use headers (##) for topic changes

CODE/EXAMPLES:
- Format examples clearly with spacing
- Show your work step-by-step
- Highlight the "why" behind each step

"""

        # ==================================================================
        # INTELLIGENT INPUT HANDLING (Critical for Voice/Spelling Issues)
        # ==================================================================
        base_prompt += f"""
# SMART INPUT INTERPRETATION

{student.full_name} may have spelling errors or speak with an accent.

RULE 1: PRIORITIZE INTENT
If you're 80%+ confident of what they mean → Just answer
Examples:
- "Lio" → Lion (answer about lions)
- "What is foto synthesis" → Photosynthesis (explain it)
- "Sell division" → Cell division (teach it)

RULE 2: ASK ONLY WHEN TRULY AMBIGUOUS
Only ask for clarification if the word could mean two completely different things AND context doesn't help.

Example of GOOD clarification:
"I'm not sure if you meant 'cell' (biology) or 'sell' (business). Which one?"

RULE 3: BE NATURAL
Handle it like a human teacher—with warmth and understanding, not like an error message.

"""

        # ==================================================================
        # SPECIAL TRIGGERS
        # ==================================================================
        base_prompt += """
# SPECIAL COMMANDS

QUIZ REQUEST:
If student asks for a quiz/test, respond ONLY with:
"Starting quiz functionality... [START_QUIZ]"

"""

        return base_prompt

# Singleton Instance
ai_service = AIService()

# ============================================================================
# EXPORTS FOR OTHER MODULES (Backward Compatibility)
# ============================================================================
# agent_service.py and others expect these to be available
from groq import Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

groq_client = None
if GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
    groq_client = Groq(api_key=GROQ_API_KEY)

    
# ============================================================================
# COMPATIBILITY WRAPPERS (Restored Functions)
# ============================================================================

def convert_markdown_to_html(text: str) -> str:
    """
    Convert markdown formatting to HTML for proper rendering
    Enhanced to handle lists and structured content better
    """
    if not text: return ""
    
    # 1. Headers
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # 2. Bold / Italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    
    # 3. Code Blocks (Basic)
    text = re.sub(r'`([^`]+)`', r'<code style="background:#f1f5f9; padding:2px 4px; rounded:4px">\1</code>', text)

    # 4. Lists (Robust)
    # Parsing line by line to handle <ul> and <ol> correctly
    lines = text.split('\n')
    html_lines = []
    in_ul = False
    in_ol = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check Unordered List
        if re.match(r'^[-*•]\s+', stripped):
            if not in_ul:
                if in_ol: 
                    html_lines.append('</ol>')
                    in_ol = False
                html_lines.append('<ul>')
                in_ul = True
            content = re.sub(r'^[-*•]\s+', '', stripped)
            html_lines.append(f'<li>{content}</li>')
            continue
            
        # Check Ordered List
        elif re.match(r'^\d+\.\s+', stripped):
            if not in_ol:
                if in_ul:
                    html_lines.append('</ul>')
                    in_ul = False
                html_lines.append('<ol>')
                in_ol = True
            content = re.sub(r'^\d+\.\s+', '', stripped)
            html_lines.append(f'<li>{content}</li>')
            continue
            
        # Normal line
        else:
            if in_ul:
                html_lines.append('</ul>')
                in_ul = False
            if in_ol:
                html_lines.append('</ol>')
                in_ol = False
            
            if stripped:
                html_lines.append(stripped + "<br/>") 
    
    if in_ul: html_lines.append('</ul>')
    if in_ol: html_lines.append('</ol>')
    
    final_text = "".join(html_lines)
    return final_text

async def generate_ai_response(
    student: Student,
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    subject: Optional[str] = None,
    session = None
) -> str:
    """Wrapper for backward compatibility"""
    return await ai_service.generate_ai_response(student, user_message, conversation_history, subject, session)

def get_adaptive_system_prompt(student: Student) -> str:
    """Wrapper for backward compatibility"""
    return ai_service._get_adaptive_system_prompt(student)


# ============================================================================
# RESTORED UTILITY FUNCTIONS (Logic copied from previous version)
# ============================================================================

def detect_question_in_message(message: str) -> bool:
    """
    Simple pattern matching to detect if a message contains a question
    Returns True if message likely contains a question
    """
    if not message:
        return False
    
    # Check for question mark
    if '?' in message:
        return True
    
    # Check for common question starters
    question_starters = [
        'what', 'where', 'when', 'why', 'who', 'how', 'which',
        'can you', 'could you', 'would you', 'do you', 'did you',
        'is', 'are', 'was', 'were', 'will', 'shall'
    ]
    
    message_lower = message.lower().strip()
    for starter in question_starters:
        if message_lower.startswith(starter):
            return True
    
    return False

def should_generate_test(conversation_history: List[Dict[str, str]]) -> bool:
    """Check if we should trigger a test based on conversation length"""
    if not conversation_history:
        return False
        
    user_messsages = [m for m in conversation_history if m.get("role") == "user"]
    # Trigger every 5 messages
    return len(user_messsages) > 0 and len(user_messsages) % 5 == 0

def generate_context_quiz(
    student: Student,
    conversation_history: List[Dict[str, str]],
    subject: str = "General",
    num_questions: int = 3
) -> List[Dict]:
    """
    OPTIMIZED: Generate context-aware quiz questions based on conversation history.
    Uses synchronous Groq client for compatibility with current router.
    """
    if not groq_client:
        return [
            {
                "type": "true_false", 
                "question": "AI service is currently offline. Please check API key.", 
                "correct_answer": "True",
                "explanation": "System maintenance."
            }
        ]
    
    # Extract recent conversation topics
    recent_messages = conversation_history[-6:] if conversation_history else []
    conversation_text = "\n".join([
        f"{'Student' if msg.get('role') == 'user' else 'AI'}: {msg.get('content', '')}"
        for msg in recent_messages
    ])
    
    import uuid
    random_seed = str(uuid.uuid4())[:8]
    
    # OPTIMIZED QUIZ PROMPT
    quiz_prompt = f"""You are a Nigerian teacher creating a quiz for {student.full_name} (Age: {student.age}).

CONVERSATION CONTEXT:
{conversation_text}

TASK: Create {num_questions} questions based STRICTLY on the conversation above about {subject}.

REQUIREMENTS:
1. Questions must reference specific details from the conversation
2. Mix question types:
   - Multiple Choice (4 options, labeled A-D)
   - True/False (based on facts discussed)
   - Short Answer (key concepts)
3. Make questions appropriate for age {student.age}
4. Ensure each question is UNIQUE (Seed: {random_seed})

OUTPUT FORMAT (JSON only, no markdown):
[
  {{
    "type": "multiple_choice",
    "question": "According to our discussion, what is...",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct_answer": "A",
    "explanation": "Brief explanation"
  }},
  {{
    "type": "true_false",
    "question": "We discussed that [specific fact]. True or False?",
    "correct_answer": "True",
    "explanation": "Brief explanation"
  }},
  {{
    "type": "short_answer",
    "question": "What concept did we explore when talking about [topic]?",
    "correct_answer": "main answer",
    "keywords": ["keyword1", "keyword2"],
    "explanation": "Brief explanation"
  }}
]

Return ONLY the JSON array. No additional text."""

    try:
        response = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL"),
            messages=[{"role": "user", "content": quiz_prompt}],
            temperature=0.8
        )
        content = response.choices[0].message.content.strip()
        
        # Clean JSON markdown if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        return json.loads(content.strip())
    except Exception as e:
        print(f"Error generating quiz: {e}")
        # Fallback question
        return [
            {
                "type": "true_false",
                "question": "Is this a fallback question due to an error?",
                "correct_answer": "True",
                "explanation": "We encountered a temporary glitch generating the quiz."
            }
        ]

def generate_test_question(student: Student, subject: str, topic: str, context: str) -> Dict:
    """Generate a single practice question (Sync)"""
    if not groq_client:
        return None    
        
    prompt = f"""Create 1 simple, age-appropriate practice question about {topic} for {student.full_name} ({student.age} years old).
    Context: {context}
    
    Return JSON: {{"question": "...", "correct_answer": "...", "topic": "{topic}"}}"""
    
    try:
        response = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        if "```" in content: content = content.split("```")[1].replace("json", "")
        return json.loads(content.strip())
    except:
        return None

def evaluate_answer(student_answer: str, correct_answer: str) -> bool:
    """Simple string match fallback"""
    s = student_answer.lower().strip()
    c = correct_answer.lower().strip()
    return s == c or c in s

def evaluate_conversation_answer(ai_question: str, student_answer: str, subject: str = None) -> dict:
    """
    OPTIMIZED: Evaluate a student's answer in flow (Sync)
    More forgiving evaluation with explicit spelling tolerance
    """
    if not groq_client:
        return {"is_correct": False, "confidence": 0, "explanation": "Offline"}
    
    # OPTIMIZED EVALUATION PROMPT
    prompt = f"""Evaluate this student's answer with understanding and flexibility.

QUESTION: {ai_question}
STUDENT'S ANSWER: {student_answer}
SUBJECT: {subject}

EVALUATION GUIDELINES:

1. SPELLING TOLERANCE
   - Ignore phonetic errors: "Lio" = Lion, "Foto" = Photo
   - Ignore minor typos: "Teh" = The
   - Focus on conceptual understanding, not perfect spelling

2. PARTIAL CREDIT
   - If the core concept is present → Mark as correct
   - If they're on the right track → Mark as correct with note

3. CONTEXT AWARENESS
   - Consider the student's age and background
   - Value effort and understanding over perfect wording

OUTPUT (JSON only):
{{
  "is_correct": true,
  "confidence": 0.95,
  "explanation": "Excellent! You understood the concept perfectly. (I noticed you meant 'photosynthesis'—great job!)"
}}

Return ONLY the JSON object."""
    
    try:
        response = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        if "```" in content: content = content.split("```")[1].replace("json", "")
        return json.loads(content.strip())
    except Exception as e:
        print(f"Evaluation error: {e}")
        return {"is_correct": False, "confidence": 0, "explanation": "Error evaluating"}

def generate_encouraging_feedback(student: Student, is_correct: bool, ans: str, corr: str, atmpt: int) -> str:
    if is_correct: 
        return f"Great job {student.full_name}! That's correct! 🌟"
    return f"Not quite. The answer was {corr}. Keep trying!"

def generate_personalized_completion_feedback(student: Student, score: float, passed: bool) -> str:
    if score >= 80:
        return f"Amazing! You scored {score}%. You're a star! 🌟"
    elif score >= 50:
        return f"Good effort! You scored {score}%. Keep practicing!"
    else:
        return f"You scored {score}%. Let's review this topic together."