// Metrics API Service
import api from './api';

export const metricsService = {
    // Get flow state analysis
    getFlowAnalysis: async () => {
        const response = await api.get('/api/student/metrics/flow-analysis');
        return response.data;
    }
};
