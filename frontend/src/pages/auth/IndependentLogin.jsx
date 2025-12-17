
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const IndependentLogin = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1); // 1: Form, 2: Success
    const [formData, setFormData] = useState({
        full_name: '',
        age: '',
        student_class: '',
        hobby: '',
        personality: 'Introvert',
        learning_profile: 'Standard',
        parent_whatsapp: '',
        school_id: null
    });
    const [credentials, setCredentials] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const payload = {
                ...formData,
                age: parseInt(formData.age),
                school_id: null
            };

            const response = await axios.post('http://localhost:8000/api/auth/student/register', payload);
            setCredentials(response.data);
            setStep(2);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">

                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">
                        Create Account
                    </h1>
                    <p className="text-gray-600">Start your independent learning journey</p>
                </div>

                {step === 1 && (
                    <>
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                                <input
                                    type="text"
                                    name="full_name"
                                    required
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                                    placeholder="e.g. Adesare Adegbagi"
                                    value={formData.full_name}
                                    onChange={handleChange}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                                    <input
                                        type="number"
                                        name="age"
                                        required
                                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                                        placeholder="10"
                                        value={formData.age}
                                        onChange={handleChange}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Grade/Class</label>
                                    <input
                                        type="text"
                                        name="student_class"
                                        required
                                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                                        placeholder="e.g. Primary 1 or SS1"
                                        value={formData.student_class}
                                        onChange={handleChange}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Favorite Hobby</label>
                                <input
                                    type="text"
                                    name="hobby"
                                    required
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                                    placeholder="e.g. Space, Dinosaurs, Singing"
                                    value={formData.hobby}
                                    onChange={handleChange}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Personality</label>
                                    <select
                                        name="personality"
                                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition bg-white"
                                        value={formData.personality}
                                        onChange={handleChange}
                                    >
                                        <option value="Introvert">Introvert</option>
                                        <option value="Extrovert">Extrovert</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Learning Style</label>
                                    <select
                                        name="learning_profile"
                                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition bg-white"
                                        value={formData.learning_profile}
                                        onChange={handleChange}
                                    >
                                        <option value="Standard">Standard</option>
                                        <option value="Personalized">Personalized</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Parent WhatsApp (Optional)</label>
                                <input
                                    type="tel"
                                    name="parent_whatsapp"
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                                    placeholder="+234..."
                                    value={formData.parent_whatsapp}
                                    onChange={handleChange}
                                />
                                <p className="text-gray-500 text-xs mt-1">For progress updates.</p>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                            >
                                {loading ? 'Creating Account...' : 'Start Learning Now'}
                            </button>
                        </form>

                        <div className="mt-6 text-center">
                            <Link to="/student/login" className="text-sm text-blue-600 hover:text-blue-800 transition">
                                Already have an account? Login here
                            </Link>
                        </div>
                    </>
                )}

                {step === 2 && credentials && (
                    <div className="text-center">
                        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>

                        <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome, {credentials.full_name}!</h2>
                        <p className="text-gray-600 mb-8">Your account has been created successfully.</p>

                        <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 mb-8 text-left">
                            <p className="text-gray-500 text-xs uppercase font-bold mb-1">Your Student ID</p>
                            <div className="text-2xl font-mono text-blue-600 font-bold mb-4 tracking-wider">{credentials.id}</div>

                            <p className="text-gray-500 text-xs uppercase font-bold mb-1">Your Default PIN</p>
                            <div className="text-2xl font-mono text-blue-600 font-bold tracking-widest">
                                {credentials.pin || "0000"}
                            </div>
                        </div>

                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8">
                            <p className="text-yellow-800 text-sm">
                                ⚠️ <strong>IMPORTANT:</strong> Save your Student ID and PIN. You will need them to log in.
                            </p>
                        </div>

                        <button
                            onClick={() => navigate('/student/login')}
                            className="w-full bg-white border border-gray-300 text-gray-700 font-semibold py-3 rounded-lg hover:bg-gray-50 transition"
                        >
                            Return to Login
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default IndependentLogin;
