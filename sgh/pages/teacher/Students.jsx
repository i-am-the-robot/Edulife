// Students Page with Roster
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherService } from '../../services/teacherService';
import StudentRoster from '../../components/teacher/StudentRoster';

export default function StudentsPage() {
    const { user, logout } = useAuth();
    const [students, setStudents] = useState([]);
    const [filteredStudents, setFilteredStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    useEffect(() => {
        loadStudents();
    }, []);

    useEffect(() => {
        filterStudents();
    }, [searchTerm, statusFilter, students]);

    const loadStudents = async () => {
        try {
            const data = await teacherService.getMyStudents();
            setStudents(data);
            setFilteredStudents(data);
        } catch (error) {
            console.error('Error loading students:', error);
        } finally {
            setLoading(false);
        }
    };

    const filterStudents = () => {
        let filtered = [...students];

        // Search filter
        if (searchTerm) {
            filtered = filtered.filter((student) =>
                student.full_name.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        // Status filter
        if (statusFilter !== 'all') {
            filtered = filtered.filter((student) => {
                const engagement = student.engagement_score || 0;
                const testSuccess = student.test_success_rate || 0;

                if (statusFilter === 'inactive') return engagement < 20;
                if (statusFilter === 'excelling') return testSuccess >= 80 && engagement >= 70;
                if (statusFilter === 'ontrack') return engagement >= 70 && !(testSuccess >= 80);
                if (statusFilter === 'attention') return engagement >= 20 && engagement < 70;
                return true;
            });
        }

        setFilteredStudents(filtered);
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Link to="/teacher/dashboard" className="text-indigo-600 hover:text-indigo-800">
                            ← Back to Dashboard
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-800">My Students</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-gray-700">Welcome, {user?.full_name || user?.name || user?.email || 'Teacher'}!</span>
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
                {/* Register Student Button */}
                <div className="mb-6">
                    <Link
                        to="/teacher/register-student"
                        className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-semibold"
                    >
                        <span className="text-xl mr-2">+</span>
                        Register New Student
                    </Link>
                </div>

                {/* Filters */}
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Search Students
                            </label>
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search by name..."
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Filter by Status
                            </label>
                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                            >
                                <option value="all">All Students</option>
                                <option value="ontrack">🟢 On Track</option>
                                <option value="attention">🟡 Needs Attention</option>
                                <option value="excelling">🔵 Excelling</option>
                                <option value="inactive">⚪ Inactive</option>
                            </select>
                        </div>
                    </div>
                    <div className="mt-4 text-sm text-gray-600">
                        Showing {filteredStudents.length} of {students.length} students
                    </div>
                </div>

                {/* Student Roster */}
                <StudentRoster students={filteredStudents} loading={loading} />
            </main>
        </div>
    );
}
