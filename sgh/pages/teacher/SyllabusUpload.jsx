// Syllabus Upload Page (Teacher)
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { teacherService } from '../../services/teacherService';

export default function SyllabusUpload() {
    const { logout } = useAuth();
    const [syllabusText, setSyllabusText] = useState('');
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setUploading(true);
        setMessage({ type: '', text: '' });

        try {
            await teacherService.uploadSyllabus(syllabusText);
            setMessage({ type: 'success', text: 'Syllabus updated successfully! The AI will now use this context.' });
        } catch (error) {
            console.error('Upload error:', error);
            setMessage({ type: 'error', text: 'Failed to update syllabus.' });
        } finally {
            setUploading(false);
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
                        <h1 className="text-2xl font-bold text-gray-800">Upload Syllabus</h1>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="bg-white rounded-lg shadow-lg p-6 max-w-3xl mx-auto">
                    <div className="mb-6">
                        <h2 className="text-xl font-semibold text-gray-800 mb-2">Update School Syllabus</h2>
                        <p className="text-gray-600 text-sm">
                            Paste your school's syllabus or curriculum text here. This information will be used by the AI
                            to answer student questions more accurately and ensure alignment with your teaching goals.
                        </p>
                    </div>

                    {message.text && (
                        <div className={`mb-6 px-4 py-3 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200'
                                : 'bg-red-50 text-red-800 border border-red-200'
                            }`}>
                            {message.text}
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Syllabus Content
                            </label>
                            <textarea
                                value={syllabusText}
                                onChange={(e) => setSyllabusText(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none h-64"
                                placeholder="Paste syllabus text here (e.g., Chapter list, topics, learning objectives)..."
                                required
                            />
                        </div>
                        <div className="flex justify-end">
                            <button
                                type="submit"
                                disabled={uploading}
                                className="px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-semibold disabled:opacity-50"
                            >
                                {uploading ? 'Updating...' : 'Update Syllabus'}
                            </button>
                        </div>
                    </form>
                </div>
            </main>
        </div>
    );
}
