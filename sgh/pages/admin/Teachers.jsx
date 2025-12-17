// Teacher Registration Page (Admin)
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminService } from '../../services/adminService';

export default function TeachersPage() {
    const { user, logout } = useAuth();
    const [teachers, setTeachers] = useState([]);
    const [schools, setSchools] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        password: '',
        app_key: '',
        address: '',
        phone: '',
        role: 'Teacher',
        subjects: '',
        specializations: '',
        years_experience: 0,
    });
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [teachersData, schoolsData] = await Promise.all([
                adminService.getTeachers(),
                adminService.getSchools(),
            ]);
            setTeachers(teachersData);
            setSchools(schoolsData);
        } catch (error) {
            console.error('Error loading data:', error);
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
            // Send data to backend
            await adminService.registerTeacher(formData);

            setSuccess('Teacher registered successfully!');
            setFormData({
                full_name: '',
                email: '',
                password: '',
                app_key: '',
                address: '',
                phone: '',
                role: 'Teacher',
                subjects: '',
                specializations: '',
                years_experience: 0,
            });
            setShowCreateForm(false);
            loadData();
        } catch (err) {
            console.error('Registration error:', err);
            setError(err.response?.data?.detail || 'Failed to register teacher');
        } finally {
            setCreating(false);
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
                        <h1 className="text-2xl font-bold text-gray-800">Teacher Management</h1>
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

                {/* Create Teacher Button */}
                <div className="mb-6">
                    <button
                        onClick={() => setShowCreateForm(!showCreateForm)}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-semibold"
                    >
                        {showCreateForm ? 'Cancel' : '+ Register New Teacher'}
                    </button>
                </div>

                {/* Create Teacher Form */}
                {showCreateForm && (
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">Register New Teacher</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Full Name *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.full_name}
                                        onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Email *
                                    </label>
                                    <input
                                        type="email"
                                        value={formData.email}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Password *
                                    </label>
                                    <input
                                        type="password"
                                        value={formData.password}
                                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        School App Key *
                                    </label>
                                    <select
                                        value={formData.app_key}
                                        onChange={(e) => setFormData({ ...formData, app_key: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                    >
                                        <option value="">Select School</option>
                                        {schools.map((school) => (
                                            <option key={school.id} value={school.app_key}>
                                                {school.name} - {school.location}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Address *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.address}
                                        onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Phone
                                    </label>
                                    <input
                                        type="tel"
                                        value={formData.phone}
                                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Role *
                                    </label>
                                    <select
                                        value={formData.role}
                                        onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    >
                                        <option value="Teacher">Teacher</option>
                                        <option value="Head_Teacher">Head Teacher</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Years of Experience
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.years_experience}
                                        onChange={(e) => setFormData({ ...formData, years_experience: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        min="0"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Subjects (comma-separated)
                                </label>
                                <input
                                    type="text"
                                    value={formData.subjects}
                                    onChange={(e) => setFormData({ ...formData, subjects: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    placeholder="e.g., Mathematics, Science, English"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Specializations (comma-separated)
                                </label>
                                <input
                                    type="text"
                                    value={formData.specializations}
                                    onChange={(e) => setFormData({ ...formData, specializations: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    placeholder="e.g., STEM Education, Special Needs"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={creating}
                                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                            >
                                {creating ? 'Registering...' : 'Register Teacher'}
                            </button>
                        </form>
                    </div>
                )}

                {/* Teachers List */}
                <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-lg font-semibold text-gray-800">
                            All Teachers ({teachers.length})
                        </h2>
                    </div>

                    {loading ? (
                        <div className="text-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                            <p className="mt-4 text-gray-600">Loading teachers...</p>
                        </div>
                    ) : teachers.length === 0 ? (
                        <div className="text-center py-12">
                            <p className="text-gray-600">No teachers registered yet</p>
                            <p className="text-gray-500 text-sm mt-2">Click "Register New Teacher" to get started</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {teachers.map((teacher) => (
                                <div key={teacher.id} className="p-6 hover:bg-gray-50 transition">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="text-lg font-semibold text-gray-800">{teacher.full_name}</h3>
                                            <p className="text-gray-600 mt-1">📧 {teacher.email}</p>
                                            <div className="mt-3 flex items-center gap-4 flex-wrap">
                                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${teacher.role === 'Head_Teacher'
                                                    ? 'bg-purple-100 text-purple-800'
                                                    : 'bg-blue-100 text-blue-800'
                                                    }`}>
                                                    {teacher.role === 'Head_Teacher' ? 'Head Teacher' : 'Teacher'}
                                                </span>
                                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${teacher.is_active
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-gray-100 text-gray-800'
                                                    }`}>
                                                    {teacher.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                                {teacher.subjects && teacher.subjects.length > 0 && (
                                                    <span className="text-sm text-gray-600">
                                                        📚 {Array.isArray(teacher.subjects) ? teacher.subjects.join(', ') : teacher.subjects}
                                                    </span>
                                                )}
                                                {teacher.years_experience > 0 && (
                                                    <span className="text-sm text-gray-600">
                                                        🎓 {teacher.years_experience} years exp.
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
