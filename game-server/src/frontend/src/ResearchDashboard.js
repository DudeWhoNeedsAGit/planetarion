import React, { useEffect, useMemo, useState, useCallback } from 'react';
import axios from 'axios';
import { useToast } from './ToastContext';
import { formatCompactNumber } from './numberFormat';

const RESEARCH_LABELS = {
  colonization_tech: 'Colonization Tech',
  astrophysics: 'Astrophysics',
  interstellar_communication: 'Interstellar Communication',
  espionage_tech: 'Espionage Tech',
  energy_tech: 'Energy Tech',
  computer_tech: 'Computer Tech',
  recycler_efficiency: 'Recycler Efficiency',
  weapons_tech: 'Weapons Tech',
  shielding_tech: 'Shielding Tech',
  armour_tech: 'Armor Tech',
};

function formatSeconds(seconds) {
  const s = Math.max(0, Math.floor(seconds || 0));
  const m = Math.floor(s / 60);
  const r = s % 60;
  if (m <= 0) return `${r}s`;
  return `${m}m ${r}s`;
}

export default function ResearchDashboard() {
  const { showSuccess, showError } = useToast();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [selectedKey, setSelectedKey] = useState('astrophysics');
  const [starting, setStarting] = useState(false);
  const [canceling, setCanceling] = useState(false);

  const fetchResearch = useCallback(async () => {
    // Keep the last good view rendered while refreshing to avoid flicker.
    if (!data) setLoading(true);
    try {
      const run = async () => {
        const res = await axios.get('/api/research');
        return res.data;
      };

      try {
        setData(await run());
      } catch (e) {
        const status = e.response?.status;
        const shouldRetry = !e.response || (typeof status === 'number' && status >= 500);
        if (!shouldRetry) throw e;

        await new Promise((r) => setTimeout(r, 250));
        setData(await run());
      }
    } catch (e) {
      showError(e.response?.data?.error || 'Failed to load research');
      if (!data) setData(null);
    } finally {
      setLoading(false);
    }
  }, [data, showError]);

  useEffect(() => {
    fetchResearch();
    const onTick = () => fetchResearch();
    window.addEventListener('planetarion:tick', onTick);
    return () => window.removeEventListener('planetarion:tick', onTick);
  }, [fetchResearch]);

  const levels = data?.levels || {};
  const costs = data?.next_level_costs || {};
  const durations = data?.next_level_durations_seconds || {};
  const rates = data?.rates || {};
  const queue = data?.queue || null;
  const tree = data?.tree?.branches || null;

  const queueRemainingSeconds = useMemo(() => {
    if (!queue?.completes_at) return null;
    const t = new Date(queue.completes_at).getTime();
    const now = Date.now();
    if (!Number.isFinite(t)) return null;
    return Math.max(0, Math.floor((t - now) / 1000));
  }, [queue?.completes_at]);

  const selectedCost = costs?.[selectedKey] ?? null;
  const selectedDuration = durations?.[selectedKey] ?? null;

  if (loading) {
    return (
      <div className="pa-card p-6" data-testid="section-research">
        <div className="text-center text-white">Loading research…</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="section-research">
      <div className="pa-card p-6">
        <h3 className="text-xl font-bold mb-2 text-white">🔬 Research Lab</h3>
        <div className="text-sm text-slate-200/80">
          Research points accrue from Research Labs on your planets and are processed on ticks.
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="pa-card p-6">
          <div className="text-slate-300/70 text-sm mb-1">Research Points</div>
          <div className="text-3xl font-bold text-blue-300" data-testid="research-points">
            {formatCompactNumber(data?.research_points ?? 0)}
          </div>
          <div className="mt-2 text-xs text-slate-300/70">
            +{formatCompactNumber(Math.floor(rates?.rp_per_hour || 0))}/h • ~{formatCompactNumber(Math.floor(rates?.rp_per_tick || 0))}/tick
          </div>
        </div>

        <div className="pa-card p-6">
          <div className="text-slate-300/70 text-sm mb-1">Colonization Tech</div>
          <div className="text-2xl font-bold text-white" data-testid="research-level-colonization">
            L{levels?.colonization_tech ?? 0}
          </div>
          <div className="text-xs text-slate-300/70 mt-2">Unlocks harder colonization targets.</div>
        </div>

        <div className="pa-card p-6">
          <div className="text-slate-300/70 text-sm mb-1">Astrophysics</div>
          <div className="text-2xl font-bold text-white" data-testid="research-level-astrophysics">
            L{levels?.astrophysics ?? 0}
          </div>
          <div className="text-xs text-slate-300/70 mt-2">Reduces travel time; improves expansion.</div>
        </div>
      </div>

      {Array.isArray(tree) && tree.length > 0 && (
        <div className="pa-card p-6" data-testid="research-tree">
          <h4 className="text-lg font-semibold mb-4 text-white">Research Tree</h4>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {tree.map((branch) => (
              <div key={branch.name} className="pa-panel p-4">
                <div className="text-white font-bold mb-3">{branch.name}</div>
                <div className="space-y-3">
                  {(branch.items || []).map((item) => (
                    <button
                      key={item.key}
                      type="button"
                      className={`w-full text-left rounded-lg border px-3 py-2 transition ${
                        selectedKey === item.key ? 'border-blue-400/50 bg-blue-950/30' : 'border-slate-600/30 hover:border-slate-500/40 hover:bg-slate-600/10'
                      }`}
                      disabled={Boolean(queue)}
                      onClick={() => setSelectedKey(item.key)}
                      data-testid={`research-tree-${item.key}`}
                      title={item.effect_hint || ''}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-slate-100 font-semibold">{item.name || RESEARCH_LABELS[item.key] || item.key}</div>
                        <div className="text-xs text-slate-200/80 font-bold">L{levels?.[item.key] ?? 0}</div>
                      </div>
                      {item.description && (
                        <div className="text-xs text-slate-300/70 mt-1">{item.description}</div>
                      )}
                      {item.effect_hint && (
                        <div className="text-[11px] text-slate-200/70 mt-1">{item.effect_hint}</div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
          {queue && (
            <div className="mt-3 text-xs text-slate-300/70">
              Tree selection is disabled while research is running.
            </div>
          )}
        </div>
      )}

      <div className="pa-card p-6">
        <h4 className="text-lg font-semibold mb-4 text-white">Research Queue</h4>

        {queue ? (
          <div className="pa-panel p-4" data-testid="research-queue-active">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-white font-semibold">
                  {RESEARCH_LABELS[queue.key] || queue.key} → Level {queue.target_level}
                </div>
                <div className="text-xs text-slate-300/70 mt-1">
                  Completes at {queue.completes_at}
                  {queueRemainingSeconds != null ? ` • ~${formatSeconds(queueRemainingSeconds)} remaining` : ''}
                </div>
              </div>
              <button
                type="button"
                className="pa-btn-secondary px-4 py-2"
                onClick={async () => {
                  setCanceling(true);
                  try {
                    await axios.post('/api/research/cancel');
                    showSuccess('Research cancelled');
                    await fetchResearch();
                  } catch (e) {
                    showError(e.response?.data?.error || 'Cancel failed');
                  } finally {
                    setCanceling(false);
                  }
                }}
                disabled={canceling}
                data-testid="research-cancel"
              >
                {canceling ? 'Canceling…' : 'Cancel'}
              </button>
            </div>
            <div className="mt-3 text-xs text-slate-300/70">
              Tip: completions are applied by server ticks; in local dev this should resolve automatically within a few seconds.
            </div>
          </div>
        ) : (
          <div className="text-slate-300/70" data-testid="research-queue-empty">
            No research in progress.
          </div>
        )}
      </div>

      <div className="pa-card p-6">
        <h4 className="text-lg font-semibold mb-4 text-white">Start Research</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-slate-200/90 mb-2">Technology</label>
            <select
              className="pa-input"
              value={selectedKey}
              onChange={(e) => setSelectedKey(e.target.value)}
              data-testid="research-select"
              disabled={Boolean(queue)}
            >
              {Object.entries(RESEARCH_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>

          <div className="text-sm text-slate-200/80">
            <div>Next level: <span className="text-white font-medium">L{(levels?.[selectedKey] ?? 0) + 1}</span></div>
            <div>Cost: <span className="text-white font-medium">{formatCompactNumber(selectedCost ?? 0)} RP</span></div>
            <div>Duration: <span className="text-white font-medium">{formatSeconds(selectedDuration ?? 0)}</span></div>
          </div>

          <div>
            <button
              type="button"
              className="w-full pa-btn-primary py-3"
              disabled={starting || Boolean(queue)}
              data-testid="research-start"
              onClick={async () => {
                setStarting(true);
                try {
                  await axios.post('/api/research/start', { key: selectedKey });
                  showSuccess('Research started');
                  await fetchResearch();
                } catch (e) {
                  showError(e.response?.data?.error || 'Start failed');
                } finally {
                  setStarting(false);
                }
              }}
            >
              {starting ? 'Starting…' : 'Start'}
            </button>
          </div>
        </div>
        {queue && (
          <div className="mt-3 text-xs text-slate-300/70">
            Finish or cancel the current research to start another.
          </div>
        )}
      </div>
    </div>
  );
}
