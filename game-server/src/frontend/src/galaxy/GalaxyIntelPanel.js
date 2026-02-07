import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { formatCompactNumber } from '../numberFormat';

function PlanetCard({
  planet,
  loading,
  centerX,
  centerY,
  centerZ,
  userId,
  onAttack = () => {},
  onSpy = () => {},
  onRecycle = () => {},
  onQuickColonize = () => {},
}) {
  if (!planet) return null;

  const isOwned = planet.user_id != null;
  const isMine = isOwned && planet.user_id === userId;
  const isEnemy = isOwned && !isMine;
  const debrisTotal = (planet?.debris?.metal || 0) + (planet?.debris?.crystal || 0) + (planet?.debris?.deuterium || 0);

  return (
    <div className="pa-panel p-4">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h5 className="text-white font-bold text-lg">{planet.name}</h5>
          <div className="text-slate-200/80 text-sm">
            {planet.x}:{planet.y}:{planet.z}{' '}
            <span className="text-slate-300/60">
              ({planet.x - centerX}:{planet.y - centerY}:{planet.z - centerZ})
            </span>
          </div>
          <div className="text-slate-300/70 text-xs mt-1">
            {isMine ? '🏠 Your planet' : isEnemy ? '⚔️ Enemy planet' : '🪐 Unowned'}
            {planet.owner_name ? ` • Owner: ${planet.owner_name}` : ''}
          </div>
        </div>
        <div className="text-right">
          <div
            className={`px-2 py-1 rounded text-xs font-medium ${
              isMine ? 'bg-green-900 text-green-300' : isEnemy ? 'bg-red-900 text-red-300' : 'bg-blue-900 text-blue-300'
            }`}
          >
            {isMine ? 'Owned' : isEnemy ? 'Enemy' : 'Available'}
          </div>
          {debrisTotal > 0 && (
            <div className="mt-1 text-xs text-purple-300">💥 Debris: {formatCompactNumber(debrisTotal)}</div>
          )}
        </div>
      </div>

      {debrisTotal > 0 && (
        <div className="pa-surface p-3 mb-3">
          <div className="text-slate-200/90 text-sm font-medium mb-1">Debris Field</div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center pa-panel p-2">
              <div className="text-slate-200/80">Metal</div>
              <div className="text-white font-bold">{formatCompactNumber(planet?.debris?.metal || 0)}</div>
            </div>
            <div className="text-center pa-panel p-2">
              <div className="text-slate-200/80">Crystal</div>
              <div className="text-white font-bold">{formatCompactNumber(planet?.debris?.crystal || 0)}</div>
            </div>
            <div className="text-center pa-panel p-2">
              <div className="text-slate-200/80">Deut</div>
              <div className="text-white font-bold">{formatCompactNumber(planet?.debris?.deuterium || 0)}</div>
            </div>
          </div>
          <button
            onClick={() => onRecycle(planet)}
            className="mt-3 w-full pa-btn-primary px-3 py-2 text-sm"
            disabled={loading}
          >
            ♻️ Send recyclers
          </button>
        </div>
      )}

      <div className="flex gap-2 flex-wrap">
        {!isOwned && (
          <button
            onClick={() => onQuickColonize(planet)}
            className="pa-btn-primary px-3 py-2 text-sm"
            disabled={loading}
          >
            🌱 Colonize
          </button>
        )}

        {isEnemy && (
          <button
            onClick={() => onSpy(planet)}
            className="pa-btn-secondary px-3 py-2 text-sm bg-amber-500/20 hover:bg-amber-500/25 border-amber-500/30 text-amber-100"
            disabled={loading}
          >
            🕵️ Spy
          </button>
        )}

        {isEnemy && (
          <button
            onClick={() => onAttack(planet)}
            className="pa-btn-danger px-3 py-2 text-sm"
            disabled={loading}
          >
            Attack
          </button>
        )}
      </div>
    </div>
  );
}

