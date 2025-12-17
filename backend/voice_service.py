"""
Voice Chat Service
Validates that student voice input is learning-related before processing.
"""
from groq import AsyncGroq
import os
from dotenv import load_dotenv

load_dotenv()

class VoiceService:
    def __init__(self):
        """Initialize Groq client for content validation"""
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL")
    
    async def validate_learning_content(self, text: str) -> dict:
        """
        Validate if the transcribed text is related to learning/education.
        
        Args:
            text: Transcribed speech from student
            
        Returns:
            dict with:
                - is_valid: bool - whether content is learning-related
                - message: str - response message
        """
        try:
            prompt = f"""You are an educational content validator. Determine if this student's question or statement is related to learning, education, or academic topics.

Student said: "{text}"

Respond with ONLY 'yes' if it's learning-related (homework, subjects, studying, exams, concepts, etc.)
Respond with ONLY 'no' if it's NOT learning-related (casual chat, games, food, etc.)

Your response:"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().lower()
            is_valid = 'yes' in answer
            
            if is_valid:
                return {
                    "is_valid": True,
                    "message": "Processing your question..."
                }
            else:
                return {
                    "is_valid": False,
                    "message": "I'm here to help with your studies! Please ask me questions about your lessons, homework, or any subject you're learning."
                }
                
        except Exception as e:
            print(f"Error validating content: {e}")
            # Default to valid to avoid blocking legitimate questions
            return {
                "is_valid": True,
                "message": "Processing your question..."
            }

# Singleton instance
voice_service = VoiceService()
