import React, { useEffect, useMemo, useState, useCallback } from 'react';
import axios from 'axios';
import { useToast } from './ToastContext';

const RESEARCH_LABELS = {
  colonization_tech: 'Colonization Tech',
  astrophysics: 'Astrophysics',
  interstellar_communication: 'Interstellar Communication',
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
      const res = await axios.get('/api/research');
      setData(res.data);
    } catch (e) {
      showError(e.response?.data?.error || 'Failed to load research');
      setData(null);
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
      <div className="bg-gray-800 rounded-lg p-6" data-testid="section-research">
        <div className="text-center text-white">Loading research…</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="section-research">
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-xl font-bold mb-2 text-white">🔬 Research Lab</h3>
        <div className="text-sm text-gray-300">
          Research points accrue from Research Labs on your planets and are processed on ticks.
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm mb-1">Research Points</div>
          <div className="text-3xl font-bold text-blue-300" data-testid="research-points">
            {(data?.research_points ?? 0).toLocaleString()}
          </div>
          <div className="mt-2 text-xs text-gray-400">
            +{Math.floor(rates?.rp_per_hour || 0).toLocaleString()}/h • ~{Math.floor(rates?.rp_per_tick || 0).toLocaleString()}/tick
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm mb-1">Colonization Tech</div>
          <div className="text-2xl font-bold text-white" data-testid="research-level-colonization">
            L{levels?.colonization_tech ?? 0}
          </div>
          <div className="text-xs text-gray-400 mt-2">Unlocks harder colonization targets.</div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm mb-1">Astrophysics</div>
          <div className="text-2xl font-bold text-white" data-testid="research-level-astrophysics">
            L{levels?.astrophysics ?? 0}
          </div>
          <div className="text-xs text-gray-400 mt-2">Reduces travel time; improves expansion.</div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4 text-white">Research Queue</h4>

        {queue ? (
          <div className="border border-gray-700 rounded p-4 bg-gray-900/30" data-testid="research-queue-active">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-white font-semibold">
                  {RESEARCH_LABELS[queue.key] || queue.key} → Level {queue.target_level}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  Completes at {queue.completes_at}
                  {queueRemainingSeconds != null ? ` • ~${formatSeconds(queueRemainingSeconds)} remaining` : ''}
                </div>
              </div>
              <button
                type="button"
                className="px-4 py-2 rounded bg-gray-700 hover:bg-gray-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
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
            <div className="mt-3 text-xs text-gray-400">
              Tip: if something is “pending tick”, click “Run tick” to process completions faster in test env.
            </div>
          </div>
        ) : (
          <div className="text-gray-400" data-testid="research-queue-empty">
            No research in progress.
          </div>
        )}
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h4 className="text-lg font-semibold mb-4 text-white">Start Research</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-gray-300 mb-2">Technology</label>
            <select
              className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              value={selectedKey}
              onChange={(e) => setSelectedKey(e.target.value)}
              data-testid="research-select"
              disabled={Boolean(queue)}
            >
              <option value="colonization_tech">Colonization Tech</option>
              <option value="astrophysics">Astrophysics</option>
              <option value="interstellar_communication">Interstellar Communication</option>
            </select>
          </div>

          <div className="text-sm text-gray-300">
            <div>Next level: <span className="text-white font-medium">L{(levels?.[selectedKey] ?? 0) + 1}</span></div>
            <div>Cost: <span className="text-white font-medium">{(selectedCost ?? 0).toLocaleString()} RP</span></div>
            <div>Duration: <span className="text-white font-medium">{formatSeconds(selectedDuration ?? 0)}</span></div>
          </div>

          <div>
            <button
              type="button"
              className="w-full px-4 py-3 rounded bg-blue-600 hover:bg-blue-700 text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed"
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
          <div className="mt-3 text-xs text-gray-400">
            Finish or cancel the current research to start another.
          </div>
        )}
      </div>
    </div>
  );
}
