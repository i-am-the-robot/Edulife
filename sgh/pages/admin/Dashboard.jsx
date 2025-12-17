// Admin Dashboard
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminService } from '../../services/adminService';

export default function AdminDashboard() {
    const { user, logout } = useAuth();
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const data = await adminService.getSystemOverview();
            setStats(data);
        } catch (error) {
            console.error('Error loading stats:', error);
            // Set default stats if API fails
            setStats({
                total_schools: 0,
                total_teachers: 0,
                total_students: 0,
                active_sessions_today: 0
            });
        } finally {
            setLoading(false);
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
                        <h1 className="text-2xl font-bold text-gray-800">EduLife Admin Portal</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-gray-700">Welcome, {user?.full_name || user?.email}!</span>
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
                    <h2 className="text-3xl font-bold mb-2">Admin Dashboard</h2>
                    <p className="text-lg opacity-90">Manage your entire EduLife system from here</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Total Schools</p>
                                <p className="text-3xl font-bold text-indigo-600">{stats?.total_schools || 0}</p>
                            </div>
                            <div className="text-4xl">🏫</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Total Teachers</p>
                                <p className="text-3xl font-bold text-purple-600">{stats?.total_teachers || 0}</p>
                            </div>
                            <div className="text-4xl">👨‍🏫</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Total Students</p>
                                <p className="text-3xl font-bold text-blue-600">{stats?.total_students || 0}</p>
                            </div>
                            <div className="text-4xl">👨‍🎓</div>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl p-6 shadow-md">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-600 text-sm">Active Today</p>
                                <p className="text-3xl font-bold text-green-600">{stats?.active_sessions_today || 0}</p>
                            </div>
                            <div className="text-4xl">📊</div>
                        </div>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Link
                        to="/admin/schools"
                        className="bg-white rounded-xl p-8 shadow-md hover:shadow-xl transition group"
                    >
                        <div className="flex items-center gap-4">
                            <div className="text-5xl">🏫</div>
                            <div>
                                <h3 className="text-xl font-bold text-gray-800 group-hover:text-indigo-600 transition">
                                    Manage Schools
                                </h3>
                                <p className="text-gray-600 mt-1">Create and manage schools</p>
                            </div>
                        </div>
                    </Link>

                    <Link
                        to="/admin/teachers"
                        className="bg-white rounded-xl p-8 shadow-md hover:shadow-xl transition group"
                    >
                        <div className="flex items-center gap-4">
                            <div className="text-5xl">👨‍🏫</div>
                            <div>
                                <h3 className="text-xl font-bold text-gray-800 group-hover:text-purple-600 transition">
                                    Manage Teachers
                                </h3>
                                <p className="text-gray-600 mt-1">Register and manage teachers</p>
                            </div>
                        </div>
                    </Link>

                    <Link
                        to="/admin/students"
                        className="bg-white rounded-xl p-8 shadow-md hover:shadow-xl transition group"
                    >
                        <div className="flex items-center gap-4">
                            <div className="text-5xl">👨‍🎓</div>
                            <div>
                                <h3 className="text-xl font-bold text-gray-800 group-hover:text-blue-600 transition">
                                    Manage Students
                                </h3>
                                <p className="text-gray-600 mt-1">Register and manage students</p>
                            </div>
                        </div>
                    </Link>

                    <Link
                        to="/admin/change-password"
                        className="bg-white rounded-xl p-8 shadow-md hover:shadow-xl transition group"
                    >
                        <div className="flex items-center gap-4">
                            <div className="text-5xl">🔒</div>
                            <div>
                                <h3 className="text-xl font-bold text-gray-800 group-hover:text-green-600 transition">
                                    Change Password
                                </h3>
                                <p className="text-gray-600 mt-1">Update your password</p>
                            </div>
                        </div>
                    </Link>
                </div>

                {/* Info Box */}
                <div className="mt-8 bg-blue-50 border-l-4 border-blue-500 p-6 rounded">
                    <h3 className="font-semibold text-blue-900 mb-2">Getting Started</h3>
                    <ol className="list-decimal list-inside space-y-2 text-blue-800">
                        <li>Create a school to get an app_key</li>
                        <li>Register teachers using the school's app_key</li>
                        <li>Teachers can then register students</li>
                        <li>Students can start learning with AI!</li>
                    </ol>
                </div>
            </main>
        </div>
    );
}
