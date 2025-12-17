// Student Schedule Page
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { studentService } from '../../services/studentService';

export default function Schedule() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [schedule, setSchedule] = useState([]);
    const [aiSchedule, setAiSchedule] = useState(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [view, setView] = useState('weekly'); // 'daily' or 'weekly'
    const [selectedDay, setSelectedDay] = useState('monday');

    useEffect(() => {
        loadSchedule();
        // Load saved AI schedule from localStorage
        // Initial load only - remove localStorage logic as we now fetch from storage
        loadSchedule();
    }, []);

    const loadSchedule = async () => {
        try {
            const [scheduleData, aiData] = await Promise.all([
                studentService.getSchedule(),
                studentService.getAiSchedule()
            ]);
            setSchedule(scheduleData);
            if (aiData?.schedule) {
                setAiSchedule(aiData.schedule);
            }
        } catch (error) {
            console.error('Error loading schedule:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateSchedule = async () => {
        console.log('=== Generate Schedule Button Clicked ===');
        try {
            setGenerating(true);
            console.log('Calling studentService.generateSchedule()...');
            const data = await studentService.generateSchedule();
            console.log('Schedule generation response:', data);
            console.log('Setting aiSchedule to:', data.schedule);
            setAiSchedule(data.schedule);
            setAiSchedule(data.schedule);
            // No need to save to localStorage as backend persists it
            console.log('Schedule generated and loaded!');
        } catch (error) {
            console.error('Error generating schedule:', error);
            console.error('Error details:', error.response?.data || error.message);
            alert(`Failed to generate schedule: ${error.response?.data?.detail || error.message}`);
        } finally {
            setGenerating(false);
            console.log('=== Generate Schedule Complete ===');
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'Scheduled':
                return 'bg-blue-100 text-blue-800';
            case 'Completed':
                return 'bg-green-100 text-green-800';
            case 'Cancelled':
                return 'bg-gray-100 text-gray-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getSubjectColor = (subject) => {
        const colors = {
            'Mathematics': 'bg-blue-100 border-blue-500',
            'Science': 'bg-green-100 border-green-500',
            'English': 'bg-purple-100 border-purple-500',
            'History': 'bg-yellow-100 border-yellow-500',
            'Geography': 'bg-teal-100 border-teal-500'
        };
        return colors[subject] || 'bg-gray-100 border-gray-500';
    };

    const getPriorityBadge = (priority) => {
        const badges = {
            'high': 'bg-red-100 text-red-700',
            'medium': 'bg-yellow-100 text-yellow-700',
            'low': 'bg-green-100 text-green-700'
        };
        return badges[priority] || 'bg-gray-100 text-gray-700';
    };

    const isUpcoming = (dateString) => {
        return new Date(dateString) > new Date();
    };

    const upcomingSessions = schedule.filter(s => isUpcoming(s.scheduled_time) && s.status === 'Scheduled');
    const pastSessions = schedule.filter(s => !isUpcoming(s.scheduled_time) || s.status !== 'Scheduled');

    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    const dayNames = {
        'monday': 'Monday',
        'tuesday': 'Tuesday',
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday'
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
                        <h1 className="text-2xl font-bold text-gray-800">My Schedule</h1>
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
                {/* AI Schedule Section */}
                <div className="mb-8">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-2xl font-bold text-gray-800">🤖 AI Study Timetable</h2>
                        <button
                            onClick={handleGenerateSchedule}
                            disabled={generating}
                            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition disabled:opacity-50 font-semibold flex items-center gap-2"
                        >
                            {generating ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <span>✨</span>
                                    Generate AI Schedule
                                </>
                            )}
                        </button>
                    </div>

                    {aiSchedule ? (
                        <>
                            {/* View Toggle */}
                            <div className="flex gap-2 mb-4">
                                <button
                                    onClick={() => setView('weekly')}
                                    className={`px-4 py-2 rounded-lg font-medium transition ${view === 'weekly'
                                        ? 'bg-purple-600 text-white'
                                        : 'bg-white text-gray-700 hover:bg-gray-100'
                                        }`}
                                >
                                    Weekly View
                                </button>
                                <button
                                    onClick={() => setView('daily')}
                                    className={`px-4 py-2 rounded-lg font-medium transition ${view === 'daily'
                                        ? 'bg-purple-600 text-white'
                                        : 'bg-white text-gray-700 hover:bg-gray-100'
                                        }`}
                                >
                                    Daily View
                                </button>
                            </div>

                            {view === 'weekly' ? (
                                /* Weekly View */
                                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                                    {days.map(day => (
                                        <div key={day} className="bg-white rounded-lg shadow p-4">
                                            <h3 className="font-bold text-lg text-gray-800 mb-3 border-b pb-2">
                                                {dayNames[day]}
                                            </h3>
                                            <div className="space-y-2">
                                                {aiSchedule[day]?.map((session, idx) => (
                                                    <div
                                                        key={idx}
                                                        onClick={() => {
                                                            if (session.type === 'study') {
                                                                navigate('/student/chat', {
                                                                    state: {
                                                                        initialPrompt: `I want to study ${session.subject}: ${session.topic}. Can you help me understand this topic?`
                                                                    }
                                                                });
                                                            }
                                                        }}
                                                        className={`p-3 rounded-lg border-l-4 ${session.type === 'break'
                                                            ? 'bg-gray-50 border-gray-300'
                                                            : getSubjectColor(session.subject) + ' cursor-pointer hover:shadow-md transition-shadow'
                                                            }`}
                                                    >
                                                        <div className="text-xs font-semibold text-gray-600 mb-1">
                                                            {session.time}
                                                        </div>
                                                        <div className="text-sm font-medium text-gray-800">
                                                            {session.topic}
                                                        </div>
                                                        {session.subject && (
                                                            <div className="text-xs text-gray-600 mt-1">
                                                                {session.subject}
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                /* Daily View */
                                <div>
                                    <div className="flex gap-2 mb-4 overflow-x-auto">
                                        {days.map(day => (
                                            <button
                                                key={day}
                                                onClick={() => setSelectedDay(day)}
                                                className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition ${selectedDay === day
                                                    ? 'bg-blue-600 text-white'
                                                    : 'bg-white text-gray-700 hover:bg-gray-100'
                                                    }`}
                                            >
                                                {dayNames[day]}
                                            </button>
                                        ))}
                                    </div>
                                    <div className="bg-white rounded-lg shadow p-6">
                                        <h3 className="text-xl font-bold text-gray-800 mb-4">
                                            {dayNames[selectedDay]} Schedule
                                        </h3>
                                        <div className="space-y-4">
                                            {aiSchedule[selectedDay]?.map((session, idx) => (
                                                <div
                                                    key={idx}
                                                    onClick={() => {
                                                        if (session.type === 'study') {
                                                            navigate('/student/chat', {
                                                                state: {
                                                                    initialPrompt: `I want to study ${session.subject}: ${session.topic}. Can you help me understand this topic?`
                                                                }
                                                            });
                                                        }
                                                    }}
                                                    className={`p-4 rounded-lg border-l-4 ${session.type === 'break'
                                                        ? 'bg-gray-50 border-gray-300'
                                                        : getSubjectColor(session.subject) + ' cursor-pointer hover:shadow-lg transition-shadow'
                                                        }`}
                                                >
                                                    <div className="flex justify-between items-start">
                                                        <div className="flex-1">
                                                            <div className="flex items-center gap-3 mb-2">
                                                                <span className="text-lg font-bold text-gray-800">
                                                                    {session.time}
                                                                </span>
                                                                <span className="text-sm text-gray-600">
                                                                    ({session.duration} min)
                                                                </span>
                                                            </div>
                                                            <h4 className="text-lg font-semibold text-gray-800 mb-1">
                                                                {session.topic}
                                                            </h4>
                                                            {session.subject && (
                                                                <p className="text-sm text-gray-600">
                                                                    Subject: {session.subject}
                                                                </p>
                                                            )}
                                                            {session.type === 'study' && (
                                                                <p className="text-xs text-purple-600 mt-2">
                                                                    👆 Click to start studying
                                                                </p>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="bg-white rounded-lg shadow p-8 text-center">
                            <p className="text-gray-600 mb-4">No AI schedule generated yet</p>
                            <p className="text-gray-500 text-sm">
                                Click "Generate AI Schedule" to create a personalized study timetable based on your syllabus and assignments
                            </p>
                        </div>
                    )}
                </div>

                {/* Upcoming Tutorial Sessions */}
                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Loading tutorial sessions...</p>
                    </div>
                ) : (
                    <>
                        <div className="mb-8">
                            <h2 className="text-2xl font-bold text-gray-800 mb-4">📅 Upcoming Tutorial Sessions</h2>
                            {upcomingSessions.length === 0 ? (
                                <div className="bg-white rounded-lg shadow p-8 text-center">
                                    <p className="text-gray-600">No upcoming tutorial sessions scheduled</p>
                                    <p className="text-gray-500 text-sm mt-2">
                                        Your teacher will schedule tutorial sessions for you
                                    </p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {upcomingSessions.map((session) => (
                                        <div
                                            key={session.id}
                                            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition border-l-4 border-indigo-500"
                                        >
                                            <div className="flex justify-between items-start">
                                                <div className="flex-1">
                                                    <h3 className="text-lg font-semibold text-gray-800 mb-2">
                                                        {session.subject || 'Tutorial Session'}
                                                    </h3>
                                                    {session.topic && (
                                                        <p className="text-gray-600 mb-3">{session.topic}</p>
                                                    )}
                                                    <div className="flex items-center gap-4 text-sm text-gray-600">
                                                        <span>📅 {new Date(session.scheduled_time).toLocaleDateString()}</span>
                                                        <span>🕐 {new Date(session.scheduled_time).toLocaleTimeString()}</span>
                                                        <span>⏱️ {session.duration_minutes} minutes</span>
                                                    </div>
                                                    {session.teacher_name && (
                                                        <p className="text-sm text-gray-600 mt-2">
                                                            👨‍🏫 With {session.teacher_name}
                                                        </p>
                                                    )}
                                                </div>
                                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(session.status)}`}>
                                                    {session.status}
                                                </span>
                                            </div>
                                            {session.notes && (
                                                <div className="mt-4 bg-blue-50 rounded p-3">
                                                    <p className="text-sm text-blue-900">
                                                        <strong>Notes:</strong> {session.notes}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
