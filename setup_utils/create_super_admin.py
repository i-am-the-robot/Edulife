"""
Create Super Admin - Fixed Version
"""
import sys
sys.path.insert(0, '.')

from sqlmodel import Session, select
from passlib.context import CryptContext
from backend.models import Admin
from backend.database import engine  # Use the same engine as backend

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("\nCreating Super Admin...")
with Session(engine) as session:
    # Check if admin exists
    statement = select(Admin).where(Admin.email == "titilolasalisukazeem1@gmail.com")
    existing = session.exec(statement).first()
    
    if existing:
        print("OK - Super Admin already exists!")
        print(f"   Email: {existing.email}")
        print(f"   School ID: {existing.school_id}")
    else:
        # Create super admin
        admin = Admin(
            full_name="Super Admin",
            email="titilolasalisukazeem1@gmail.com",
            hashed_password=pwd_context.hash("Project2025"),
            school_id=None,  # NULL = Super Admin
            is_active=True
        )
        
        session.add(admin)
        session.commit()
        
        print("=" * 60)
        print("OK - SUPER ADMIN CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Email: titilolasalisukazeem1@gmail.com")
        print(f"Password: Project2025")
        print(f"School ID: NULL (Super Admin - Full Access)")
        print("=" * 60)
        print("\nPermissions:")
        print("   - Create and manage ALL schools")
        print("   - Create school-specific admins")
        print("   - View all teachers and students")
        print("   - Full system access")
        print("=" * 60)
