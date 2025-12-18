"""
Voice Answer Parser
Intelligently parses voice input to match quiz answer options
"""
from typing import List, Optional
import re
from difflib import SequenceMatcher


def parse_voice_answer(voice_input: str, options: List[str]) -> Optional[str]:
    """
    Parse voice input to match quiz options
    
    Handles multiple formats:
    - Letter only: "A", "B", "C", "D"
    - With "option": "option A", "option B"
    - Ordinal: "first one", "second one", "third", "fourth"
    - Full text: Match to option content
    
    Args:
        voice_input: Raw voice input from student
        options: List of options like ["A) Photosynthesis", "B) Respiration", ...]
    
    Returns:
        Matched letter (A, B, C, D) or None if no match
    """
    if not voice_input or not options:
        return None
    
    # Clean input
    voice_input = voice_input.strip().lower()
    
    # Extract option letters from options list
    option_letters = []
    for opt in options:
        match = re.match(r'^([A-D])\)', opt)
        if match:
            option_letters.append(match.group(1))
    
    if not option_letters:
        return None
    
    # Pattern 1: Direct letter match ("a", "b", "c", "d")
    if voice_input.upper() in option_letters:
        return voice_input.upper()
    
    # Pattern 2: "option X" format
    option_match = re.search(r'option\s+([a-d])', voice_input)
    if option_match:
        return option_match.group(1).upper()
    
    # Pattern 3: Ordinal numbers
    ordinal_map = {
        'first': 'A',
        '1st': 'A',
        'one': 'A',
        'second': 'B',
        '2nd': 'B',
        'two': 'B',
        'third': 'C',
        '3rd': 'C',
        'three': 'C',
        'fourth': 'D',
        '4th': 'D',
        'four': 'D'
    }
    
    for ordinal, letter in ordinal_map.items():
        if ordinal in voice_input and letter in option_letters:
            return letter
    
    # Pattern 4: Fuzzy match to option content
    best_match = None
    best_score = 0.0
    
    for i, option in enumerate(options):
        # Extract option text (remove "A) ", "B) ", etc.)
        option_text = re.sub(r'^[A-D]\)\s*', '', option).lower()
        
        # Calculate similarity
        similarity = SequenceMatcher(None, voice_input, option_text).ratio()
        
        # Also check if voice input is contained in option
        if voice_input in option_text:
            similarity = max(similarity, 0.8)
        
        # Check if any significant word from voice input is in option
        voice_words = set(voice_input.split())
        option_words = set(option_text.split())
        common_words = voice_words & option_words
        
        if common_words and len(voice_input) > 3:
            word_match_score = len(common_words) / max(len(voice_words), 1)
            similarity = max(similarity, word_match_score * 0.7)
        
        if similarity > best_score and similarity > 0.6:  # Threshold
            best_score = similarity
            best_match = option_letters[i] if i < len(option_letters) else None
    
    return best_match


def parse_voice_command(voice_input: str) -> Optional[str]:
    """
    Parse voice commands for quiz navigation
    
    Returns:
        - "next" for next question
        - "submit" for submitting quiz
        - "repeat" for repeating question
        - None if no command detected
    """
    if not voice_input:
        return None
    
    voice_input = voice_input.strip().lower()
    
    # Next question commands
    next_commands = ['next', 'next question', 'move on', 'continue', 'go on']
    if any(cmd in voice_input for cmd in next_commands):
        return "next"
    
    # Submit commands
    submit_commands = ['submit', 'finish', 'done', 'complete', 'end quiz']
    if any(cmd in voice_input for cmd in submit_commands):
        return "submit"
    
    # Repeat commands
    repeat_commands = ['repeat', 'say again', 'what was that', 'repeat question']
    if any(cmd in voice_input for cmd in repeat_commands):
        return "repeat"
    
    # Confirmation (yes/no)
    if voice_input in ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok']:
        return "yes"
    
    if voice_input in ['no', 'nope', 'nah', 'not yet']:
        return "no"
    
    return None


def is_answer_input(voice_input: str) -> bool:
    """
    Determine if voice input is likely an answer vs a command
    
    Returns:
        True if input looks like an answer, False if it's a command
    """
    if not voice_input:
        return False
    
    voice_input = voice_input.strip().lower()
    
    # Check if it's a command
    if parse_voice_command(voice_input):
        return False
    
    # Check if it's a letter or option reference
    if re.match(r'^[a-d]$', voice_input):
        return True
    
    if 'option' in voice_input:
        return True
    
    # Check for ordinals
    ordinals = ['first', 'second', 'third', 'fourth', '1st', '2nd', '3rd', '4th']
    if any(ord in voice_input for ord in ordinals):
        return True
    
    # If it's longer text, assume it's an answer attempt
    if len(voice_input) > 3:
        return True
    
    return False
