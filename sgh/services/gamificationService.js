// Gamification API Service
import api from './api';

export const gamificationService = {
    // Get all achievements with unlock status
    getAchievements: async () => {
        const response = await api.get('/api/student/achievements');
        return response.data;
    },

    // Get power-up inventory
    getPowerUps: async () => {
        const response = await api.get('/api/student/powerups');
        return response.data;
    },

    // Use a power-up
    usePowerUp: async (powerUpId) => {
        const response = await api.post(`/api/student/powerups/${powerUpId}/use`);
        return response.data;
    }
};
