// Student Profile Page with Tabs
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherService } from '../../services/teacherService';
import ChatHistoryViewer from '../../components/teacher/ChatHistoryViewer';
import TestResultsViewer from '../../components/teacher/TestResultsViewer';
import AssignmentSubmissionsViewer from '../../components/teacher/AssignmentSubmissionsViewer';
import AssignmentDetailModal from '../../components/teacher/AssignmentDetailModal';

export default function StudentProfile() {
    const { studentId } = useParams();
    const { user, logout } = useAuth();
    const [student, setStudent] = useState(null);
    const [chatHistory, setChatHistory] = useState([]);
    const [testResults, setTestResults] = useState([]);
    const [assignments, setAssignments] = useState([]);
    const [activeTab, setActiveTab] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [dataLoading, setDataLoading] = useState(false);
    const [selectedSubmissionId, setSelectedSubmissionId] = useState(null);

    useEffect(() => {
        loadStudentData();
    }, [studentId]);

    useEffect(() => {
        if (activeTab === 'chat' && chatHistory.length === 0) {
            loadChatHistory();
        } else if (activeTab === 'tests' && testResults.length === 0) {
            loadTestResults();
        } else if (activeTab === 'assignments' && assignments.length === 0) {
            loadAssignments();
        }
    }, [activeTab]);

    const loadStudentData = async () => {
        try {
            const data = await teacherService.getStudentDetail(studentId);
            setStudent(data);
        } catch (error) {
            console.error('Error loading student:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadChatHistory = async () => {
        setDataLoading(true);
        try {
            const data = await teacherService.getStudentChatHistory(studentId);
            setChatHistory(data);
        } catch (error) {
            console.error('Error loading chat history:', error);
        } finally {
            setDataLoading(false);
        }
    };

    const loadTestResults = async () => {
        setDataLoading(true);
        try {
            const data = await teacherService.getStudentTestResults(studentId);
            setTestResults(data);
        } catch (error) {
            console.error('Error loading test results:', error);
        } finally {
            setDataLoading(false);
        }
    };

    const loadAssignments = async () => {
        setDataLoading(true);
        try {
            const data = await teacherService.getStudentAssignments(studentId);
            setAssignments(data);
        } catch (error) {
            console.error('Error loading assignments:', error);
        } finally {
            setDataLoading(false);
        }
    };

    const handleViewAssignmentDetails = (submissionId) => {
        setSelectedSubmissionId(submissionId);
    };


    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading student profile...</p>
                </div>
            </div>
        );
    }

    if (!student) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-gray-600">Student not found</p>
                    <Link to="/teacher/students" className="text-indigo-600 hover:text-indigo-800 mt-4 inline-block">
                        ← Back to Students
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Link to="/teacher/students" className="text-indigo-600 hover:text-indigo-800">
                            ← Back to Students
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-800">{student.full_name}</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-gray-700">Welcome, {user?.full_name || user?.name || user?.email || 'Teacher'}!</span>
                        <button
                            onClick={logout}
                            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Student Info Card */}
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div>
                            <p className="text-sm text-gray-600">Class</p>
                            <p className="text-lg font-semibold text-gray-800">{student.student_class}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-600">Age</p>
                            <p className="text-lg font-semibold text-gray-800">{student.age} years</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-600">Hobby</p>
                            <p className="text-lg font-semibold text-gray-800">{student.hobby}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-600">Personality</p>
                            <p className="text-lg font-semibold text-gray-800">{student.personality}</p>
                        </div>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <p className="text-sm text-gray-600 mb-1">Engagement Score</p>
                        <p className="text-3xl font-bold text-indigo-600">{student.engagement_score || 0}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <p className="text-sm text-gray-600 mb-1">Total Sessions</p>
                        <p className="text-3xl font-bold text-purple-600">{student.total_sessions || 0}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <p className="text-sm text-gray-600 mb-1">Test Success Rate</p>
                        <p className="text-3xl font-bold text-green-600">{student.test_success_rate || 0}%</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="bg-white rounded-lg shadow">
                    <div className="border-b border-gray-200">
                        <nav className="flex -mb-px">
                            <button
                                onClick={() => setActiveTab('overview')}
                                className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeTab === 'overview'
                                    ? 'border-indigo-600 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                Overview
                            </button>
                            <button
                                onClick={() => setActiveTab('chat')}
                                className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeTab === 'chat'
                                    ? 'border-indigo-600 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                Chat History
                            </button>
                            <button
                                onClick={() => setActiveTab('tests')}
                                className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeTab === 'tests'
                                    ? 'border-indigo-600 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                Test Results
                            </button>
                            <button
                                onClick={() => setActiveTab('assignments')}
                                className={`px-6 py-4 text-sm font-medium border-b-2 transition ${activeTab === 'assignments'
                                    ? 'border-indigo-600 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                Assignments
                            </button>
                        </nav>
                    </div>

                    <div className="p-6">
                        {activeTab === 'overview' && (
                            <div className="space-y-6">
                                <div>
                                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Student Information</h3>
                                    <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                                        <p><span className="font-medium">Student ID:</span> {student.student_id}</p>
                                        <p><span className="font-medium">Login Frequency:</span> {student.login_frequency || 0} times/week</p>
                                        <p><span className="font-medium">Last Active:</span> {student.last_active ? new Date(student.last_active).toLocaleString() : 'Never'}</p>
                                    </div>
                                </div>
                                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                                    <p className="text-sm text-blue-800">
                                        <strong>Note:</strong> This student's learning profile is adapted to their needs.
                                        All interactions are personalized while maintaining inclusivity.
                                    </p>
                                </div>
                            </div>
                        )}

                        {activeTab === 'chat' && (
                            <ChatHistoryViewer chatHistory={chatHistory} loading={dataLoading} />
                        )}

                        {activeTab === 'tests' && (
                            <TestResultsViewer testResults={testResults} loading={dataLoading} />
                        )}

                        {activeTab === 'assignments' && (
                            <AssignmentSubmissionsViewer
                                assignments={assignments}
                                loading={dataLoading}
                                onViewDetails={handleViewAssignmentDetails}
                            />
                        )}
                    </div>
                </div>
            </main>

            {/* Assignment Detail Modal */}
            {selectedSubmissionId && (
                <AssignmentDetailModal
                    submissionId={selectedSubmissionId}
                    onClose={() => setSelectedSubmissionId(null)}
                />
            )}
        </div>
    );
}
