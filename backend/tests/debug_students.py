
import os
import sys
from sqlmodel import Session, select, create_engine

# Add backend to path
sys.path.append(os.path.join(os.getcwd()))

from backend.database import DB_PATH
from backend.models import User, Student, School

print(f"Checking database at: {DB_PATH}")
engine = create_engine(f"sqlite:///{DB_PATH}")

def check_data():
    with Session(engine) as session:
        print("\n--- TEACHERS ---")
        teachers = session.exec(select(User).where(User.role == "Teacher")).all()
        for t in teachers:
            print(f"Teacher: {t.full_name} (ID: {t.id})")
            print(f"  School ID: {t.school_id}")
            print(f"  Email: {t.email}")

        print("\n--- STUDENTS ---")
        students = session.exec(select(Student)).all()
        for s in students:
            print(f"Student: {s.full_name} (ID: {s.id})")
            print(f"  School ID: {s.school_id}")
            print(f"  Created By: {s.created_by_user_id}")
            print(f"  Is Active: {s.is_active}")
            
        print("\n--- SCHOOLS ---")
        schools = session.exec(select(School)).all()
        for s in schools:
            print(f"School: {s.name} (ID: {s.id})")

if __name__ == "__main__":
    check_data()
