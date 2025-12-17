// Student Tasks Page
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { studentService } from '../../services/studentService';

export default function StudentTasks() {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [tasks, setTasks] = useState([]);
    const [studyStatuses, setStudyStatuses] = useState({});
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState('');

    useEffect(() => {
        loadTasks();
    }, []);

    const loadTasks = async () => {
        try {
            const data = await studentService.getTasks();
            setTasks(data);

            // Load study status for each task
            const statuses = {};
            for (const task of data) {
                try {
                    const status = await studentService.getStudyStatus(task.id);
                    statuses[task.id] = status;
                } catch (error) {
                    console.error(`Error loading study status for task ${task.id}:`, error);
                    statuses[task.id] = { exists: false };
                }
            }
            setStudyStatuses(statuses);
        } catch (error) {
            console.error('Error loading tasks:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleStartStudy = async (task) => {
        try {
            // Start or continue study session
            const sessionData = await studentService.startStudySession(task.id);

            // Always pass taskData so the Done button appears
            // Only difference: don't trigger auto-prompt for continuing sessions
            const taskDataParam = encodeURIComponent(JSON.stringify({
                title: task.title,
                description: task.description,
                taskId: task.id
            }));

            if (sessionData.action === 'start') {
                // New session - will auto-prompt
                navigate(`/student/chat?session=${sessionData.session_id}&task=${taskDataParam}`);
            } else {
                // Continuing session - pass taskData but add flag to prevent auto-prompt
                navigate(`/student/chat?session=${sessionData.session_id}&task=${taskDataParam}&continuing=true`);
            }
        } catch (error) {
            console.error('Error starting study session:', error);
            setMessage('Failed to start study session. Please try again.');
            setTimeout(() => setMessage(''), 3000);
        }
    };

    const handleMarkDone = async (taskId) => {
        try {
            await studentService.completeTask(taskId);
            setMessage('Task completed! Great job! 🎉');
            loadTasks(); // Refresh list
            setTimeout(() => setMessage(''), 3000);
        } catch (error) {
            console.error('Error completing task:', error);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Link to="/student/dashboard" className="text-indigo-600 hover:text-indigo-800">
                            ← Back to Dashboard
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-800">My Assignments</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {message && (
                    <div className="mb-6 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg text-center font-semibold animate-bounce">
                        {message}
                    </div>
                )}

                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Loading assignments...</p>
                    </div>
                ) : tasks.length === 0 ? (
                    <div className="text-center py-12 bg-white rounded-lg shadow">
                        <p className="text-6xl mb-4">🎉</p>
                        <h2 className="text-xl font-bold text-gray-800">No Assignments!</h2>
                        <p className="text-gray-600 mt-2">You're all caught up. Great work!</p>
                    </div>
                ) : (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {tasks.map((task) => (
                            <div key={task.id} className={`bg-white rounded-xl shadow-lg overflow-hidden border-l-8 ${task.status === 'completed' ? 'border-green-500' : 'border-blue-500'
                                }`}>
                                <div className="p-6">
                                    <div className="flex justify-between items-start mb-4">
                                        <h3 className="text-lg font-bold text-gray-800">{task.title}</h3>
                                        {task.status === 'completed' && (
                                            <span className="text-green-600 text-xl">✓</span>
                                        )}
                                    </div>
                                    <p className="text-gray-600 mb-4 text-sm">{task.description}</p>

                                    <div className="text-sm text-gray-500 mb-6 space-y-1">
                                        <p>📅 Due: {new Date(task.due_date).toLocaleDateString()}</p>
                                        <p>👨‍🏫 {task.teacher_name}</p>
                                    </div>

                                    {task.status !== 'completed' ? (
                                        <div className="space-y-2">
                                            {studyStatuses[task.id]?.exists ? (
                                                <>
                                                    <button
                                                        onClick={() => handleStartStudy(task)}
                                                        className="w-full py-3 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg hover:from-green-700 hover:to-teal-700 transition font-semibold flex items-center justify-center gap-2"
                                                    >
                                                        <span>📚</span>
                                                        Continue Studying
                                                    </button>
                                                    <div className="text-xs text-gray-500 text-center">
                                                        {studyStatuses[task.id]?.conversation_count || 0} messages exchanged
                                                    </div>
                                                </>
                                            ) : (
                                                <button
                                                    onClick={() => handleStartStudy(task)}
                                                    className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition font-semibold flex items-center justify-center gap-2"
                                                >
                                                    <span>🤖</span>
                                                    Start Study with AI
                                                </button>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="w-full py-2 bg-gray-100 text-green-700 rounded-lg text-center font-medium">
                                            Completed
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
