# EduLife v2.0

## Fresh Build - Complete Educational Platform

### Overview
EduLife v2.0 is a comprehensive, inclusive educational platform with:
- **Admin Dashboard** - System-wide management and monitoring
- **Teacher Dashboard** - Detailed student insights with complete chat history and test results
- **Student Dashboard** - Engaging AI-powered learning experience
- **Inclusive AI** - Adaptive support that never mentions learning profiles to students

### Project Structure
```
EduLife/
├── backend/
│   ├── .env                 # Environment variables (Groq API key)
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLModel database models (7 tables)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # Authentication & authorization
│   ├── utils.py             # Utility functions
│   ├── main.py              # FastAPI application
│   ├── admin_api.py         # Admin endpoints (TODO)
│   ├── teacher_api.py       # Teacher endpoints (TODO)
│   ├── student_api.py       # Student endpoints (TODO)
│   └── chat_api.py          # AI chat endpoints (TODO)
├── .venv/                   # Python virtual environment
├── database.db              # SQLite database
└── start_backend.bat        # Start server script
```

### Database Models
1. **Admin** - System administrators
2. **School** - Schools with unique app keys
3. **User** - Teachers with roles and specializations
4. **Student** - Students with learning profiles (never shown to them)
5. **ChatHistory** - All AI conversations
6. **TestResult** - All interactive test results
7. **Tutorial** - Scheduled teacher-student sessions

### Setup

1. **Install Dependencies:**
```bash
.venv\Scripts\activate
pip install -r backend\requirements.txt
```

2. **Configure Environment:**
Edit `backend\.env` and add your Groq API key:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

3. **Start Backend:**
```bash
start_backend.bat
```

Or manually:
```bash
.venv\Scripts\activate
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

4. **Access API Documentation:**
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Current Status
✅ Database models created
✅ Authentication system ready
✅ Schemas defined
✅ Main app structure complete

🚧 In Progress:
- Admin API endpoints
- Teacher API endpoints
- Student API endpoints
- AI Chat system with Groq

### Next Steps
1. Implement Admin API (school, teacher, student management)
2. Implement Teacher API (student insights, chat history viewer)
3. Implement Student API (profile, progress, chat history)
4. Implement AI Chat API with auto-testing and inclusive language
5. Build frontend dashboards

### Key Features
- **Role-Based Access Control**: Admin, Head Teacher, Teacher
- **Complete Tracking**: All conversations and tests recorded
- **Inclusive Design**: Learning profiles never mentioned to students
- **Adaptive AI**: Invisible support based on student needs
- **Encouraging Feedback**: Always positive, celebrating effort

### Technology Stack
- **Backend**: FastAPI, SQLModel, SQLite
- **Auth**: JWT tokens, bcrypt password hashing
- **AI**: Groq API with meta-llama/llama-4-scout-17b-16e-instruct
- **Visuals**: DuckDuckGo Search + Wikipedia (Fallback) - **No API Key Required**
- **Frontend**: React + Vite (to be built)

---

Built with ❤️ for inclusive education
