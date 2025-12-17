// Teacher Dashboard Home
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherService } from '../../services/teacherService';

export default function TeacherDashboard() {
    const { user, logout } = useAuth();
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        onTrack: 0,
        needsAttention: 0,
        excelling: 0,
        inactive: 0,
    });
    const [pendingAssignments, setPendingAssignments] = useState({ pending_count: 0, recent_submissions: [] });

    useEffect(() => {
        loadStudents();
        loadPendingAssignments();
    }, []);

    const loadStudents = async () => {
        try {
            const data = await teacherService.getMyStudents();
            setStudents(data);
            calculateStats(data);
        } catch (error) {
            console.error('Error loading students:', error);
        } finally {
            setLoading(false);
        }
    };

    const calculateStats = (studentList) => {
        const stats = {
            onTrack: 0,
            needsAttention: 0,
            excelling: 0,
            inactive: 0,
        };

        studentList.forEach((student) => {
            const engagement = student.engagement_score || 0;
            const testSuccess = student.test_success_rate || 0;

            if (engagement < 20) {
                stats.inactive++;
            } else if (testSuccess >= 80 && engagement >= 70) {
                stats.excelling++;
            } else if (engagement >= 70) {
                stats.onTrack++;
            } else {
                stats.needsAttention++;
            }
        });

        setStats(stats);
    };

    const loadPendingAssignments = async () => {
        try {
            const data = await teacherService.getPendingAssignments();
            setPendingAssignments(data);
        } catch (error) {
            console.error('Error loading pending assignments:', error);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">EduLife Teacher Portal</h1>
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
                {/* Welcome Section */}
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 text-white mb-8">
                    <h2 className="text-3xl font-bold mb-2">Welcome back, {user?.full_name}!</h2>
                    <p className="text-lg opacity-90">
                        You have {students.length} student{students.length !== 1 ? 's' : ''} to support today.
                    </p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-green-500">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">On Track</p>
                                <p className="text-3xl font-bold text-green-600">{stats.onTrack}</p>
                            </div>
                            <div className="text-4xl">🟢</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-orange-500">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Needs Attention</p>
                                <p className="text-3xl font-bold text-orange-600">{stats.needsAttention}</p>
                            </div>
                            <div className="text-4xl">🟡</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-blue-500">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Excelling</p>
                                <p className="text-3xl font-bold text-blue-600">{stats.excelling}</p>
                            </div>
                            <div className="text-4xl">🔵</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-gray-400">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Inactive</p>
                                <p className="text-3xl font-bold text-gray-600">{stats.inactive}</p>
                            </div>
                            <div className="text-4xl">⚪</div>
                        </div>
                    </div>
                </div>

                {/* Pending Assignments Section */}
                {pendingAssignments.pending_count > 0 && (
                    <div className="bg-white rounded-xl shadow-md p-6 mb-8">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                                <span>📝</span>
                                Pending Assignment Reviews
                            </h3>
                            <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">
                                {pendingAssignments.pending_count} pending
                            </span>
                        </div>
                        <div className="space-y-3">
                            {pendingAssignments.recent_submissions.map((submission) => (
                                <Link
                                    key={submission.submission_id}
                                    to={`/teacher/students/${submission.student_id}`}
                                    className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition border border-gray-200"
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <p className="font-medium text-gray-800">{submission.student_name}</p>
                                            <p className="text-sm text-gray-600 mt-1">{submission.task_title}</p>
                                        </div>
                                        <div className="text-right ml-4">
                                            <p className="text-lg font-bold text-green-600">
                                                {submission.final_score !== null ? `${submission.final_score}%` : 'N/A'}
                                            </p>
                                            <p className="text-xs text-gray-500 mt-1">
                                                {new Date(submission.completed_at).toLocaleDateString()}
                                            </p>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                )}

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <Link
                        to="/teacher/students"
                        className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition group border border-gray-100"
                    >
                        <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition">
                            <span className="text-2xl">👥</span>
                        </div>
                        <h3 className="text-xl font-bold text-gray-800 mb-2">My Students</h3>
                        <p className="text-gray-600 mb-4">View and monitor all students</p>
                        <span className="text-indigo-600 font-medium group-hover:underline">View Students →</span>
                    </Link>

                    <Link
                        to="/teacher/students"
                        className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition group border border-gray-100"
                    >
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition">
                            <span className="text-2xl">➕</span>
                        </div>
                        <h3 className="text-xl font-bold text-gray-800 mb-2">Register Student</h3>
                        <p className="text-gray-600 mb-4">Add new students</p>
                        <span className="text-indigo-600 font-medium group-hover:underline">Register →</span>
                    </Link>


                    {/* Task Scheduler */}
                    <Link to="/teacher/tasks" className="block p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition group border border-gray-100">
                        <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition">
                            <span className="text-2xl">📅</span>
                        </div>
                        <h3 className="text-xl font-bold text-gray-800 mb-2">Task Scheduler</h3>
                        <p className="text-gray-600 mb-4">
                            Assign homework and tasks to students.
                        </p>
                        <span className="text-indigo-600 font-medium group-hover:underline">Manage Tasks →</span>
                    </Link>

                    {/* Syllabus Upload */}
                    <Link to="/teacher/syllabus" className="block p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition group border border-gray-100">
                        <div className="w-12 h-12 bg-pink-100 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition">
                            <span className="text-2xl">📝</span>
                        </div>
                        <h3 className="text-xl font-bold text-gray-800 mb-2">Update Syllabus</h3>
                        <p className="text-gray-600 mb-4">
                            Upload or update the school syllabus context.
                        </p>
                        <span className="text-indigo-600 font-medium group-hover:underline">Upload Syllabus →</span>
                    </Link>

                    <Link
                        to="/teacher/change-password"
                        className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition group border border-gray-100"
                    >
                        <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition">
                            <span className="text-2xl">🔒</span>
                        </div>
                        <h3 className="text-xl font-bold text-gray-800 mb-2">Change Password</h3>
                        <p className="text-gray-600 mb-4">Update your password</p>
                        <span className="text-indigo-600 font-medium group-hover:underline">Update →</span>
                    </Link>
                </div>
            </main>
        </div>
    );
}
