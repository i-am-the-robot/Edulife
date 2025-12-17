"""
Database Reset Script
Deletes the old database and creates a new one with the updated schema
WARNING: This will delete all existing data!
"""
import os
import sys

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(__file__))

db_path = os.path.join(os.path.dirname(__file__), 'database.db')

print("=" * 60)
print("DATABASE RESET SCRIPT")
print("=" * 60)
print(f"\nDatabase path: {db_path}")

if os.path.exists(db_path):
    print("\nWARNING: This will DELETE the existing database!")
    print("All data will be lost!")
    response = input("\nDo you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("\nOperation cancelled.")
        sys.exit(0)
    
    # Delete old database
    os.remove(db_path)
    print("\n[X] Old database deleted")
else:
    print("\n[i] No existing database found")

# Import models and create new database
print("\n[*] Creating new database with updated schema...")

try:
    from database import create_db_and_tables
    from models import *  # Import all models
    
    create_db_and_tables()
    print("[OK] Database created successfully!")
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print("\nThe database has been recreated with the latest schema.")
    print("You can now restart the backend server.")
    
except Exception as e:
    print(f"\n[ERROR] Failed to create database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
