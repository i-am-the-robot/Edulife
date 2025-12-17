// Student Dashboard Page
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { studentService } from '../../services/studentService';
import PowerUpInventory from '../../components/student/PowerUpInventory';

export default function StudentDashboard() {
    const { user, logout } = useAuth();
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadProfile();
    }, []);

    const loadProfile = async () => {
        try {
            const data = await studentService.getProfile();
            setProfile(data);
        } catch (error) {
            console.error('Error loading profile:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">EduLife</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-gray-700">Hi, {profile?.full_name || user?.full_name}! 👋</span>
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
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl p-8 text-white mb-8">
                    <h2 className="text-3xl font-bold mb-2">Welcome back, {profile?.full_name}!</h2>
                    <p className="text-lg opacity-90">Ready to learn something amazing today? 🚀</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Engagement Score</p>
                                <p className="text-3xl font-bold text-blue-600">
                                    {profile?.engagement_score || 0}%
                                </p>
                            </div>
                            <div className="text-4xl">📊</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Total Sessions</p>
                                <p className="text-3xl font-bold text-purple-600">
                                    {profile?.total_sessions || 0}
                                </p>
                            </div>
                            <div className="text-4xl">💬</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Achievements</p>
                                <p className="text-3xl font-bold text-green-600">
                                    {profile?.achievements_count || 0}
                                </p>
                            </div>
                            <div className="text-4xl">🏆</div>
                        </div>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <Link
                        to="/student/chat"
                        className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition group flex items-center gap-4"
                    >
                        <div className="text-5xl">🤖</div>
                        <div>
                            <h3 className="text-xl font-bold text-gray-800 group-hover:text-blue-600 transition">
                                Chat with AI Buddy
                            </h3>
                            <p className="text-gray-600 mt-1">Ask questions and learn together!</p>
                        </div>
                    </Link>

                    <Link
                        to="/student/chat-history"
                        className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition group flex items-center gap-4"
                    >
                        <div className="text-5xl">📚</div>
                        <div>
                            <h3 className="text-xl font-bold text-gray-800 group-hover:text-purple-600 transition">
                                My Chat History
                            </h3>
                            <p className="text-gray-600 mt-1">Review past conversations</p>
                        </div>
                    </Link>

                    {/* Tasks / Assignments */}
                    <Link to="/student/tasks" className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition group flex items-center gap-4">
                        <div className="text-5xl">📝</div>
                        <div>
                            <h3 className="text-xl font-bold text-gray-800 group-hover:text-indigo-600 transition">
                                My Assignments
                            </h3>
                            <p className="text-gray-600 mt-1">
                                View and complete your tasks
                            </p>
                        </div>
                    </Link>

                    <Link
                        to="/student/achievements"
                        className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition group flex items-center gap-4"
                    >
                        <div className="text-5xl">🌟</div>
                        <div>
                            <h3 className="text-xl font-bold text-gray-800 group-hover:text-green-600 transition">
                                My Achievements
                            </h3>
                            <p className="text-gray-600 mt-1">See your badges and progress</p>
                        </div>
                    </Link>

                    <Link
                        to="/student/schedule"
                        className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition group flex items-center gap-4"
                    >
                        <div className="text-5xl">📅</div>
                        <div>
                            <h3 className="text-xl font-bold text-gray-800 group-hover:text-orange-600 transition">
                                My Schedule
                            </h3>
                            <p className="text-gray-600 mt-1">View upcoming tutorials</p>
                        </div>
                    </Link>
                </div>

                {/* Power-Ups Quick Access */}
                <div className="mt-8">
                    <PowerUpInventory />
                </div>
            </main>
        </div>
    );
}
