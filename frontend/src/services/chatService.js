// Chat API Service
import api from './api';

export const chatService = {
    // Send message to AI
    sendMessage: async (studentId, message, subject = null, sessionId = null) => {
        const response = await api.post('/api/chat/message', {
            student_id: studentId,
            message,
            subject,
            session_id: sessionId,
        });
        return response.data;
    },

    // Submit test answer
    submitTestAnswer: async (testResultId, studentAnswer) => {
        const response = await api.post('/api/chat/test/submit', {
            test_result_id: testResultId,
            student_answer: studentAnswer,
        });
        return response.data;
    },

    // Get test question
    getTest: async (testId) => {
        const response = await api.get(`/api/chat/test/${testId}`);
        return response.data;
    },
};
