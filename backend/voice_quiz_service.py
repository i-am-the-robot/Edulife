"""
Voice Quiz Service
Converts quiz questions and results to natural voice format
"""
from typing import Dict, List


class VoiceQuizService:
    """Service for converting quiz data to voice-friendly format"""
    
    @staticmethod
    def read_question(question_data: Dict, question_number: int, total_questions: int) -> str:
        """
        Convert question to natural voice format
        
        Args:
            question_data: Question dict with 'question', 'options', etc.
            question_number: Current question number (1-indexed)
            total_questions: Total number of questions
        
        Returns:
            Voice-friendly question text
        """
        question_text = question_data.get("question", "")
        options = question_data.get("options", [])
        
        # Build voice output
        voice_text = f"Question {question_number} of {total_questions}. "
        voice_text += f"{question_text} "
        
        # Read options
        for option in options:
            voice_text += f"{option}. "
        
        # Add prompt
        if question_number == total_questions:
            voice_text += "This is the last question. Say your answer: A, B, C, or D."
        else:
            voice_text += "Say your answer: A, B, C, or D."
        
        return voice_text
    
    @staticmethod
    def read_score_explanation(results: Dict, student_name: str) -> str:
        """
        Convert quiz results to natural voice explanation
        
        Args:
            results: Results dict from QuizSession.calculate_score()
            student_name: Student's name for personalization
        
        Returns:
            Voice-friendly score explanation
        """
        score = results.get("score", 0)
        total = results.get("total", 0)
        percentage = results.get("percentage", 0)
        detailed_results = results.get("detailed_results", [])
        
        # Opening
        voice_text = f"Great job, {student_name}! "
        
        # Score announcement
        if percentage >= 90:
            voice_text += f"You scored {score} out of {total}! That's {percentage:.0f} percent! Excellent work! "
        elif percentage >= 70:
            voice_text += f"You scored {score} out of {total}. That's {percentage:.0f} percent! Well done! "
        elif percentage >= 50:
            voice_text += f"You scored {score} out of {total}. That's {percentage:.0f} percent. Good effort! "
        else:
            voice_text += f"You scored {score} out of {total}. That's {percentage:.0f} percent. Don't worry, let's learn from this! "
        
        # Detailed explanation
        voice_text += "Let me explain what you got right and wrong. "
        
        for result in detailed_results:
            q_num = result.get("question_number", 0)
            is_correct = result.get("is_correct", False)
            student_answer = result.get("student_answer", "")
            correct_answer = result.get("correct_answer", "")
            explanation = result.get("explanation", "")
            
            if is_correct:
                voice_text += f"Question {q_num}: Correct! You said {student_answer}. {explanation} "
            else:
                voice_text += f"Question {q_num}: Not quite. You said {student_answer}, but the answer is {correct_answer}. {explanation} "
        
        # Closing encouragement
        if percentage >= 70:
            voice_text += "Keep up the great work!"
        else:
            voice_text += "Want to try another quiz to practice?"
        
        return voice_text
    
    @staticmethod
    def read_confirmation(question_number: int, total_questions: int) -> str:
        """
        Read confirmation before submitting quiz
        
        Returns:
            Voice-friendly confirmation message
        """
        if question_number == total_questions:
            return "That was the last question! Ready to submit your quiz? Say yes to submit, or no to review your answers."
        return "Ready to move to the next question? Say next."
    
    @staticmethod
    def read_answer_confirmation(answer: str) -> str:
        """
        Confirm detected answer
        
        Returns:
            Voice-friendly confirmation
        """
        return f"Got it! You selected {answer}."
    
    @staticmethod
    def read_unclear_input() -> str:
        """
        Message when voice input is unclear
        
        Returns:
            Voice-friendly error message
        """
        return "I didn't catch that. Please say A, B, C, or D, or say repeat to hear the question again."
    
    @staticmethod
    def read_quiz_start(subject: str, total_questions: int) -> str:
        """
        Introduction when starting voice quiz
        
        Returns:
            Voice-friendly intro message
        """
        return f"Starting your {subject} quiz! You have {total_questions} questions. I'll read each question and the options. Just say A, B, C, or D for your answer. Say next to move forward, or repeat if you want to hear the question again. Let's begin!"
    
    @staticmethod
    def read_progress(current: int, total: int, answered: int) -> str:
        """
        Read current progress
        
        Returns:
            Voice-friendly progress update
        """
        remaining = total - answered
        return f"You're on question {current} of {total}. {remaining} questions remaining."


# Singleton instance
voice_quiz_service = VoiceQuizService()
