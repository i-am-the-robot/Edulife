@echo off
echo ============================================================
echo EduLife v2.0 - Database Setup
echo ============================================================
echo.

echo Step 1: Deleting old databases...
del /f /q database.db 2>nul
del /f /q edulife.db 2>nul
echo OK - Old databases deleted
echo.

echo Step 2: Creating database tables...
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); from backend.database import create_db_and_tables; create_db_and_tables(); print('OK - Tables created')"
echo.

echo Step 3: Creating Super Admin account...
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); from sqlmodel import Session, select; from passlib.context import CryptContext; from backend.models import Admin; from backend.database import engine; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); session = Session(engine); admin = Admin(full_name='Super Admin', email='titilolasalisukazeem1@gmail.com', hashed_password=pwd_context.hash('Project2025'), school_id=None, is_active=True); session.add(admin); session.commit(); print('OK - Super Admin created'); print('Email: titilolasalisukazeem1@gmail.com'); print('Password: Project2025'); print('School ID: NULL (Super Admin)')"
echo.

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo You can now login at: http://localhost:5174
echo Email: titilolasalisukazeem1@gmail.com
echo Password: Project2025
echo ============================================================
pause
