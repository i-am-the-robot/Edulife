// Shared Login Page for Teachers and Admins
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function TeacherAdminLogin() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [userType, setUserType] = useState('teacher');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const result = await login({ email, password }, userType);

        if (result.success) {
            navigate(`/${result.role}/dashboard`);
        } else {
            setError(result.error);
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
                <div className="text-center mb-8">
                    <Link to="/login" className="inline-block">
                        <h1 className="text-4xl font-bold text-gray-800 mb-2 hover:scale-105 transition-transform cursor-pointer">
                            EduLife
                        </h1>
                    </Link>
                    <p className="text-gray-600 text-lg">Learn Without Limits</p>
                    <p className="text-gray-500 mt-2">
                        {userType === 'teacher' ? 'Teacher Portal' : 'Admin Portal'}
                    </p>
                </div>

                {/* User Type Toggle */}
                <div className="flex gap-2 mb-6">
                    <button
                        type="button"
                        onClick={() => setUserType('teacher')}
                        className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${userType === 'teacher'
                            ? 'bg-indigo-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                    >
                        Teacher
                    </button>
                    <button
                        type="button"
                        onClick={() => setUserType('admin')}
                        className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${userType === 'admin'
                            ? 'bg-indigo-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                    >
                        Admin
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                            Email Address
                        </label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                            placeholder="your.email@school.com"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                            placeholder="Enter your password"
                            required
                        />
                    </div>

                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-indigo-700 hover:to-purple-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Logging in...' : 'Sign In'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <Link
                        to="/student/login"
                        className="text-sm text-indigo-600 hover:text-indigo-800 transition"
                    >
                        Student? Click here to login
                    </Link>
                    <div className="mt-2">
                        <Link
                            to="/teacher/register"
                            className="text-sm text-indigo-600 hover:text-indigo-800 transition"
                        >
                            New teacher? Register with your school app key
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
