// Test Results Viewer Component
export default function TestResultsViewer({ testResults, loading }) {
    if (loading) {
        return (
            <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading test results...</p>
            </div>
        );
    }

    if (!testResults || testResults.length === 0) {
        return (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
                <p className="text-gray-600">No test results yet</p>
                <p className="text-gray-500 text-sm mt-2">Test results will appear here once the student completes practice questions</p>
            </div>
        );
    }

    const successRate = testResults.length > 0
        ? (testResults.filter(t => t.is_correct).length / testResults.length * 100).toFixed(0)
        : 0;

    return (
        <div>
            {/* Success Rate Card */}
            <div className="bg-gradient-to-r from-green-500 to-blue-500 rounded-lg p-6 text-white mb-6">
                <h3 className="text-lg font-semibold mb-2">Overall Success Rate</h3>
                <p className="text-4xl font-bold">{successRate}%</p>
                <p className="text-sm opacity-90 mt-1">
                    {testResults.filter(t => t.is_correct).length} correct out of {testResults.length} attempts
                </p>
            </div>

            {/* Test Results List */}
            <div className="space-y-4">
                {testResults.map((test) => (
                    <div key={test.id} className="bg-white rounded-lg shadow p-6">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <span className="text-sm font-medium text-indigo-600">{test.subject}</span>
                                {test.topic && <span className="text-sm text-gray-500 ml-2">• {test.topic}</span>}
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${test.is_correct
                                        ? 'bg-green-100 text-green-800'
                                        : 'bg-orange-100 text-orange-800'
                                    }`}>
                                    {test.is_correct ? '✓ Correct' : '✗ Incorrect'}
                                </span>
                                <span className="text-sm text-gray-500">
                                    {new Date(test.timestamp).toLocaleString()}
                                </span>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div>
                                <p className="text-xs text-gray-600 mb-1">Question:</p>
                                <p className="text-gray-800 font-medium">{test.question}</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="bg-blue-50 rounded-lg p-3">
                                    <p className="text-xs text-gray-600 mb-1">Student's Answer:</p>
                                    <p className="text-gray-800">{test.student_answer || 'No answer provided'}</p>
                                </div>

                                {!test.is_correct && (
                                    <div className="bg-green-50 rounded-lg p-3">
                                        <p className="text-xs text-gray-600 mb-1">Correct Answer:</p>
                                        <p className="text-gray-800">{test.correct_answer}</p>
                                    </div>
                                )}
                            </div>

                            {test.ai_feedback && (
                                <div className="bg-gray-50 rounded-lg p-3">
                                    <p className="text-xs text-gray-600 mb-1">AI Feedback:</p>
                                    <p className="text-gray-800">{test.ai_feedback}</p>
                                </div>
                            )}

                            {test.attempt_number > 1 && (
                                <div className="text-sm text-gray-600">
                                    Attempt #{test.attempt_number}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
