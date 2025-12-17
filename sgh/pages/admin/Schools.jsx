// School Management Page
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminService } from '../../services/adminService';

export default function SchoolsPage() {
    const { user, logout } = useAuth();
    const [schools, setSchools] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        location: '',
    });
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        loadSchools();
    }, []);

    const loadSchools = async () => {
        try {
            const data = await adminService.getSchools();
            setSchools(data);
        } catch (error) {
            console.error('Error loading schools:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setCreating(true);

        try {
            const newSchool = await adminService.createSchool(formData);
            setSuccess(`School created! App Key: ${newSchool.app_key}`);
            setFormData({ name: '', location: '' });
            setShowCreateForm(false);
            loadSchools();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create school');
        } finally {
            setCreating(false);
        }
    };

    const copyAppKey = (appKey) => {
        navigator.clipboard.writeText(appKey);
        alert('App Key copied to clipboard!');
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
                        <h1 className="text-2xl font-bold text-gray-800">School Management</h1>
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
                {/* Success/Error Messages */}
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

                {/* Create School Button */}
                <div className="mb-6">
                    <button
                        onClick={() => setShowCreateForm(!showCreateForm)}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-semibold"
                    >
                        {showCreateForm ? 'Cancel' : '+ Create New School'}
                    </button>
                </div>

                {/* Create School Form */}
                {showCreateForm && (
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">Create New School</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    School Name *
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    placeholder="e.g., Example High School"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Location *
                                </label>
                                <input
                                    type="text"
                                    value={formData.location}
                                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    placeholder="e.g., Lagos, Nigeria"
                                    required
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={creating}
                                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                            >
                                {creating ? 'Creating...' : 'Create School'}
                            </button>
                        </form>
                    </div>
                )}

                {/* Schools List */}
                <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-lg font-semibold text-gray-800">
                            All Schools ({schools.length})
                        </h2>
                    </div>

                    {loading ? (
                        <div className="text-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                            <p className="mt-4 text-gray-600">Loading schools...</p>
                        </div>
                    ) : schools.length === 0 ? (
                        <div className="text-center py-12">
                            <p className="text-gray-600">No schools created yet</p>
                            <p className="text-gray-500 text-sm mt-2">Click "Create New School" to get started</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {schools.map((school) => (
                                <div key={school.id} className="p-6 hover:bg-gray-50 transition">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <h3 className="text-lg font-semibold text-gray-800">{school.name}</h3>
                                            <p className="text-gray-600 mt-1">📍 {school.location}</p>
                                            <div className="mt-3 flex items-center gap-4">
                                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${school.is_active
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-gray-100 text-gray-800'
                                                    }`}>
                                                    {school.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                                <span className="text-sm text-gray-500">
                                                    Created: {new Date(school.created_at).toLocaleDateString()}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="ml-6">
                                            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                                                <p className="text-xs text-indigo-600 font-medium mb-1">App Key</p>
                                                <div className="flex items-center gap-2">
                                                    <code className="text-sm font-mono text-indigo-900 bg-white px-3 py-1 rounded border border-indigo-200">
                                                        {school.app_key}
                                                    </code>
                                                    <button
                                                        onClick={() => copyAppKey(school.app_key)}
                                                        className="px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition"
                                                    >
                                                        Copy
                                                    </button>
                                                </div>
                                                <p className="text-xs text-gray-600 mt-2">
                                                    Teachers need this to register
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Info Box */}
                <div className="mt-6 bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                    <h3 className="font-semibold text-blue-900 mb-2">About App Keys</h3>
                    <p className="text-blue-800 text-sm">
                        Each school has a unique app_key. Teachers must use this key when registering to be automatically
                        associated with the correct school. Keep these keys secure and only share them with authorized teachers.
                    </p>
                </div>
            </main>
        </div>
    );
}
