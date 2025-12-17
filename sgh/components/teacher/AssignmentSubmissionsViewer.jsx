// Assignment Submissions Viewer Component
import { useState } from 'react';

export default function AssignmentSubmissionsViewer({ assignments, loading, onViewDetails }) {
    const getStatusBadge = (status) => {
        const badges = {
            'completed': { color: 'bg-green-100 text-green-800', icon: '✅', label: 'Completed' },
            'in_progress': { color: 'bg-blue-100 text-blue-800', icon: '🔄', label: 'In Progress' },
            'quiz_pending': { color: 'bg-yellow-100 text-yellow-800', icon: '⏳', label: 'Quiz Pending' }
        };
        return badges[status] || { color: 'bg-gray-100 text-gray-800', icon: '❓', label: status };
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

    if (loading) {
        return (
            <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading assignments...</p>
            </div>
        );
    }

    if (!assignments || assignments.length === 0) {
        return (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
                <div className="text-6xl mb-4">📝</div>
                <p className="text-gray-600 text-lg">No assignment submissions yet</p>
                <p className="text-gray-500 text-sm mt-2">Assignments will appear here once students start working on them</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {assignments.map((assignment) => {
                const statusBadge = getStatusBadge(assignment.status);

                return (
                    <div
                        key={assignment.id}
                        className="bg-white rounded-lg shadow-sm hover:shadow-md transition p-6 border border-gray-100"
                    >
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex-1">
                                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                                    {assignment.task_title}
                                </h3>
                                <p className="text-sm text-gray-600 line-clamp-2">
                                    {assignment.task_description}
                                </p>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusBadge.color} flex items-center gap-1 ml-4`}>
                                <span>{statusBadge.icon}</span>
                                {statusBadge.label}
                            </span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                            <div>
                                <p className="text-xs text-gray-500 mb-1">Due Date</p>
                                <p className="text-sm font-medium text-gray-800">
                                    {formatDate(assignment.task_due_date)}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 mb-1">Started</p>
                                <p className="text-sm font-medium text-gray-800">
                                    {formatDate(assignment.started_at)}
                                </p>
                            </div>
                            {assignment.status === 'completed' && (
                                <>
                                    <div>
                                        <p className="text-xs text-gray-500 mb-1">Quiz Score</p>
                                        <p className="text-sm font-medium text-indigo-600">
                                            {assignment.quiz_score !== null ? `${assignment.quiz_score}%` : 'N/A'}
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-gray-500 mb-1">Final Score</p>
                                        <p className="text-sm font-medium text-green-600">
                                            {assignment.final_score !== null ? `${assignment.final_score}%` : 'N/A'}
                                        </p>
                                    </div>
                                </>
                            )}
                            {assignment.status === 'in_progress' && (
                                <div className="col-span-2">
                                    <p className="text-xs text-gray-500 mb-1">Progress</p>
                                    <p className="text-sm font-medium text-blue-600">
                                        {assignment.conversation_count} messages exchanged
                                    </p>
                                </div>
                            )}
                        </div>

                        {assignment.status === 'completed' && (
                            <div className="flex justify-between items-center pt-4 border-t border-gray-100">
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <span>📅</span>
                                    <span>Submitted: {formatDate(assignment.completed_at)}</span>
                                    {assignment.has_summary && (
                                        <>
                                            <span className="mx-2">•</span>
                                            <span>🤖 AI Summary Available</span>
                                        </>
                                    )}
                                </div>
                                <button
                                    onClick={() => onViewDetails(assignment.id)}
                                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium text-sm"
                                >
                                    View Details →
                                </button>
                            </div>
                        )}

                        {assignment.status === 'in_progress' && (
                            <div className="pt-4 border-t border-gray-100">
                                <p className="text-sm text-gray-600 italic">
                                    Student is currently working on this assignment
                                </p>
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
