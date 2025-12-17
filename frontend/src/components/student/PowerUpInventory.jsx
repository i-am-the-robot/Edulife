import { useState, useEffect } from 'react';
import { gamificationService } from '../../services/gamificationService';

const PowerUpInventory = () => {
    const [powerUps, setPowerUps] = useState([]);
    const [loading, setLoading] = useState(true);
    const [using, setUsing] = useState(null);

    useEffect(() => {
        loadPowerUps();
    }, []);

    const loadPowerUps = async () => {
        try {
            const data = await gamificationService.getPowerUps();
            setPowerUps(data);
        } catch (error) {
            console.error('Failed to load power-ups:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleUsePowerUp = async (powerUpId) => {
        setUsing(powerUpId);
        try {
            const result = await gamificationService.usePowerUp(powerUpId);
            alert(`${result.name} activated! ${result.effect}`);
            await loadPowerUps(); // Refresh inventory
        } catch (error) {
            alert('Failed to use power-up');
        } finally {
            setUsing(null);
        }
    };

    if (loading) return <div className="text-gray-500">Loading power-ups...</div>;

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">⚡ Power-Ups</h3>

            {powerUps.length === 0 ? (
                <p className="text-gray-500 text-center py-4">
                    No power-ups yet. Earn them by completing achievements!
                </p>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {powerUps.map((powerUp) => (
                        <div
                            key={powerUp.id}
                            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="text-2xl">{powerUp.icon}</span>
                                        <h4 className="font-semibold text-gray-800">{powerUp.name}</h4>
                                    </div>
                                    <p className="text-sm text-gray-600 mb-2">{powerUp.description}</p>
                                    {powerUp.duration > 0 && (
                                        <p className="text-xs text-gray-500">Duration: {powerUp.duration} min</p>
                                    )}
                                </div>
                                <div className="ml-3 text-center">
                                    <div className="bg-blue-100 text-blue-700 rounded-full w-10 h-10 flex items-center justify-center font-bold mb-2">
                                        {powerUp.quantity}
                                    </div>
                                    <button
                                        onClick={() => handleUsePowerUp(powerUp.id)}
                                        disabled={powerUp.quantity === 0 || using === powerUp.id}
                                        className="px-3 py-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-xs rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition"
                                    >
                                        {using === powerUp.id ? 'Using...' : 'Use'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default PowerUpInventory;
