// Timetable API Service
import api from './api';

export const timetableService = {
    // Get weekly timetable
    getTimetable: async (day = null) => {
        const params = day ? { day } : {};
        const response = await api.get('/api/student/timetable', { params });
        return response.data;
    },

    // Generate AI-recommended timetable
    generateTimetable: async () => {
        const response = await api.post('/api/student/timetable/generate');
        return response.data;
    },

    // Mark a slot as completed
    completeSlot: async (slotId) => {
        const response = await api.put(`/api/student/timetable/${slotId}/complete`);
        return response.data;
    }
};
