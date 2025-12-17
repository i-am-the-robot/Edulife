import { useState, useEffect } from 'react';
import { gamificationService } from '../../services/gamificationService';

// Define all possible achievements matching backend logic
const ALL_ACHIEVEMENTS = [
    // Session-based
    { id: 'first_steps', name: "First Steps", description: "Completed your first session", icon: "🌟", points: 10, type: 'session', threshold: 1 },
    { id: 'curious_learner', name: "Curious Learner", description: "Completed 10 sessions", icon: "📚", points: 20, type: 'session', threshold: 10 },
    { id: 'chat_master', name: "Chat Master", description: "Completed 50 sessions", icon: "🎓", points: 50, type: 'session', threshold: 50 },
    { id: 'conversation_king', name: "Conversation King", description: "Completed 100 sessions", icon: "👑", points: 100, type: 'session', threshold: 100 },

    // Test-based
    { id: 'test_taker', name: "Test Taker", description: "Completed 5 tests", icon: "📝", points: 15, type: 'test', threshold: 5 },
    { id: 'getting_good', name: "Getting Good", description: "Answered 10 questions correctly", icon: "💡", points: 30, type: 'test-correct', threshold: 10 },
    { id: 'test_champion', name: "Test Champion", description: "90%+ success rate", icon: "🏆", points: 100, type: 'test-success', threshold: 0.9 },

    // Streak-based
    { id: 'streak_keeper', name: "Streak Keeper", description: "Active for 3 days", icon: "🔥", points: 20, type: 'streak', threshold: 3 },
    { id: 'week_warrior', name: "Week Warrior", description: "Active for 7 days", icon: "⭐", points: 50, type: 'streak', threshold: 7 },
    { id: 'month_master', name: "Month Master", description: "Active for 30 days", icon: "🎖️", points: 100, type: 'streak', threshold: 30 },

    // Engagement-based
    { id: 'rising_star', name: "Rising Star", description: "Earned 100+ engagement points", icon: "🌟", points: 80, type: 'engagement', threshold: 100 },
    { id: 'high_flyer', name: "High Flyer", description: "Earned 200+ engagement points", icon: "🚀", points: 150, type: 'engagement', threshold: 200 },
    { id: 'elite_scholar', name: "Elite Scholar", description: "Earned 500+ engagement points", icon: "🎓", points: 300, type: 'engagement', threshold: 500 },
    { id: 'legendary_learner', name: "Legendary Learner", description: "Earned 1000+ engagement points", icon: "👑", points: 500, type: 'engagement', threshold: 1000 },
];

const AchievementBadge = ({ fullPage = false }) => {
    const [achievements, setAchievements] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAchievements();
    }, []);

    const loadAchievements = async () => {
        try {
            const data = await gamificationService.getAchievements();
            console.log("🏆 Achievements Data:", data);

            // Backend returns { badges: [], total_sessions: 0, ... }
            // We need to merge this with ALL_ACHIEVEMENTS
            const earnedBadges = data.badges || [];
            const earnedNames = new Set(earnedBadges.map(b => b.name));

            const processedAchievements = ALL_ACHIEVEMENTS.map(ach => ({
                ...ach,
                unlocked: earnedNames.has(ach.name),
                rarity: 'common' // Default rarity as backend doesn't always send it for unearned
            }));

            setAchievements(processedAchievements);
            setStats(data);
        } catch (error) {
            console.error('Failed to load achievements:', error);
            // Fallback to showing all locked
            setAchievements(ALL_ACHIEVEMENTS.map(a => ({ ...a, unlocked: false })));
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="text-gray-500 text-center py-8">Loading achievements...</div>;

    const unlockedCount = achievements?.filter(a => a.unlocked).length || 0;
    const totalCount = achievements?.length || 0;
    const totalPoints = achievements?.reduce((sum, a) => sum + (a.points || 0), 0) || 0; // Total possible points
    const earnedPoints = achievements?.reduce((sum, a) => a.unlocked ? sum + (a.points || 0) : sum, 0) || 0;

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
                <h3 className="text-xl font-bold text-gray-800">🏆 Achievements</h3>
            </div>

            <div className="mb-6">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Progress ({earnedPoints} pts earned)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                        className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-1000"
                        style={{ width: `${totalCount > 0 ? (unlockedCount / totalCount) * 100 : 0}%` }}
                    ></div>
                </div>
            </div>

            <div className={`grid gap-4 ${fullPage ? 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4' : 'grid-cols-2 md:grid-cols-3'}`}>
                {achievements.filter(a => a.unlocked).length > 0 ? (
                    achievements.filter(a => a.unlocked).map((ach) => (
                        <div
                            key={ach.id}
                            className="relative border-2 rounded-xl p-4 transition-all duration-300 transform hover:scale-105 bg-gradient-to-br from-yellow-50 to-orange-50 border-orange-200 shadow-md"
                        >
                            <div className="text-4xl mb-3 text-center filter drop-shadow-sm">{ach.icon}</div>
                            <h4 className="font-bold text-sm text-center mb-1 text-gray-800">{ach.name}</h4>
                            <p className="text-xs text-center text-gray-600 mb-3 min-h-[2.5em]">{ach.description}</p>

                            <div className="text-center">
                                <span className="text-xs font-bold px-3 py-1 rounded-full bg-orange-100 text-orange-700">
                                    {ach.points} pts
                                </span>
                            </div>

                            {ach.is_new && (
                                <div className="mt-2 text-center absolute -top-2 -right-2">
                                    <span className="flex h-6 w-6 relative">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-6 w-6 bg-red-500 flex items-center justify-center text-white text-xs font-bold">NEW!</span>
                                    </span>
                                </div>
                            )}
                        </div>
                    ))
                ) : (
                    <div className="col-span-full py-12 text-center bg-gray-50 rounded-xl border-2 border-dashed border-gray-300">
                        <div className="text-6xl mb-4">🚀</div>
                        <h3 className="text-xl font-bold text-gray-800 mb-2">No Achievements Yet</h3>
                        <p className="text-gray-600 max-w-md mx-auto">
                            Start chatting with the AI, taking tests, and learning consistently to unlock your first badge!
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AchievementBadge;
