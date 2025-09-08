import React, { useState, useEffect } from 'react';
import './ColonizationOpportunities.css';

const ColonizationOpportunities = ({ user, onColonizePlanet }) => {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);

  useEffect(() => {
    fetchColonizationOpportunities();
    // Update every 15 seconds
    const interval = setInterval(fetchColonizationOpportunities, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchColonizationOpportunities = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/combat/colonization-opportunities', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setOpportunities(data);
      } else {
        console.error('Failed to fetch colonization opportunities');
      }
    } catch (error) {
      console.error('Error fetching colonization opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTimeRemaining = (expiresAt) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry - now;

    if (diffMs <= 0) {
      return { expired: true, text: 'Expired' };
    }

    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (diffHours > 0) {
      return {
        expired: false,
        text: `${diffHours}h ${diffMins}m`,
        hours: diffHours,
        urgent: diffHours < 1
      };
    } else {
      return {
        expired: false,
        text: `${diffMins}m`,
        hours: 0,
        urgent: diffMins < 30
      };
    }
  };

  const handleColonizeClick = (planet) => {
    setSelectedOpportunity(planet);
  };

  const handleConfirmColonize = async () => {
    if (!selectedOpportunity) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/fleet/colonize-defenseless', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          target_planet_id: selectedOpportunity.id
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Colonization fleet sent! ETA: ${result.eta} seconds`);
        setSelectedOpportunity(null);
        // Refresh opportunities
        fetchColonizationOpportunities();
        // Notify parent component
        if (onColonizePlanet) {
          onColonizePlanet(selectedOpportunity);
        }
      } else {
        const error = await response.json();
        alert(`Failed to colonize: ${error.error}`);
      }
    } catch (error) {
      console.error('Error colonizing planet:', error);
      alert('Failed to colonize planet');
    }
  };

  return (
    <div className="colonization-opportunities">
      <div className="opportunities-header">
        <h3>Colonization Opportunities</h3>
        <button
          onClick={fetchColonizationOpportunities}
          className="refresh-button"
          disabled={loading}
        >
          {loading ? '⟳' : '🔄'}
        </button>
      </div>

      {loading && <div className="loading">Scanning for opportunities...</div>}

      {!loading && opportunities.length === 0 && (
        <div className="no-opportunities">
          <div className="no-opportunities-icon">🌌</div>
          <p>No defenseless planets available for colonization</p>
          <small>Defeated planets will appear here as colonization opportunities</small>
        </div>
      )}

      <div className="opportunities-list">
        {opportunities.map(planet => (
          <ColonizationCard
            key={planet.id}
            planet={planet}
            onColonize={handleColonizeClick}
            formatTimeRemaining={formatTimeRemaining}
          />
        ))}
      </div>

      {selectedOpportunity && (
        <ColonizationDialog
          planet={selectedOpportunity}
          onConfirm={handleConfirmColonize}
          onCancel={() => setSelectedOpportunity(null)}
          formatTimeRemaining={formatTimeRemaining}
        />
      )}
    </div>
  );
};

const ColonizationCard = ({ planet, onColonize, formatTimeRemaining }) => {
  const timeRemaining = formatTimeRemaining(planet.colonizationWindow?.expiresAt);

  return (
    <div className={`colonization-card ${timeRemaining.urgent ? 'urgent' : ''} ${timeRemaining.expired ? 'expired' : ''}`}>
      <div className="planet-header">
        <div className="planet-info">
          <h4>{planet.name}</h4>
          <p className="coordinates">📍 {planet.x}:{planet.y}:{planet.z}</p>
          <p className="previous-owner">
            Previous Owner: <span className="owner-name">{planet.previousOwner || 'Unknown'}</span>
          </p>
        </div>

        <div className="time-remaining">
          <div className={`timer ${timeRemaining.urgent ? 'urgent' : ''}`}>
            {timeRemaining.expired ? '⏰' : '⏳'} {timeRemaining.text}
          </div>
          {!timeRemaining.expired && (
            <div className="timer-label">
              {timeRemaining.urgent ? 'Expires soon!' : 'Time remaining'}
            </div>
          )}
        </div>
      </div>

      <div className="planet-resources">
        <div className="resource-grid">
          <div className="resource-item">
            <span className="resource-icon">⚡</span>
            <span className="resource-value">{planet.metal || 0}</span>
            <span className="resource-label">Metal</span>
          </div>
          <div className="resource-item">
            <span className="resource-icon">💎</span>
            <span className="resource-value">{planet.crystal || 0}</span>
            <span className="resource-label">Crystal</span>
          </div>
          <div className="resource-item">
            <span className="resource-icon">⚛️</span>
            <span className="resource-value">{planet.deuterium || 0}</span>
            <span className="resource-label">Deuterium</span>
          </div>
        </div>
      </div>

      {planet.buildings && planet.buildings.length > 0 && (
        <div className="planet-buildings">
          <h5>Existing Buildings:</h5>
          <div className="buildings-list">
            {planet.buildings.slice(0, 3).map((building, index) => (
              <span key={index} className="building-tag">
                {building.type} L{building.level}
              </span>
            ))}
            {planet.buildings.length > 3 && (
              <span className="building-tag more">+{planet.buildings.length - 3} more</span>
            )}
          </div>
        </div>
      )}

      <div className="card-actions">
        <button
          onClick={() => onColonize(planet)}
          disabled={timeRemaining.expired}
          className={`colonize-button ${timeRemaining.expired ? 'disabled' : ''}`}
        >
          {timeRemaining.expired ? '⏰ Expired' : '🚀 Colonize Now'}
        </button>
      </div>
    </div>
  );
};

const ColonizationDialog = ({ planet, onConfirm, onCancel, formatTimeRemaining }) => {
  const timeRemaining = formatTimeRemaining(planet.colonizationWindow?.expiresAt);

  return (
    <div className="modal">
      <div className="colonization-dialog">
        <div className="dialog-header">
          <h3>Confirm Colonization</h3>
          <button onClick={onCancel} className="close-button">×</button>
        </div>

        <div className="dialog-content">
          <div className="planet-summary">
            <h4>{planet.name}</h4>
            <p className="coordinates">📍 {planet.x}:{planet.y}:{planet.z}</p>
            <p className="previous-owner">
              Previous Owner: <strong>{planet.previousOwner || 'Unknown'}</strong>
            </p>
          </div>

          <div className="colonization-details">
            <div className="detail-item">
              <span className="label">Time Remaining:</span>
              <span className={`value ${timeRemaining.urgent ? 'urgent' : ''}`}>
                {timeRemaining.expired ? 'Expired' : timeRemaining.text}
              </span>
            </div>

            <div className="detail-item">
              <span className="label">Resources Available:</span>
              <span className="value">
                {planet.metal || 0} Metal, {planet.crystal || 0} Crystal, {planet.deuterium || 0} Deuterium
              </span>
            </div>

            {planet.buildings && planet.buildings.length > 0 && (
              <div className="detail-item">
                <span className="label">Existing Buildings:</span>
                <span className="value">
                  {planet.buildings.length} building{planet.buildings.length !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>

          <div className="colonization-warnings">
            <div className="warning-item">
              <span className="warning-icon">⚠️</span>
              <span className="warning-text">
                This planet will become your colony once the colonization fleet arrives
              </span>
            </div>

            <div className="warning-item">
              <span className="warning-icon">⏰</span>
              <span className="warning-text">
                Other players can also attempt to colonize this planet before the opportunity expires
              </span>
            </div>
          </div>
        </div>

        <div className="dialog-actions">
          <button onClick={onCancel} className="cancel-button">
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={timeRemaining.expired}
            className={`confirm-button ${timeRemaining.expired ? 'disabled' : ''}`}
          >
            {timeRemaining.expired ? 'Expired' : '🚀 Send Colonization Fleet'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ColonizationOpportunities;
