import React, { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import planetImage from './images/p4.png';
import { useToast } from './ToastContext';
import GalaxyMinimap from './galaxy/GalaxyMinimap';
import { useGalaxySseRefresh } from './galaxy/useGalaxySseRefresh';
import GalaxyIntelPanel from './galaxy/GalaxyIntelPanel';
import GalaxyBackground from './galaxy/GalaxyBackground';
import GalaxyFleetOverlay from './galaxy/GalaxyFleetOverlay';

const DEFAULT_GALAXY_RANGE = 2000;
const WORLD_SCALE_FALLBACK = 0.12; // convert coordinate units -> pixels (higher = more spread out)
const MINIMAP_RANGE_MULTIPLIER = 12; // minimap shows a much wider area than the main viewport range
const TARGET_MARKERS_PER_SCREEN = 4;
const MAX_RENDERED_MARKERS = 75;

function GalaxyMap({ user, planets, onClose, onNavigateSection }) {
  const { showSuccess, showError } = useToast();
  const [systems, setSystems] = useState([]);
  const [minimapSystems, setMinimapSystems] = useState([]);
  const [movingFleets, setMovingFleets] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [loading, setLoading] = useState(true); // Start with loading true
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [galaxyLoaded, setGalaxyLoaded] = useState(false);
  const [galaxyRange, setGalaxyRange] = useState(DEFAULT_GALAXY_RANGE);
  const [zoom, setZoom] = useState(1);
  const [viewOffset, setViewOffset] = useState({ x: 0, y: 0 });
  const [showGrid, setShowGrid] = useState(true);
  const [showAllMarkers, setShowAllMarkers] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const mapRef = useRef(null);
  const [mapSize, setMapSize] = useState({ width: 0, height: 0 });
  const [needsRefresh, setNeedsRefresh] = useState(false);
  const refreshTimerRef = useRef(null);
  const [nowMs, setNowMs] = useState(() => Date.now());

  // Stabilize background starfield so it doesn't "flicker" on re-renders (e.g. while panning/zooming).
  const starfield = React.useMemo(() => {
    const stars = Array.from({ length: 200 }, (_, i) => ({
      key: `star-${i}`,
      sizeClass: i % 10 === 0 ? 'w-1 h-1' : i % 5 === 0 ? 'w-0.5 h-0.5' : 'w-px h-px',
      left: Math.random() * 100,
      top: Math.random() * 100,
      twinkleSeconds: 2 + Math.random() * 3,
      delaySeconds: Math.random() * 3
    }));
    const particles = Array.from({ length: 30 }, (_, i) => ({
      key: `particle-${i}`,
      left: Math.random() * 100,
      top: Math.random() * 100,
      floatSeconds: 10 + Math.random() * 20,
      delaySeconds: Math.random() * 10
    }));
    return { stars, particles };
  }, []);

  // Get user's home planet coordinates as center
  const homePlanet = (planets || []).find(p => p.user_id == user.id) || (planets || [])[0]; // fallback if user_id isn't present
  const centerX = homePlanet?.x || 100; // Default to 100 instead of 0
  const centerY = homePlanet?.y || 200;
  const centerZ = homePlanet?.z || 300;

  // Adaptive world scale: fit the selected range into the visible viewport so the map
  // doesn't look "over-clustered" around the center.
  const worldScale = useMemo(() => {
    const range = Math.max(1, Number(galaxyRange || DEFAULT_GALAXY_RANGE));
    const w = Math.max(1, Number(mapSize.width || 0));
    const h = Math.max(1, Number(mapSize.height || 0));
    const minSide = Math.max(1, Math.min(w, h));
    // Half of the min side maps to +/-range. Use 0.45 to keep padding for UI.
    const scale = (minSide * 0.45) / range;
    return Math.max(0.03, Math.min(0.45, Number.isFinite(scale) ? scale : WORLD_SCALE_FALLBACK));
  }, [galaxyRange, mapSize.height, mapSize.width]);

  const viewCenterX = useMemo(() => {
    return Math.round(centerX - viewOffset.x / (zoom * worldScale));
  }, [centerX, viewOffset.x, zoom, worldScale]);

  const viewCenterY = useMemo(() => {
    return Math.round(centerY - viewOffset.y / (zoom * worldScale));
  }, [centerY, viewOffset.y, zoom, worldScale]);

  const mapAnchor = useMemo(() => {
    const width = Number(mapSize.width || 0);
    const height = Number(mapSize.height || 0);
    // Fallback to legacy constants if we haven't measured yet.
    if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
      return { x: 200, y: 150 };
    }
    return { x: Math.round(width / 2), y: Math.round(height / 2) };
  }, [mapSize.height, mapSize.width]);

  // Galaxy refresh is event-driven (SSE). The map is mostly static; we refresh summaries on meaningful events.
  useGalaxySseRefresh({
    onRelevantEvent: () => setNeedsRefresh(true),
  });

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

  const displaySystems = useMemo(() => {
    if (showAllMarkers) return systems || [];

    // Render a readable selection based on screen-density instead of a hard cap.
    // This keeps ~3–4 markers visible at default zoom, while allowing more when zooming in.
    const userId = user?.id;
    const range = Math.max(1, Number(galaxyRange || DEFAULT_GALAXY_RANGE));

    const scale = worldScale * zoom;
    const w = Math.max(1, Number(mapSize.width || 1));
    const h = Math.max(1, Number(mapSize.height || 1));
    const area = w * h;
    const baseMinDist = Math.sqrt(area / TARGET_MARKERS_PER_SCREEN) * 0.55;
    const minDistPx = Math.max(80, Math.min(260, baseMinDist / Math.max(0.75, zoom)));
    const minDistSq = minDistPx * minDistPx;

    const isPirates = (s) => s.relation === 'pirates' || s.flags?.has_pirates;
    const isSelf = (s) => s.relation === 'self' || (s.owner_id != null && s.owner_id === userId);
    const isOtherPlayer = (s) => s.owner_id != null && s.owner_id !== userId && !isPirates(s);
    const isUnownedUnexplored = (s) => s.owner_id == null && !s.explored;

    const candidates = (systems || []).map((s) => {
      const dx = (s.x || 0) - viewCenterX;
      const dy = (s.y || 0) - viewCenterY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      // Project into screen-space (relative to viewport center).
      const px = dx * scale;
      const py = dy * scale;
      return { s, dist, px, py };
    });

    const score = ({ s, dist }) => {
      let bonus = 0;
      if (isSelf(s)) bonus -= 20000;
      else if (isPirates(s)) bonus -= 15000;
      else if (isOtherPlayer(s)) bonus -= 12000;
      else if (isUnownedUnexplored(s)) bonus -= 8000;
      else if (s.explored) bonus -= 2000;
      return dist + bonus;
    };

    candidates.sort((a, b) => score(a) - score(b));

    const selected = [];
    const selectedKeys = new Set();
    const occupied = [];

    for (const c of candidates) {
      if (selected.length >= MAX_RENDERED_MARKERS) break;
      // Skip systems outside the main query radius to avoid minimap-only dots.
      if (c.dist > range * 1.05) continue;

      const key = c.s.key || `${c.s.x}:${c.s.y}:${c.s.z}`;
      if (selectedKeys.has(key)) continue;

      let ok = true;
      for (const p of occupied) {
        const dx = c.px - p.x;
        const dy = c.py - p.y;
        if (dx * dx + dy * dy < minDistSq) {
          ok = false;
          break;
        }
      }
      if (!ok) continue;

      selectedKeys.add(key);
      selected.push(c.s);
      occupied.push({ x: c.px, y: c.py });
    }

    if (selected.length === 0 && candidates.length > 0) {
      selected.push(candidates[0].s);
    }

    return selected;
  }, [showAllMarkers, systems, user?.id, viewCenterX, viewCenterY, galaxyRange, worldScale, zoom, mapSize.width, mapSize.height]);

  const displaySystemKeys = useMemo(() => {
    return new Set((displaySystems || []).map((s) => s.key || `${s.x}:${s.y}:${s.z}`));
  }, [displaySystems]);

  const lastFetchCenterRef = React.useRef({ x: centerX, y: centerY, z: centerZ });

  useEffect(() => {
    const updateSize = () => {
      const el = mapRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      setMapSize({ width: rect.width, height: rect.height });
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  useEffect(() => {
    // Load galaxy data once when component mounts.
    if (!galaxyLoaded) {
      fetchNearbySystems();
      fetchMinimapSystems();
      fetchMovingFleets();
    }
    // No polling: coordinates are mostly static. Ownership/type changes are handled via SSE (below),
    // plus explicit refreshes on pan/range changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [galaxyLoaded]);

  useEffect(() => {
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, []);

  // Lightweight animation ticker for fleet movement (client-side interpolation).
  useEffect(() => {
    const t = setInterval(() => setNowMs(Date.now()), 250);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!galaxyLoaded) return;
    if (isDragging) return;
    // When the user pans far enough that the viewport center moved, refresh the marker dataset.
    const last = lastFetchCenterRef.current;
    const dx = Math.abs((last?.x ?? 0) - viewCenterX);
    const dy = Math.abs((last?.y ?? 0) - viewCenterY);
    if (dx > 250 || dy > 250) {
      fetchNearbySystems({ background: true, overrideCenter: { x: viewCenterX, y: viewCenterY, z: centerZ } });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [viewCenterX, viewCenterY, isDragging, galaxyLoaded]);

  useEffect(() => {
    if (!galaxyLoaded) return;
    fetchNearbySystems({ background: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [galaxyRange]);

  const fetchNearbySystems = async ({ background = false, overrideCenter = null } = {}) => {
    try {
      if (background) {
        setRefreshing(true);
      } else {
        setLoading(true);
        setError(null);
      }

      const center = overrideCenter || { x: viewCenterX, y: viewCenterY, z: centerZ };
      // Let the backend choose the default range based on research unless overridden.
      // GalaxyMap is 2D for now, so keep queries on the current Z slice.
      const params = galaxyRange ? { range: galaxyRange, z_band: 0 } : { z_band: 0 };
      const res = await axios.get(`/api/galaxy/nearby/${center.x}/${center.y}/${center.z}`, { params });

      const nextSystems = Array.isArray(res.data?.systems) ? res.data.systems : [];
      setSystems(nextSystems);
      const serverRange = res.data?.meta?.range;
      if (typeof serverRange === 'number' && !Number.isNaN(serverRange) && serverRange > 0) {
        setGalaxyRange(serverRange);
      }
      setGalaxyLoaded(true);
      lastFetchCenterRef.current = { x: center.x, y: center.y, z: center.z };
    } catch (error) {
      console.error('❌ Error fetching galaxy data:', error);
      setError('Failed to load galaxy data');
    } finally {
      if (background) {
        setRefreshing(false);
      } else {
        setLoading(false);
      }
    }
  };

  const fetchMinimapSystems = async ({ background = false } = {}) => {
    try {
      if (background) {
        setRefreshing(true);
      }

      const minimapRange = Math.max(1, Number(galaxyRange || DEFAULT_GALAXY_RANGE)) * MINIMAP_RANGE_MULTIPLIER;
      const params = { range: minimapRange, z_band: 0, limit: 1500 };
      const res = await axios.get(`/api/galaxy/nearby/${centerX}/${centerY}/${centerZ}`, { params });
      const nextSystems = Array.isArray(res.data?.systems) ? res.data.systems : [];
      setMinimapSystems(nextSystems);
    } catch (e) {
      // Non-fatal: minimap can fall back to main systems.
    } finally {
      if (background) {
        setRefreshing(false);
      }
    }
  };

  const parseCoords = (coords) => {
    if (!coords || typeof coords !== 'string') return null;
    const parts = coords.split(':').map((v) => parseInt(v, 10));
    if (parts.length !== 3 || parts.some((n) => !Number.isFinite(n))) return null;
    return { x: parts[0], y: parts[1], z: parts[2] };
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
        // GalaxyMap is 2D on the player's Z-slice.
        .filter((f) => f.start.z === centerZ && f.target.z === centerZ)
        .filter((f) => f.status !== 'stationed');

      setMovingFleets(next);
    } catch (e) {
      // Non-fatal: map can still function without fleet overlays.
    } finally {
      if (background) setRefreshing(false);
    }
  };

  const handleExploreSystem = async (system) => {
    if (system.explored) return;

    // Send exploration fleet
    setLoading(true);
    try {
      // Find a fleet to send (simplified - use first available)
      const fleetResponse = await axios.get('/api/fleet');
      const fleetData = Array.isArray(fleetResponse.data) ? fleetResponse.data : [];
      const availableFleet = fleetData.find(f => f.status === 'stationed');

      if (!availableFleet) {
        showError('No available fleets for exploration! Build ships in the Shipyard first.');
        return;
      }

      await axios.post('/api/fleet/send', {
        fleet_id: availableFleet.id,
        mission: 'explore',
        target_x: system.x,
        target_y: system.y,
        target_z: system.z
      });

      showSuccess(`🚀 Exploration fleet sent to ${system.x}:${system.y}:${system.z}!`, 4000);
      // Refresh markers after sending exploration.
      await fetchNearbySystems();
    } catch (error) {
      console.error('Error sending exploration fleet:', error);
      showError('Failed to send exploration fleet. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Zoom controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.5));
  const resetView = () => {
    setZoom(1);
    setViewOffset({ x: 0, y: 0 });
  };

  // Calculate system position for grid display
  const getSystemPosition = (system) => {
    const relativeX = (system.x - centerX) * worldScale * zoom + viewOffset.x;
    const relativeY = (system.y - centerY) * worldScale * zoom + viewOffset.y;
    return { x: relativeX, y: relativeY };
  };

  const getPositionFromCoords = React.useCallback(({ x, y }) => {
    const relativeX = (x - centerX) * worldScale * zoom + viewOffset.x;
    const relativeY = (y - centerY) * worldScale * zoom + viewOffset.y;
    return { x: relativeX + mapAnchor.x, y: relativeY + mapAnchor.y };
  }, [centerX, centerY, worldScale, zoom, viewOffset.x, viewOffset.y, mapAnchor.x, mapAnchor.y]);

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
      const start = getPositionFromCoords(f.start);
      const target = getPositionFromCoords(f.target);

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

      const color = colorByMission(f.mission);
      const title = `Fleet #${f.id} • ${f.mission} • ${f.status}`;
      return { id: f.id, start, target, dot, color, title };
    });
  }, [movingFleets, nowMs, getPositionFromCoords]);

  // Mouse drag handlers for panning
  const handleMouseDown = (e) => {
    if (e.button === 0) { // Left mouse button only
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
      e.preventDefault();
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      const deltaX = e.clientX - dragStart.x;
      const deltaY = e.clientY - dragStart.y;
      setViewOffset(prev => ({
        x: prev.x + deltaX,
        y: prev.y + deltaY
      }));
      setDragStart({ x: e.clientX, y: e.clientY });
      e.preventDefault();
    }
  };

  const handleMouseUp = (e) => {
    if (isDragging) {
      setIsDragging(false);
      e.preventDefault();
    }
  };

  const handleMouseLeave = (e) => {
    if (isDragging) {
      setIsDragging(false);
    }
  };

  // Mouse wheel zoom handler
  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom(prev => Math.max(0.5, Math.min(2, prev + zoomFactor)));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" data-testid="galaxy-modal">
      <div className="bg-gray-800 rounded-lg p-6 max-w-6xl w-full h-5/6 flex flex-col" data-testid="galaxy-modal-content">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-white">Galaxy Map</h2>
          <button
            onClick={onClose}
            data-testid="galaxy-close"
            className="text-gray-400 hover:text-white text-xl"
          >
            ✕
          </button>
        </div>

        {/* Controls */}
        <div className="flex justify-between items-center mb-4">
          <div className="text-sm text-gray-300">
            Center: {viewCenterX}:{viewCenterY}:{centerZ} | Zoom: {Math.round(zoom * 100)}% | Range: {galaxyRange} units
            {refreshing && <span className="ml-2 text-xs text-blue-300">(updating…)</span>}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAllMarkers((v) => !v)}
              className={`px-3 py-1 text-white rounded text-sm ${showAllMarkers ? 'bg-purple-600 hover:bg-purple-500' : 'bg-gray-600 hover:bg-gray-500'}`}
              title={showAllMarkers ? 'Showing all markers in-range' : 'Showing a readability-optimized subset'}
              data-testid="galaxy-toggle-all-markers"
            >
              Markers {showAllMarkers ? 'ALL' : 'SMART'}
            </button>
            <button
              onClick={handleZoomOut}
              className="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded text-sm"
              disabled={zoom <= 0.5}
            >
              −
            </button>
            <button
              onClick={handleZoomIn}
              className="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded text-sm"
              disabled={zoom >= 2}
            >
              +
            </button>
            <button
              onClick={resetView}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm"
            >
              Reset
            </button>
            <button
              onClick={() => setShowGrid(!showGrid)}
              className={`px-3 py-1 text-white rounded text-sm ${
                showGrid ? 'bg-green-600 hover:bg-green-500' : 'bg-gray-600 hover:bg-gray-500'
              }`}
            >
              Grid {showGrid ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && !galaxyLoaded && (
          <div className="flex-1 bg-gray-900 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <div className="text-white text-lg font-semibold">Loading Galaxy Data...</div>
              <div className="text-gray-400 text-sm mt-2">Fetching all planets and systems</div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="flex-1 bg-gray-900 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="text-red-500 text-4xl mb-4">⚠️</div>
              <div className="text-white text-lg font-semibold">Failed to Load Galaxy</div>
              <div className="text-gray-400 text-sm mt-2">{error}</div>
              <button
                onClick={() => fetchNearbySystems()}
                className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Map Container */}
        {(!loading || galaxyLoaded) && !error && (
          <div
            className={`flex-1 bg-gray-900 rounded-lg overflow-hidden relative galaxy-background ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
            ref={mapRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseLeave}
            onWheel={handleWheel}
          >
            <GalaxyMinimap
              galaxyRange={galaxyRange}
              centerZ={centerZ}
              anchorCenter={{ x: centerX, y: centerY }}
              cameraCenter={{ x: viewCenterX, y: viewCenterY }}
              systems={minimapSystems?.length ? minimapSystems : systems}
              renderedKeys={displaySystemKeys}
              onSelectSystem={(s) => setSelectedSystem(s)}
              rangeMultiplier={MINIMAP_RANGE_MULTIPLIER}
            />

            {/* Deep Space Background */}
          <GalaxyBackground starfield={starfield} />
          {/* Grid Background */}
          {showGrid && (
            <div data-test="grid" className="absolute inset-0 opacity-60 pointer-events-none">
              <svg width="100%" height="100%" className="text-gray-300">
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1.5"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
              </svg>
            </div>
          )}

          {/* Coordinate Labels */}
          <div data-test="coords" className="absolute top-2 left-2 text-xs text-white font-mono bg-black bg-opacity-70 px-3 py-2 rounded-lg border border-gray-600 shadow-lg">
            <div className="font-semibold text-blue-300">Coordinates:</div>
            <div className="text-yellow-300">X: {Math.round(centerX - viewOffset.x / (zoom * worldScale))}</div>
            <div className="text-green-300">Y: {Math.round(centerY - viewOffset.y / (zoom * worldScale))}</div>
            <div className="text-purple-300">Z: {centerZ}</div>
          </div>

          <GalaxyFleetOverlay fleetOverlay={fleetOverlay} onNavigateSection={onNavigateSection} />

          {/* Systems Display */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="relative">

              {displaySystems.map((system) => {
                const pos = getSystemPosition(system);

                // Determine system ownership status
                // system.planets is a number (count), not an array
                const hasColonies = system.planets && system.planets > 0;
                const relation = system.relation || (system.owner_id == user.id ? 'self' : (hasColonies ? 'enemy' : 'unowned'));
                const isOwnedByUser = relation === 'self';
                const isAllyColony = relation === 'ally';
                const isPirateColony = relation === 'pirates';
                const isEnemyColony = hasColonies && !isOwnedByUser && !isAllyColony;

                // Enhanced system marker with planet image background
                let borderClass = '';
                let markerIcon = '';
                let textColor = 'text-white';

                // "Explored" should control intel/detail UI, not basic visibility. Keep markers fully visible
                // even when unexplored so the galaxy feels like a real decision surface.
                if (system.explored) {
                  if (isOwnedByUser) {
                    borderClass = 'border-green-400 hover:border-green-300';
                    markerIcon = '🏠';
                  } else if (isPirateColony) {
                    borderClass = 'border-orange-400 hover:border-orange-300';
                    markerIcon = '🏴‍☠️';
                  } else if (isAllyColony) {
                    borderClass = 'border-purple-400 hover:border-purple-300';
                    markerIcon = '🤝';
                  } else if (isEnemyColony) {
                    borderClass = 'border-red-400 hover:border-red-300';
                    markerIcon = '⚔️';
                  } else {
                    borderClass = 'border-blue-400 hover:border-blue-300';
                    markerIcon = '';
                  }
                } else {
                  borderClass = 'border-gray-400 hover:border-gray-300';
                  markerIcon = '';
                  textColor = 'text-gray-300';
                }

                const systemKey = system.key || `${system.x}:${system.y}:${system.z}`;

                return (
                  <div key={systemKey} className="absolute" style={{ left: `${pos.x + mapAnchor.x}px`, top: `${pos.y + mapAnchor.y}px`, transform: 'translate(-50%, -50%)' }}>
                    {/* Coordinates above the planet */}
                    <div className="text-center mb-1 pointer-events-none">
                      <div className={`text-xs font-bold ${textColor} bg-black bg-opacity-70 px-2 py-1 rounded shadow-lg pointer-events-none`}>
                        {system.x - centerX}:{system.y - centerY}
                      </div>
                    </div>

                    {/* Planet marker */}
                    <div
                      data-test-marker="system-marker"
                      className={`system-marker w-16 h-16 rounded-full border-2 cursor-pointer transition-all duration-200 flex items-center justify-center text-xs font-bold ${borderClass}`}
                      style={{
                        zIndex: system.explored ? 10 : 5,
                        backgroundImage: `url(${planetImage})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        backgroundRepeat: 'no-repeat'
                      }}
                      onMouseDown={(e) => e.stopPropagation()}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedSystem(system);
                      }}
                      title={`${system.x}:${system.y}:${system.z} - ${system.explored ? `${system.planets} planets` : 'Unexplored'}${isOwnedByUser ? ' (Your Colony)' : isEnemyColony ? ' (Enemy Colony)' : ''}`}
                    >
                      <div className="text-center">
                        <div className={`text-xs opacity-75 ${textColor}`}>
                          {system.explored ? `${system.planets}P` : '???'}
                        </div>
                        {hasColonies && (
                          <div className={`text-xs font-bold ${textColor}`}>
                            {markerIcon}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Center Marker (Player Location) */}
              <div
                data-test="player-marker"
                className="absolute w-4 h-4 bg-yellow-400 rounded-full border-2 border-yellow-200"
                style={{
                  left: `${mapAnchor.x + viewOffset.x}px`,
                  top: `${mapAnchor.y + viewOffset.y}px`,
                  transform: 'translate(-50%, -50%)',
                  zIndex: 15
                }}
                title="Your home system"
              />
            </div>
          </div>

          {/* Enhanced Legend */}
          <div className="absolute bottom-2 right-2 bg-gray-800 bg-opacity-90 p-3 rounded text-xs text-gray-300 max-w-xs">
            <div className="font-bold text-white mb-2">Legend</div>
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                <span>Home System</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-600 rounded-full"></div>
                <span>Your Colonies</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-purple-600 rounded-full"></div>
                <span>Alliance</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-600 rounded-full"></div>
                <span>Enemy Colonies</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-orange-600 rounded-full"></div>
                <span>Pirate Camps</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
                <span>Explored Systems</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-gray-600 rounded-full"></div>
                <span>Unexplored Systems</span>
              </div>
            </div>
          </div>
          </div>
        )}

        {selectedSystem && (
          <GalaxyIntelPanel
            system={selectedSystem}
            onClose={() => setSelectedSystem(null)}
            onExplore={handleExploreSystem}
            loading={loading}
            userId={user?.id}
            centerX={centerX}
            centerY={centerY}
            centerZ={centerZ}
            onNavigateSection={onNavigateSection}
          />
        )}
      </div>
    </div>
  );
}

export default GalaxyMap;
