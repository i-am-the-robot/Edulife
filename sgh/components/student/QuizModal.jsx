// Quiz Modal Component
import { useState } from 'react';

export default function QuizModal({ questions, onSubmit, onClose, title = "Quiz Time!" }) {
    const [answers, setAnswers] = useState(Array(questions.length).fill(''));
    const [currentQuestion, setCurrentQuestion] = useState(0);

    const handleAnswerChange = (index, value) => {
        const newAnswers = [...answers];
        newAnswers[index] = value;
        setAnswers(newAnswers);
    };

    const handleNext = () => {
        if (currentQuestion < questions.length - 1) {
            setCurrentQuestion(currentQuestion + 1);
        }
    };

    const handlePrevious = () => {
        if (currentQuestion > 0) {
            setCurrentQuestion(currentQuestion - 1);
        }
    };

    const handleSubmit = () => {
        // Check if all questions are answered
        const unanswered = answers.findIndex(a => !a.trim());
        if (unanswered !== -1) {
            alert(`Please answer question ${unanswered + 1} before submitting.`);
            setCurrentQuestion(unanswered);
            return;
        }
        onSubmit(answers);
    };

    const question = questions[currentQuestion];
    const progress = ((currentQuestion + 1) / questions.length) * 100;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-xl">
                    <h2 className="text-2xl font-bold">{title}</h2>
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
                                onClick={() => setCurrentQuestion(idx)}
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
            </div>
        </div>
    );
}
