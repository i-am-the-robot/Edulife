# Backend Server Restart Instructions

## Problem
After resetting the database, the backend server is still running with the old database schema cached in memory. This causes:
- CORS errors (server not responding properly)
- 500 Internal Server Errors (trying to access old schema)

## Solution: Restart the Backend Server

### Step 1: Stop the Current Backend Server
1. Find the terminal/command prompt running the backend
2. Press `Ctrl+C` to stop the server

### Step 2: Start the Backend Server Again
```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Step 3: Verify Server is Running
You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 4: Test the API
Open browser and go to: `http://127.0.0.1:8000/health`

You should see:
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

## After Restart

The database is now empty, so you need to:

1. **Register Admin** (if not already done)
   - Go to frontend admin registration page
   - Create admin account

2. **Create School**
   - Login as admin
   - Create a school
   - Note the app_key generated

3. **Register Teachers**
   - Use the school's app_key
   - Create teacher accounts

4. **Create Students**
   - Login as teacher
   - Create student accounts

5. **Test Assignment Flow**
   - Login as student
   - Start an assignment
   - Complete quiz and final assessment
   - Login as teacher
   - View the submission in student profile → Assignments tab

## Troubleshooting

### If CORS errors persist:
- Make sure backend is running on `http://127.0.0.1:8000`
- Make sure frontend is running on `http://localhost:5173`
- Check browser console for exact error

### If 500 errors persist:
- Check backend terminal for error messages
- Verify database was reset successfully (check for `database.db` file)
- Try deleting `database.db` and running `reset_database_auto.py` again
