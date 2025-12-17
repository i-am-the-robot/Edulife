"""
AI Service - Quiz Generation and Grading Functions
Handles periodic quizzes and final assessments for assignment study sessions
"""
from typing import List, Dict
import json
from groq import Groq
from .models import Student

# Import from main ai_service
try:
    from .ai_service import groq_client, GROQ_MODEL
except:
    groq_client = None
    GROQ_MODEL = os.getenv("GROQ_MODEL")

# ============================================================================
# ASSIGNMENT QUIZ GENERATION
# ============================================================================

def generate_periodic_quiz(
    student: Student,
    conversation_history: List[Dict[str, str]],
    subject: str
) -> List[Dict[str, any]]:
    """
    Generate 3-4 mixed-format quiz questions based on recent conversation
    Mix of multiple choice, true/false, and short answer
    """
    if not groq_client:
        return []
    
    # Get last 5 exchanges for context
    recent_exchanges = conversation_history[-10:] if len(conversation_history) >= 10 else conversation_history
    conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_exchanges])
    
    prompt = f"""Based on this recent learning conversation about {subject}, generate 3-4 quiz questions to check understanding.

Conversation:
{conversation_text}

Generate a MIX of question types:
- 1-2 multiple choice questions (with 4 options A/B/C/D)
- 1 true/false question
- 1 short answer question

Return ONLY a JSON array with this exact format:
[
  {{
    "type": "multiple_choice",
    "question": "question text",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct_answer": "A",
    "explanation": "why this is correct"
  }},
  {{
    "type": "true_false",
    "question": "statement to evaluate",
    "correct_answer": "True",
    "explanation": "explanation"
  }},
  {{
    "type": "short_answer",
    "question": "question requiring brief answer",
    "correct_answer": "expected answer",
    "keywords": ["key", "words", "to", "check"],
    "explanation": "explanation"
  }}
]"""
    
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        
        questions = json.loads(response.choices[0].message.content)
        return questions
    except Exception as e:
        print(f"Quiz generation error: {e}")
        return []

def generate_final_assessment(
    student: Student,
    full_conversation: List[Dict[str, str]],
    subject: str,
    assignment_title: str
) -> List[Dict[str, any]]:
    """
    Generate 5 comprehensive quiz questions based on entire conversation
    Covers all main topics discussed
    """
    if not groq_client:
        return []
    
    conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in full_conversation])
    
    prompt = f"""Based on this complete learning session about "{assignment_title}" in {subject}, generate 5 comprehensive assessment questions.

Full Conversation:
{conversation_text}

Generate a MIX of question types covering ALL main topics discussed:
- 2 multiple choice questions
- 1 true/false question
- 2 short answer questions

Return ONLY a JSON array with this exact format:
[
  {{
    "type": "multiple_choice",
    "question": "question text",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct_answer": "A",
    "explanation": "why this is correct"
  }},
  ...
]"""
    
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
        
        questions = json.loads(response.choices[0].message.content)
        return questions
    except Exception as e:
        print(f"Final assessment generation error: {e}")
        return []

def grade_quiz_answers(
    questions: List[Dict[str, any]],
    student_answers: List[str],
    passing_threshold: float = 0.7
) -> Dict[str, any]:
    """
    Grade quiz answers with 70% passing threshold
    Returns score, feedback, and pass/fail status
    """
    if len(questions) != len(student_answers):
        return {"error": "Mismatch between questions and answers"}
    
    total_questions = len(questions)
    correct_count = 0
    detailed_feedback = []
    
    for i, (question, student_answer) in enumerate(zip(questions, student_answers)):
        q_type = question.get("type")
        correct_answer = question.get("correct_answer", "")
        explanation = question.get("explanation", "")
        
        is_correct = False
        
        if q_type == "multiple_choice":
            # Exact match for multiple choice
            ans_upper = student_answer.strip().upper()
            corr_upper = correct_answer.strip().upper()
            
            # Direct Key Match (A == A)
            if ans_upper == corr_upper:
                is_correct = True
            else:
                # Content Match Logic
                # Check if the student provided the TEXT of the correct answer
                options = question.get("options", [])
                correct_option_text = ""
                
                # Find the text for the correct answer key
                for opt in options:
                    # distinct formats: "A) Text" or "A. Text"
                    if opt.upper().startswith(f"{corr_upper})") or opt.upper().startswith(f"{corr_upper}."):
                        # Extract "Text" part
                        correct_option_text = opt[2:].strip().lower()
                        break
                
                if correct_option_text and correct_option_text in student_answer.lower():
                    is_correct = True
                
                # Reverse check: Did they provide the text for a WRONG answer? (To avoid false positives if they just repeated the question)
                # (Skipping for now to keep it lenient and helpful for kids)
        
        elif q_type == "true_false":
            # Case-insensitive match for true/false
            is_correct = student_answer.strip().lower() == correct_answer.strip().lower()
        
        elif q_type == "short_answer":
            # Keyword-based grading for short answer
            keywords = question.get("keywords", [])
            student_lower = student_answer.lower()
            
            # Check if at least 60% of keywords are present
            keyword_matches = sum(1 for kw in keywords if kw.lower() in student_lower)
            is_correct = keyword_matches >= len(keywords) * 0.6
        
        if is_correct:
            correct_count += 1
            detailed_feedback.append({
                "question_num": i + 1,
                "correct": True,
                "feedback": f"✅ Correct! {explanation}"
            })
        else:
            detailed_feedback.append({
                "question_num": i + 1,
                "correct": False,
                "feedback": f"❌ Not quite. The correct answer is: {correct_answer}. {explanation}"
            })
    
    score = (correct_count / total_questions) * 100
    passed = score >= (passing_threshold * 100)
    
    return {
        "score": score,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "passed": passed,
        "passing_threshold": passing_threshold * 100,
        "detailed_feedback": detailed_feedback
    }

def generate_study_summary(
    student: Student,
    conversation_history: List[Dict[str, str]],
    quiz_score: float,
    final_score: float,
    subject: str,
    assignment_title: str
) -> str:
    """
    Generate a concise summary for teacher submission
    Includes: topics covered, engagement level, quiz performance
    """
    if not groq_client:
        return f"Student completed assignment '{assignment_title}' with quiz score: {quiz_score}%, final score: {final_score}%"
    
    conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[:20]])  # First 20 messages
    
    prompt = f"""Generate a brief summary (3-4 sentences) of this student's learning session for their teacher.

Student: {student.full_name}
Assignment: {assignment_title}
Subject: {subject}
Periodic Quiz Score: {quiz_score}%
Final Assessment Score: {final_score}%

Conversation Sample:
{conversation_text}

Include:
- Main topics covered
- Student engagement/understanding level
- Overall performance

Keep it concise and professional."""
    
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Summary generation error: {e}")
        return f"Student completed '{assignment_title}' with periodic quiz score: {quiz_score}%, final score: {final_score}%"
