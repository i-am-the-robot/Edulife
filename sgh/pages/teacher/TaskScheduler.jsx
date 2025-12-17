// Task Scheduler Page (Teacher)
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherService } from '../../services/teacherService';

export default function TaskScheduler() {
    const { user, logout } = useAuth();
    const [tasks, setTasks] = useState([]);
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        due_date: '',
        student_id: '',
    });
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [tasksData, studentsData] = await Promise.all([
                teacherService.getTasks(),
                teacherService.getStudents(),
            ]);
            setTasks(tasksData);
            setStudents(studentsData);
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
            await teacherService.createTask(formData);
            setSuccess('Task assigned successfully!');
            setFormData({
                title: '',
                description: '',
                due_date: '',
                student_id: '',
            });
            setShowCreateForm(false);
            loadData();
        } catch (err) {
            console.error('Task creation error:', err);
            setError('Failed to create task');
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (taskId) => {
        if (!window.confirm('Are you sure you want to delete this task?')) return;
        try {
            await teacherService.deleteTask(taskId);
            setSuccess('Task deleted successfully');
            loadData();
        } catch (err) {
            setError('Failed to delete task');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Link to="/teacher/dashboard" className="text-indigo-600 hover:text-indigo-800">
                            ← Back to Dashboard
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-800">Task Scheduler</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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

                <div className="mb-6">
                    <button
                        onClick={() => setShowCreateForm(!showCreateForm)}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-semibold"
                    >
                        {showCreateForm ? 'Cancel' : '+ Assign New Task'}
                    </button>
                </div>

                {showCreateForm && (
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">Assign New Task</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
                                <input
                                    type="text"
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    rows="3"
                                    required
                                />
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Due Date</label>
                                    <input
                                        type="datetime-local"
                                        value={formData.due_date}
                                        onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Assign To</label>
                                    <select
                                        value={formData.student_id}
                                        onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                    >
                                        <option value="">Select Student</option>
                                        {students.map((student) => (
                                            <option key={student.id} value={student.id}>
                                                {student.full_name}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <button
                                type="submit"
                                disabled={creating}
                                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                            >
                                {creating ? 'Assigning...' : 'Assign Task'}
                            </button>
                        </form>
                    </div>
                )}

                <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-lg font-semibold text-gray-800">Assigned Tasks ({tasks.length})</h2>
                    </div>

                    {loading ? (
                        <div className="text-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                        </div>
                    ) : tasks.length === 0 ? (
                        <div className="text-center py-12">
                            <p className="text-gray-600">No tasks assigned yet</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {tasks.map((task) => (
                                <div key={task.id} className="p-6 hover:bg-gray-50 transition">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="text-lg font-semibold text-gray-800">{task.title}</h3>
                                            <p className="text-gray-600 mt-1">{task.description}</p>
                                            <div className="mt-2 flex gap-4 text-sm text-gray-500">
                                                <span>👤 {task.student_name}</span>
                                                <span>📅 Due: {new Date(task.due_date).toLocaleString()}</span>
                                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${task.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                                                    }`}>
                                                    {task.status.toUpperCase()}
                                                </span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleDelete(task.id)}
                                            className="text-red-600 hover:text-red-800"
                                        >
                                            Delete
                                        </button>
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
