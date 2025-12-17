// Admin API Service
import api from './api';

export const adminService = {
    // School Management
    createSchool: async (data) => {
        const response = await api.post('/api/admin/schools', data);
        return response.data;
    },

    getSchools: async () => {
        const response = await api.get('/api/admin/schools');
        return response.data;
    },

    getSchool: async (schoolId) => {
        const response = await api.get(`/api/admin/schools/${schoolId}`);
        return response.data;
    },

    updateSchool: async (schoolId, data) => {
        const response = await api.put(`/api/admin/schools/${schoolId}`, data);
        return response.data;
    },

    deactivateSchool: async (schoolId) => {
        const response = await api.delete(`/api/admin/schools/${schoolId}`);
        return response.data;
    },

    // Teacher Management
    registerTeacher: async (data) => {
        const response = await api.post('/api/admin/teachers', data);
        return response.data;
    },

    getTeachers: async () => {
        const response = await api.get('/api/admin/teachers');
        return response.data;
    },

    // Student Management
    registerStudent: async (data) => {
        const response = await api.post('/api/admin/students', data);
        return response.data;
    },

    getStudents: async () => {
        const response = await api.get('/api/admin/students');
        return response.data;
    },

    // Analytics
    getSystemOverview: async () => {
        const response = await api.get('/api/admin/analytics/overview');
        return response.data;
    },

    // Password change
    changePassword: async (data) => {
        const response = await api.put('/api/admin/change-password', data);
        return response.data;
    },
};
