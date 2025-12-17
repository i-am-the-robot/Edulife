// AI Chat Interface Component
import { useState, useEffect, useRef, useCallback } from 'react';
import { chatService } from '../../services/chatService';
import { studentService } from '../../services/studentService';
import { useAuth } from '../../context/AuthContext';
import QuizModal from './QuizModal';
import { useVoiceChat } from '../../hooks/useVoiceChat';
import api from '../../services/api';

export default function ChatInterface({ initialSessionId = null, taskData = null, initialPrompt = null }) {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [subject, setSubject] = useState('');
    const [sessionId, setSessionId] = useState(initialSessionId);
    const [loading, setLoading] = useState(false);
    const [loadingSession, setLoadingSession] = useState(false);
    const [pendingTest, setPendingTest] = useState(null);
    const [testAnswer, setTestAnswer] = useState('');
    const messagesEndRef = useRef(null);
    const { user } = useAuth();
    const [taskInitialized, setTaskInitialized] = useState(false);

    // Ref for session ID to avoid stale closures in voice callback
    const sessionIdRef = useRef(initialSessionId);
    useEffect(() => { sessionIdRef.current = sessionId; }, [sessionId]);

    // Assignment study session state
    const [conversationCount, setConversationCount] = useState(0);
    const [showQuiz, setShowQuiz] = useState(false);
    const [quizQuestions, setQuizQuestions] = useState([]);
    const [quizType, setQuizType] = useState('periodic'); // 'periodic' or 'final'
    const [currentCharIndex, setCurrentCharIndex] = useState(-1);
    const [showFinalAssessment, setShowFinalAssessment] = useState(false);
    const [interimTranscript, setInterimTranscript] = useState(''); // Real-time transcription

    const [responseToSpeak, setResponseToSpeak] = useState(null);

    const [quizVoiceInput, setQuizVoiceInput] = useState(null);

    // Voice chat handler with real-time transcription
    // Voice chat handler with streaming response for low latency
    const handleVoiceInput = useCallback(async (transcript, isFinal) => {
        console.log('📝 Voice input:', { transcript, isFinal });

        // If Quiz is active, route voice there
        if (showQuiz) {
            setQuizVoiceInput({ text: transcript, isFinal });
            return;
        }

        if (!isFinal) {
            setInterimTranscript(transcript);
            return;
        }

        // Final transcript - submit to AI
        setInterimTranscript('');
        setLoading(true);
        setMessages((prev) => [...prev, { role: 'user', content: transcript }]);
        setCurrentCharIndex(-1);

        try {
            console.log('🌐 Streaming from API:', transcript);
            const currentSessionId = sessionIdRef.current;
            const token = sessionStorage.getItem('token'); // Get auth token directly

            // Use fetch for streaming support (axios doesn't support streaming well in browser)
            const response = await fetch(`http://127.0.0.1:8000/api/student/chat/voice?text=${encodeURIComponent(transcript)}${currentSessionId ? `&session_id=${currentSessionId}` : ''}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Failed to connect to voice endpoint');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiResponseText = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (!line.trim()) continue;

                    try {
                        const data = JSON.parse(line);
                        console.log('📦 Stream chunk:', data);

                        if (data.type === 'session_info') {
                            // Update session ID if new
                            if (data.session_id && !currentSessionId) {
                                setSessionId(data.session_id);
                            }
                        } else if (data.type === 'response') {
                            // TUtor Response (Main text)
                            aiResponseText = data.content;

                            // Add to UI immediately
                            setMessages((prev) => [
                                ...prev,
                                {
                                    role: 'assistant',
                                    content: aiResponseText,
                                    isVoice: true
                                },
                            ]);

                            // SPEAK IMMEDIATELY
                            setResponseToSpeak(aiResponseText);

                        } else if (data.type === 'control') {
                            // Background Agent Actions
                            const newData = data.data; // Wrapper inside control

                            // 1. Quiz Trigger
                            if (newData.quiz) {
                                console.log('🎯 Quiz triggered via stream:', newData.quiz);
                                // Small delay to let speech start first
                                setTimeout(() => {
                                    setQuizQuestions(newData.quiz.questions);
                                    setQuizType('periodic');
                                    setShowQuiz(true);
                                }, 1000);
                            }

                            // 2. Schedule Created
                            if (newData.schedule_msg) {
                                // Append to message content
                                setMessages(prev => {
                                    const last = prev[prev.length - 1];
                                    if (last && last.role === 'assistant') {
                                        return [
                                            ...prev.slice(0, -1),
                                            { ...last, content: last.content + newData.schedule_msg }
                                        ];
                                    }
                                    return prev;
                                });
                            }

                            // 3. Badges
                            if (newData.new_badges && newData.new_badges.length > 0) {
                                // Just log for now, frontend might have a badge toast component
                                console.log("🏆 New Badges:", newData.new_badges);
                            }
                        }

                    } catch (e) {
                        console.warn('⚠️ Stream parse warning (ignoring):', e.message);
                    }
                }
            }

        } catch (error) {
            console.error('❌ Voice chat critical error:', error);
            // Only show error to user if we haven't received ANY response yet
            // If we already streamed text, it's likely just a chunk error at the end
            setMessages(prev => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content.length > 0) {
                    return prev; // Don't append error if we already have content
                }
                const errorMsg = "Sorry, I couldn't process that. Please try again!";
                setResponseToSpeak(errorMsg);
                return [...prev, { role: 'assistant', content: errorMsg }];
            });
        } finally {
            setLoading(false);
        }
    }, [showQuiz]);


    // Helper to render message content with typewriter effect and markdown images
    const renderMessageContent = (message, index) => {
        const isLastMessage = index === messages.length - 1;
        const isAISpeaking = isLastMessage && message.role === 'assistant' && isSpeaking && currentCharIndex >= 0;

        let contentToDisplay = message.content;

        if (isAISpeaking) {
            const sliceIndex = Math.min(currentCharIndex + 5, message.content.length);
            contentToDisplay = message.content.slice(0, sliceIndex) + ' ▋';
        }

        // Parse markdown images: ![alt](url) -> <img src="url" alt="alt" />
        // Also simple bold parsing: **text** -> <b>text</b> (already done by backend but safe to keep)
        const parseMarkdown = (text) => {
            let html = text;
            // Image parser: ![alt](url)
            html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="rounded-lg shadow-md max-w-full my-2 block" />');

            // Clean up: Remove any raw Pollinations URLs that might have leaked (e.g. from examples)
            // But don't remove if they are inside the src attribute of the img tag we just created!
            // Actually, simply replacing the markdown usage is enough. 
            // If the AI outputs "Here is: https://image.pollinations...", we might want to hide/convert that too.

            // Auto-convert raw image URLs to images if they are on their own line
            html = html.replace(/(^|\n)(https:\/\/image\.pollinations\.ai\/[^\s]+)(\n|$)/g, '$1<img src="$2" alt="Generated Image" class="rounded-lg shadow-md max-w-full my-2 block" />$3');

            // Bold parser (backup)
            html = html.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
            return html;
        };

        return (
            <div
                className="text-gray-800 whitespace-pre-wrap"
                dangerouslySetInnerHTML={{ __html: parseMarkdown(contentToDisplay) }}
            />
        );
    };

    // Initialize voice chat with manual control
    // Start disabled by default
    const [voiceEnabled, setVoiceEnabled] = useState(false);

    // Memoize handleVoiceInput to prevent re-creation
    // This is critical for the voice hook stability
    const stableHandleVoiceInput = useCallback((transcript, isFinal) => {
        handleVoiceInput(transcript, isFinal);
    }, [handleVoiceInput]);

    const {
        isListening,
        isSpeaking,
        isSupported,
        error: voiceError,
        speak,
        stopSpeaking,
        pauseListening,
        resumeListening,
        startListening,
        stopListening
    } = useVoiceChat(
        stableHandleVoiceInput, // Callback for transcripts
        voiceEnabled      // Feature toggle
    );

    // Effect to trigger speech when AI responds
    useEffect(() => {
        if (responseToSpeak && speak) {
            console.log('📢 Triggering speech for:', responseToSpeak);
            speak(responseToSpeak, (index) => {
                setCurrentCharIndex(index);
            });
            setResponseToSpeak(null); // Clear after triggering
        }
    }, [responseToSpeak, speak]);

    // Log voice status for debugging
    useEffect(() => {
        console.log('Voice Status:', { isSupported, isListening, isSpeaking, voiceError, voiceEnabled });
    }, [isSupported, isListening, isSpeaking, voiceError, voiceEnabled]);

    // Check if we're continuing a session (don't auto-prompt)
    const searchParams = new URLSearchParams(window.location.search);
    const isContinuing = searchParams.get('continuing') === 'true';

    // Track if initial prompt has been sent
    const hasStartedConversation = useRef(false);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load previous session messages if initialSessionId is provided
    useEffect(() => {
        if (initialSessionId) {
            loadSessionMessages(initialSessionId);
        } else if (!sessionId && !taskData) {
            // New Logic: Check for latest session to resume (Cross-device continuity)
            const fetchLatestSession = async () => {
                try {
                    const sessions = await studentService.getChatSessions();
                    if (sessions && sessions.length > 0) {
                        const lastSession = sessions[0];

                        // Check if session is recent (within 24 hours)
                        const lastMessageTime = new Date(lastSession.last_message_time);
                        const hoursSinceLastMessage = (Date.now() - lastMessageTime) / (1000 * 60 * 60);

                        if (hoursSinceLastMessage < 24) {
                            console.log("🔄 Resuming recent session:", lastSession.session_id);
                            setSessionId(lastSession.session_id);
                            // Load the session messages immediately
                            await loadSessionMessages(lastSession.session_id);
                            // Optional: Resume subject too
                            if (lastSession.subject && lastSession.subject !== "General") {
                                setSubject(lastSession.subject);
                            }
                        } else {
                            console.log("⏰ Last session too old, starting fresh");
                        }
                    }
                } catch (err) {
                    console.error("Failed to resume session:", err);
                }
            };
            fetchLatestSession();
        }
    }, [initialSessionId, taskData]); // Runs on mount (sessionId check inside)

    // Sync session ID to URL so it persists on refresh
    useEffect(() => {
        if (sessionId) {
            const url = new URL(window.location);
            if (url.searchParams.get('session') !== sessionId) {
                url.searchParams.set('session', sessionId);
                window.history.replaceState({}, '', url);
            }
        }
    }, [sessionId]);

    // Auto-start conversation about task if taskData is provided AND not continuing
    // Auto-start conversation about task if taskData is provided AND not continuing
    useEffect(() => {
        let timeoutId;
        if (taskData && !hasStartedConversation.current && !loading && !isContinuing) {
            // Use timeout to prevent double-fire in Strict Mode (mount/unmount/mount)
            timeoutId = setTimeout(() => {
                hasStartedConversation.current = true;
                startTaskConversation(taskData);
            }, 50);
        }
        return () => {
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [taskData, loading, isContinuing]);

    // Auto-send initial prompt from schedule
    useEffect(() => {
        let timeoutId;
        if (initialPrompt && !hasStartedConversation.current && !loading) {
            timeoutId = setTimeout(() => {
                hasStartedConversation.current = true;
                handleSendMessage(initialPrompt);
            }, 50);
        }
        return () => {
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [initialPrompt, loading]);

    const startTaskConversation = async (task) => {
        setLoading(true);

        // Send task context to AI as the first message
        const taskMessage = `I need help with my assignment: "${task.title}". The assignment is: ${task.description}. Can you help me understand this topic?`;

        // Add user message to chat
        setMessages([{ role: 'user', content: taskMessage }]);

        try {
            const response = await chatService.sendMessage(
                user.id,
                taskMessage,
                subject || null,
                sessionId
            );

            // Set session ID if new
            if (!sessionId && response.session_id) {
                setSessionId(response.session_id);
            }

            // Add AI response to chat
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: response.ai_response },
            ]);

            // Check if test was generated
            if (response.tests_generated && response.tests_generated.length > 0) {
                setPendingTest(response.tests_generated[0]);
            }
        } catch (error) {
            console.error('Task conversation error:', error);
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: "I'm having trouble connecting. Let me try again!",
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const loadSessionMessages = async (sessionIdToLoad) => {
        setLoadingSession(true);
        try {
            const data = await studentService.getSessionMessages(sessionIdToLoad);

            // Convert chat history to message format
            const loadedMessages = [];
            if (data && data.length > 0 && data[0].conversations) {
                // Backend now returns in chronological order when filtering by session
                data[0].conversations.forEach(conv => {
                    loadedMessages.push({ role: 'user', content: conv.student_message });
                    loadedMessages.push({ role: 'assistant', content: conv.ai_response });

                    // Set subject from first message
                    if (!subject && conv.subject) {
                        setSubject(conv.subject);
                    }
                });
            }

            setMessages(loadedMessages);
        } catch (error) {
            console.error('Error loading session:', error);
        } finally {
            setLoadingSession(false);
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim() || loading) return;

        const userMessage = inputMessage.trim();
        setInputMessage('');
        setLoading(true);

        // Add user message to chat
        setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

        // Auto-retry logic
        const maxRetries = 3;
        let retryCount = 0;
        let success = false;

        while (retryCount < maxRetries && !success) {
            try {
                const response = await chatService.sendMessage(
                    user.id,
                    userMessage,
                    subject || null,
                    sessionId
                );

                // Set session ID if new
                if (!sessionId && response.session_id) {
                    setSessionId(response.session_id);
                }

                // Add AI response to chat
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: response.ai_response },
                ]);

                // Increment conversation count if this is an assignment session
                if (taskData) {
                    const newCount = conversationCount + 1;
                    setConversationCount(newCount);

                    // Check if we should trigger periodic quiz (every 5 exchanges)
                    if (newCount % 5 === 0 && newCount > 0) {
                        await triggerPeriodicQuiz();
                    }
                }

                // Check if test was generated
                if (response.tests_generated && response.tests_generated.length > 0) {
                    setPendingTest(response.tests_generated[0]);
                }

                success = true;
            } catch (error) {
                retryCount++;
                console.error(`Chat error (attempt ${retryCount}/${maxRetries}):`, error);

                if (retryCount < maxRetries) {
                    // Show reconnecting message
                    setMessages((prev) => [
                        ...prev,
                        {
                            role: 'system',
                            content: `🔄 Connection lost! Attempting to reconnect... (Attempt ${retryCount}/${maxRetries})`,
                            isRetrying: true
                        },
                    ]);

                    // Wait before retry (exponential backoff: 1s, 2s, 4s)
                    await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retryCount - 1)));

                    // Remove retry message before next attempt
                    setMessages((prev) => prev.filter(msg => !msg.isRetrying));
                } else {
                    // All retries failed
                    setMessages((prev) => [
                        ...prev,
                        {
                            role: 'assistant',
                            content: "😔 I'm having trouble connecting right now. Please check your internet connection and try again!",
                        },
                    ]);
                }
            }
        }

        setLoading(false);
    };

    const handleSubmitTest = async (e) => {
        e.preventDefault();
        if (!testAnswer.trim() || !pendingTest) return;

        setLoading(true);

        try {
            const response = await chatService.submitTestAnswer(
                pendingTest.test_id,
                testAnswer
            );

            // Add test result to chat
            setMessages((prev) => [
                ...prev,
                {
                    role: 'system',
                    content: response.feedback,
                    isCorrect: response.is_correct,
                },
            ]);

            setPendingTest(null);
            setTestAnswer('');
        } catch (error) {
            console.error('Test submission error:', error);
        } finally {
            setLoading(false);
        }
    };

    // ============================================================================
    // QUIZ HANDLING FUNCTIONS
    // ============================================================================

    const triggerPeriodicQuiz = async () => {
        try {
            // Generate context-aware quiz questions from backend
            const quizData = await studentService.generateQuiz(sessionId, subject);

            if (quizData && quizData.questions && quizData.questions.length > 0) {
                setQuizQuestions(quizData.questions);
                setQuizType('periodic');
                setShowQuiz(true);
            } else {
                console.error('No quiz questions generated');
            }
        } catch (error) {
            console.error('Error triggering periodic quiz:', error);
            // Fallback to simple question if API fails
            setQuizQuestions([
                {
                    type: 'true_false',
                    question: 'Did you understand the concepts we discussed?',
                    correct_answer: 'True'
                }
            ]);
            setQuizType('periodic');
            setShowQuiz(true);
        }
    };

    const handleQuizSubmit = async (answers) => {
        try {
            setLoading(true);

            if (taskData) {
                // Assignment-based quiz submission
                if (quizType === 'periodic') {
                    // Submit periodic quiz
                    const result = await studentService.submitQuiz(taskData.taskId, answers);

                    // Show feedback
                    setMessages((prev) => [
                        ...prev,
                        {
                            role: 'system',
                            content: `Quiz completed! Score: ${result.score}% ${result.passed ? '✅ Great job!' : '📚 Keep studying!'}`,
                            isCorrect: result.passed
                        }
                    ]);
                } else if (quizType === 'final') {
                    // Submit final assessment
                    const result = await studentService.submitFinalAssessment(taskData.taskId, answers);

                    // Show completion message
                    setMessages((prev) => [
                        ...prev,
                        {
                            role: 'system',
                            content: `🎉 Assignment completed! Final score: ${result.score}%\n\n${result.summary}\n\nYour work has been submitted to your teacher!`,
                            isCorrect: result.passed
                        }
                    ]);
                }
            } else {
                // Normal chat quiz - just show feedback without backend submission
                // Calculate simple score
                let correct = 0;
                quizQuestions.forEach((q, idx) => {
                    if (answers[idx] === q.correct_answer) {
                        correct++;
                    }
                });
                const score = Math.round((correct / quizQuestions.length) * 100);
                const passed = score >= 70;

                setMessages((prev) => [
                    ...prev,
                    {
                        role: 'system',
                        content: `Quiz completed! You got ${correct} out of ${quizQuestions.length} correct (${score}%) ${passed ? '✅ Great job!' : '📚 Keep practicing!'}`,
                        isCorrect: passed
                    }
                ]);
            }

            setShowQuiz(false);
            setQuizQuestions([]);
        } catch (error) {
            console.error('Error submitting quiz:', error);
            alert('Failed to submit quiz. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleMarkAsDone = async () => {
        if (!taskData) {
            console.error('No taskData available');
            return;
        }

        console.log('handleMarkAsDone called with taskData:', taskData);

        try {
            setLoading(true);

            // Generate final assessment
            console.log('Calling completeAssignment with taskId:', taskData.taskId);
            const result = await studentService.completeAssignment(taskData.taskId);

            console.log('completeAssignment result:', result);

            if (result.questions && result.questions.length > 0) {
                console.log('Setting quiz questions:', result.questions);
                setQuizQuestions(result.questions);
                setQuizType('final');
                setShowQuiz(true);
            } else {
                console.error('No questions in result:', result);
                alert('Failed to generate final assessment. Please try again.');
            }
        } catch (error) {
            console.error('Error generating final assessment:', error);
            console.error('Error details:', error.response?.data || error.message);
            alert(`Failed to generate final assessment: ${error.response?.data?.detail || error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleTakeTest = async () => {
        if (loading) return;

        try {
            setLoading(true);

            if (taskData) {
                // Assignment session - generate final assessment
                const result = await studentService.completeAssignment(taskData.taskId);

                if (result.questions && result.questions.length > 0) {
                    setQuizQuestions(result.questions);
                    setQuizType('final');
                    setShowQuiz(true);
                } else {
                    alert('Failed to generate final assessment. Please try again.');
                }
            } else {
                // Regular session - generate context-aware quiz from backend
                try {
                    const quizData = await studentService.generateQuiz(sessionId, subject);

                    if (quizData && quizData.questions && quizData.questions.length > 0) {
                        setQuizQuestions(quizData.questions);
                        setQuizType('periodic');
                        setShowQuiz(true);
                    } else {
                        // Fallback if no questions generated
                        alert('Not enough conversation history to generate a quiz. Chat more first!');
                    }
                } catch (error) {
                    console.error('Quiz generation error:', error);
                    alert('Failed to generate quiz. Please try again.');
                }
            }
        } catch (error) {
            console.error('Error in handleTakeTest:', error);
            alert('Failed to generate test. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-t-lg">
                <div className="flex justify-between items-center">
                    <div className="flex-1">
                        <h2 className="text-xl font-bold">AI Learning Buddy 🤖</h2>
                        <p className="text-sm opacity-90">Ask me anything! I'm here to help you learn.</p>
                        {sessionId && messages.length > 0 && (
                            <p className="text-xs opacity-75 mt-1">
                                📝 Continuing conversation from {new Date(messages[0].timestamp || Date.now()).toLocaleDateString()}
                            </p>
                        )}
                    </div>
                    <div className="flex gap-2">
                        {sessionId && (
                            <button
                                onClick={() => {
                                    setSessionId(null);
                                    setMessages([]);
                                    setSubject('');
                                    const url = new URL(window.location);
                                    url.searchParams.delete('session');
                                    window.history.replaceState({}, '', url);
                                }}
                                className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg font-semibold transition flex items-center gap-2 backdrop-blur-sm"
                                title="Start a new conversation"
                            >
                                <span>🆕</span>
                                <span className="hidden sm:inline">New Chat</span>
                            </button>
                        )}
                        <button
                            onClick={handleTakeTest}
                            disabled={loading}
                            className="px-6 py-2 bg-white text-purple-600 rounded-lg hover:bg-gray-100 disabled:opacity-50 font-semibold transition flex items-center gap-2"
                        >
                            <span>📝</span>
                            Take Test
                        </button>
                    </div>
                </div>
            </div>

            {/* Subject Selector */}
            <div className="p-4 border-b">
                <select
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                >
                    <option value="">All Subjects</option>
                    <option value="Mathematics">Mathematics</option>
                    <option value="Science">Science</option>
                    <option value="English">English</option>
                    <option value="History">History</option>
                    <option value="Art">Art</option>
                </select>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center text-gray-500 mt-8">
                        <p className="text-lg">👋 Hi there!</p>
                        <p className="mt-2">Start a conversation by asking me a question!</p>
                    </div>
                )}

                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        {message.role === 'user' ? (
                            <div
                                className={`max-w-[80%] rounded-lg p-3 bg-blue-500 text-white`}
                            >
                                <p className="whitespace-pre-wrap">{message.content}</p>
                            </div>
                        ) : (
                            <div className="flex items-start gap-3 max-w-[80%]">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold flex-shrink-0">
                                    AI
                                </div>
                                <div
                                    className={`flex-1 rounded-lg p-3 shadow-sm ${message.role === 'system'
                                        ? message.isCorrect
                                            ? 'bg-green-100 text-green-800 border border-green-300'
                                            : 'bg-orange-100 text-orange-800 border border-orange-300'
                                        : 'bg-gray-100 text-gray-800'
                                        }`}
                                >
                                    {renderMessageContent(message, index)}
                                    {message.timestamp && (
                                        <span className="text-xs text-gray-400 mt-2 block">
                                            {new Date(message.timestamp).toLocaleTimeString()}
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-lg p-3">
                            <div className="flex space-x-2">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Test Question */}
            {pendingTest && (
                <div className="p-4 bg-purple-50 border-t border-purple-200">
                    <div className="mb-2">
                        <p className="font-semibold text-purple-800">Practice Question:</p>
                        <p className="text-gray-700 mt-1">{pendingTest.question}</p>
                    </div>
                    <form onSubmit={handleSubmitTest} className="flex gap-2">
                        <input
                            type="text"
                            value={testAnswer}
                            onChange={(e) => setTestAnswer(e.target.value)}
                            placeholder="Your answer..."
                            className="flex-1 px-4 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50"
                        >
                            Submit
                        </button>
                    </form>
                </div>
            )}

            {/* Real-time Transcription Display */}
            {interimTranscript && isListening && (
                <div className="p-4 bg-blue-50 border-t border-blue-200">
                    <div className="flex items-center gap-2">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                        </span>
                        <span className="text-sm text-blue-600 font-medium">You're saying:</span>
                    </div>
                    <p className="mt-2 text-gray-800 italic">"{interimTranscript}"</p>
                    <p className="mt-1 text-xs text-gray-500">Stop speaking for 2 seconds to submit...</p>
                </div>
            )}

            {/* Input Form */}
            <form onSubmit={handleSendMessage} className="p-4 border-t">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder="Type your message..."
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={loading || !inputMessage.trim()}
                        className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition disabled:opacity-50 font-semibold"
                    >
                        Send
                    </button>
                </div>
                {taskData && conversationCount > 0 && (
                    <div className="mt-2 text-xs text-gray-500 text-center">
                        {conversationCount} message{conversationCount !== 1 ? 's' : ''} exchanged
                        {conversationCount % 5 === 4 && ' • Quiz coming up next!'}
                    </div>
                )}

                {/* Voice Status Indicator */}
                {isSupported && (
                    <div className="mt-3 flex flex-col items-center gap-2">
                        <div className="flex items-center justify-center gap-2 text-sm">
                            {isSpeaking ? (
                                <div className="flex items-center gap-2 text-purple-600 animate-pulse">
                                    <span className="text-lg">🔊</span>
                                    <span className="font-medium">AI is speaking...</span>
                                </div>
                            ) : isListening ? (
                                <div className="flex items-center gap-2 text-green-600">
                                    <span className="relative flex h-3 w-3">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                                    </span>
                                    <span className="font-medium">🎤 Listening...</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 text-gray-400">
                                    <span>🎤</span>
                                    <span>Voice inactive</span>
                                </div>
                            )}
                        </div>

                        {/* Voice Toggle Button */}
                        <button
                            type="button"
                            onClick={() => {
                                const newState = !voiceEnabled;
                                console.log('🔘 Voice Button Clicked! Current:', voiceEnabled, '→ New:', newState);
                                setVoiceEnabled(newState);

                                // Explicitly handle stop/start
                                if (voiceEnabled) {
                                    console.log('🛑 Stopping speech & listening...');
                                    stopSpeaking();
                                    stopListening();
                                } else {
                                    console.log('▶️ Starting voice mode...');
                                    startListening();
                                }
                            }}
                            className={`px-4 py-2 rounded-lg font-medium transition ${voiceEnabled
                                ? 'bg-red-500 hover:bg-red-600 text-white'
                                : 'bg-green-500 hover:bg-green-600 text-white'
                                }`}
                        >
                            {voiceEnabled ? '🔇 Stop Voice Chat' : '🎤 Start Voice Chat'}
                        </button>
                    </div>
                )}

                {/* Voice Error */}
                {voiceError && (
                    <div className="mt-2 text-xs text-orange-600 text-center">
                        ⚠️ {voiceError}
                    </div>
                )}
            </form>

            {/* Quiz Modal */}
            {showQuiz && quizQuestions.length > 0 && (
                <QuizModal
                    questions={quizQuestions}
                    onSubmit={handleQuizSubmit}
                    onClose={() => setShowQuiz(false)}
                    title={quizType === 'final' ? '🎓 Final Assessment' : '📝 Quick Quiz!'}
                    voiceInput={quizVoiceInput}
                    speak={speak}
                    isListening={isListening}
                />
            )}
        </div>
    );
}
