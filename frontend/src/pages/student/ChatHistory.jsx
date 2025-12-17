// Student Chat History Page - Session-Based View
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { studentService } from '../../services/studentService';

export default function ChatHistory() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterSubject, setFilterSubject] = useState('all');

    useEffect(() => {
        loadChatSessions();
    }, []);

    const loadChatSessions = async () => {
        try {
            const data = await studentService.getChatSessions();
            setSessions(data);
        } catch (error) {
            console.error('Error loading chat sessions:', error);
        } finally {
            setLoading(false);
        }
    };

    const subjects = ['all', ...new Set(sessions.map(s => s.subject).filter(Boolean))];

    const filteredSessions = filterSubject === 'all'
        ? sessions
        : sessions.filter(s => s.subject === filterSubject);

    const handleContinueSession = (sessionId) => {
        navigate(`/student/chat?session=${sessionId}`);
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Link to="/student/dashboard" className="text-indigo-600 hover:text-indigo-800">
                            ← Back to Dashboard
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-800">My Chat History</h1>
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
                {/* Filter */}
                <div className="bg-white rounded-lg shadow p-4 mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Filter by Subject
                    </label>
                    <select
                        value={filterSubject}
                        onChange={(e) => setFilterSubject(e.target.value)}
                        className="w-full md:w-64 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                    >
                        {subjects.map((subject) => (
                            <option key={subject} value={subject}>
                                {subject === 'all' ? 'All Subjects' : subject}
                            </option>
                        ))}
                    </select>
                    <p className="text-sm text-gray-600 mt-2">
                        Showing {filteredSessions.length} of {sessions.length} study sessions
                    </p>
                </div>

                {/* Chat Sessions */}
                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Loading your study sessions...</p>
                    </div>
                ) : filteredSessions.length === 0 ? (
                    <div className="bg-white rounded-lg shadow p-12 text-center">
                        <div className="text-6xl mb-4">💬</div>
                        <p className="text-gray-600 text-lg">No study sessions yet</p>
                        <p className="text-gray-500 mt-2">Start chatting with your AI buddy to create your first session!</p>
                        <Link
                            to="/student/chat"
                            className="mt-4 inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                        >
                            Start New Session
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {filteredSessions.map((session) => (
                            <div
                                key={session.session_id}
                                className="bg-white rounded-xl shadow-md hover:shadow-xl transition p-6 cursor-pointer"
                                onClick={() => handleContinueSession(session.session_id)}
                            >
                                {/* Session Header */}
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <span className="inline-block px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                                            {session.subject}
                                        </span>
                                    </div>
                                    <span className="text-sm text-gray-500">
                                        {new Date(session.last_message_time).toLocaleDateString()}
                                    </span>
                                </div>

                                {/* Session Info */}
                                <div className="mb-4">
                                    <p className="text-gray-600 text-sm mb-2">
                                        <span className="font-medium">{session.message_count}</span> messages
                                    </p>
                                    <p className="text-gray-700 italic line-clamp-2">
                                        "{session.last_message_preview}..."
                                    </p>
                                </div>

                                {/* Session Time */}
                                <div className="flex items-center justify-between text-sm text-gray-500">
                                    <span>
                                        Started: {new Date(session.start_time).toLocaleString()}
                                    </span>
                                </div>

                                {/* Continue Button */}
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleContinueSession(session.session_id);
                                    }}
                                    className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
                                >
                                    Continue Conversation →
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                {/* New Session Button */}
                <div className="mt-8 text-center">
                    <Link
                        to="/student/chat"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
                    >
                        <span className="text-xl">+</span>
                        Start New Study Session
                    </Link>
                </div>
            </main>
        </div>
    );
}
