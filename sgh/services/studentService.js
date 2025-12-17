// Student API Service
import api from './api';

export const studentService = {
    // Get student profile
    getProfile: async () => {
        const response = await api.get('/api/student/profile');
        return response.data;
    },

    // Get student subjects
    getSubjects: async () => {
        const response = await api.get('/api/student/subjects');
        return response.data;
    },

    // Get achievements
    getAchievements: async () => {
        const response = await api.get('/api/student/achievements');
        return response.data;
    },

    // Get schedule
    getSchedule: async () => {
        const response = await api.get('/api/student/schedule');
        return response.data;
    },

    // Get chat history
    getChatHistory: async () => {
        const response = await api.get('/api/student/chat-history');
        return response.data;
    },

    // Get chat sessions (grouped by session_id)
    getChatSessions: async () => {
        const response = await api.get('/api/student/chat-sessions');
        return response.data;
    },

    // Get messages for a specific session
    getSessionMessages: async (sessionId) => {
        const response = await api.get(`/api/student/chat-history?session_id=${sessionId}`);
        return response.data;
    },

    // Mark chat as favorite
    toggleFavorite: async (chatId) => {
        const response = await api.put(`/api/student/chat-history/${chatId}/favorite`);
        return response.data;
    },

    // Task Management
    getTasks: async (filter = '') => {
        const response = await api.get('/api/student/tasks', { params: { status_filter: filter } });
        return response.data;
    },

    completeTask: async (taskId) => {
        const response = await api.put(`/api/student/tasks/${taskId}/complete`);
        return response.data;
    },

    // ============================================================================
    // ASSIGNMENT STUDY SESSION METHODS
    // ============================================================================

    // Start or continue study session for an assignment
    startStudySession: async (taskId) => {
        const response = await api.post(`/api/student/assignments/${taskId}/start-study`);
        return response.data;
    },

    // Get study session status
    getStudyStatus: async (taskId) => {
        const response = await api.get(`/api/student/assignments/${taskId}/study-status`);
        return response.data;
    },

    // Submit periodic quiz answers
    submitQuiz: async (taskId, answers) => {
        const response = await api.post(`/api/student/assignments/${taskId}/submit-quiz`, answers);
        return response.data;
    },

    // Initiate assignment completion (generates final assessment)
    completeAssignment: async (taskId) => {
        const response = await api.post(`/api/student/assignments/${taskId}/complete`);
        return response.data;
    },

    // Submit final assessment answers
    submitFinalAssessment: async (taskId, answers) => {
        const response = await api.post(`/api/student/assignments/${taskId}/submit-final`, answers);
        return response.data;
    },

    // Generate AI-powered weekly schedule
    generateSchedule: async () => {
        const response = await api.post('/api/student/generate-schedule');
        return response.data;
    },

    // Generate context-aware quiz questions
    generateQuiz: async (sessionId = null, subject = 'General') => {
        const response = await api.post('/api/student/generate-quiz', null, {
            params: { session_id: sessionId, subject }
        });
        return response.data;
    }
};
