import { useState, useEffect } from 'react';
import { gamificationService } from '../../services/gamificationService';

const AchievementBadge = ({ fullPage = false }) => {
    const [achievements, setAchievements] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAchievements();
    }, []);

    const loadAchievements = async () => {
        try {
            const data = await gamificationService.getAchievements();
            console.log("🏆 Achievements Data:", data);
            setAchievements(data);
        } catch (error) {
            console.error('Failed to load achievements:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="text-gray-500">Loading...</div>;
    if (!achievements) return null;

    // Normalize data structure (handle both array and object responses)
    let displayData = {
        unlocked_count: 0,
        total_count: 0,
        total_points: 0,
        achievements: []
    };

    if (Array.isArray(achievements)) {
        // Handle array response (legacy or direct list)
        displayData.achievements = achievements;
        displayData.total_count = achievements.length;
        displayData.unlocked_count = achievements.filter(a => a.unlocked).length;
        displayData.total_points = achievements.reduce((sum, a) => sum + (a.points || 0), 0);
    } else {
        // Handle object response (new structure)
        displayData = achievements;
    }

    const { unlocked_count, total_count, total_points, achievements: items } = displayData;

    const getRarityColor = (rarity) => {
        const colors = {
            common: 'bg-gray-100 border-gray-300 text-gray-700',
            rare: 'bg-blue-100 border-blue-300 text-blue-700',
            epic: 'bg-purple-100 border-purple-300 text-purple-700',
            legendary: 'bg-yellow-100 border-yellow-300 text-yellow-700'
        };
        return colors[rarity] || colors.common;
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-gray-800">🏆 Achievements (System Active)</h3>
                <div className="text-sm text-gray-600">
                    {unlocked_count} / {total_count} unlocked
                </div>
            </div>

            <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{total_points} points</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                        className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all"
                        style={{ width: `${total_count > 0 ? (unlocked_count / total_count) * 100 : 0}%` }}
                    ></div>
                </div>
            </div>

            <div className={`grid gap-3 ${fullPage ? 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4' : 'grid-cols-2 md:grid-cols-3'}`}>
                {items?.map((ach) => (
                    <div
                        key={ach.id}
                        className={`border-2 rounded-lg p-3 transition-all ${ach.unlocked
                            ? getRarityColor(ach.rarity)
                            : 'bg-gray-50 border-gray-200 opacity-50'
                            }`}
                    >
                        <div className="text-3xl mb-2 text-center">{ach.icon}</div>
                        <h4 className="font-semibold text-sm text-center mb-1">{ach.name}</h4>
                        <p className="text-xs text-center opacity-75">{ach.description}</p>
                        <div className="text-center mt-2">
                            <span className="text-xs font-bold">{ach.points} pts</span>
                        </div>
                        {ach.unlocked && ach.is_new && (
                            <div className="mt-2 text-center">
                                <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">NEW!</span>
                            </div>
                        )}
                    </div>
                ))}
                
                {(!items || items.length === 0) && (
                    <div className="col-span-full border border-red-300 bg-red-50 p-4 rounded text-center">
                        <p className="text-red-600 font-bold">No achievements found.</p>
                        {displayData.debug_info && (
                            <div className="mt-2 text-xs text-left bg-white p-2 rounded border border-red-200 overflow-auto">
                                <p><strong>Debug Info:</strong></p>
                                <p>DB Path: {displayData.debug_info.db_path}</p>
                                <p>Found: {displayData.debug_info.achievements_found} items</p>
                                <p>Please send this screenshot to the developer.</p>
                            </div>
                        )}
                        {!displayData.debug_info && (
                            <p className="text-xs text-gray-500 mt-2">Backend returned 0 items (No debug info)</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AchievementBadge;
