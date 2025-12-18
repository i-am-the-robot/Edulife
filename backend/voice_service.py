"""
Voice Service - Twilio Integration
Handles voice chat functionality with text-to-speech and speech-to-text
Ensures voice and text responses are identical in content (markdown stripped for voice)
"""
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

load_dotenv()

class VoiceService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            print("WARNING: Twilio credentials not found. Voice features will be disabled.")
    
    def create_voice_response(self, ai_text: str) -> str:
        """
        Create a TwiML voice response from AI text
        Strips markdown and formats for natural speech
        """
        from .media_service import prepare_voice_response
        
        # Strip markdown and prepare for voice
        voice_text = prepare_voice_response(ai_text)
        
        response = VoiceResponse()
        response.say(voice_text, voice='alice', language='en-NG')  # Nigerian English
        
        # Gather next input
        gather = Gather(
            input='speech',
            action='/voice/process',
            timeout=5,
            language='en-NG'
        )
        response.append(gather)
        
        return str(response)
    
    def process_speech_input(self, speech_result: str) -> str:
        """
        Process speech input from Twilio
        Returns the transcribed text
        """
        return speech_result.strip() if speech_result else ""
    
    def make_outbound_call(self, to_number: str, message: str):
        """
        Make an outbound call with a message
        """
        if not self.client:
            print("Cannot make call: Twilio not configured")
            return None
        
        from .media_service import prepare_voice_response
        voice_message = prepare_voice_response(message)
        
        try:
            call = self.client.calls.create(
                twiml=f'<Response><Say voice="alice" language="en-NG">{voice_message}</Say></Response>',
                to=to_number,
                from_=self.phone_number
            )
            return call.sid
        except Exception as e:
            print(f"Error making call: {e}")
            return None

# Singleton instance
voice_service = VoiceService()
