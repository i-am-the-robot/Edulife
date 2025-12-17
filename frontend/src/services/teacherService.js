// Teacher API Service
import api from './api';

export const teacherService = {
    // Get my students (or all school students for Head Teacher)
    getMyStudents: async () => {
        const response = await api.get('/api/teacher/students');
        return response.data;
    },

    // Get detailed student profile
    getStudentDetail: async (studentId) => {
        const response = await api.get(`/api/teacher/students/${studentId}`);
        return response.data;
    },

    // Get student chat history
    getStudentChatHistory: async (studentId, filters = {}) => {
        const params = new URLSearchParams(filters);
        const response = await api.get(`/api/teacher/students/${studentId}/chat-history?${params}`);
        return response.data;
    },

    // Get student test results
    getStudentTestResults: async (studentId, filters = {}) => {
        const params = new URLSearchParams(filters);
        const response = await api.get(`/api/teacher/students/${studentId}/test-results?${params}`);
        return response.data;
    },

    // Get student analytics
    getStudentAnalytics: async (studentId) => {
        const response = await api.get(`/api/teacher/students/${studentId}/analytics`);
        return response.data;
    },

    // Schedule tutorial
    scheduleTutorial: async (data) => {
        const response = await api.post('/api/teacher/tutorials', data);
        return response.data;
    },

    // Get all tutorials
    getTutorials: async () => {
        const response = await api.get('/api/teacher/tutorials');
        return response.data;
    },

    // Register new student
    registerStudent: async (studentData) => {
        const response = await api.post('/api/teacher/students', studentData);
        return response.data;
    },

    // Update tutorial
    updateTutorial: async (tutorialId, data) => {
        const response = await api.put(`/api/teacher/tutorials/${tutorialId}`, data);
        return response.data;
    },

    // Cancel tutorial
    cancelTutorial: async (tutorialId) => {
        const response = await api.delete(`/api/teacher/tutorials/${tutorialId}`);
        return response.data;
    },

    // Generate student report
    generateReport: async (studentId) => {
        const response = await api.get(`/api/teacher/students/${studentId}/report`);
        return response.data;
    },

    // Task Scheduler Methods
    createTask: async (data) => {
        const response = await api.post('/api/teacher/tasks', null, { params: data });
        return response.data;
    },

    getTasks: async () => {
        const response = await api.get('/api/teacher/tasks');
        return response.data;
    },

    deleteTask: async (taskId) => {
        await api.delete(`/api/teacher/tasks/${taskId}`);
    },

    // Syllabus Management
    uploadSyllabus: async (text) => {
        const response = await api.post('/api/teacher/syllabus/upload', null, { params: { syllabus_text: text } });
        return response.data;
    },

    // Get list of students (aliased for cleaner code in TaskScheduler)
    getStudents: async () => {
        return teacherService.getMyStudents();
    },

    // Assignment Submissions
    getStudentAssignments: async (studentId, statusFilter = null) => {
        const params = statusFilter ? { status_filter: statusFilter } : {};
        const response = await api.get(`/api/teacher/students/${studentId}/assignment-submissions`, { params });
        return response.data;
    },

    getAssignmentDetails: async (submissionId) => {
        const response = await api.get(`/api/teacher/assignments/${submissionId}/details`);
        return response.data;
    },

    getPendingAssignments: async () => {
        const response = await api.get('/api/teacher/assignments/pending');
        return response.data;
    }
};
