import React, { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { backendBaseUrl } from './apiBase';

function Overview({ user, planets, onNavigateSection }) {
  const [activity, setActivity] = useState([]);
  const [activityLoading, setActivityLoading] = useState(false);
  const [debrisSummary, setDebrisSummary] = useState({ count: 0, total: 0 });
  const [researchSummary, setResearchSummary] = useState({ points: 0, queue: null, nextSuggestionKey: null });
  const sseHealthyRef = useRef(false);

  const mergeActivity = (prev, next) => {
    const byId = new Map();
    (Array.isArray(prev) ? prev : []).forEach((e) => {
      if (e && e.id != null) byId.set(e.id, e);
    });
    (Array.isArray(next) ? next : []).forEach((e) => {
      if (!e || e.id == null) return;
      // Defensive: hide per-tick resource rows or malformed rows that pollute the feed.
      const hasType = typeof e.event_type === 'string' && e.event_type.trim() !== '';
      const hasDesc = typeof e.event_description === 'string' && e.event_description.trim() !== '';
      if (!hasType && !hasDesc) return;
      if (!byId.has(e.id)) byId.set(e.id, e);
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
    // Commander Suggestions inputs (cheap, lightweight):
    // - known debris fields (combat/debris)
    // - research queue + RP (research)
    const loadCommanderContext = async () => {
      try {
        const [debrisRes, researchRes] = await Promise.all([
          axios.get('/api/combat/debris'),
          axios.get('/api/research'),
        ]);

        const debris = Array.isArray(debrisRes.data?.debris_fields) ? debrisRes.data.debris_fields : [];
        const total = debris.reduce((sum, df) => {
          const r = df?.resources || {};
          return sum + (r.metal || 0) + (r.crystal || 0) + (r.deuterium || 0);
        }, 0);
        setDebrisSummary({ count: debris.length, total });

        const rp = Number(researchRes.data?.research_points || 0) || 0;
        const queue = researchRes.data?.queue || null;
        const nextLevelCosts = researchRes.data?.next_level_costs || {};
        const levels = researchRes.data?.levels || {};
        // Suggest one “high ROI” tech if affordable and no queue is running.
        const candidateOrder = ['astrophysics', 'colonization_tech', 'recycler_efficiency', 'weapons_tech', 'energy_tech'];
        const nextSuggestionKey = !queue
          ? candidateOrder.find((k) => typeof nextLevelCosts?.[k] === 'number' && rp >= nextLevelCosts[k])
          : null;
        setResearchSummary({ points: rp, queue, nextSuggestionKey, levels });
      } catch (e) {
        // Non-fatal: keep defaults.
      }
    };
    loadCommanderContext();
    const onTick = () => {
      // If SSE is connected, avoid refetching on every tick; the stream will deliver new events.
      if (!sseHealthyRef.current) fetchActivity();
    };
    window.addEventListener('planetarion:tick', onTick);

    // Event-driven updates (SSE). Fallback to existing tick/polling behavior on error.
    const token = localStorage.getItem('token');
    let es = null;
    if (token) {
      try {
        const sseUrl = `${backendBaseUrl}/api/events/stream?token=${encodeURIComponent(token)}`;
        es = new EventSource(sseUrl);
        es.addEventListener('activity', (evt) => {
          try {
            const payload = JSON.parse(evt.data || '{}');
            if (!payload || payload.id == null) return;
            setActivity((prev) => mergeActivity(prev, [payload]));
          } catch (e) {
            // ignore
          }
        });
        // If stream is open, no need to spam fetches.
        es.addEventListener('open', () => {
          sseHealthyRef.current = true;
        });
        es.addEventListener('error', () => {
          sseHealthyRef.current = false;
          try {
            es.close();
          } catch (e) {
            // ignore
          }
          es = null;
        });
      } catch (e) {
        es = null;
      }
    }

    return () => {
      window.removeEventListener('planetarion:tick', onTick);
      sseHealthyRef.current = false;
      if (es) {
        try {
          es.close();
        } catch (e) {
          // ignore
        }
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activityItems = useMemo(() => {
    return (activity || []).slice(0, 10).map((log) => {
      const type = (log?.event_type || '').toLowerCase();
      let icon = '📝';
      if (type.includes('combat')) icon = '⚔️';
      else if (type.includes('planet_capture') || type.includes('colon')) icon = '🪐';
      else if (type.includes('rename')) icon = '✏️';
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
      <div className="pa-card p-6 bg-gradient-to-r from-blue-600/20 to-teal-500/10 text-white">
        <h2 className="text-2xl font-bold mb-2">Welcome back, {user.username}!</h2>
        <p className="text-slate-200/80">Your empire spans {planets.length} planet{planets.length !== 1 ? 's' : ''} across the galaxy.</p>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Planets */}
        <div className="pa-card p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🪐</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Planets</h3>
              <p className="text-slate-300/70">Colonies</p>
            </div>
          </div>
          <div className="text-3xl font-bold text-blue-400">{planets.length}</div>
        </div>

        {/* Total Resources */}
        <div className="pa-card p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">💰</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Resources</h3>
              <p className="text-slate-300/70">Total Value</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-green-400">
            {(totalResources.metal + totalResources.crystal + totalResources.deuterium).toLocaleString()}
          </div>
        </div>

        {/* Production */}
        <div className="pa-card p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">⚡</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Production</h3>
              <p className="text-slate-300/70">Per Hour</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-yellow-400">
            {(totalProduction.metal + totalProduction.crystal + totalProduction.deuterium).toLocaleString()}
          </div>
        </div>

        {/* Buildings */}
        <div className="pa-card p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🏗️</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Buildings</h3>
              <p className="text-slate-300/70">Total Level</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-purple-400">
            {Object.values(totalBuildings).reduce((sum, level) => sum + level, 0)}
          </div>
        </div>
      </div>

      {/* Commander Suggestions */}
      <div className="pa-card p-6" data-testid="commander-suggestions">
        <h3 className="text-xl font-bold mb-4 text-white">Commander Suggestions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="pa-panel p-4">
            <div className="text-white font-semibold mb-1">♻️ Recycle known debris</div>
            <div className="text-slate-200/80 mb-3">
              {debrisSummary.count > 0
                ? `${debrisSummary.count} debris field(s) visible • ~${debrisSummary.total.toLocaleString()} total resources`
                : 'No known debris fields right now.'}
            </div>
            <button
              type="button"
              className="pa-btn-primary px-3 py-2"
              disabled={debrisSummary.count === 0}
              onClick={() => onNavigateSection?.('combat')}
              data-testid="commander-suggest-open-combat"
            >
              Open Combat
            </button>
          </div>

          <div className="pa-panel p-4">
            <div className="text-white font-semibold mb-1">🔬 Keep research running</div>
            <div className="text-slate-200/80 mb-3">
              {researchSummary.queue
                ? `Research in progress: ${researchSummary.queue.key} → L${researchSummary.queue.target_level}`
                : `No research in progress • ${Number(researchSummary.points || 0).toLocaleString()} RP available`}
            </div>
            <button
              type="button"
              className="pa-btn-primary px-3 py-2"
              onClick={() => onNavigateSection?.('research')}
              data-testid="commander-suggest-open-research"
            >
              Open Research
            </button>
            {!researchSummary.queue && researchSummary.nextSuggestionKey && (
              <div className="mt-2 text-xs text-slate-200/80">
                Suggested: <span className="text-white font-medium">{String(researchSummary.nextSuggestionKey).replace(/_/g, ' ')}</span> (affordable now)
              </div>
            )}
          </div>

          <div className="pa-panel p-4">
            <div className="text-white font-semibold mb-1">🌌 Pick your next target</div>
            <div className="text-slate-200/80 mb-3">
              Use the map to find pirates nearby, scout, and plan attacks.
            </div>
            <button
              type="button"
              className="pa-btn-secondary px-3 py-2"
              onClick={() => onNavigateSection?.('galaxy')}
              data-testid="commander-suggest-open-galaxy"
            >
              Open Galaxy Map
            </button>
          </div>

          <div className="pa-panel p-4">
            <div className="text-white font-semibold mb-1">🚀 Build ships for the next fight</div>
            <div className="text-slate-200/80 mb-3">
              Stock up on fighters + recyclers so every win turns into profit.
            </div>
            <button
              type="button"
              className="pa-btn-secondary px-3 py-2"
              onClick={() => onNavigateSection?.('shipyard')}
              data-testid="commander-suggest-open-shipyard"
            >
              Open Shipyard
            </button>
          </div>
        </div>
      </div>

      {/* Resource Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="pa-card p-6">
          <h3 className="text-xl font-bold mb-4 text-metal">Metal Resources</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-300/70">Current:</span>
              <span className="text-metal font-bold">{totalResources.metal.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300/70">Production:</span>
              <span className="text-metal">{totalProduction.metal.toLocaleString()}/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300/70">Mines:</span>
              <span className="text-metal">{totalBuildings.metal_mine} total</span>
            </div>
          </div>
        </div>

        <div className="pa-card p-6">
          <h3 className="text-xl font-bold mb-4 text-crystal">Crystal Resources</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-300/70">Current:</span>
              <span className="text-crystal font-bold">{totalResources.crystal.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300/70">Production:</span>
              <span className="text-crystal">{totalProduction.crystal.toLocaleString()}/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300/70">Mines:</span>
              <span className="text-crystal">{totalBuildings.crystal_mine} total</span>
            </div>
          </div>
        </div>

        <div className="pa-card p-6">
          <h3 className="text-xl font-bold mb-4 text-deuterium">Deuterium Resources</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-300/70">Current:</span>
              <span className="text-deuterium font-bold">{totalResources.deuterium.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300/70">Production:</span>
              <span className="text-deuterium">{totalProduction.deuterium.toLocaleString()}/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300/70">Synthesizers:</span>
              <span className="text-deuterium">{totalBuildings.deuterium_synthesizer} total</span>
            </div>
          </div>
        </div>
      </div>

      {/* Next Steps */}
      <div className="pa-card p-6">
        <h3 className="text-xl font-bold mb-4 text-white">Next Steps</h3>
        <ul className="space-y-2 text-slate-200/80 text-sm">
          <li>🌌 Open Galaxy Map, find enemies / pirates / allies.</li>
          <li>🔬 Build a Research Lab to generate research points.</li>
          <li>🕵️ Build espionage probes and send an Espionage mission to scout targets.</li>
          <li>⚔️ Attack an enemy (or pirates) and check the Combat Center for reports.</li>
          <li>♻️ After combat, send recyclers to collect debris.</li>
          <li>⏱️ If something says “pending tick”, click “Run tick” (test env) or POST `/api/tick`.</li>
        </ul>
      </div>

      {/* Recent Activity Placeholder */}
      <div className="pa-card p-6">
        <h3 className="text-xl font-bold mb-4 text-white">Recent Activity</h3>
        <div className="space-y-3">
          {activityItems.length === 0 ? (
            <div className="text-center text-slate-300/70 py-4" data-testid="overview-activity-empty">
              {activityLoading ? 'Loading activity…' : 'No recent activity yet. Explore, fight, and colonize to generate events.'}
            </div>
          ) : (
            <div className="space-y-3" data-testid="overview-activity-list">
              {activityItems.map((item) => (
                <div key={item.id} className="flex items-center space-x-3 p-3 pa-panel" data-testid="overview-activity-item">
                  <span className="text-xl">{item.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-white truncate">{item.description}</p>
                    <p className="text-slate-300/70 text-sm">
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
