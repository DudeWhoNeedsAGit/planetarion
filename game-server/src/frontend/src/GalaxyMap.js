import React, { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { useToast } from './ToastContext';
import { useGalaxySseRefresh } from './galaxy/useGalaxySseRefresh';
import GalaxyIntelPanel from './galaxy/GalaxyIntelPanel';
import GalaxyCanvas from './galaxy/GalaxyCanvas';
import GalaxyMinimapV2 from './galaxy/GalaxyMinimapV2';
import { usePanZoom2D } from './galaxy/usePanZoom2D';
import styles from './galaxy/GalaxyMap.module.css';

const DEFAULT_GALAXY_RANGE = 2000;
const MINIMAP_RANGE_MULTIPLIER = 12;
const MAP_SPACING_FACTOR = 10; // purely visual; does not change coordinates or gameplay

function parseCoords(coords) {
  if (!coords || typeof coords !== 'string') return null;
  const parts = coords.split(':').map((v) => parseInt(v, 10));
  if (parts.length !== 3 || parts.some((n) => !Number.isFinite(n))) return null;
  return { x: parts[0], y: parts[1], z: parts[2] };
}

export default function GalaxyMap({ user, planets, onClose, onNavigateSection }) {
  const { showSuccess, showError } = useToast();

  const [systems, setSystems] = useState([]);
  const [minimapSystems, setMinimapSystems] = useState([]);
  const [movingFleets, setMovingFleets] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [galaxyLoaded, setGalaxyLoaded] = useState(false);
  const [galaxyRange] = useState(DEFAULT_GALAXY_RANGE);
  const [showGrid, setShowGrid] = useState(true);
  const [viewportSize, setViewportSize] = useState({ w: 0, h: 0 });
  const [nowMs, setNowMs] = useState(() => Date.now());

  const refreshTimerRef = useRef(null);
  const lastFetchCenterRef = useRef(null);
  const [needsRefresh, setNeedsRefresh] = useState(false);
  const fetchInFlightRef = useRef(false);

  const homePlanet = (planets || []).find((p) => p.user_id === user.id) || (planets || [])[0];
  const homeX = homePlanet?.x || 100;
  const homeY = homePlanet?.y || 200;
  const centerZ = homePlanet?.z || 300;
  const homeCenter = useMemo(() => ({ x: homeX, y: homeY, z: centerZ }), [homeX, homeY, centerZ]);

  const worldScale = useMemo(() => {
    const range = Math.max(1, Number(galaxyRange || DEFAULT_GALAXY_RANGE));
    const w = Math.max(1, Number(viewportSize.w || 0));
    const h = Math.max(1, Number(viewportSize.h || 0));
    const minSide = Math.max(1, Math.min(w, h));
    const scale = (minSide * 0.45) / range;
    const base = Math.max(0.03, Math.min(2.5, Number.isFinite(scale) ? scale : 0.12));
    return base * MAP_SPACING_FACTOR;
  }, [galaxyRange, viewportSize.h, viewportSize.w]);

  const {
    center: cameraCenter,
    setCenter: setCameraCenter,
    zoom,
    setZoom,
    zoomIn,
    zoomOut,
    reset,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    wheelListener,
  } = usePanZoom2D({
    initialCenter: { x: homeX, y: homeY },
    minZoom: 0.06,
    maxZoom: 4,
  });

  const viewCenterX = useMemo(() => Math.round(Number(cameraCenter?.x || 0)), [cameraCenter?.x]);
  const viewCenterY = useMemo(() => Math.round(Number(cameraCenter?.y || 0)), [cameraCenter?.y]);

  useGalaxySseRefresh({
    onRelevantEvent: () => setNeedsRefresh(true),
  });

  useEffect(() => {
    const t = setInterval(() => setNowMs(Date.now()), 250);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!needsRefresh) return;
    if (!galaxyLoaded) return;
    setNeedsRefresh(false);

    if (refreshTimerRef.current) return;
    refreshTimerRef.current = setTimeout(() => {
      refreshTimerRef.current = null;
      fetchNearbySystems({ background: true });
      fetchMinimapSystems({ background: true });
      fetchMovingFleets({ background: true });
    }, 750);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [needsRefresh, galaxyLoaded]);

  useEffect(() => {
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, []);

  const effectiveFetchRange = useMemo(() => {
    const base = Math.max(1, Number(galaxyRange || DEFAULT_GALAXY_RANGE));
    const z = Math.max(0.06, Number(zoom || 1));
    // Zoom out => see more space; fetch more so the view is populated.
    return Math.min(60000, Math.ceil(base / z));
  }, [galaxyRange, zoom]);

  const fetchLimit = useMemo(() => {
    const r = effectiveFetchRange;
    if (r <= 2500) return 600;
    if (r <= 12000) return 1500;
    return 2200;
  }, [effectiveFetchRange]);

  const fetchNearbySystems = async ({ background = false, overrideCenter = null } = {}) => {
    try {
      if (fetchInFlightRef.current) return;
      fetchInFlightRef.current = true;

      if (background) setRefreshing(true);
      else {
        setLoading(true);
        setError(null);
      }

      const center = overrideCenter || { x: viewCenterX, y: viewCenterY, z: centerZ };
      const params = { range: effectiveFetchRange, z_band: 0, limit: fetchLimit };
      const res = await axios.get(`/api/galaxy/nearby/${center.x}/${center.y}/${center.z}`, { params });

      const nextSystems = Array.isArray(res.data?.systems) ? res.data.systems : [];
      setSystems(nextSystems);

      setGalaxyLoaded(true);
      lastFetchCenterRef.current = { x: center.x, y: center.y, z: center.z };
    } catch (e) {
      console.error('❌ Error fetching galaxy data:', e);
      setError('Failed to load galaxy data');
    } finally {
      fetchInFlightRef.current = false;
      if (background) setRefreshing(false);
      else setLoading(false);
    }
  };

  const fetchMinimapSystems = async ({ background = false } = {}) => {
    try {
      if (background) setRefreshing(true);
      const minimapRange = Math.max(1, Number(galaxyRange || DEFAULT_GALAXY_RANGE)) * MINIMAP_RANGE_MULTIPLIER;
      const params = { range: minimapRange, z_band: 0, limit: 1500 };
      const res = await axios.get(`/api/galaxy/nearby/${homeX}/${homeY}/${centerZ}`, { params });
      const nextSystems = Array.isArray(res.data?.systems) ? res.data.systems : [];
      setMinimapSystems(nextSystems);
    } catch (e) {
      // non-fatal
    } finally {
      if (background) setRefreshing(false);
    }
  };

  const fetchMovingFleets = async ({ background = false } = {}) => {
    try {
      if (background) setRefreshing(true);
      const res = await axios.get('/api/fleet', { params: { include_inventory: 0 } });
      const fleets = Array.isArray(res.data) ? res.data : [];

      const next = fleets
        .map((f) => {
          const travel = f?.travel_info || null;
          if (!travel) return null;
          const start = parseCoords(travel.start_coordinates);
          const target = parseCoords(travel.target_coordinates);
          if (!start || !target) return null;

          const depMs = f?.departure_time ? new Date(f.departure_time).getTime() : null;
          const arrMs = f?.arrival_time ? new Date(f.arrival_time).getTime() : null;

          return {
            id: f.id,
            mission: f.mission,
            status: f.status,
            start,
            target,
            departureMs: Number.isFinite(depMs) ? depMs : null,
            arrivalMs: Number.isFinite(arrMs) ? arrMs : null,
            progressPct: typeof travel.progress_percentage === 'number' ? travel.progress_percentage : null,
          };
        })
        .filter(Boolean)
        .filter((f) => f.start.z === centerZ && f.target.z === centerZ)
        .filter((f) => f.status !== 'stationed');

      setMovingFleets(next);
    } catch (e) {
      // non-fatal
    } finally {
      if (background) setRefreshing(false);
    }
  };

  useEffect(() => {
    if (galaxyLoaded) return;
    fetchNearbySystems();
    fetchMinimapSystems();
    fetchMovingFleets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [galaxyLoaded]);

  useEffect(() => {
    if (!galaxyLoaded) return;
    fetchNearbySystems({ background: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [galaxyRange]);

  useEffect(() => {
    if (!galaxyLoaded) return;
    const last = lastFetchCenterRef.current;
    if (!last) return;

    const dx = Math.abs((last?.x ?? 0) - viewCenterX);
    const dy = Math.abs((last?.y ?? 0) - viewCenterY);
    if (dx <= 250 && dy <= 250) return;

    // Debounce panning so we don't spam the backend while dragging.
    if (refreshTimerRef.current) return;
    refreshTimerRef.current = setTimeout(() => {
      refreshTimerRef.current = null;
      fetchNearbySystems({ background: true, overrideCenter: { x: viewCenterX, y: viewCenterY, z: centerZ } });
    }, 250);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [viewCenterX, viewCenterY, galaxyLoaded]);

  useEffect(() => {
    if (!galaxyLoaded) return;
    // Zoom changes what is visible; refetch with an effective range that matches zoom.
    if (refreshTimerRef.current) return;
    refreshTimerRef.current = setTimeout(() => {
      refreshTimerRef.current = null;
      fetchNearbySystems({ background: true });
    }, 220);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoom, galaxyLoaded, effectiveFetchRange]);

  const fleetOverlay = useMemo(() => {
    const colorByMission = (mission) => {
      const m = String(mission || '').toLowerCase();
      if (m.includes('attack')) return '#ef4444';
      if (m.includes('recycle')) return '#22c55e';
      if (m.includes('colon')) return '#14b8a6';
      if (m.includes('explor')) return '#a855f7';
      if (m.includes('espion')) return '#f59e0b';
      return '#60a5fa';
    };

    return (movingFleets || []).map((f) => {
      const start = { x: (f.start.x - homeX) * worldScale, y: (f.start.y - homeY) * worldScale };
      const target = { x: (f.target.x - homeX) * worldScale, y: (f.target.y - homeY) * worldScale };

      let t = 0;
      if (f.departureMs != null && f.arrivalMs != null && f.arrivalMs > f.departureMs) {
        t = Math.max(0, Math.min(1, (nowMs - f.departureMs) / (f.arrivalMs - f.departureMs)));
      } else if (typeof f.progressPct === 'number') {
        t = Math.max(0, Math.min(1, f.progressPct / 100));
      }

      const dot = {
        x: start.x + (target.x - start.x) * t,
        y: start.y + (target.y - start.y) * t,
      };

      return { id: f.id, start, target, dot, color: colorByMission(f.mission), title: `Fleet #${f.id} • ${f.mission} • ${f.status}` };
    });
  }, [movingFleets, nowMs, homeX, homeY, worldScale]);

  const handleExploreSystem = async (system) => {
    if (system.explored) return;

    setLoading(true);
    try {
      const fleetResponse = await axios.get('/api/fleet');
      const fleetData = Array.isArray(fleetResponse.data) ? fleetResponse.data : [];
      const availableFleet = fleetData.find((f) => f.status === 'stationed');
      if (!availableFleet) {
        showError('No stationed fleets available for exploration.');
        return;
      }

      await axios.post('/api/fleet/send', {
        fleet_id: availableFleet.id,
        mission: 'explore',
        target_x: system.x,
        target_y: system.y,
        target_z: system.z,
      });

      showSuccess(`🚀 Exploration fleet sent to ${system.x}:${system.y}:${system.z}!`, 4000);
      await fetchNearbySystems();
    } catch (e) {
      console.error('Error sending exploration fleet:', e);
      showError('Failed to send exploration fleet. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const selectedKey = selectedSystem?.key || (selectedSystem ? `${selectedSystem.x}:${selectedSystem.y}:${selectedSystem.z}` : null);

  return (
    <div className="fixed inset-0 bg-black/75 flex items-center justify-center z-50" data-testid="galaxy-modal">
      <div className="pa-modal p-6 max-w-6xl w-full h-5/6 flex flex-col" data-testid="galaxy-modal-content">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-white">Galaxy Map</h2>
          <button onClick={onClose} data-testid="galaxy-close" className="pa-btn-ghost px-3 py-2 text-sm">
            Close
          </button>
        </div>

        <div className="flex justify-between items-center mb-4">
          <div className="text-sm text-slate-200/80">
            Center: {viewCenterX}:{viewCenterY}:{centerZ} | Zoom: {Math.round(zoom * 100)}% | Range: {galaxyRange} units
            {refreshing && <span className="ml-2 text-xs text-blue-300">(updating…)</span>}
          </div>
          <div className="flex items-center space-x-2">
            <button onClick={zoomOut} className="pa-btn-secondary px-3 py-1 text-sm" disabled={zoom <= 0.06}>
              −
            </button>
            <button onClick={zoomIn} className="pa-btn-secondary px-3 py-1 text-sm" disabled={zoom >= 4}>
              +
            </button>
            <button onClick={reset} className="pa-btn-primary px-3 py-1 text-sm">
              Reset
            </button>
            <button
              onClick={() => {
                const minSide = Math.max(1, Math.min(Number(viewportSize.w || 0), Number(viewportSize.h || 0)));
                const minimapRange = Math.max(1, Number(galaxyRange || DEFAULT_GALAXY_RANGE)) * MINIMAP_RANGE_MULTIPLIER;
                const target = minSide / (2 * minimapRange * Math.max(0.0001, worldScale));
                setZoom(target);
              }}
              className="pa-btn-secondary px-3 py-1 text-sm"
              title="Zoom out to roughly fit the minimap range into view"
            >
              Fit
            </button>
            <button
              onClick={() => setShowGrid((v) => !v)}
              className={`${showGrid ? 'pa-btn-primary' : 'pa-btn-secondary'} px-3 py-1 text-sm`}
            >
              Grid {showGrid ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>

        {loading && !galaxyLoaded && (
          <div className="flex-1 pa-panel flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
              <div className="text-white text-lg font-semibold">Loading Galaxy Data…</div>
              <div className="text-slate-300/70 text-sm mt-2">Fetching all planets and systems</div>
            </div>
          </div>
        )}

        {error && !loading && (
          <div className="flex-1 pa-panel flex items-center justify-center">
            <div className="text-center">
              <div className="text-red-500 text-4xl mb-4">⚠️</div>
              <div className="text-white text-lg font-semibold">Failed to Load Galaxy</div>
              <div className="text-slate-300/70 text-sm mt-2">{error}</div>
              <button onClick={() => fetchNearbySystems()} className="mt-4 pa-btn-primary px-4 py-2">
                Retry
              </button>
            </div>
          </div>
        )}

        {(!loading || galaxyLoaded) && !error && (
          <div className={`flex-1 ${styles.mapViewport}`}>
            <GalaxyMinimapV2
              systems={minimapSystems?.length ? minimapSystems : systems}
              homeCenter={homeCenter}
              cameraCenter={{ x: viewCenterX, y: viewCenterY }}
              viewportSize={viewportSize}
              zoom={zoom}
              worldScale={worldScale}
              minimapRangeUnits={Math.max(1, Number(galaxyRange || DEFAULT_GALAXY_RANGE)) * MINIMAP_RANGE_MULTIPLIER}
              onFocus={(next) => setCameraCenter(next)}
            />

            <GalaxyCanvas
              homeCenter={homeCenter}
              center={{ x: viewCenterX, y: viewCenterY }}
              zoom={zoom}
              worldScale={worldScale}
              systems={systems}
              selectedKey={selectedKey}
              onSelectSystem={(s) => setSelectedSystem(s)}
              onViewportSize={(s) => setViewportSize(s)}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              wheelListener={wheelListener}
              showGrid={showGrid}
              movingFleetOverlay={fleetOverlay}
            />

            <div className={styles.legend}>
              <div className={styles.legendTitle}>Legend</div>
              <div className={styles.legendGrid}>
                <div className={styles.legendItem}>
                  <span className={styles.swatch} style={{ background: '#3b82f6' }} />
                  Yours
                </div>
                <div className={styles.legendItem}>
                  <span className={styles.swatch} style={{ background: '#f59e0b' }} />
                  Players
                </div>
                <div className={styles.legendItem}>
                  <span className={styles.swatch} style={{ background: '#ef4444' }} />
                  Pirates
                </div>
                <div className={styles.legendItem}>
                  <span className={styles.swatch} style={{ background: '#94a3b8' }} />
                  Unknown
                </div>
                <div className={styles.legendItem}>
                  <span className={styles.swatchRing} />
                  Debris
                </div>
              </div>
            </div>

            {selectedSystem && (
              <div className={styles.intelPanelWrap} data-testid="galaxy-intel-panel">
                <GalaxyIntelPanel
                  system={selectedSystem}
                  onClose={() => setSelectedSystem(null)}
                  onExplore={handleExploreSystem}
                  loading={loading}
                  userId={user?.id}
                  centerX={homeX}
                  centerY={homeY}
                  centerZ={centerZ}
                  onNavigateSection={onNavigateSection}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
