import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import AchievementBadge from '../../components/student/AchievementBadge';

export default function Achievements() {
    const { user, logout } = useAuth();

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Link to="/student/dashboard" className="text-indigo-600 hover:text-indigo-800">
                            ← Back to Dashboard
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-800">My Achievements</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-gray-700">Hi, {user?.full_name}!</span>
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
                {/* Stats Banner */}
                <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl p-8 text-white mb-8">
                    <h2 className="text-3xl font-bold mb-2">Keep Up the Great Work!</h2>
                    <p className="text-lg opacity-90">
                        Unlock more achievements by staying consistent and learning new topics! 🚀
                    </p>
                </div>

                {/* Gamification Dashboard */}
                <div className="space-y-8">
                    {/* Achievements Grid */}
                    <AchievementBadge fullPage={true} />
                </div>

                {/* Upcoming Achievements */}
                <div className="mt-12 bg-blue-50 border-l-4 border-blue-500 p-6 rounded">
                    <h3 className="font-semibold text-blue-900 mb-2">🎯 Keep Going!</h3>
                    <p className="text-blue-800 text-sm">
                        Continue chatting, taking tests, and staying consistent to unlock more achievements!
                        Every conversation and every test brings you closer to your next reward.
                    </p>
                </div>
            </main>
        </div>
    );
}
