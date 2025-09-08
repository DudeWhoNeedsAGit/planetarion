import React, { useState, useEffect } from 'react';
import './BattleReports.css';

const BattleReports = ({ user }) => {
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
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/combat/reports?filter=${filter}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setReports(data);
      } else {
        console.error('Failed to fetch battle reports');
      }
    } catch (error) {
      console.error('Error fetching battle reports:', error);
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
      const losses = JSON.parse(lossesJson);
      return Object.values(losses).reduce((total, count) => total + count, 0);
    } catch {
      return 0;
    }
  };

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
        {reports.length === 0 && !loading ? (
          <div className="no-reports">No battle reports found</div>
        ) : (
          reports.map(report => (
            <BattleReportCard
              key={report.id}
              report={report}
              onClick={() => setSelectedReport(report)}
              formatTimeAgo={formatTimeAgo}
              calculateTotalLosses={calculateTotalLosses}
            />
          ))
        )}
      </div>

      {selectedReport && (
        <BattleReportDetail
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
          formatTimeAgo={formatTimeAgo}
          calculateTotalLosses={calculateTotalLosses}
        />
      )}
    </div>
  );
};

const BattleReportCard = ({ report, onClick, formatTimeAgo, calculateTotalLosses }) => {
  const isVictory = report.winner_id === report.attacker_id;
  const timeAgo = formatTimeAgo(report.timestamp);

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
          <h3>{report.planet_name || `Planet ${report.planet_id}`}</h3>
          <p>{report.attacker_name} vs {report.defender_name}</p>
          <span className="timestamp">{timeAgo}</span>
        </div>
      </div>

      <div className="casualties-summary">
        <div className="attacker-losses">
          Attacker: {calculateTotalLosses(report.attacker_losses)} ships lost
        </div>
        <div className="defender-losses">
          Defender: {calculateTotalLosses(report.defender_losses)} ships lost
        </div>
      </div>

      {(report.debris_metal > 0 || report.debris_crystal > 0) && (
        <div className="debris-info">
          Debris: {report.debris_metal} Metal, {report.debris_crystal} Crystal
        </div>
      )}
    </div>
  );
};

const BattleReportDetail = ({ report, onClose, formatTimeAgo, calculateTotalLosses }) => {
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

  const isVictory = report.winner_id === report.attacker_id;

  return (
    <div className="battle-report-detail modal">
      <div className="modal-header">
        <h2>Detailed Battle Report</h2>
        <button onClick={onClose} className="close-button">×</button>
      </div>

      <div className="battle-summary">
        <div className="participants">
          <div className="attacker">
            <h3>{report.attacker_name}</h3>
            <p>Attacker</p>
          </div>
          <div className="vs">VS</div>
          <div className="defender">
            <h3>{report.defender_name}</h3>
            <p>Defender</p>
          </div>
        </div>

        <div className="outcome">
          <h3 className={isVictory ? 'victory-text' : 'defeat-text'}>
            {report.winner_name} Wins!
          </h3>
        </div>
      </div>

      <div className="combat-rounds">
        <h3>Combat Rounds</h3>
        {roundDetails.length === 0 ? (
          <p>No round details available</p>
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

      <div className="final-results">
        <div className="final-losses">
          <h4>Final Losses</h4>
          <div className="losses-breakdown">
            <ShipLosses losses={report.attacker_losses} label="Attacker" />
            <ShipLosses losses={report.defender_losses} label="Defender" />
          </div>
        </div>

        <div className="debris-field">
          <h4>Debris Field</h4>
          <p>{report.debris_metal} Metal, {report.debris_crystal} Crystal</p>
          {report.debris_recycled && (
            <p className="recycled-notice">Already collected</p>
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
    parsedLosses = JSON.parse(losses);
  } catch {
    return <div>{label}: Unable to parse losses</div>;
  }

  return (
    <div className="ship-losses">
      <h5>{label} Losses:</h5>
      {Object.entries(parsedLosses).map(([shipType, count]) => (
        count > 0 && (
          <div key={shipType} className="loss-item">
            {shipType}: {count}
          </div>
        )
      ))}
    </div>
  );
};

export default BattleReports;
