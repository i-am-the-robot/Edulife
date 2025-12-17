// Student Chat Page (Full Page with Chat Interface)
import { Link, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import ChatInterface from '../../components/student/ChatInterface';

export default function ChatPage() {
    const { user, logout } = useAuth();
    const [searchParams] = useSearchParams();
    const location = useLocation();
    const sessionId = searchParams.get('session');
    const taskParam = searchParams.get('task');

    // Get initial prompt from navigation state (from schedule)
    const initialPrompt = location.state?.initialPrompt;

    // Parse task data if present
    let taskData = null;
    if (taskParam) {
        try {
            taskData = JSON.parse(decodeURIComponent(taskParam));
        } catch (e) {
            console.error('Error parsing task data:', e);
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex flex-col">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Link to="/student/dashboard" className="text-blue-600 hover:text-blue-800">
                            ← Back to Dashboard
                        </Link>
                        <h1 className="text-xl font-bold text-gray-800">AI Learning Buddy</h1>
                        {sessionId && (
                            <span className="text-sm text-gray-600 bg-blue-100 px-3 py-1 rounded-full">
                                Continuing session
                            </span>
                        )}
                        {taskData && (
                            <span className="text-sm text-white bg-gradient-to-r from-blue-600 to-purple-600 px-3 py-1 rounded-full font-medium">
                                📚 Studying: {taskData.title}
                            </span>
                        )}
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

            {/* Chat Interface */}
            <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
                <div className="h-[calc(100vh-12rem)]">
                    <ChatInterface initialSessionId={sessionId} taskData={taskData} initialPrompt={initialPrompt} />
                </div>
            </main>
        </div>
    );
}
