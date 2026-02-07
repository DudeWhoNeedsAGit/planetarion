import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import './BattleReports.css';
import { formatCompactNumber } from './numberFormat';

const formatShipLabel = (key) =>
  String(key || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase());

const formatNumber = (value) => {
  return formatCompactNumber(value || 0);
};

const BattleReports = ({ user, onNavigateSection }) => {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [filter, setFilter] = useState('all'); // all, victories, defeats, recent
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchBattleReports();
    // Real-time updates every 30 seconds
    const interval = setInterval(fetchBattleReports, 30000);
    return () => clearInterval(interval);
  }, [filter]);

  const fetchBattleReports = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/combat/reports', { params: { limit: 50, offset: 0 } });
      const reportsArray = Array.isArray(response.data?.reports) ? response.data.reports : [];
      setReports(reportsArray);
    } catch (error) {
      console.error('Error fetching battle reports:', error);
      setReports([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

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

  const filteredReports = useMemo(() => {
    const now = Date.now();
    return (reports || []).filter((report) => {
      if (!report) return false;
      const isVictory = report?.winner?.id === user?.id;
      if (filter === 'victories') return isVictory;
      if (filter === 'defeats') return !isVictory;
      if (filter === 'recent') {
        const ts = report?.timestamp ? new Date(report.timestamp).getTime() : 0;
        return ts > 0 && now - ts <= 24 * 60 * 60 * 1000;
      }
      return true;
    });
  }, [reports, filter, user?.id]);

  return (
    <div className="battle-reports">
      <div className="reports-header">
        <h2>Battle History</h2>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="filter-select"
        >
          <option value="all">All Battles</option>
          <option value="victories">Victories</option>
          <option value="defeats">Defeats</option>
          <option value="recent">Last 24 Hours</option>
        </select>
      </div>

      {loading && <div className="loading">Loading battle reports...</div>}

      <div className="reports-list">
        {filteredReports.length === 0 && !loading ? (
          <div className="no-reports">No battle reports found</div>
        ) : (
          filteredReports.map(report => (
            <BattleReportCard
              key={report.id}
              report={report}
              userId={user?.id}
              onClick={() => setSelectedReport(report)}
              formatTimeAgo={formatTimeAgo}
              calculateTotalLosses={calculateTotalLosses}
            />
          ))
        )}
      </div>

      {selectedReport && (
        <BattleReportDetailModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
          formatTimeAgo={formatTimeAgo}
          calculateTotalLosses={calculateTotalLosses}
          userId={user?.id}
          onNavigateSection={onNavigateSection}
        />
      )}
    </div>
  );
};

const BattleReportCard = ({ report, userId, onClick, formatTimeAgo, calculateTotalLosses }) => {
  const isVictory = report?.winner?.id === userId;
  const timeAgo = formatTimeAgo(report.timestamp);
  const planetName = report?.planet?.name || `Planet ${report?.planet?.id || 'N/A'}`;
  const coords = report?.planet?.coordinates ? `(${report.planet.coordinates})` : '';
  const attackerLosses = calculateTotalLosses(report.attacker_losses);
  const defenderLosses = calculateTotalLosses(report.defender_losses);

  return (
    <div
      className={`battle-report-card ${isVictory ? 'victory' : 'defeat'}`}
      onClick={onClick}
    >
      <div className="report-header">
        <div className="outcome-indicator">
          {isVictory ? '🏆' : '💀'}
        </div>
        <div className="battle-info">
          <h3>{planetName} <span className="coords">{coords}</span></h3>
          <p>{report?.attacker?.username || 'Unknown'} vs {report?.defender?.username || 'Unknown'}</p>
          <span className="timestamp">{timeAgo}</span>
        </div>
      </div>

      <div className="casualties-summary">
        <div className="attacker-losses">Attacker lost: <strong>{formatNumber(attackerLosses)}</strong></div>
        <div className="defender-losses">Defender lost: <strong>{formatNumber(defenderLosses)}</strong></div>
      </div>

      {(report.debris_metal > 0 || report.debris_crystal > 0 || report.debris_deuterium > 0) && (
        <div className="debris-info">
          Debris: {formatNumber(report.debris_metal)} Metal, {formatNumber(report.debris_crystal)} Crystal, {formatNumber(report.debris_deuterium)} Deut
        </div>
      )}
    </div>
  );
};

export const BattleReportDetailModal = ({ report, onClose, formatTimeAgo, calculateTotalLosses, userId, onNavigateSection }) => {
  const [roundDetails, setRoundDetails] = useState([]);

  useEffect(() => {
    if (report.rounds) {
      try {
        setRoundDetails(JSON.parse(report.rounds));
      } catch (error) {
        console.error('Error parsing round details:', error);
        setRoundDetails([]);
      }
    }
  }, [report]);

  const isVictory = report?.winner?.id === userId;
  const attackerName = report?.attacker?.username || 'Unknown';
  const defenderName = report?.defender?.username || 'Unknown';
  const winnerName = report?.winner?.username || 'Unknown';
  const planetName = report?.planet?.name || 'Unknown';
  const coords = report?.planet?.coordinates ? report.planet.coordinates : '';
  const targetPlanetId = report?.planet?.id || null;

  const dispatchFleetPreset = (preset) => {
    try {
      localStorage.setItem('fleetSendPreset', JSON.stringify(preset));
      window.dispatchEvent(new CustomEvent('planetarion:fleetSendPreset', { detail: preset }));
    } catch (e) {
      // ignore
    }
    onClose?.();
    onNavigateSection?.('fleets');
  };

  const openTargetInGalaxy = () => {
    const raw = String(coords || '');
    const parts = raw.split(':').map((v) => parseInt(v, 10));
    if (parts.length === 3 && parts.every((n) => Number.isFinite(n))) {
      try {
        localStorage.setItem('planetarion:galaxy:focus', JSON.stringify({ x: parts[0], y: parts[1], z: parts[2] }));
      } catch (e) {
        // ignore
      }
    }
    onClose?.();
    onNavigateSection?.('galaxy');
  };

  return (
    <div className="battle-report-detail modal">
      <div className="battle-report-modal">
        <div className="modal-header">
          <div className="modal-title">
            <div className="modal-title-row">
              <span className="modal-outcome-icon">{isVictory ? '🏆' : '💀'}</span>
              <h2>Battle Report</h2>
            </div>
            <div className="modal-subtitle">
              {planetName}{coords ? ` (${coords})` : ''} • {formatTimeAgo(report.timestamp)}
            </div>
          </div>
          <button onClick={onClose} className="close-button" aria-label="Close">×</button>
        </div>

        <div className="battle-summary">
          <div className="summary-grid">
            <div className="summary-card">
              <div className="summary-label">Attacker</div>
              <div className="summary-value">{attackerName}</div>
              <div className="summary-meta">Ships lost: {formatNumber(calculateTotalLosses(report.attacker_losses))}</div>
            </div>
            <div className="summary-card">
              <div className="summary-label">Defender</div>
              <div className="summary-value">{defenderName}</div>
              <div className="summary-meta">Ships lost: {formatNumber(calculateTotalLosses(report.defender_losses))}</div>
            </div>
            <div className="summary-card summary-card-wide">
              <div className="summary-label">Outcome</div>
              <div className={`summary-value ${isVictory ? 'victory-text' : 'defeat-text'}`}>{winnerName} wins</div>
              <div className="summary-meta">
                Debris: {formatNumber(report.debris_metal)}M / {formatNumber(report.debris_crystal)}C / {formatNumber(report.debris_deuterium)}D
              </div>
            </div>
          </div>
        </div>

        <div className="final-results">
          <div className="final-losses">
            <h4>Losses</h4>
            <div className="losses-breakdown">
              <ShipLosses losses={report.attacker_losses} label="Attacker" />
              <ShipLosses losses={report.defender_losses} label="Defender" />
            </div>
          </div>

          <div className="debris-field">
            <h4>Debris Field</h4>
            <p>{formatNumber(report.debris_metal)} Metal, {formatNumber(report.debris_crystal)} Crystal, {formatNumber(report.debris_deuterium)} Deut</p>
            {report.debris_recycled && (
              <p className="recycled-notice">Already collected</p>
            )}
          </div>
        </div>

        <div className="mt-4 p-3 border border-slate-500/25 rounded-md bg-slate-900/40" data-testid="combat-outcome-cta-card">
          <div className="text-sm text-slate-200/90 font-semibold mb-2">Next action</div>
          <div className="flex gap-2 flex-wrap">
            <button
              type="button"
              className="pa-btn-primary px-3 py-2 text-sm"
              data-testid="combat-cta-send-recyclers"
              disabled={!targetPlanetId}
              onClick={() => {
                if (!targetPlanetId) return;
                dispatchFleetPreset({ mission: 'recycle', target_planet_id: targetPlanetId });
              }}
            >
              Send recyclers
            </button>
            <button
              type="button"
              className="pa-btn-secondary px-3 py-2 text-sm"
              data-testid="combat-cta-attack-again"
              disabled={!targetPlanetId}
              onClick={() => {
                if (!targetPlanetId) return;
                dispatchFleetPreset({ mission: 'attack', target_planet_id: targetPlanetId });
              }}
            >
              Attack again
            </button>
            <button
              type="button"
              className="pa-btn-secondary px-3 py-2 text-sm"
              data-testid="combat-cta-open-target-galaxy"
              onClick={openTargetInGalaxy}
            >
              Open target
            </button>
          </div>
        </div>

        <div className="combat-rounds">
          <h3>Combat Rounds</h3>
          {roundDetails.length === 0 ? (
            <p className="empty-hint">No round details available</p>
          ) : (
            roundDetails.map((round, index) => (
              <CombatRound
                key={index}
                round={round}
                roundNumber={index + 1}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const CombatRound = ({ round, roundNumber }) => {
  return (
    <div className="combat-round">
      <h4>Round {roundNumber}</h4>

      <div className="round-stats">
        <div className="firepower">
          <div className="attacker-fire">
            Attacker Firepower: {round.attacker_fire || 0}
          </div>
          <div className="defender-fire">
            Defender Firepower: {round.defender_fire || 0}
          </div>
        </div>

        <div className="damage">
          <div className="attacker-damage">
            Attacker Damage Dealt: {round.attacker_damage || 0}
          </div>
          <div className="defender-damage">
            Defender Damage Dealt: {round.defender_damage || 0}
          </div>
        </div>
      </div>
    </div>
  );
};

const ShipLosses = ({ losses, label }) => {
  let parsedLosses = {};
  try {
    parsedLosses = typeof losses === 'string' ? JSON.parse(losses) : (losses || {});
  } catch {
    return <div className="ship-losses">{label}: Unable to parse losses</div>;
  }

  const rows = Object.entries(parsedLosses)
    .filter(([, count]) => (count || 0) > 0)
    .sort((a, b) => (b[1] || 0) - (a[1] || 0));
  const total = rows.reduce((sum, [, count]) => sum + (count || 0), 0);

  return (
    <div className="ship-losses">
      <h5>{label} Losses <span className="loss-total">({formatNumber(total)})</span></h5>
      {rows.length === 0 ? (
        <div className="loss-item muted">No losses</div>
      ) : (
        <div className="loss-table">
          {rows.map(([shipType, count]) => (
            <div key={shipType} className="loss-row">
              <div className="loss-ship">{formatShipLabel(shipType)}</div>
              <div className="loss-count">{formatNumber(count)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BattleReports;
