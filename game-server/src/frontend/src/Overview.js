import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

function Overview({ user, planets }) {
  const [activity, setActivity] = useState([]);
  const [activityLoading, setActivityLoading] = useState(false);

  const mergeActivity = (prev, next) => {
    const byId = new Map();
    (Array.isArray(prev) ? prev : []).forEach((e) => {
      if (e && e.id != null) byId.set(e.id, e);
    });
    (Array.isArray(next) ? next : []).forEach((e) => {
      if (e && e.id != null && !byId.has(e.id)) byId.set(e.id, e);
    });
    return Array.from(byId.values()).sort((a, b) => {
      const ta = new Date(a.timestamp || 0).getTime();
      const tb = new Date(b.timestamp || 0).getTime();
      if (tb !== ta) return tb - ta;
      return (b.id || 0) - (a.id || 0);
    });
  };

  const fetchActivity = async () => {
    setActivityLoading(true);
    try {
      const res = await axios.get('/api/tick/logs', { params: { limit: 20, offset: 0 } });
      const logs = Array.isArray(res.data?.logs) ? res.data.logs : [];
      setActivity((prev) => mergeActivity(prev, logs));
    } catch (e) {
      // Non-fatal: keep whatever we already have.
      console.warn('Failed to fetch activity logs:', e);
    } finally {
      setActivityLoading(false);
    }
  };

  useEffect(() => {
    fetchActivity();
    const onTick = () => fetchActivity();
    window.addEventListener('planetarion:tick', onTick);
    return () => window.removeEventListener('planetarion:tick', onTick);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activityItems = useMemo(() => {
    return (activity || []).slice(0, 10).map((log) => {
      const type = (log?.event_type || '').toLowerCase();
      let icon = '📝';
      if (type.includes('combat')) icon = '⚔️';
      else if (type.includes('planet_capture') || type.includes('colon')) icon = '🪐';
      else if (type.includes('recycle')) icon = '♻️';
      else if (type.includes('pirate')) icon = '🏴‍☠️';
      else if (type.includes('espion')) icon = '🕵️';
      else if (type.includes('fleet')) icon = '🚀';

      return {
        id: log.id,
        icon,
        description: log.event_description || log.event_type || 'Activity',
        timestamp: log.timestamp || null,
      };
    });
  }, [activity]);

  const totalResources = planets.reduce((sum, planet) => ({
    metal: sum.metal + planet.resources.metal,
    crystal: sum.crystal + planet.resources.crystal,
    deuterium: sum.deuterium + planet.resources.deuterium
  }), { metal: 0, crystal: 0, deuterium: 0 });

  const totalProduction = planets.reduce((sum, planet) => ({
    metal: sum.metal + (planet.production_rates?.metal_per_hour || 0),
    crystal: sum.crystal + (planet.production_rates?.crystal_per_hour || 0),
    deuterium: sum.deuterium + (planet.production_rates?.deuterium_per_hour || 0)
  }), { metal: 0, crystal: 0, deuterium: 0 });

  const totalBuildings = planets.reduce((sum, planet) => ({
    metal_mine: sum.metal_mine + planet.structures.metal_mine,
    crystal_mine: sum.crystal_mine + planet.structures.crystal_mine,
    deuterium_synthesizer: sum.deuterium_synthesizer + planet.structures.deuterium_synthesizer,
    solar_plant: sum.solar_plant + planet.structures.solar_plant,
    fusion_reactor: sum.fusion_reactor + planet.structures.fusion_reactor
  }), { metal_mine: 0, crystal_mine: 0, deuterium_synthesizer: 0, solar_plant: 0, fusion_reactor: 0 });

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-space-blue to-blue-600 rounded-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">Welcome back, {user.username}!</h2>
        <p className="text-blue-100">Your empire spans {planets.length} planet{planets.length !== 1 ? 's' : ''} across the galaxy.</p>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Planets */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🪐</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Planets</h3>
              <p className="text-gray-400">Colonies</p>
            </div>
          </div>
          <div className="text-3xl font-bold text-blue-400">{planets.length}</div>
        </div>

        {/* Total Resources */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">💰</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Resources</h3>
              <p className="text-gray-400">Total Value</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-green-400">
            {(totalResources.metal + totalResources.crystal + totalResources.deuterium).toLocaleString()}
          </div>
        </div>

        {/* Production */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">⚡</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Production</h3>
              <p className="text-gray-400">Per Hour</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-yellow-400">
            {(totalProduction.metal + totalProduction.crystal + totalProduction.deuterium).toLocaleString()}
          </div>
        </div>

        {/* Buildings */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🏗️</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Buildings</h3>
              <p className="text-gray-400">Total Level</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-purple-400">
            {Object.values(totalBuildings).reduce((sum, level) => sum + level, 0)}
          </div>
        </div>
      </div>

      {/* Resource Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4 text-metal">Metal Resources</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Current:</span>
              <span className="text-metal font-bold">{totalResources.metal.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Production:</span>
              <span className="text-metal">{totalProduction.metal.toLocaleString()}/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Mines:</span>
              <span className="text-metal">{totalBuildings.metal_mine} total</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4 text-crystal">Crystal Resources</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Current:</span>
              <span className="text-crystal font-bold">{totalResources.crystal.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Production:</span>
              <span className="text-crystal">{totalProduction.crystal.toLocaleString()}/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Mines:</span>
              <span className="text-crystal">{totalBuildings.crystal_mine} total</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4 text-deuterium">Deuterium Resources</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Current:</span>
              <span className="text-deuterium font-bold">{totalResources.deuterium.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Production:</span>
              <span className="text-deuterium">{totalProduction.deuterium.toLocaleString()}/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Synthesizers:</span>
              <span className="text-deuterium">{totalBuildings.deuterium_synthesizer} total</span>
            </div>
          </div>
        </div>
      </div>

      {/* Next Steps */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4 text-white">Next Steps</h3>
        <ul className="space-y-2 text-gray-300 text-sm">
          <li>🌌 Open Galaxy Map, find enemies / pirates / allies.</li>
          <li>🔬 Build a Research Lab to generate research points.</li>
          <li>🕵️ Build espionage probes and send an Espionage mission to scout targets.</li>
          <li>⚔️ Attack an enemy (or pirates) and check the Combat Center for reports.</li>
          <li>♻️ After combat, send recyclers to collect debris.</li>
          <li>⏱️ If something says “pending tick”, click “Run tick” (test env) or POST `/api/tick`.</li>
        </ul>
      </div>

      {/* Recent Activity Placeholder */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4 text-white">Recent Activity</h3>
        <div className="space-y-3">
          {activityItems.length === 0 ? (
            <div className="text-center text-gray-400 py-4" data-testid="overview-activity-empty">
              {activityLoading ? 'Loading activity…' : 'No recent activity yet. Explore, fight, and colonize to generate events.'}
            </div>
          ) : (
            <div className="space-y-3" data-testid="overview-activity-list">
              {activityItems.map((item) => (
                <div key={item.id} className="flex items-center space-x-3 p-3 bg-gray-700 rounded" data-testid="overview-activity-item">
                  <span className="text-xl">{item.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-white truncate">{item.description}</p>
                    <p className="text-gray-400 text-sm">
                      {item.timestamp ? new Date(item.timestamp).toLocaleString() : '—'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Overview;
