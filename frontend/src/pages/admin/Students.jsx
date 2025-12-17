import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminService } from '../../services/adminService';
import { teacherService } from '../../services/teacherService';
import { authService } from '../../services/authService';

export default function StudentsPage() {
    const { user, logout } = useAuth();
    const [students, setStudents] = useState([]);
    const [schools, setSchools] = useState([]);
    const [teachers, setTeachers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [formData, setFormData] = useState({
        full_name: '',
        age: '',
        student_class: '',
        hobby: '',
        personality: 'Introvert',
        support_type: 'None',
        learning_profile: 'Standard',
        school_id: '',
    });
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [createdStudentId, setCreatedStudentId] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            let studentsData, schoolsData;

            if (user?.role === 'teacher') {
                // Teachers: load their students and auto-select their school

                // Robustness: If user.school_id is missing (stale session), fetch fresh details
                let currentSchoolId = user.school_id;
                let teacherName = user.full_name;

                if (!currentSchoolId) {
                    try {
                        const freshUser = await authService.getCurrentUser();
                        currentSchoolId = freshUser.school_id;
                        teacherName = freshUser.full_name;
                        // Use fresh user data to populate schools list
                    } catch (err) {
                        console.error("Failed to refresh user data", err);
                    }
                }

                studentsData = await teacherService.getMyStudents();
                schoolsData = currentSchoolId ? [{ id: currentSchoolId, name: 'Your School', location: '' }] : [];

                // Auto-select teacher's school
                if (currentSchoolId && !formData.school_id) {
                    setFormData(prev => ({ ...prev, school_id: currentSchoolId.toString() }));
                }
            } else {
                // Admins: load all students, schools, and teachers
                const teachersData = await adminService.getTeachers();
                [studentsData, schoolsData] = await Promise.all([
                    adminService.getStudents(),
                    adminService.getSchools(),
                ]);
                setTeachers(teachersData);
            }

            setStudents(studentsData);
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
        setCreatedStudentId('');

        try {
            const studentData = {
                ...formData,
                age: parseInt(formData.age),
                school_id: parseInt(formData.school_id),
            };

            let response;
            if (user?.role === 'teacher') {
                response = await teacherService.registerStudent(studentData);
            } else {
                response = await adminService.registerStudent(studentData);
            }
            const studentId = response.id || response.student_id;
            setCreatedStudentId(studentId);
            setSuccess(`Student registered! Student ID: ${studentId}`);
            setFormData({
                full_name: '',
                age: '',
                student_class: '',
                hobby: '',
                personality: 'Introvert',
                support_type: 'None',
                learning_profile: 'Standard',
                school_id: user?.role === 'teacher' ? user.school_id?.toString() : '',
            });
            setShowCreateForm(false);
            loadData();
        } catch (err) {
            console.error('Registration error:', err);
            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                if (Array.isArray(detail)) {
                    const errorMessages = detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join(', ');
                    setError(errorMessages);
                } else if (typeof detail === 'string') {
                    setError(detail);
                } else {
                    setError('Failed to register student. Please check all fields.');
                }
            } else {
                setError('Failed to register student. Please try again.');
            }
        } finally {
            setCreating(false);
        }
    };

    const copyStudentId = (studentId) => {
        navigator.clipboard.writeText(studentId);
        alert('Student ID copied to clipboard!');
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Link to={user?.role === 'teacher' ? '/teacher/dashboard' : '/admin/dashboard'} className="text-indigo-600 hover:text-indigo-800">
                            ← Back to Dashboard
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-800">Student Management</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-gray-700">Welcome, {user?.full_name || user?.name || user?.email || 'Teacher'}!</span>
                        <button onClick={logout} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition">
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {success && (
                    <div className="mb-6 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg">
                        <p>{success}</p>
                        {createdStudentId && (
                            <button
                                onClick={() => copyStudentId(createdStudentId)}
                                className="mt-2 px-4 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                            >
                                Copy Student ID
                            </button>
                        )}
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
                        {showCreateForm ? 'Cancel' : '+ Register New Student'}
                    </button>
                </div>

                {showCreateForm && (
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">Register New Student</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Full Name *</label>
                                    <input
                                        type="text"
                                        value={formData.full_name}
                                        onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Age *</label>
                                    <input
                                        type="number"
                                        value={formData.age}
                                        onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        min="5"
                                        max="18"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Class *</label>
                                    <input
                                        type="text"
                                        value={formData.student_class}
                                        onChange={(e) => setFormData({ ...formData, student_class: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        placeholder="e.g., Grade 8"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Hobby</label>
                                    <input
                                        type="text"
                                        value={formData.hobby}
                                        onChange={(e) => setFormData({ ...formData, hobby: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        placeholder="e.g., Reading, Sports"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Parent WhatsApp Number
                                        <span className="text-xs text-gray-500 ml-2">(for notifications)</span>
                                    </label>
                                    <input
                                        type="tel"
                                        value={formData.parent_whatsapp || ''}
                                        onChange={(e) => setFormData({ ...formData, parent_whatsapp: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        placeholder="+2348012345678"
                                    />
                                    <p className="text-xs text-gray-500 mt-1">
                                        Parents will receive WhatsApp updates about their child's progress.
                                    </p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Personality</label>
                                    <select
                                        value={formData.personality}
                                        onChange={(e) => setFormData({ ...formData, personality: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    >
                                        <option value="Introvert">Introvert</option>
                                        <option value="Extrovert">Extrovert</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Support Type</label>
                                    <select
                                        value={formData.support_type}
                                        onChange={(e) => setFormData({ ...formData, support_type: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    >
                                        <option value="None">None</option>
                                        <option value="Dyslexia">Dyslexia</option>
                                        <option value="DownSyndrome">Down Syndrome</option>
                                        <option value="Autism">Autism</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">School *</label>
                                    <select
                                        value={formData.school_id}
                                        onChange={(e) => setFormData({ ...formData, school_id: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                        disabled={user?.role === 'teacher'}
                                    >
                                        <option value="">Select School</option>
                                        {(schools || []).map((school) => (
                                            <option key={school.id} value={school.id}>
                                                {school.name}{school.location ? ` - ${school.location}` : ''}
                                            </option>
                                        ))}
                                    </select>
                                    {user?.role === 'teacher' && (
                                        <p className="text-xs text-gray-500 mt-1">Auto-selected: Your school</p>
                                    )}
                                </div>
                                {user?.role === 'admin' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Assign Teacher
                                            <span className="text-xs text-gray-500 ml-2">(optional)</span>
                                        </label>
                                        <select
                                            value={formData.assigned_teacher_id || ''}
                                            onChange={(e) => setFormData({ ...formData, assigned_teacher_id: e.target.value })}
                                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        >
                                            <option value="">No teacher assigned</option>
                                            {(teachers || [])
                                                .filter(teacher => teacher.school_id === parseInt(formData.school_id))
                                                .map((teacher) => (
                                                    <option key={teacher.id} value={teacher.id}>
                                                        {teacher.full_name} ({teacher.email})
                                                    </option>
                                                ))}
                                        </select>
                                        <p className="text-xs text-gray-500 mt-1">
                                            Assign a teacher to manage this student. Only teachers from the selected school are shown.
                                        </p>
                                    </div>
                                )}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Learning Profile *</label>
                                    <select
                                        value={formData.learning_profile}
                                        onChange={(e) => setFormData({ ...formData, learning_profile: e.target.value })}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                        required
                                    >
                                        <option value="Standard">Standard</option>
                                        <option value="Personalized">Personalized</option>
                                    </select>
                                </div>
                            </div>
                            <button
                                type="submit"
                                disabled={creating}
                                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                            >
                                {creating ? 'Registering...' : 'Register Student'}
                            </button>
                        </form>
                    </div>
                )}

                <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-lg font-semibold text-gray-800">All Students ({students?.length || 0})</h2>
                    </div>

                    {loading ? (
                        <div className="text-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                            <p className="mt-4 text-gray-600">Loading students...</p>
                        </div>
                    ) : students?.length === 0 ? (
                        <div className="text-center py-12">
                            <p className="text-gray-600">No students registered yet</p>
                            <p className="text-gray-500 text-sm mt-2">Click "Register New Student" to get started</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200">
                            {(students || []).map((student) => (
                                <div key={student.id} className="p-6 hover:bg-gray-50 transition">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                                                {student.full_name}
                                                {student.support_type && student.support_type !== 'None' && (
                                                    <span
                                                        className="text-lg cursor-help"
                                                        title={`${student.support_type} support`}
                                                    >
                                                        {student.support_type === 'Dyslexia' && '🔵'}
                                                        {student.support_type === 'Autism' && '🟢'}
                                                        {student.support_type === 'Down Syndrome' && '🟡'}
                                                    </span>
                                                )}
                                            </h3>
                                            <p className="text-gray-600 mt-1">{student.age} years • {student.student_class}</p>
                                            <div className="mt-3 flex items-center gap-4 flex-wrap">
                                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${student.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                                    {student.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                                {student.hobby && <span className="text-sm text-gray-600">🎯 {student.hobby}</span>}
                                                <span className="text-sm text-gray-600">
                                                    {student.personality === 'Introvert' ? '🤫' : '🎉'} {student.personality}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="ml-6">
                                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                                <p className="text-xs text-blue-600 font-medium mb-1">Student ID</p>
                                                <div className="flex items-center gap-2">
                                                    <code className="text-sm font-mono text-blue-900 bg-white px-3 py-1 rounded border border-blue-200">
                                                        {student.id}
                                                    </code>
                                                    <button
                                                        onClick={() => copyStudentId(student.id)}
                                                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
                                                    >
                                                        Copy
                                                    </button>
                                                </div>
                                                <p className="text-xs text-gray-600 mt-2">Use this ID to login</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="mt-6 bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                    <h3 className="font-semibold text-blue-900 mb-2">About Student IDs</h3>
                    <p className="text-blue-800 text-sm">
                        Each student gets a unique ID for login. Students don't need passwords - they just enter their ID.
                        Make sure to copy and share the Student ID with the student after registration.
                    </p>
                </div>
            </main>
        </div>
    );
}
