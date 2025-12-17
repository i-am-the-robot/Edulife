// Quiz Modal Component
import { useState, useEffect, useCallback, useRef } from 'react';

export default function QuizModal({ questions, onSubmit, onClose, title = "Quiz Time!", voiceInput, speak, isListening }) {
    const [answers, setAnswers] = useState(Array(questions.length).fill(''));
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [voiceFeedback, setVoiceFeedback] = useState('');
    const hasSpokenRef = useRef(false);

    // Answer change handler
    const handleAnswerChange = useCallback((index, value) => {
        setAnswers(prev => {
            const newAnswers = [...prev];
            newAnswers[index] = value;
            return newAnswers;
        });
    }, []);

    // Navigation handlers
    const handleNext = useCallback(() => {
        if (currentQuestion < questions.length - 1) {
            setCurrentQuestion(prev => prev + 1);
            setVoiceFeedback('');
            hasSpokenRef.current = false; // Reset spoken flag for new question
        }
    }, [currentQuestion, questions.length]);

    const handlePrevious = useCallback(() => {
        if (currentQuestion > 0) {
            setCurrentQuestion(prev => prev - 1);
            setVoiceFeedback('');
            hasSpokenRef.current = false;
        }
    }, [currentQuestion]);

    const handleSubmit = useCallback(() => {
        // Check if all questions are answered
        const unanswered = answers.findIndex(a => !a.trim());
        if (unanswered !== -1) {
            setVoiceFeedback(`Please answer question ${unanswered + 1} first.`);
            setCurrentQuestion(unanswered);
            hasSpokenRef.current = false;
            return;
        }
        onSubmit(answers);
    }, [answers, onSubmit]);

    // Fuzzy match helper (Levenshtein distance based similarity)
    const calculateSimilarity = (s1, s2) => {
        const longer = s1.length > s2.length ? s1 : s2;
        const shorter = s1.length > s2.length ? s2 : s1;
        const longerLength = longer.length;
        if (longerLength === 0) {
            return 1.0;
        }

        const costs = new Array();
        for (let i = 0; i <= longer.length; i++) {
            let lastValue = i;
            for (let j = 0; j <= shorter.length; j++) {
                if (i === 0) {
                    costs[j] = j;
                } else {
                    if (j > 0) {
                        let newValue = costs[j - 1];
                        if (longer.charAt(i - 1) !== shorter.charAt(j - 1)) {
                            newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
                        }
                        costs[j - 1] = lastValue;
                        lastValue = newValue;
                    }
                }
            }
            if (i > 0) {
                costs[shorter.length] = lastValue;
            }
        }
        return (longerLength - costs[shorter.length]) / parseFloat(longerLength);
    };

    // MAP VOICE COMMANDS TO ACTIONS
    // =========================================================
    const processVoiceCommand = useCallback((transcript) => {
        const lower = transcript.toLowerCase().replace(/[.,!?;:]/g, '').trim();
        console.log('🎤 Quiz Voice Command:', lower);

        // NAVIGATION
        if (lower === 'next' || lower.includes('next question') || lower.includes('go forward')) {
            handleNext();
            return;
        }
        if (lower === 'previous' || lower === 'back' || lower.includes('go back')) {
            handlePrevious();
            return;
        }
        if (lower === 'submit' || lower.includes('submit quiz') || lower.includes('finish') || lower.includes('done')) {
            handleSubmit();
            return;
        }

        // CONTROL
        if (lower.includes('repeat') || lower.includes('read again') || lower === 'read') {
            hasSpokenRef.current = false;
            // Trigger reading by resetting spoken flag AND calling check
            // Since effect depends on [currentQuestion], and that didn't change, we need to manually trigger speak or force update.
            // Simple way: just speak it now since we have the data
            const q = questions[currentQuestion];
            if (q) {
                let textToRead = `${q.question}.`;
                if (q.type === 'multiple_choice') {
                    textToRead += "Options are: ";
                    q.options.forEach(opt => textToRead += `${opt}.`);
                }
                if (speak) speak(textToRead);
            }
            return;
        }

        // ANSWERS
        const question = questions[currentQuestion];
        let detectedAnswer = null;

        if (question.type === 'multiple_choice') {
            // 1. Direct Option Check (A, B, C, D)
            const words = lower.split(' ');
            if (lower === 'option a' || lower === 'a' || words.includes('a')) detectedAnswer = question.options[0]?.[0];
            else if (lower === 'option b' || lower === 'b' || words.includes('b')) detectedAnswer = question.options[1]?.[0];
            else if (lower === 'option c' || lower === 'c' || words.includes('c')) detectedAnswer = question.options[2]?.[0];
            else if (lower === 'option d' || lower === 'd' || words.includes('d')) detectedAnswer = question.options[3]?.[0];

            // 2. Fuzzy Content Matching
            if (!detectedAnswer) {
                let bestMatch = null;
                let bestScore = 0;

                question.options.forEach(opt => {
                    // opt is "A) Cat" => "Cat"
                    const optionText = opt.substring(3).toLowerCase().replace(/[.,!?;:]/g, '').trim();
                    const score = calculateSimilarity(lower, optionText);

                    if (score > bestScore) {
                        bestScore = score;
                        bestMatch = opt[0];
                    }

                    if (lower.includes(optionText) && optionText.length > 2) {
                        bestScore = 1.0;
                        bestMatch = opt[0];
                    }
                });

                if (bestScore > 0.6) {
                    detectedAnswer = bestMatch;
                }
            }
        }
        else if (question.type === 'true_false') {
            if (lower.includes('true') || lower.includes('yes')) detectedAnswer = 'True';
            else if (lower.includes('false') || lower.includes('no')) detectedAnswer = 'False';
        }
        else if (question.type === 'short_answer') {
            handleAnswerChange(currentQuestion, transcript);
            setVoiceFeedback(`Typed: "${transcript}"`);
            return;
        }

        if (detectedAnswer) {
            handleAnswerChange(currentQuestion, detectedAnswer);
            setVoiceFeedback(`Selected: ${detectedAnswer} `);
        } else if (question.type !== 'short_answer') {
            setVoiceFeedback(`Didn't catch that. Say "A", "B", or the answer.`);
        }

    }, [currentQuestion, questions, handleNext, handlePrevious, handleSubmit, handleAnswerChange, speak, calculateSimilarity]);


    // VOICE INPUT EFFECT from Parent
    useEffect(() => {
        if (voiceInput) {
            if (voiceInput.isFinal) {
                processVoiceCommand(voiceInput.text);
            } else {
                setVoiceFeedback(`... ${voiceInput.text}`);
            }
        }
    }, [voiceInput, processVoiceCommand]);

    // AUTO-READ QUESTION
    // =========================================================
    useEffect(() => {
        // Read question when it changes (and hasn't been spoken yet)
        if (!hasSpokenRef.current && questions[currentQuestion]) {
            const q = questions[currentQuestion];
            let textToRead = `Question ${currentQuestion + 1}. ${q.question}. `;

            if (q.type === 'multiple_choice') {
                textToRead += "Options are: ";
                q.options.forEach(opt => textToRead += `${opt}. `);
            } else if (q.type === 'true_false') {
                textToRead += "Is it True or False?";
            }

            console.log('📢 Reading Question:', textToRead);
            if (speak) speak(textToRead);
            hasSpokenRef.current = true;
        }
    }, [currentQuestion, questions, speak]);

    const question = questions[currentQuestion];
    const progress = ((currentQuestion + 1) / questions.length) * 100;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-xl relative">
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 text-white/80 hover:text-white"
                    >
                        ✕
                    </button>
                    <h2 className="text-2xl font-bold flex items-center gap-2">
                        {title}
                        {isListening && <span className="animate-pulse text-xs bg-red-500 px-2 py-1 rounded-full">REL</span>}
                    </h2>
                    <p className="text-sm opacity-90 mt-1">
                        Question {currentQuestion + 1} of {questions.length}
                    </p>
                    {/* Progress Bar */}
                    <div className="mt-4 bg-white bg-opacity-30 rounded-full h-2">
                        <div
                            className="bg-white h-2 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>

                {/* Question Content */}
                <div className="p-6">
                    <div className="mb-6">
                        <div className="flex items-start gap-3 mb-4">
                            <span className="flex-shrink-0 w-8 h-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center font-bold">
                                {currentQuestion + 1}
                            </span>
                            <p className="text-lg font-medium text-gray-800 flex-1">
                                {question.question}
                            </p>
                        </div>

                        {/* Answer Input based on question type */}
                        {question.type === 'multiple_choice' && (
                            <div className="space-y-3 ml-11">
                                {question.options.map((option, idx) => (
                                    <label
                                        key={idx}
                                        className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition ${answers[currentQuestion] === option[0]
                                            ? 'border-purple-500 bg-purple-50'
                                            : 'border-gray-200 hover:border-purple-300'
                                            }`}
                                    >
                                        <input
                                            type="radio"
                                            name={`question-${currentQuestion}`}
                                            value={option[0]}
                                            checked={answers[currentQuestion] === option[0]}
                                            onChange={(e) => handleAnswerChange(currentQuestion, e.target.value)}
                                            className="mr-3"
                                        />
                                        <span className="text-gray-700">{option}</span>
                                    </label>
                                ))}
                            </div>
                        )}

                        {question.type === 'true_false' && (
                            <div className="space-y-3 ml-11">
                                {['True', 'False'].map((option) => (
                                    <label
                                        key={option}
                                        className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition ${answers[currentQuestion] === option
                                            ? 'border-purple-500 bg-purple-50'
                                            : 'border-gray-200 hover:border-purple-300'
                                            }`}
                                    >
                                        <input
                                            type="radio"
                                            name={`question-${currentQuestion}`}
                                            value={option}
                                            checked={answers[currentQuestion] === option}
                                            onChange={(e) => handleAnswerChange(currentQuestion, e.target.value)}
                                            className="mr-3"
                                        />
                                        <span className="text-gray-700">{option}</span>
                                    </label>
                                ))}
                            </div>
                        )}

                        {question.type === 'short_answer' && (
                            <div className="ml-11">
                                <textarea
                                    value={answers[currentQuestion]}
                                    onChange={(e) => handleAnswerChange(currentQuestion, e.target.value)}
                                    placeholder="Type your answer here..."
                                    className="w-full p-4 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none resize-none"
                                    rows="4"
                                />
                            </div>
                        )}

                        {voiceFeedback && (
                            <div className="ml-11 mt-4 text-sm text-purple-600 font-medium animate-pulse">
                                🎤 {voiceFeedback}
                            </div>
                        )}
                    </div>
                </div>

                {/* Navigation Footer */}
                <div className="p-6 bg-gray-50 rounded-b-xl flex justify-between items-center border-t">
                    <button
                        onClick={handlePrevious}
                        disabled={currentQuestion === 0}
                        className="px-6 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                    >
                        ← Previous
                    </button>

                    <div className="flex gap-2">
                        {questions.map((_, idx) => (
                            <button
                                key={idx}
                                onClick={() => {
                                    setCurrentQuestion(idx);
                                    hasSpokenRef.current = false;
                                }}
                                className={`w-8 h-8 rounded-full text-sm font-medium transition ${idx === currentQuestion
                                    ? 'bg-purple-600 text-white'
                                    : answers[idx]
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-gray-200 text-gray-600'
                                    }`}
                            >
                                {idx + 1}
                            </button>
                        ))}
                    </div>

                    {currentQuestion === questions.length - 1 ? (
                        <button
                            onClick={handleSubmit}
                            className="px-8 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition font-semibold"
                        >
                            Submit Quiz
                        </button>
                    ) : (
                        <button
                            onClick={handleNext}
                            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium"
                        >
                            Next →
                        </button>
                    )}
                </div>

                {/* Voice Info */}
                <div className="bg-gray-100 p-2 text-center text-xs text-gray-500 border-t">
                    Optional: Say "Option A", "Next", "Repeat", or "Submit" to control with voice.
                </div>
            </div>
        </div>
    );
}
