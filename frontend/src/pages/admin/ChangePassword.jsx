// Admin Password Change Page
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminService } from '../../services/adminService';

export default function ChangePassword() {
    const { user, logout } = useAuth();
    const [formData, setFormData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        // Validate passwords
        if (formData.newPassword.length < 8) {
            setError('New password must be at least 8 characters long');
            return;
        }

        if (formData.newPassword !== formData.confirmPassword) {
            setError('New passwords do not match');
            return;
        }

        setLoading(true);

        try {
            await adminService.changePassword({
                current_password: formData.currentPassword,
                new_password: formData.newPassword,
            });
            setSuccess('Password changed successfully!');
            setFormData({
                currentPassword: '',
                newPassword: '',
                confirmPassword: '',
            });
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to change password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Link to="/admin/dashboard" className="text-indigo-600 hover:text-indigo-800">
                            ← Back to Dashboard
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-800">Change Password</h1>
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
            <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="bg-white rounded-lg shadow p-8">
                    <div className="mb-6">
                        <h2 className="text-xl font-bold text-gray-800 mb-2">Update Your Password</h2>
                        <p className="text-gray-600">
                            Choose a strong password to keep your account secure.
                        </p>
                    </div>

                    {success && (
                        <div className="mb-6 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg">
                            {success}
                        </div>
                    )}

                    {error && (
                        <div className="mb-6 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Current Password *
                            </label>
                            <input
                                type="password"
                                value={formData.currentPassword}
                                onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                New Password *
                            </label>
                            <input
                                type="password"
                                value={formData.newPassword}
                                onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                minLength="8"
                                required
                            />
                            <p className="text-xs text-gray-500 mt-1">Minimum 8 characters</p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Confirm New Password *
                            </label>
                            <input
                                type="password"
                                value={formData.confirmPassword}
                                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                required
                            />
                        </div>

                        <div className="flex gap-4">
                            <button
                                type="submit"
                                disabled={loading}
                                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                            >
                                {loading ? 'Changing Password...' : 'Change Password'}
                            </button>
                            <Link
                                to="/admin/dashboard"
                                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                            >
                                Cancel
                            </Link>
                        </div>
                    </form>

                    <div className="mt-8 bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                        <h3 className="font-semibold text-blue-900 mb-2">Password Tips</h3>
                        <ul className="text-blue-800 text-sm space-y-1">
                            <li>• Use at least 8 characters</li>
                            <li>• Include uppercase and lowercase letters</li>
                            <li>• Add numbers and special characters</li>
                            <li>• Avoid common words or personal information</li>
                        </ul>
                    </div>
                </div>
            </main>
        </div>
    );
}
