# Add to backend/admin_router.py after imports

from .schemas import PasswordChange

# Add this endpoint after the analytics section

@router.put("/change-password")
async def change_admin_password(
    password_data: PasswordChange,
    session: Session = Depends(get_db_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Change admin password"""
    from .auth import verify_password, get_password_hash
    
    # Verify current password
    if not verify_password(password_data.current_password, current_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_admin.hashed_password = get_password_hash(password_data.new_password)
    session.add(current_admin)
    session.commit()
    
    return {"message": "Password changed successfully"}
