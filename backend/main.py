"""
EduLife v2.0 - Main FastAPI Application
Complete educational platform with Admin, Teacher, and Student dashboards
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create database tables on startup"""
    create_db_and_tables()
    yield

# Create FastAPI app
app = FastAPI(
    title="EduLife v2.0 API",
    description="Inclusive Educational Platform with AI-Powered Learning",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to EduLife v2.0 API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "operational"
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# Include routers
from .auth_router import router as auth_router
from .admin_router import router as admin_router
from .teacher_router import router as teacher_router
from .student_router import router as student_router
from .chat_router import router as chat_router
from .assignment_study_router import router as assignment_study_router
from .agent_router import router as agent_router
from .notification_router import router as notification_router

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(teacher_router)
app.include_router(student_router)
app.include_router(chat_router)
app.include_router(assignment_study_router)
app.include_router(agent_router)
app.include_router(notification_router)