function SystemStatistics({ planets }) {
  const totalPlanets = planets.length;
  const ownedPlanets = planets.filter((p) => p.user_id).length;
  const unownedPlanets = totalPlanets - ownedPlanets;
  const totalDebris = planets.reduce((sum, p) => {
    const d = p?.debris || {};
    return sum + (d.metal || 0) + (d.crystal || 0) + (d.deuterium || 0);
  }, 0);

  return (
    <div className="pa-card p-4 mb-4">
      <h4 className="text-white font-bold mb-3 flex items-center">📊 System Statistics</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div className="text-center pa-panel p-3">
          <div className="text-2xl font-bold text-blue-400">{totalPlanets}</div>
          <div className="text-slate-300/70 text-xs">Total Planets</div>
        </div>
        <div className="text-center pa-panel p-3">
          <div className="text-2xl font-bold text-green-400">{ownedPlanets}</div>
          <div className="text-slate-300/70 text-xs">Colonized</div>
        </div>
        <div className="text-center pa-panel p-3">
          <div className="text-2xl font-bold text-slate-200/80">{unownedPlanets}</div>
          <div className="text-slate-300/70 text-xs">Available</div>
        </div>
        <div className="text-center pa-panel p-3">
          <div className="text-2xl font-bold text-purple-300">{formatCompactNumber(totalDebris)}</div>
          <div className="text-slate-300/70 text-xs">Debris Total</div>
        </div>
      </div>
    </div>
  );
}

export default function GalaxyIntelPanel({
  system,
  onClose,
  onExplore,
  loading,
  userId,
  centerX,
  centerY,
  centerZ,
  onNavigateSection,
}) {
  const [planets, setPlanets] = useState([]);

  useEffect(() => {
    if (!system) return;
    const fetchSystemPlanets = async () => {
      try {
        const res = await axios.get(`/api/galaxy/system/${system.x}/${system.y}/${system.z}`);
        setPlanets(Array.isArray(res.data) ? res.data : []);
      } catch (e) {
        setPlanets([]);
      }
    };
    fetchSystemPlanets();
  }, [system]);

  if (!system) return null;

  const goToFleetsWithPreset = (preset) => {
    try {
      localStorage.setItem('fleetSendPreset', JSON.stringify(preset));
      // Storage events don't fire in the same tab; dispatch a local event for an immediate handoff.
      window.dispatchEvent(new CustomEvent('planetarion:fleetSendPreset', { detail: preset }));
    } catch (e) {
      // ignore
    }
    if (typeof onNavigateSection === 'function') onNavigateSection('fleets');
  };

  return (
    <div className="pa-card p-6 h-full overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="flex-1">
          <h3 className="text-2xl font-bold text-white flex items-center">🌌 System {system.x}:{system.y}:{system.z}</h3>
          <div className="text-slate-300/70 mt-1 flex items-center">
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                system.explored ? 'bg-blue-900/40 text-blue-300' : 'bg-slate-900/40 text-slate-200/80'
              }`}
            >
              {system.explored ? '✅ Explored' : '❓ Unexplored'}
            </span>
          </div>
        </div>
        <button onClick={onClose} className="pa-btn-ghost px-3 py-2 text-sm ml-4">
          Close
        </button>
      </div>

      <SystemStatistics planets={planets} />

      {!system.explored && (
        <div className="mb-4 pa-panel p-3">
          <div className="text-slate-200/90 font-medium mb-2">Unexplored system</div>
          <div className="text-slate-300/70 text-sm mb-3">Send an exploration fleet to reveal planets in this system.</div>
          <button
            onClick={() => onExplore?.(system)}
            disabled={loading}
            className="pa-btn-primary px-3 py-2 text-sm"
          >
            🚀 Send exploration fleet
          </button>
        </div>
      )}

      <div>
        <h4 className="text-white font-bold mb-4 flex items-center">🪐 Planets ({planets.length})</h4>

        {planets.length === 0 ? (
          <div className="text-slate-300/70 text-center py-8 pa-panel">
            <div className="text-4xl mb-2">🌌</div>
            <div>No planets discovered yet</div>
            <div className="text-sm mt-2">Send an exploration fleet to discover planets in this system</div>
          </div>
        ) : (
          <div className="space-y-4">
            {planets.map((planet) => (
              <PlanetCard
                key={planet.id}
                planet={planet}
                loading={loading}
                centerX={centerX}
                centerY={centerY}
                centerZ={centerZ}
                userId={userId}
                onAttack={(p) => goToFleetsWithPreset({ mission: 'attack', target_planet_id: p.id })}
                onSpy={(p) => goToFleetsWithPreset({ mission: 'espionage', target_planet_id: p.id })}
                onRecycle={(p) => goToFleetsWithPreset({ mission: 'recycle', target_planet_id: p.id })}
                onQuickColonize={(p) => goToFleetsWithPreset({ mission: 'colonize', target_planet_id: p.id, target_x: p.x, target_y: p.y, target_z: p.z })}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
