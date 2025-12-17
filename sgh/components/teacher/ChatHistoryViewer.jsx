// Chat History Viewer Component
export default function ChatHistoryViewer({ chatHistory, loading }) {
    if (loading) {
        return (
            <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading chat history...</p>
            </div>
        );
    }

    if (!chatHistory || chatHistory.length === 0) {
        return (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
                <p className="text-gray-600">No chat history yet</p>
                <p className="text-gray-500 text-sm mt-2">Conversations will appear here once the student starts chatting</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {chatHistory.map((chat) => (
                <div key={chat.id} className="bg-white rounded-lg shadow p-6">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <span className="text-sm font-medium text-indigo-600">{chat.subject || 'General'}</span>
                            {chat.topic && <span className="text-sm text-gray-500 ml-2">• {chat.topic}</span>}
                        </div>
                        <span className="text-sm text-gray-500">
                            {new Date(chat.timestamp).toLocaleString()}
                        </span>
                    </div>

                    <div className="space-y-3">
                        <div className="bg-blue-50 rounded-lg p-3">
                            <p className="text-xs text-gray-600 mb-1">Student:</p>
                            <p className="text-gray-800">{chat.student_message}</p>
                        </div>

                        <div className="bg-gray-50 rounded-lg p-3">
                            <p className="text-xs text-gray-600 mb-1">AI Response:</p>
                            <p className="text-gray-800">{chat.ai_response}</p>
                        </div>
                    </div>

                    {chat.is_favorite && (
                        <div className="mt-3 flex items-center text-yellow-600 text-sm">
                            <span>⭐ Marked as favorite</span>
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}
