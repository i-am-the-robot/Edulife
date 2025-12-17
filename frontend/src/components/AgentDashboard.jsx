import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AgentDashboard.css';

const AgentDashboard = ({ studentId }) => {
    const [agentData, setAgentData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activePlans, setActivePlans] = useState([]);

    useEffect(() => {
        loadAgentData();
    }, [studentId]);

    const loadAgentData = async () => {
        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}` };

            // Get agent memory
            const memoryRes = await axios.get(
                'http://localhost:8000/api/agent/memory/me',
                { headers }
            );

            // Get active plans
            const plansRes = await axios.get(
                'http://localhost:8000/api/agent/plans/active',
                { headers }
            );

            // Get recent actions
            const actionsRes = await axios.get(
                `http://localhost:8000/api/agent/actions/${studentId}?limit=5`,
                { headers }
            );

            setAgentData({
                memory: memoryRes.data,
                actions: actionsRes.data
            });
            setActivePlans(plansRes.data);
            setLoading(false);
        } catch (error) {
            console.error('Error loading agent data:', error);
            setLoading(false);
        }
    };

    const triggerDailyCheckIn = async () => {
        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}` };

            const res = await axios.get(
                'http://localhost:8000/api/agent/multi-agent/daily-check-in',
                { headers }
            );

            alert('Daily check-in complete! Check the console for details.');
            console.log('Daily Check-in:', res.data);
        } catch (error) {
            console.error('Error running check-in:', error);
        }
    };

    if (loading) {
        return <div className="agent-dashboard loading">Loading agent data...</div>;
    }

    return (
        <div className="agent-dashboard">
            <div className="dashboard-header">
                <h2>🤖 Your AI Agents</h2>
                <button onClick={triggerDailyCheckIn} className="btn-check-in">
                    Daily Check-in
                </button>
            </div>

            {/* Agent Memory Summary */}
            <div className="agent-section">
                <h3>📊 Learning Insights</h3>
                <div className="insights-grid">
                    <div className="insight-card">
                        <div className="insight-icon">🎯</div>
                        <div className="insight-content">
                            <div className="insight-label">Active Goals</div>
                            <div className="insight-value">
                                {agentData?.memory?.active_goals_count || 0}
                            </div>
                        </div>
                    </div>

                    <div className="insight-card">
                        <div className="insight-icon">✅</div>
                        <div className="insight-content">
                            <div className="insight-label">Mastered Topics</div>
                            <div className="insight-value">
                                {agentData?.memory?.mastered_topics_count || 0}
                            </div>
                        </div>
                    </div>

                    <div className="insight-card">
                        <div className="insight-icon">📚</div>
                        <div className="insight-content">
                            <div className="insight-label">Topics to Review</div>
                            <div className="insight-value">
                                {agentData?.memory?.topics_to_revisit_count || 0}
                            </div>
                        </div>
                    </div>

                    <div className="insight-card">
                        <div className="insight-icon">💡</div>
                        <div className="insight-content">
                            <div className="insight-label">Effective Strategies</div>
                            <div className="insight-value">
                                {agentData?.memory?.effective_strategies_count || 0}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Active Plans */}
            {activePlans.length > 0 && (
                <div className="agent-section">
                    <h3>📅 Active Study Plans</h3>
                    <div className="plans-list">
                        {activePlans.map((plan) => (
                            <div key={plan.id} className="plan-card">
                                <div className="plan-header">
                                    <span className="plan-type">{plan.plan_type}</span>
                                    <span className="plan-progress">
                                        Step {plan.current_step} / {plan.total_steps}
                                    </span>
                                </div>
                                <div className="plan-goal">{plan.goal}</div>
                                {plan.deadline && (
                                    <div className="plan-deadline">
                                        Due: {new Date(plan.deadline).toLocaleDateString()}
                                    </div>
                                )}
                                <div className="plan-progress-bar">
                                    <div
                                        className="plan-progress-fill"
                                        style={{
                                            width: `${(plan.current_step / plan.total_steps) * 100}%`
                                        }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Recent Agent Actions */}
            <div className="agent-section">
                <h3>🔄 Recent Agent Activity</h3>
                <div className="actions-list">
                    {agentData?.actions?.slice(0, 5).map((action) => (
                        <div key={action.id} className="action-item">
                            <div className="action-icon">
                                {action.action_type.includes('tutoring') && '🎓'}
                                {action.action_type.includes('assessment') && '📝'}
                                {action.action_type.includes('scheduling') && '📅'}
                                {action.action_type.includes('motivation') && '💪'}
                                {action.action_type.includes('check_in') && '👋'}
                                {action.action_type.includes('quiz') && '❓'}
                            </div>
                            <div className="action-content">
                                <div className="action-type">
                                    {action.action_type.replace(/_/g, ' ')}
                                </div>
                                <div className="action-reasoning">{action.reasoning}</div>
                                <div className="action-meta">
                                    <span className="action-outcome">{action.outcome}</span>
                                    {action.effectiveness_score && (
                                        <span className="action-effectiveness">
                                            Effectiveness: {(action.effectiveness_score * 100).toFixed(0)}%
                                        </span>
                                    )}
                                    <span className="action-time">
                                        {new Date(action.timestamp).toLocaleTimeString()}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Mastered Topics */}
            {agentData?.memory?.mastered_topics?.length > 0 && (
                <div className="agent-section">
                    <h3>🏆 Mastered Topics</h3>
                    <div className="topics-grid">
                        {agentData.memory.mastered_topics.map((topic, idx) => (
                            <div key={idx} className="topic-badge mastered">
                                {topic.topic}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Topics to Revisit */}
            {agentData?.memory?.topics_to_revisit?.length > 0 && (
                <div className="agent-section">
                    <h3>📖 Topics to Review</h3>
                    <div className="topics-grid">
                        {agentData.memory.topics_to_revisit.map((topic, idx) => (
                            <div key={idx} className="topic-badge review">
                                <div className="topic-name">{topic.topic}</div>
                                {topic.reason && (
                                    <div className="topic-reason">{topic.reason}</div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AgentDashboard;
