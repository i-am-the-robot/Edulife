// Assignment Detail Modal Component
import { useState, useEffect } from 'react';
import { teacherService } from '../../services/teacherService';

export default function AssignmentDetailModal({ submissionId, onClose }) {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeSection, setActiveSection] = useState('summary');

    useEffect(() => {
        loadDetails();
    }, [submissionId]);

    const loadDetails = async () => {
        try {
            setLoading(true);
            const data = await teacherService.getAssignmentDetails(submissionId);
            setDetails(data);
        } catch (error) {
            console.error('Error loading assignment details:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const renderQuizSection = () => {
        if (!details.quiz.questions || details.quiz.questions.length === 0) {
            return <p className="text-gray-500 italic">No quiz questions available</p>;
        }

        return (
            <div className="space-y-4">
                <div className="bg-indigo-50 rounded-lg p-4 mb-4">
                    <p className="text-sm text-indigo-800">
                        <strong>Quiz Score:</strong> {details.quiz.score !== null ? `${details.quiz.score}%` : 'Not graded'}
                    </p>
                </div>
                {details.quiz.questions.map((question, idx) => (
                    <div key={idx} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-start gap-3 mb-3">
                            <span className="flex-shrink-0 w-8 h-8 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-sm">
                                {idx + 1}
                            </span>
                            <div className="flex-1">
                                <p className="font-medium text-gray-800">{question.question}</p>
                                {question.type === 'multiple_choice' && question.options && (
                                    <div className="mt-2 space-y-1">
                                        {question.options.map((option, optIdx) => (
                                            <p key={optIdx} className="text-sm text-gray-600">
                                                {option}
                                            </p>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="ml-11 space-y-2">
                            <div className="bg-blue-50 rounded p-3">
                                <p className="text-xs text-gray-600 mb-1">Student Answer:</p>
                                <p className="text-sm text-gray-800">
                                    {details.quiz.answers[idx] || 'No answer provided'}
                                </p>
                            </div>
                            <div className="bg-green-50 rounded p-3">
                                <p className="text-xs text-gray-600 mb-1">Correct Answer:</p>
                                <p className="text-sm text-gray-800">{question.correct_answer}</p>
                            </div>
                            {details.quiz.answers[idx] === question.correct_answer ? (
                                <p className="text-sm text-green-600 font-medium">✅ Correct</p>
                            ) : (
                                <p className="text-sm text-red-600 font-medium">❌ Incorrect</p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    const renderFinalAssessment = () => {
        if (!details.final_assessment.questions || details.final_assessment.questions.length === 0) {
            return <p className="text-gray-500 italic">No final assessment available</p>;
        }

        return (
            <div className="space-y-4">
                <div className="bg-green-50 rounded-lg p-4 mb-4">
                    <p className="text-sm text-green-800">
                        <strong>Final Score:</strong> {details.final_assessment.score !== null ? `${details.final_assessment.score}%` : 'Not graded'}
                    </p>
                </div>
                {details.final_assessment.questions.map((question, idx) => (
                    <div key={idx} className="bg-gray-50 rounded-lg p-4">
                        <div className="flex items-start gap-3 mb-3">
                            <span className="flex-shrink-0 w-8 h-8 bg-green-100 text-green-600 rounded-full flex items-center justify-center font-bold text-sm">
                                {idx + 1}
                            </span>
                            <div className="flex-1">
                                <p className="font-medium text-gray-800">{question.question}</p>
                                {question.type === 'multiple_choice' && question.options && (
                                    <div className="mt-2 space-y-1">
                                        {question.options.map((option, optIdx) => (
                                            <p key={optIdx} className="text-sm text-gray-600">
                                                {option}
                                            </p>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="ml-11 space-y-2">
                            <div className="bg-blue-50 rounded p-3">
                                <p className="text-xs text-gray-600 mb-1">Student Answer:</p>
                                <p className="text-sm text-gray-800">
                                    {details.final_assessment.answers[idx] || 'No answer provided'}
                                </p>
                            </div>
                            <div className="bg-green-50 rounded p-3">
                                <p className="text-xs text-gray-600 mb-1">Correct Answer:</p>
                                <p className="text-sm text-gray-800">{question.correct_answer}</p>
                            </div>
                            {details.final_assessment.answers[idx] === question.correct_answer ? (
                                <p className="text-sm text-green-600 font-medium">✅ Correct</p>
                            ) : (
                                <p className="text-sm text-red-600 font-medium">❌ Incorrect</p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    if (loading) {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full p-8">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Loading assignment details...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (!details) {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full p-8">
                    <p className="text-center text-gray-600">Failed to load assignment details</p>
                    <button
                        onClick={onClose}
                        className="mt-4 mx-auto block px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                    >
                        Close
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-xl shadow-2xl max-w-5xl w-full my-8">
                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 rounded-t-xl">
                    <div className="flex justify-between items-start">
                        <div className="flex-1">
                            <h2 className="text-2xl font-bold mb-2">{details.task.title}</h2>
                            <p className="text-sm opacity-90 mb-3">{details.task.description}</p>
                            <div className="flex items-center gap-4 text-sm">
                                <span>👤 {details.student.full_name}</span>
                                <span>•</span>
                                <span>📚 {details.student.student_class}</span>
                                <span>•</span>
                                <span>📅 Due: {formatDate(details.task.due_date)}</span>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-2 transition"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-4 gap-4 p-6 bg-gray-50 border-b">
                    <div className="text-center">
                        <p className="text-2xl font-bold text-indigo-600">
                            {details.quiz.score !== null ? `${details.quiz.score}%` : 'N/A'}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">Quiz Score</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">
                            {details.final_assessment.score !== null ? `${details.final_assessment.score}%` : 'N/A'}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">Final Score</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">
                            {details.time_spent_minutes || 'N/A'}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">Minutes Spent</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-purple-600">
                            {details.conversation_count}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">Messages</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="border-b border-gray-200">
                    <nav className="flex -mb-px">
                        <button
                            onClick={() => setActiveSection('summary')}
                            className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeSection === 'summary'
                                    ? 'border-indigo-600 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            📊 Summary
                        </button>
                        <button
                            onClick={() => setActiveSection('quiz')}
                            className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeSection === 'quiz'
                                    ? 'border-indigo-600 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            📝 Periodic Quiz
                        </button>
                        <button
                            onClick={() => setActiveSection('final')}
                            className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeSection === 'final'
                                    ? 'border-indigo-600 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            🎯 Final Assessment
                        </button>
                        <button
                            onClick={() => setActiveSection('conversation')}
                            className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeSection === 'conversation'
                                    ? 'border-indigo-600 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            💬 Conversation
                        </button>
                    </nav>
                </div>

                {/* Content */}
                <div className="p-6 max-h-96 overflow-y-auto">
                    {activeSection === 'summary' && (
                        <div className="space-y-4">
                            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
                                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                                    <span>🤖</span>
                                    AI-Generated Summary
                                </h3>
                                {details.summary ? (
                                    <p className="text-gray-700 whitespace-pre-wrap">{details.summary}</p>
                                ) : (
                                    <p className="text-gray-500 italic">No summary available</p>
                                )}
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <p className="text-sm text-gray-600 mb-1">Started</p>
                                    <p className="font-medium text-gray-800">{formatDate(details.started_at)}</p>
                                </div>
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <p className="text-sm text-gray-600 mb-1">Completed</p>
                                    <p className="font-medium text-gray-800">{formatDate(details.completed_at)}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeSection === 'quiz' && renderQuizSection()}

                    {activeSection === 'final' && renderFinalAssessment()}

                    {activeSection === 'conversation' && (
                        <div className="space-y-3">
                            {details.conversation_history && details.conversation_history.length > 0 ? (
                                details.conversation_history.map((msg, idx) => (
                                    <div key={idx} className="space-y-2">
                                        <div className="bg-blue-50 rounded-lg p-3">
                                            <p className="text-xs text-gray-600 mb-1">
                                                Student • {formatDate(msg.timestamp)}
                                            </p>
                                            <p className="text-sm text-gray-800">{msg.student_message}</p>
                                        </div>
                                        <div className="bg-gray-50 rounded-lg p-3 ml-4">
                                            <p className="text-xs text-gray-600 mb-1">AI Response</p>
                                            <p className="text-sm text-gray-800">{msg.ai_response}</p>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="text-gray-500 italic text-center py-8">No conversation history available</p>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 bg-gray-50 rounded-b-xl border-t flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
