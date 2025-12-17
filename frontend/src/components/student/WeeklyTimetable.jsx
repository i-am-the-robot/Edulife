import { useState, useEffect } from 'react';
import { timetableService } from '../../services/timetableService';

const WeeklyTimetable = () => {
    const [timetable, setTimetable] = useState([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);

    const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    useEffect(() => {
        loadTimetable();
    }, []);

    const loadTimetable = async () => {
        try {
            const data = await timetableService.getTimetable();
            setTimetable(data);
        } catch (error) {
            console.error('Failed to load timetable:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerate = async () => {
        setGenerating(true);
        try {
            await timetableService.generateTimetable();
            await loadTimetable();
            alert('Timetable generated successfully!');
        } catch (error) {
            alert('Failed to generate timetable');
        } finally {
            setGenerating(false);
        }
    };

    const handleComplete = async (slotId) => {
        try {
            await timetableService.completeSlot(slotId);
            await loadTimetable();
        } catch (error) {
            alert('Failed to mark as complete');
        }
    };

    const getActivityColor = (type) => {
        const colors = {
            study: 'bg-blue-100 border-blue-300 text-blue-700',
            quiz: 'bg-purple-100 border-purple-300 text-purple-700',
            break: 'bg-green-100 border-green-300 text-green-700'
        };
        return colors[type] || colors.study;
    };

    const getActivityIcon = (type) => {
        const icons = { study: '📚', quiz: '📝', break: '☕' };
        return icons[type] || '📚';
    };

    const groupByDay = () => {
        const grouped = {};
        DAYS.forEach(day => { grouped[day] = []; });
        timetable.forEach(slot => {
            if (grouped[slot.day_of_week]) {
                grouped[slot.day_of_week].push(slot);
            }
        });
        return grouped;
    };

    if (loading) return <div className="text-gray-500">Loading timetable...</div>;

    const groupedTimetable = groupByDay();

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-800">📅 Weekly Timetable</h3>
                <button
                    onClick={handleGenerate}
                    disabled={generating}
                    className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:opacity-90 disabled:opacity-50 transition"
                >
                    {generating ? 'Generating...' : '🤖 Generate AI Schedule'}
                </button>
            </div>

            {timetable.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                    No timetable yet. Click "Generate AI Schedule" to create one!
                </p>
            ) : (
                <div className="space-y-4">
                    {DAYS.map(day => (
                        <div key={day} className="border border-gray-200 rounded-lg p-4">
                            <h4 className="font-semibold text-gray-700 mb-3">{day}</h4>
                            {groupedTimetable[day].length === 0 ? (
                                <p className="text-sm text-gray-400">No activities</p>
                            ) : (
                                <div className="space-y-2">
                                    {groupedTimetable[day].map(slot => (
                                        <div
                                            key={slot.id}
                                            className={`border-l-4 p-3 rounded ${getActivityColor(slot.activity_type)} ${slot.is_completed ? 'opacity-50' : ''
                                                }`}
                                        >
                                            <div className="flex justify-between items-start">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span>{getActivityIcon(slot.activity_type)}</span>
                                                        <span className="font-semibold text-sm">
                                                            {slot.start_time} - {slot.end_time}
                                                        </span>
                                                        {slot.subject && (
                                                            <span className="text-xs bg-white px-2 py-1 rounded">
                                                                {slot.subject}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-sm">{slot.description}</p>
                                                    {slot.focus_topic && (
                                                        <p className="text-xs opacity-75 mt-1">Focus: {slot.focus_topic}</p>
                                                    )}
                                                </div>
                                                {!slot.is_completed && (
                                                    <button
                                                        onClick={() => handleComplete(slot.id)}
                                                        className="ml-3 px-3 py-1 bg-white border border-gray-300 rounded text-xs hover:bg-gray-50 transition"
                                                    >
                                                        ✓ Done
                                                    </button>
                                                )}
                                                {slot.is_completed && (
                                                    <span className="ml-3 text-green-600 text-sm">✓ Completed</span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default WeeklyTimetable;
