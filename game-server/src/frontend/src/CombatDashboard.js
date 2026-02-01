import React, { useMemo, useState } from 'react';
import axios from 'axios';
import BattleReports, { BattleReportDetailModal } from './BattleReports';
import './CombatDashboard.css';

const CombatDashboard = ({ user, planets = [], onNavigateSection }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedReport, setSelectedReport] = useState(null);
  const [recycleConfig, setRecycleConfig] = useState(null);

  const ownedPlanets = useMemo(() => {
    // Dashboard passes owned planets from `/api/planet`.
    return Array.isArray(planets) ? planets : [];
  }, [planets]);

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const reportTime = new Date(timestamp);
    const diffMs = now - reportTime;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const calculateTotalLosses = (lossesJson) => {
    try {
      const losses = typeof lossesJson === 'string' ? JSON.parse(lossesJson) : (lossesJson || {});
      return Object.values(losses).reduce((total, count) => total + (count || 0), 0);
    } catch {
      return 0;
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'battles', label: 'Battle Reports', icon: '⚔️' },
    { id: 'spy', label: 'Spy Reports', icon: '🕵️' },
    { id: 'statistics', label: 'Statistics', icon: '📈' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <CombatOverview
            user={user}
            onNavigate={setActiveTab}
            onSelectReport={setSelectedReport}
            onNavigateSection={onNavigateSection}
            planets={ownedPlanets}
            onConfigureRecycle={(payload) => setRecycleConfig(payload)}
          />
        );
      case 'battles':
        return <BattleReports user={user} />;
      case 'spy':
        return <SpyReports />;
      case 'statistics':
        return <CombatStatistics user={user} />;
      default:
        return (
          <CombatOverview
            user={user}
            onNavigate={setActiveTab}
            onSelectReport={setSelectedReport}
            onNavigateSection={onNavigateSection}
          />
        );
    }
  };

  return (
    <div className="combat-dashboard" data-testid="combat-dashboard">
      <div className="dashboard-header">
        <h1>Combat Center</h1>
        <p className="dashboard-subtitle">
          Manage battles and view reports
        </p>
      </div>

      <div className="dashboard-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            data-testid={`combat-tab-${tab.id}`}
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

      {selectedReport && (
        <BattleReportDetailModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
          formatTimeAgo={formatTimeAgo}
          calculateTotalLosses={calculateTotalLosses}
          userId={user?.id}
        />
      )}

      {recycleConfig && (
        <RecycleConfigModal
          config={recycleConfig}
          planets={ownedPlanets}
          onClose={() => setRecycleConfig(null)}
          onConfirm={({ startPlanetId, focus }) => {
            const targetPlanetId = recycleConfig?.target_planet_id;
            if (!targetPlanetId) return;
            const preset = {
              mission: 'recycle',
              target_planet_id: targetPlanetId,
              start_planet_id: startPlanetId || null,
              recycle_focus: focus || 'proportional',
            };
            localStorage.setItem('fleetSendPreset', JSON.stringify(preset));
            try {
              window.dispatchEvent(new CustomEvent('planetarion:fleetSendPreset', { detail: preset }));
            } catch (e) {
              console.warn('Failed to dispatch fleetSendPreset event:', e);
            }
            setRecycleConfig(null);
            onNavigateSection?.('fleets');
          }}
        />
      )}
    </div>
  );
};

