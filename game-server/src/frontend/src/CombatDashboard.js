import React, { useState } from 'react';
import BattleReports from './BattleReports';
import ColonizationOpportunities from './ColonizationOpportunities';
import './CombatDashboard.css';

const CombatDashboard = ({ user }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'battles', label: 'Battle Reports', icon: '⚔️' },
    { id: 'colonization', label: 'Colonization', icon: '🚀' },
    { id: 'statistics', label: 'Statistics', icon: '📈' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <CombatOverview user={user} />;
      case 'battles':
        return <BattleReports user={user} />;
      case 'colonization':
        return <ColonizationOpportunities user={user} />;
      case 'statistics':
        return <CombatStatistics user={user} />;
      default:
        return <CombatOverview user={user} />;
    }
  };

  return (
    <div className="combat-dashboard">
      <div className="dashboard-header">
        <h1>Combat Center</h1>
        <p className="dashboard-subtitle">
          Manage battles, view reports, and seize colonization opportunities
        </p>
      </div>

      <div className="dashboard-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      <div className="dashboard-content">
        {renderTabContent()}
      </div>
    </div>
  );
};

const CombatOverview = ({ user }) => {
  const [stats, setStats] = useState({
    totalVictories: 0,
    totalDefeats: 0,
    planetsConquered: 0,
    planetsLost: 0,
    debrisCollected: 0,
    activeFleets: 0,
    recentBattles: []
  });

  // Mock data - in real implementation, this would fetch from API
  React.useEffect(() => {
    // Simulate loading stats
    setStats({
      totalVictories: 12,
      totalDefeats: 3,
      planetsConquered: 5,
      planetsLost: 1,
      debrisCollected: 15420,
      activeFleets: 3,
      recentBattles: [
        { id: 1, type: 'victory', planet: 'Alpha Centauri', time: '2h ago' },
        { id: 2, type: 'defeat', planet: 'Beta Orionis', time: '5h ago' },
        { id: 3, type: 'victory', planet: 'Gamma Draconis', time: '1d ago' }
      ]
    });
  }, []);

  return (
    <div className="combat-overview">
      <div className="stats-grid">
        <StatCard
          title="Combat Record"
          value={`${stats.totalVictories}W - ${stats.totalDefeats}L`}
          icon="🏆"
          color="success"
        />
        <StatCard
          title="Territorial Control"
          value={`${stats.planetsConquered} conquered`}
          icon="🌍"
          color="primary"
        />
        <StatCard
          title="Debris Collected"
          value={stats.debrisCollected.toLocaleString()}
          icon="💎"
          color="warning"
        />
        <StatCard
          title="Active Fleets"
          value={stats.activeFleets}
          icon="🚀"
          color="info"
        />
      </div>

      <div className="overview-sections">
        <div className="overview-section">
          <h3>Recent Battles</h3>
          <div className="recent-battles">
            {stats.recentBattles.map(battle => (
              <div key={battle.id} className={`recent-battle ${battle.type}`}>
                <div className="battle-icon">
                  {battle.type === 'victory' ? '🏆' : '💀'}
                </div>
                <div className="battle-info">
                  <div className="battle-planet">{battle.planet}</div>
                  <div className="battle-time">{battle.time}</div>
                </div>
                <div className="battle-type">
                  {battle.type === 'victory' ? 'Victory' : 'Defeat'}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="overview-section">
          <h3>Quick Actions</h3>
          <div className="quick-actions">
            <button className="action-button primary">
              <span className="action-icon">⚔️</span>
              <span>View All Battles</span>
            </button>
            <button className="action-button secondary">
              <span className="action-icon">🚀</span>
              <span>Check Colonization</span>
            </button>
            <button className="action-button tertiary">
              <span className="action-icon">📊</span>
              <span>View Statistics</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon, color }) => {
  return (
    <div className={`stat-card ${color}`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <div className="stat-value">{value}</div>
        <div className="stat-title">{title}</div>
      </div>
    </div>
  );
};

const CombatStatistics = ({ user }) => {
  const [stats, setStats] = useState({
    totalBattles: 0,
    winRate: 0,
    totalShipsLost: 0,
    totalShipsDestroyed: 0,
    favoriteShip: 'Light Fighter',
    mostActivePlanet: 'Home Planet',
    averageBattleDuration: '5.2 rounds'
  });

  React.useEffect(() => {
    // Simulate loading detailed statistics
    setStats({
      totalBattles: 47,
      winRate: 78,
      totalShipsLost: 1250,
      totalShipsDestroyed: 2100,
      favoriteShip: 'Cruiser',
      mostActivePlanet: 'Alpha Centauri',
      averageBattleDuration: '4.8 rounds'
    });
  }, []);

  return (
    <div className="combat-statistics">
      <div className="stats-summary">
        <h3>Combat Performance</h3>
        <div className="performance-metrics">
          <div className="metric">
            <span className="metric-label">Win Rate</span>
            <span className="metric-value">{stats.winRate}%</span>
          </div>
          <div className="metric">
            <span className="metric-label">Total Battles</span>
            <span className="metric-value">{stats.totalBattles}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Avg Duration</span>
            <span className="metric-value">{stats.averageBattleDuration}</span>
          </div>
        </div>
      </div>

      <div className="detailed-stats">
        <div className="stat-section">
          <h4>Casualties</h4>
          <div className="casualty-stats">
            <div className="stat-item">
              <span>Ships Lost:</span>
              <span className="value loss">{stats.totalShipsLost.toLocaleString()}</span>
            </div>
            <div className="stat-item">
              <span>Ships Destroyed:</span>
              <span className="value victory">{stats.totalShipsDestroyed.toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="stat-section">
          <h4>Preferences</h4>
          <div className="preference-stats">
            <div className="stat-item">
              <span>Favorite Ship:</span>
              <span className="value">{stats.favoriteShip}</span>
            </div>
            <div className="stat-item">
              <span>Most Active Planet:</span>
              <span className="value">{stats.mostActivePlanet}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CombatDashboard;
