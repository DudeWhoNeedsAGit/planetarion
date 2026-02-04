import React, { useEffect, useState } from 'react';
import axios from 'axios';

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
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h5 className="text-white font-bold text-lg">{planet.name}</h5>
          <div className="text-gray-300 text-sm">
            {planet.x}:{planet.y}:{planet.z}{' '}
            <span className="text-gray-500">
              ({planet.x - centerX}:{planet.y - centerY}:{planet.z - centerZ})
            </span>
          </div>
          <div className="text-gray-400 text-xs mt-1">
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
            <div className="mt-1 text-xs text-purple-300">💥 Debris: {debrisTotal.toLocaleString()}</div>
          )}
        </div>
      </div>

      {debrisTotal > 0 && (
        <div className="bg-gray-800 rounded p-3 mb-3">
          <div className="text-gray-200 text-sm font-medium mb-1">Debris Field</div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center bg-gray-900 p-2 rounded">
              <div className="text-gray-300">Metal</div>
              <div className="text-white font-bold">{(planet?.debris?.metal || 0).toLocaleString()}</div>
            </div>
            <div className="text-center bg-gray-900 p-2 rounded">
              <div className="text-gray-300">Crystal</div>
              <div className="text-white font-bold">{(planet?.debris?.crystal || 0).toLocaleString()}</div>
            </div>
            <div className="text-center bg-gray-900 p-2 rounded">
              <div className="text-gray-300">Deut</div>
              <div className="text-white font-bold">{(planet?.debris?.deuterium || 0).toLocaleString()}</div>
            </div>
          </div>
          <button
            onClick={() => onRecycle(planet)}
            className="mt-3 w-full px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded text-sm"
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
            className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm"
            disabled={loading}
          >
            🌱 Colonize
          </button>
        )}

        {isEnemy && (
          <button
            onClick={() => onSpy(planet)}
            className="px-3 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded text-sm"
            disabled={loading}
          >
            🕵️ Spy
          </button>
        )}

        {isEnemy && (
          <button
            onClick={() => onAttack(planet)}
            className="px-3 py-2 bg-red-600 hover:bg-red-500 text-white rounded text-sm"
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
    <div className="bg-gray-700 rounded-lg p-4 mb-4 border border-gray-600">
      <h4 className="text-white font-bold mb-3 flex items-center">📊 System Statistics</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div className="text-center bg-gray-800 p-3 rounded">
          <div className="text-2xl font-bold text-blue-400">{totalPlanets}</div>
          <div className="text-gray-400 text-xs">Total Planets</div>
        </div>
        <div className="text-center bg-gray-800 p-3 rounded">
          <div className="text-2xl font-bold text-green-400">{ownedPlanets}</div>
          <div className="text-gray-400 text-xs">Colonized</div>
        </div>
        <div className="text-center bg-gray-800 p-3 rounded">
          <div className="text-2xl font-bold text-gray-400">{unownedPlanets}</div>
          <div className="text-gray-400 text-xs">Available</div>
        </div>
        <div className="text-center bg-gray-800 p-3 rounded">
          <div className="text-2xl font-bold text-purple-300">{totalDebris.toLocaleString()}</div>
          <div className="text-gray-400 text-xs">Debris Total</div>
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
    <div className="mt-6 bg-gray-800 rounded-lg p-6 max-h-96 overflow-y-auto border border-gray-600">
      <div className="flex justify-between items-center mb-6">
        <div className="flex-1">
          <h3 className="text-2xl font-bold text-white flex items-center">🌌 System {system.x}:{system.y}:{system.z}</h3>
          <div className="text-gray-400 mt-1 flex items-center">
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                system.explored ? 'bg-blue-900 text-blue-300' : 'bg-gray-900 text-gray-300'
              }`}
            >
              {system.explored ? '✅ Explored' : '❓ Unexplored'}
            </span>
          </div>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-white text-xl ml-4">
          ✕
        </button>
      </div>

      <SystemStatistics planets={planets} />

      {!system.explored && (
        <div className="mb-4 bg-gray-900 border border-gray-600 rounded p-3">
          <div className="text-gray-200 font-medium mb-2">Unexplored system</div>
          <div className="text-gray-400 text-sm mb-3">Send an exploration fleet to reveal planets in this system.</div>
          <button
            onClick={() => onExplore?.(system)}
            disabled={loading}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded text-sm"
          >
            🚀 Send exploration fleet
          </button>
        </div>
      )}

      <div>
        <h4 className="text-white font-bold mb-4 flex items-center">🪐 Planets ({planets.length})</h4>

        {planets.length === 0 ? (
          <div className="text-gray-400 text-center py-8 bg-gray-700 rounded-lg">
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
