// Teacher Self-Registration Page
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';
import { adminService } from '../../services/adminService';

export default function TeacherRegister() {
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        password: '',
        app_key: '',
        address: '',
        phone: '',
        role: 'Teacher',
        subjects: '',
        years_experience: 0,
        specializations: '',
    });
    const [schools, setSchools] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        loadSchools();
    }, []);

    const loadSchools = async () => {
        try {
            const data = await adminService.getSchools();
            setSchools(data);
        } catch (err) {
            console.error('Error loading schools:', err);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await authService.registerTeacher(formData);
            setSuccess(true);
            setTimeout(() => navigate('/login'), 2000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-2xl">
                <div className="text-center mb-8">
                    <Link to="/login">
                        <h1 className="text-4xl font-bold text-gray-800 mb-2 hover:scale-105 transition-transform cursor-pointer">
                            EduLife
                        </h1>
                    </Link>
                    <p className="text-gray-600 text-lg">Learn Without Limits</p>
                    <p className="text-gray-500 mt-2">Teacher Registration</p>
                </div>

                {success ? (
                    <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg text-center">
                        <p className="font-semibold">Registration Successful!</p>
                        <p className="text-sm mt-1">Redirecting to login...</p>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                                {error}
                            </div>
                        )}

                        <div className="grid grid-cols-2 gap-4">
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
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Password *
                                </label>
                                <input
                                    type="password"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    minLength="8"
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

                        <div className="grid grid-cols-2 gap-4">
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
                                    Years of Experience
                                </label>
                                <input
                                    type="number"
                                    value={formData.years_experience}
                                    onChange={(e) => setFormData({ ...formData, years_experience: parseInt(e.target.value) })}
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
                                placeholder="e.g., Mathematics, Science"
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
                                placeholder="e.g., Special needs, STEM"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition disabled:opacity-50"
                        >
                            {loading ? 'Registering...' : 'Register as Teacher'}
                        </button>

                        <div className="text-center mt-4">
                            <Link to="/login" className="text-indigo-600 hover:text-indigo-800 text-sm">
                                Already have an account? Login here
                            </Link>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
