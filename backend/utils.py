"""
Utility functions for EduLife v2.0
"""
import secrets
import string
from datetime import datetime, timezone
from typing import Optional

def generate_app_key(length: int = 12) -> str:
    """
    Generate a unique school app key
    Format: XXXX-XXXX-XXXX (alphanumeric uppercase)
    """
    chars = string.ascii_uppercase + string.digits
    key = ''.join(secrets.choice(chars) for _ in range(length))
    # Format with dashes for readability
    return f"{key[:4]}-{key[4:8]}-{key[8:]}"

def generate_student_id(school_id: int) -> str:
    """
    Generate unique student ID
    Format: {school_id}_student_{timestamp}
    """
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)  # Milliseconds for uniqueness
    return f"{school_id}_student_{timestamp}"

def calculate_engagement_score(
    login_frequency: int,
    total_sessions: int,
    total_tests: int,
    test_success_rate: float
) -> float:
    """
    Calculate student engagement score (0-100)
    Based on login frequency, sessions, tests, and success rate
    """
    # Weighted formula
    login_score = min(login_frequency * 10, 30)  # Max 30 points
    session_score = min(total_sessions * 2, 30)   # Max 30 points
    test_score = min(total_tests, 20)             # Max 20 points
    success_score = test_success_rate * 0.2       # Max 20 points
    
    total = login_score + session_score + test_score + success_score
    return round(min(total, 100.0), 2)

def get_status_indicator(engagement_score: Optional[float], last_active: Optional[datetime]) -> str:
    """
    Get student status indicator for teacher dashboard
    Returns: 'on_track', 'needs_attention', 'excelling', 'inactive'
    """
    if last_active is None:
        return 'inactive'
    
    # Check if inactive (no activity in 7 days)
    # Handle both timezone-aware and naive datetimes
    if last_active.tzinfo is None:
        # If last_active is naive, assume it's UTC and make it aware
        last_active = last_active.replace(tzinfo=timezone.utc)
    
    days_since_active = (datetime.now(timezone.utc) - last_active).days
    if days_since_active > 7:
        return 'inactive'
    
    if engagement_score is None:
        return 'needs_attention'
    
    # Determine status based on engagement score
    if engagement_score >= 80:
        return 'excelling'
    elif engagement_score >= 60:
        return 'on_track'
    else:
        return 'needs_attention'
