// Authentication Service
import api from './api';

export const authService = {
    // Admin login
    loginAdmin: async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await api.post('/api/auth/admin/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return response.data;
    },

    // Teacher login
    loginTeacher: async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await api.post('/api/auth/teacher/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return response.data;
    },

    // Student login (ID-based, no password)
    loginStudent: async (studentId, pin) => {
        const response = await api.post(`/api/auth/student/login?student_id=${studentId}&pin=${pin}`);
        return response.data;
    },

    // Register admin
    registerAdmin: async (data) => {
        const response = await api.post('/api/auth/admin/register', data);
        return response.data;
    },

    // Register teacher
    registerTeacher: async (data) => {
        const response = await api.post('/api/auth/teacher/register', data);
        return response.data;
    },

    // Get current user
    getCurrentUser: async () => {
        const response = await api.get('/api/auth/me');
        return response.data;
    },


};
