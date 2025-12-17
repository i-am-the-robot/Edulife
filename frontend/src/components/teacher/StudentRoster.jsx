// Student Roster Component
import { Link } from 'react-router-dom';

export default function StudentRoster({ students, loading }) {
    const getStatusColor = (student) => {
        const engagement = student.engagement_score || 0;
        const testSuccess = student.test_success_rate || 0;

        if (engagement < 20) return 'gray'; // Inactive
        if (testSuccess >= 80 && engagement >= 70) return 'blue'; // Excelling
        if (engagement >= 70) return 'green'; // On track
        return 'orange'; // Needs attention
    };

    const getStatusLabel = (student) => {
        const engagement = student.engagement_score || 0;
        const testSuccess = student.test_success_rate || 0;

        if (engagement < 20) return 'Inactive';
        if (testSuccess >= 80 && engagement >= 70) return 'Excelling';
        if (engagement >= 70) return 'On Track';
        return 'Needs Attention';
    };

    const getStatusIcon = (student) => {
        const color = getStatusColor(student);
        const icons = {
            green: '🟢',
            orange: '🟡',
            blue: '🔵',
            gray: '⚪',
        };
        return icons[color];
    };

    const formatLastActive = (dateString) => {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    if (loading) {
        return (
            <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading students...</p>
            </div>
        );
    }

    if (students.length === 0) {
        return (
            <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-600 text-lg">No students found</p>
                <p className="text-gray-500 text-sm mt-2">Students will appear here once they're registered</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Student
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Engagement
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Sessions
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Last Active
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {students.map((student) => (
                            <tr key={student.id} className="hover:bg-gray-50 transition">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div>
                                        <div className="text-sm font-medium text-gray-900 flex items-center gap-2">
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
                                        </div>
                                        <div className="text-sm text-gray-500">{student.student_class}</div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="flex items-center gap-2">
                                        <span className="text-xl">{getStatusIcon(student)}</span>
                                        <span className="text-sm text-gray-700">{getStatusLabel(student)}</span>
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                            <div
                                                className={`h-2 rounded-full ${getStatusColor(student) === 'green'
                                                    ? 'bg-green-500'
                                                    : getStatusColor(student) === 'blue'
                                                        ? 'bg-blue-500'
                                                        : getStatusColor(student) === 'orange'
                                                            ? 'bg-orange-500'
                                                            : 'bg-gray-400'
                                                    }`}
                                                style={{ width: `${student.engagement_score || 0}%` }}
                                            ></div>
                                        </div>
                                        <span className="text-sm text-gray-700">{student.engagement_score || 0}%</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                    {student.total_sessions || 0}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatLastActive(student.last_active)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    <Link
                                        to={`/teacher/students/${student.id}`}
                                        className="text-indigo-600 hover:text-indigo-900 font-medium"
                                    >
                                        View Details →
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
