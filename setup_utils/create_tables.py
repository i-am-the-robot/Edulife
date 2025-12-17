"""
Create Database Tables
"""
import sys
sys.path.insert(0, '.')

print("Creating database tables...")
print("-" * 60)

from backend.database import create_db_and_tables

# This will create all tables
create_db_and_tables()

print("OK - Database tables created successfully!")
print("-" * 60)
print("\nYou can now run: .venv\\Scripts\\python.exe create_super_admin.py")