const SpyReports = () => {
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState([]);

  React.useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await axios.get('/api/espionage/reports', { params: { limit: 25, offset: 0 } });
        const next = Array.isArray(res.data?.reports) ? res.data.reports : [];
        setReports(next);
      } catch (e) {
        console.warn('Failed to load spy reports:', e);
        setReports([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="combat-overview">
      <div className="overview-section">
        <h3>Spy Reports</h3>
        {loading ? (
          <div className="no-reports">Loading…</div>
        ) : reports.length === 0 ? (
          <div className="no-reports">No spy reports yet. Use Galaxy Map → Spy.</div>
        ) : (
          <div className="recent-battles">
            {reports.map((r) => {
              const planet = r?.intel?.planet;
              const owner = r?.intel?.owner;
              const resources = r?.intel?.resources;
              const time = r?.timestamp ? new Date(r.timestamp).toLocaleString() : '';
              return (
                <div key={r.id} className="recent-battle" data-testid="spy-report">
                  <div className="battle-icon">🕵️</div>
                  <div className="battle-details">
                    <div className="battle-title">
                      {planet?.name || 'Unknown planet'} {planet?.coordinates ? `(${planet.coordinates})` : ''}
                    </div>
                    <div className="battle-description">
                      Owner: {owner?.username || owner?.user_id || 'Unknown'} • {time}
                    </div>
                    {resources && (
                      <div className="battle-description">
                        Metal {Number(resources.metal || 0).toLocaleString()} • Crystal {Number(resources.crystal || 0).toLocaleString()} • Deut {Number(resources.deuterium || 0).toLocaleString()}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

const RecycleConfigModal = ({ config, planets, onClose, onConfirm }) => {
  const [startPlanetId, setStartPlanetId] = useState(() => {
    const first = (Array.isArray(planets) && planets.length > 0) ? planets[0] : null;
    return first?.id ?? '';
  });
  const [focus, setFocus] = useState('proportional');

  const targetLabel = config?.target_label || 'debris field';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" data-testid="combat-recycle-config-modal">
      <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white">Send recyclers</h3>
          <button className="text-gray-400 hover:text-white" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="text-sm text-gray-300 mb-4">
          Target: <span className="text-white font-medium">{targetLabel}</span>
        </div>

        <div className="mb-4">
          <label className="block text-gray-300 mb-2">Source planet (where recyclers depart)</label>
          <select
            className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            data-testid="combat-recycle-source-planet"
            value={startPlanetId}
            onChange={(e) => setStartPlanetId(e.target.value)}
          >
            {(Array.isArray(planets) ? planets : []).map((p) => (
              <option key={p.id} value={p.id}>
                {(p.is_home_planet ? '🏠 ' : '🌍 ') + p.name} ({p.x}:{p.y}:{p.z})
              </option>
            ))}
          </select>
        </div>

        <div className="mb-4">
          <label className="block text-gray-300 mb-2">Recycling focus</label>
          <div className="space-y-2 text-sm text-gray-200">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="recycle-focus"
                value="proportional"
                checked={focus === 'proportional'}
                onChange={() => setFocus('proportional')}
                data-testid="combat-recycle-focus-proportional"
              />
              <span>Proportional (split capacity across available debris)</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="recycle-focus"
                value="metal"
                checked={focus === 'metal'}
                onChange={() => setFocus('metal')}
                data-testid="combat-recycle-focus-metal"
              />
              <span>Metal only</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="recycle-focus"
                value="crystal"
                checked={focus === 'crystal'}
                onChange={() => setFocus('crystal')}
                data-testid="combat-recycle-focus-crystal"
              />
              <span>Crystal only</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="recycle-focus"
                value="deuterium"
                checked={focus === 'deuterium'}
                onChange={() => setFocus('deuterium')}
                data-testid="combat-recycle-focus-deuterium"
              />
              <span>Deuterium only</span>
            </label>
          </div>
          <div className="mt-2 text-xs text-gray-400">
            Tip: pick “Metal only”/“Crystal only” for strategic focus, or keep proportional for automatic cleanup.
          </div>
        </div>

        <div className="flex gap-3">
          <button
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            data-testid="combat-recycle-continue"
            onClick={() => onConfirm({ startPlanetId: startPlanetId ? parseInt(startPlanetId, 10) : null, focus })}
          >
            Continue
          </button>
          <button
            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
            data-testid="combat-recycle-cancel"
            onClick={onClose}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

const CombatOverview = ({ user, planets, onNavigate, onSelectReport, onNavigateSection, onConfigureRecycle }) => {
  const [stats, setStats] = useState({
    totalVictories: 0,
    totalDefeats: 0,
    totalBattles: 0,
    winRate: 0,
    visibleDebris: 0,
    recentBattles: []
  });
  const [loading, setLoading] = useState(true);
  const [debrisFields, setDebrisFields] = useState([]);

  React.useEffect(() => {
    const loadOverview = async () => {
      setLoading(true);
      try {
        const [statsRes, reportsRes, debrisRes] = await Promise.all([
          axios.get('/api/combat/statistics'),
          axios.get('/api/combat/reports', { params: { limit: 5, offset: 0 } }),
          axios.get('/api/combat/debris')
        ]);

        const fleetStats = statsRes.data?.fleet_statistics || {};
        const battleStats = statsRes.data?.battle_statistics || {};
        const reports = Array.isArray(reportsRes.data?.reports) ? reportsRes.data.reports : [];
        const debris = Array.isArray(debrisRes.data?.debris_fields) ? debrisRes.data.debris_fields : [];
        const visibleDebris = debris.reduce((sum, df) => {
          const resources = df?.resources || {};
          return sum + (resources.metal || 0) + (resources.crystal || 0) + (resources.deuterium || 0);
        }, 0);

        setStats({
          totalVictories: fleetStats.total_victories || 0,
          totalDefeats: fleetStats.total_defeats || 0,
          totalBattles: battleStats.total_battles || 0,
          winRate: Math.round(battleStats.win_rate || 0),
          visibleDebris,
          recentBattles: reports
        });
        setDebrisFields(debris);
      } catch (e) {
        console.warn('Failed to load combat overview:', e);
        setStats({
          totalVictories: 0,
          totalDefeats: 0,
          totalBattles: 0,
          winRate: 0,
          visibleDebris: 0,
          recentBattles: []
        });
        setDebrisFields([]);
      } finally {
        setLoading(false);
      }
    };

    loadOverview();
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
          title="Win Rate"
          value={`${stats.winRate}%`}
          icon="🌍"
          color="primary"
        />
        <StatCard
          title="Visible Debris"
          value={stats.visibleDebris.toLocaleString()}
          icon="💎"
          color="warning"
        />
        <StatCard
          title="Total Battles"
          value={stats.totalBattles}
          icon="🚀"
          color="info"
        />
      </div>

      <div className="overview-section" style={{ marginTop: '16px' }}>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-sm text-gray-200">
          <div className="font-semibold text-white mb-1">Gameplay rules (MVP)</div>
          <ul className="text-gray-300" style={{ paddingLeft: '18px', listStyle: 'disc' }}>
            <li>Winning a battle does not always grant ownership. A planet is captured only when the defender is eliminated/undefended (Option A).</li>
            <li>Debris fields appear from battles you participated in (or explored intel) and must be recycled to turn into resources.</li>
          </ul>
        </div>
      </div>

      <div className="overview-sections">
        <div className="overview-section">
          <h3>Recent Battles</h3>
          <div className="recent-battles" data-testid="combat-recent-battles">
            {loading ? (
              <div className="no-reports">Loading…</div>
            ) : stats.recentBattles.length === 0 ? (
              <div className="no-reports">No recent battles</div>
            ) : (
              stats.recentBattles.map((report) => {
                const isVictory = report?.winner?.id === user?.id;
                const planetLabel = report?.planet?.name
                  ? `${report.planet.name} (${report.planet.coordinates})`
                  : 'Unknown planet';
                const opponent = isVictory ? report?.defender?.username : report?.attacker?.username;
                const time = report?.timestamp ? new Date(report.timestamp).toLocaleString() : '';

                return (
                  <div
                    key={report.id}
                    className={`recent-battle ${isVictory ? 'victory' : 'defeat'}`}
                    data-testid="combat-recent-battle"
                    role="button"
                    tabIndex={0}
                    onClick={() => onSelectReport?.(report)}
                  >
                    <div className="battle-icon">{isVictory ? '🏆' : '💀'}</div>
                    <div className="battle-info">
                      <div className="battle-planet">{planetLabel}</div>
                      <div className="battle-time">{time}</div>
                      <div className="battle-opponent">vs {opponent || 'Unknown'}</div>
                    </div>
                    <div className="battle-type">{isVictory ? 'Victory' : 'Defeat'}</div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="overview-section">
          <h3>Debris Fields</h3>
          <div className="recent-battles" data-testid="combat-debris-fields">
            {loading ? (
              <div className="no-reports">Loading…</div>
            ) : debrisFields.length === 0 ? (
              <div className="no-reports">No debris fields visible</div>
            ) : (
              debrisFields.slice(0, 5).map((df) => {
                const planet = df?.planet;
                const resources = df?.resources || {};
                const total = (resources.metal || 0) + (resources.crystal || 0) + (resources.deuterium || 0);
                const label = planet?.name
                  ? `${planet.name}${planet.coordinates ? ` (${planet.coordinates})` : ''}`
                  : `Planet ${planet?.id || ''}`;

                return (
                  <div key={df.id} className="recent-battle" data-testid="combat-debris-field">
                    <div className="battle-icon">💥</div>
                    <div className="battle-info">
                      <div className="battle-planet">{label}</div>
                      <div className="battle-time">
                        {resources.metal || 0}M / {resources.crystal || 0}C / {resources.deuterium || 0}D (total {total})
                      </div>
                    </div>
                    <div className="battle-type">
                      <button
                        className="action-button primary"
                        data-testid="combat-send-recyclers"
                        onClick={() => {
                          if (!planet?.id) return;
                          const label = planet?.name
                            ? `${planet.name}${planet.coordinates ? ` (${planet.coordinates})` : ''}`
                            : `Planet ${planet?.id || ''}`;
                          onConfigureRecycle?.({ target_planet_id: planet.id, target_label: label, planets });
                        }}
                      >
                        Send recyclers
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="overview-section">
          <h3>Quick Actions</h3>
          <div className="quick-actions">
            <button className="action-button primary" onClick={() => onNavigate?.('battles')}>
              <span className="action-icon">⚔️</span>
              <span>View All Battles</span>
            </button>
            <button className="action-button secondary">
              <span className="action-icon">🚀</span>
              <span>Fleet Missions</span>
            </button>
            <button className="action-button tertiary" onClick={() => onNavigate?.('statistics')}>
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
