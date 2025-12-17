// Student Login Page with PIN
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function StudentLogin() {
    const [studentId, setStudentId] = useState('');
    const [pin, setPin] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const result = await login({ studentId, pin }, 'student');

        if (result.success) {
            navigate('/student/dashboard');
        } else {
            setError(result.error);
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
                <div className="text-center mb-8">
                    <Link to="/login" className="inline-block">
                        <h1 className="text-4xl font-bold text-gray-800 mb-2 hover:scale-105 transition-transform cursor-pointer">
                            EduLife
                        </h1>
                    </Link>
                    <p className="text-gray-600 text-lg">Learn Without Limits</p>
                    <p className="text-gray-500 mt-2">Welcome back, learner! 🎓</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label htmlFor="studentId" className="block text-sm font-medium text-gray-700 mb-2">
                            Your Student ID
                        </label>
                        <input
                            id="studentId"
                            type="text"
                            value={studentId}
                            onChange={(e) => setStudentId(e.target.value)}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                            placeholder="Enter your student ID"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="pin" className="block text-sm font-medium text-gray-700 mb-2">
                            4-Digit PIN
                        </label>
                        <input
                            id="pin"
                            type="password"
                            value={pin}
                            onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 4))}
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-center text-2xl tracking-widest"
                            placeholder="••••"
                            maxLength="4"
                            pattern="\d{4}"
                            required
                        />
                        <p className="text-xs text-gray-500 mt-1">Enter your 4-digit PIN</p>
                    </div>

                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Logging in...' : 'Start Learning'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <Link
                        to="/login"
                        className="text-sm text-blue-600 hover:text-blue-800 transition"
                    >
                        ← Teacher or Admin? Click here to login
                    </Link>
                </div>
            </div>
        </div>
    );
}
