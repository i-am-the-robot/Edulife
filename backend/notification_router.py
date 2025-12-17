"""
Notification Router
API endpoints for agent notifications
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Dict, List
from datetime import datetime

from .database import get_db_session
from .models import Student, AgentNotification
from .auth import oauth2_scheme
from .notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

# Helper to get current student
async def get_current_student(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session)
) -> Student:
    """Get current authenticated student"""
    from .auth import decode_token
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    
    try:
        payload = decode_token(token)
        student_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        
        if student_id is None or user_type != "student":
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    student = session.get(Student, student_id)
    if student is None or not student.is_active:
        raise credentials_exception
    
    return student


@router.get("/unread", response_model=List[Dict])
async def get_unread_notifications(
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Get all unread notifications for current student"""
    notifications = NotificationService.get_unread_notifications(
        current_student.id,
        session
    )
    
    return [
        {
            "id": n.id,
            "type": n.notification_type,
            "agent": n.agent_type,
            "title": n.title,
            "message": n.message,
            "action_url": n.action_url,
            "priority": n.priority,
            "created_at": n.created_at.isoformat()
        }
        for n in notifications
    ]


@router.get("/all", response_model=List[Dict])
async def get_all_notifications(
    limit: int = 50,
    include_read: bool = True,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Get all notifications for current student"""
    notifications = NotificationService.get_all_notifications(
        current_student.id,
        session,
        limit=limit,
        include_read=include_read
    )
    
    return [
        {
            "id": n.id,
            "type": n.notification_type,
            "agent": n.agent_type,
            "title": n.title,
            "message": n.message,
            "action_url": n.action_url,
            "priority": n.priority,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
            "read_at": n.read_at.isoformat() if n.read_at else None
        }
        for n in notifications
    ]


@router.get("/count", response_model=Dict)
async def get_notification_count(
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Get count of unread notifications"""
    count = NotificationService.get_notification_count(
        current_student.id,
        session,
        unread_only=True
    )
    
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=Dict)
async def mark_notification_as_read(
    notification_id: int,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Mark a notification as read"""
    # Verify notification belongs to student
    notification = session.get(AgentNotification, notification_id)
    if not notification or notification.student_id != current_student.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    NotificationService.mark_as_read(notification_id, session)
    
    return {"success": True, "notification_id": notification_id}


@router.post("/mark-all-read", response_model=Dict)
async def mark_all_as_read(
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Mark all notifications as read"""
    NotificationService.mark_all_as_read(current_student.id, session)
    
    return {"success": True, "message": "All notifications marked as read"}


@router.delete("/{notification_id}", response_model=Dict)
async def delete_notification(
    notification_id: int,
    current_student: Student = Depends(get_current_student),
    session: Session = Depends(get_db_session)
):
    """Delete a notification"""
    notification = session.get(AgentNotification, notification_id)
    if not notification or notification.student_id != current_student.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    session.delete(notification)
    session.commit()
    
    return {"success": True, "notification_id": notification_id}


@router.post("/cleanup", response_model=Dict)
async def cleanup_expired_notifications(
    session: Session = Depends(get_db_session)
):
    """Delete expired notifications (admin/background task)"""
    deleted_count = NotificationService.delete_expired_notifications(session)
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} expired notifications"
    }
