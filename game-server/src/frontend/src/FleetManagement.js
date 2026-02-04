import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import axios from 'axios';
import { useToast } from './ToastContext';
import AnimatedButton from './AnimatedButton';
import { backendBaseUrl } from './apiBase';

const FLEET_SHIP_KEYS = [
  'small_cargo',
  'large_cargo',
  'light_fighter',
  'heavy_fighter',
  'cruiser',
  'battleship',
  'colony_ship',
  'recycler',
  'espionage_probe',
  'bomber',
  'destroyer',
  'deathstar',
  'battlecruiser',
];

function computeAvailableShipsForPlanet({ planet, fleets }) {
  const byKey = Object.fromEntries(FLEET_SHIP_KEYS.map((k) => [k, 0]));
  if (!planet) return byKey;

  // Prefer the dedicated inventory fleet on this planet.
  const inventoryFleet =
    (fleets || []).find((f) => f?.status === 'stationed' && f?.mission === 'inventory' && f?.start_planet_id === planet?.id) ||
    (fleets || []).find((f) => f?.status === 'stationed' && f?.mission === 'stationed' && f?.start_planet_id === planet?.id) ||
    (fleets || []).find((f) => f?.status === 'stationed' && f?.start_planet_id === planet?.id) ||
    null;

  const inventoryShips = inventoryFleet?.ships || null;
  const usesFleetInventory = Boolean(inventoryShips);

  FLEET_SHIP_KEYS.forEach((k) => {
    byKey[k] = (inventoryShips?.[k] ?? planet.ships?.[k]) || 0;
  });

  // Only subtract active fleets when we're using planet-level inventory (legacy fallback).
  if (!usesFleetInventory) {
    (fleets || []).forEach((fleet) => {
      if (fleet.status === 'traveling' || fleet.status === 'returning') {
        const ships = fleet.ships || {};
        FLEET_SHIP_KEYS.forEach((k) => {
          byKey[k] = Math.max(0, byKey[k] - (ships[k] || 0));
        });
      }
    });
  }

  return byKey;
}

function FleetManagement({ user, planets = [] }) {
  const [fleets, setFleets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showSendForm, setShowSendForm] = useState(false);
  const [selectedFleet, setSelectedFleet] = useState(null);
  const selectedPlanetStorageKey = useMemo(() => {
    const userId = user?.id ?? 'anon';
    return `planetarion:fleet:selectedPlanetId:${userId}`;
  }, [user?.id]);

  const [selectedPlanetId, setSelectedPlanetId] = useState(() => {
    try {
      // Prefer user-scoped key, fallback to a legacy global key.
      const userId = user?.id ?? 'anon';
      const scopedKey = `planetarion:fleet:selectedPlanetId:${userId}`;
      const raw = localStorage.getItem(scopedKey) || localStorage.getItem('planetarion:fleet:selectedPlanetId');
      if (!raw) return null;
      const parsed = parseInt(raw, 10);
      return Number.isFinite(parsed) ? parsed : null;
    } catch (e) {
      return null;
    }
  });
  const [allPlanets, setAllPlanets] = useState([]);
  const [sendPreset, setSendPreset] = useState(null);
  const [activeSendPreset, setActiveSendPreset] = useState(null);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const sseHealthyRef = useRef(false);
  const { showSuccess, showError } = useToast();

  // Helper function for ETA calculation
  const calculateETA = (arrivalTime) => {
    if (!arrivalTime) return null;
    const now = new Date();
    const arrival = new Date(arrivalTime);
    const diff = arrival - now;
    return Math.max(0, Math.floor(diff / 1000)); // seconds remaining
  };

  // Data normalization functions
  const normalizePlanet = useCallback((planet) => {
    const coordinates = planet.coordinates || `${planet.x}:${planet.y}:${planet.z}`;
    const [x, y, z] = typeof coordinates === 'string' ? coordinates.split(':').map((v) => parseInt(v, 10)) : [planet.x, planet.y, planet.z];

    return {
      ...planet,
      x: Number.isFinite(x) ? x : planet.x,
      y: Number.isFinite(y) ? y : planet.y,
      z: Number.isFinite(z) ? z : planet.z,
      coordinates,
      resources: planet.resources || {
        metal: planet.metal || 0,
        crystal: planet.crystal || 0,
        deuterium: planet.deuterium || 0
      },
      structures: planet.structures || {
        metal_mine: planet.metal_mine || 0,
        crystal_mine: planet.crystal_mine || 0,
        deuterium_synthesizer: planet.deuterium_synthesizer || 0,
        solar_plant: planet.solar_plant || 0,
        fusion_reactor: planet.fusion_reactor || 0
      },
      ships: planet.ships || {
        small_cargo: planet.small_cargo || 0,
        large_cargo: planet.large_cargo || 0,
        light_fighter: planet.light_fighter || 0,
        heavy_fighter: planet.heavy_fighter || 0,
        cruiser: planet.cruiser || 0,
        battleship: planet.battleship || 0,
        colony_ship: planet.colony_ship || 0,
        recycler: planet.recycler || 0
      }
    };
  }, []);

  const normalizeFleet = useCallback((fleet) => ({
    ...fleet,
    ships: fleet.ships || {},
    eta: fleet.eta || calculateETA(fleet.arrival_time) // Single source of truth for ETA
  }), []);

  const fetchTimeline = useCallback(async () => {
    setTimelineLoading(true);
    try {
      const response = await axios.get('/api/tick/logs', { params: { limit: 25, offset: 0 } });
      const logsRaw = Array.isArray(response.data?.logs) ? response.data.logs : [];
      // Defensive: filter out resource-only rows (no event_type/description) that can
      // appear if the backend is running an older build/config.
      const logs = logsRaw.filter((evt) => {
        const hasType = typeof evt?.event_type === 'string' && evt.event_type.trim() !== '';
        const hasDesc = typeof evt?.event_description === 'string' && evt.event_description.trim() !== '';
        return hasType || hasDesc;
      });
      // Merge so the UI doesn't "blink" by removing items between refreshes.
      setTimelineEvents((prev) => {
        const merged = [];
        const seen = new Set();
        [...logs, ...(Array.isArray(prev) ? prev : [])].forEach((evt) => {
          if (!evt || evt.id == null) return;
          if (seen.has(evt.id)) return;
          seen.add(evt.id);
          merged.push(evt);
        });
        return merged.slice(0, 50);
      });
    } catch (error) {
      console.warn('Failed to fetch tick logs:', error);
      // Keep last known timelineEvents to avoid flicker on transient failures.
    } finally {
      setTimelineLoading(false);
    }
  }, []);

  const fetchFleets = useCallback(async () => {
    try {
      // Include the inventory fleet so shipyard-built ships (recyclers/colony ships/etc)
      // show up in availability calculations and quick-send flows.
      const response = await axios.get('/api/fleet', { params: { include_inventory: 1 } });
      console.log('DEBUG: Fleet API Response:', response.data); // API response validation

      if (!Array.isArray(response.data)) {
        throw new Error('Invalid fleet data format from API');
      }

      setFleets(response.data);
    } catch (error) {
      console.error('Error fetching fleets:', error);
      showError('Failed to load fleets. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  // Memoized computations for performance
  const userPlanets = useMemo(() =>
    (planets || [])
      // Dashboard already passes only owned planets from `/api/planet`, which historically didn't include `user_id`.
      // Treat missing `user_id` as owned to avoid filtering everything out.
      .filter((planet) => planet.user_id == null || planet.user_id === user?.id)
      .map(normalizePlanet),
    [planets, user?.id, normalizePlanet]
  );

  const selectedPlanet = useMemo(() => {
    if (selectedPlanetId == null) return null;
    return userPlanets.find((p) => p.id === selectedPlanetId) || null;
  }, [userPlanets, selectedPlanetId]);

  const normalizedFleets = useMemo(() =>
    fleets.map(normalizeFleet),
    [fleets, normalizeFleet]
  );

  useEffect(() => {
    fetchFleets();
  }, [fetchFleets]);

  // Auto-refresh fleets so server-side ticks are reflected without manual clicks.
  useEffect(() => {
    const interval = setInterval(() => {
      fetchFleets();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchFleets]);

  // Event-driven fleet timeline: subscribe to activity SSE and append relevant events.
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return undefined;

    let es;
    try {
      const sseUrl = `${backendBaseUrl}/api/events/stream?token=${encodeURIComponent(token)}`;
      es = new EventSource(sseUrl);
    } catch (e) {
      return undefined;
    }

    const onActivity = (evt) => {
      try {
        const payload = JSON.parse(evt.data || '{}');
        if (!payload || payload.id == null) return;
        const type = (payload.event_type || '').toLowerCase();
        // Only keep “interesting” events in the Fleet timeline.
        const keep =
          type.includes('fleet') ||
          type.includes('combat') ||
          type.includes('recycle') ||
          type.includes('colon') ||
          type.includes('planet_capture') ||
          type.includes('espion');
        if (!keep) return;

        setTimelineEvents((prev) => {
          const merged = [];
          const seen = new Set();
          [payload, ...(Array.isArray(prev) ? prev : [])].forEach((e) => {
            if (!e || e.id == null) return;
            if (seen.has(e.id)) return;
            seen.add(e.id);
            merged.push(e);
          });
          return merged.slice(0, 50);
        });
      } catch (e) {
        // ignore
      }
    };

    es.addEventListener('activity', onActivity);
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
    });

    return () => {
      sseHealthyRef.current = false;
      try {
        es.close();
      } catch (e) {
        // ignore
      }
    };
  }, []);

  // Cross-screen "quick send" support (e.g. from Combat debris list).
  useEffect(() => {
    try {
      const raw = localStorage.getItem('fleetSendPreset');
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object') return;
      // One-shot: clear immediately so it doesn't affect other tests/sessions.
      localStorage.removeItem('fleetSendPreset');
      setSendPreset(parsed);
    } catch (e) {
      console.warn('Failed to parse fleetSendPreset:', e);
      localStorage.removeItem('fleetSendPreset');
    }
  }, []);

  // Also accept in-tab events (storage events don't fire in the same tab).
  useEffect(() => {
    const onPreset = (evt) => {
      const preset = evt?.detail;
      if (!preset || typeof preset !== 'object') return;
      setSendPreset(preset);
    };
    window.addEventListener('planetarion:fleetSendPreset', onPreset);
    return () => window.removeEventListener('planetarion:fleetSendPreset', onPreset);
  }, []);

  useEffect(() => {
    if (!sendPreset) return;
    if (loading) return;

    const openSendForFleet = (fleet) => {
      setSelectedFleet(fleet);
      setActiveSendPreset(sendPreset);
      setShowSendForm(true);
    };

    const findStationedFleet = ({ requireRecyclers, planetId }) =>
      normalizedFleets.find((f) => {
        if (f.status !== 'stationed') return false;
        if (f.mission === 'inventory') return false;
        if (planetId != null && f.start_planet_id !== planetId) return false;
        if (!requireRecyclers) return true;
        return (f?.ships?.recycler || 0) > 0;
      });

    const findInventoryFleetWithRecyclers = ({ planetId }) =>
      normalizedFleets.find((f) => {
        if (f.status !== 'stationed') return false;
        if (f.mission !== 'inventory') return false;
        if (planetId != null && f.start_planet_id !== planetId) return false;
        return (f?.ships?.recycler || 0) > 0;
      });

    const preferredPlanetId = sendPreset?.start_planet_id ?? selectedPlanetId ?? null;

    const run = async () => {
      if (preferredPlanetId != null) {
        try {
          setSelectedPlanetId(preferredPlanetId);
        } catch (e) {
          // ignore
        }
      }

      // Spy presets: if the player built probes into the inventory fleet but hasn't created a probe fleet,
      // auto-create a 1-probe fleet so the one-click UX from Galaxy works.
      if (sendPreset.mission === 'espionage') {
        const eligible =
          normalizedFleets.find((f) => {
            if (f.status !== 'stationed') return false;
            if (f.mission === 'inventory') return false;
            if (preferredPlanetId != null && f.start_planet_id !== preferredPlanetId) return false;
            return (f?.ships?.espionage_probe || 0) > 0;
          }) ||
          normalizedFleets.find((f) => {
            if (f.status !== 'stationed') return false;
            if (f.mission === 'inventory') return false;
            return (f?.ships?.espionage_probe || 0) > 0;
          });

        if (eligible) {
          openSendForFleet(eligible);
          return;
        }

        const inv =
          normalizedFleets.find((f) => {
            if (f.status !== 'stationed') return false;
            if (f.mission !== 'inventory') return false;
            if (preferredPlanetId != null && f.start_planet_id !== preferredPlanetId) return false;
            return (f?.ships?.espionage_probe || 0) > 0;
          }) ||
          normalizedFleets.find((f) => f.status === 'stationed' && f.mission === 'inventory' && (f?.ships?.espionage_probe || 0) > 0);

        if (!inv) {
          showError('No espionage probes available. Build probes first (Shipyard) or create a probe fleet.');
          setSendPreset(null);
          return;
        }

        try {
          const count = Math.max(1, inv?.ships?.espionage_probe || 0);
          const resp = await axios.post('/api/fleet', {
            start_planet_id: inv.start_planet_id,
            ships: { espionage_probe: count }
          });
          const created = resp.data?.fleet;
          if (!created) throw new Error('Missing fleet in response');
          await fetchFleets();
          openSendForFleet(created);
          return;
        } catch (e) {
          console.error('Failed to auto-create probe fleet:', e);
          showError(e.response?.data?.error || 'Failed to create probe fleet automatically.');
          setSendPreset(null);
          return;
        }
      }

      // For recycle presets: if the player only built recyclers but hasn't created a recycler fleet,
      // auto-create a recycler-only fleet from the inventory fleet so the one-click UX works.
      if (sendPreset.mission === 'recycle') {
        const eligible =
          findStationedFleet({ requireRecyclers: true, planetId: preferredPlanetId }) ||
          findStationedFleet({ requireRecyclers: true, planetId: null });

        if (eligible) {
          openSendForFleet(eligible);
          return;
        }

        const inv =
          findInventoryFleetWithRecyclers({ planetId: preferredPlanetId }) ||
          findInventoryFleetWithRecyclers({ planetId: null });

        if (!inv) {
          showError('No recyclers available. Build recyclers first (Shipyard) or create a recycler fleet.');
          setSendPreset(null);
          return;
        }

        try {
          const count = inv?.ships?.recycler || 0;
          const resp = await axios.post('/api/fleet', {
            start_planet_id: inv.start_planet_id,
            ships: { recycler: count }
          });
          const created = resp.data?.fleet;
          if (!created) throw new Error('Missing fleet in response');
          await fetchFleets();
          openSendForFleet(created);
          return;
        } catch (e) {
          console.error('Failed to auto-create recycler fleet:', e);
          showError(e.response?.data?.error || 'Failed to create recycler fleet automatically.');
          setSendPreset(null);
          return;
        }
      }

      // Generic preset: pick any stationed non-inventory fleet.
      const eligible =
        findStationedFleet({ requireRecyclers: false, planetId: preferredPlanetId }) ||
        findStationedFleet({ requireRecyclers: false, planetId: null });

      if (!eligible) {
        showError('No stationed fleet available.');
        setSendPreset(null);
        return;
      }

      openSendForFleet(eligible);
    };

    run();
    // Keep sendPreset for the modal to consume; clear after opening.
  }, [sendPreset, loading, normalizedFleets, selectedPlanetId, showError, fetchFleets]);

  // Fleet send modal needs enemy/unowned planets, which are not included in /api/planet.
  useEffect(() => {
    const fetchAllPlanets = async () => {
      try {
        const response = await axios.get('/api/planets');
        if (Array.isArray(response.data)) {
          setAllPlanets(response.data);
        }
      } catch (error) {
        // Non-fatal: fall back to owned planets only.
        console.warn('Failed to fetch all planets for targeting:', error);
      }
    };
    fetchAllPlanets();
  }, []);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  // Stable planet selection - prevent flicker during async updates
  useEffect(() => {
    if (userPlanets.length === 0) return;

    // If there is no selection (or it no longer exists), pick a deterministic default.
    const stillValid = selectedPlanetId != null && userPlanets.some((p) => p.id === selectedPlanetId);
    if (!stillValid) {
      const homePlanet = userPlanets.find((p) => p.is_home_planet);
      setSelectedPlanetId(homePlanet?.id ?? userPlanets[0].id);
    }
  }, [userPlanets, selectedPlanetId]);

  // Persist selection across remounts / tab toggles.
  useEffect(() => {
    try {
      if (selectedPlanetId == null) return;
      localStorage.setItem(selectedPlanetStorageKey, String(selectedPlanetId));
      // Back-compat key for earlier builds/tests.
      localStorage.setItem('planetarion:fleet:selectedPlanetId', String(selectedPlanetId));
    } catch (e) {
      // ignore
    }
  }, [selectedPlanetId, selectedPlanetStorageKey]);

  // Refresh fleet state when the dashboard triggers a tick.
  useEffect(() => {
    const onTick = () => {
      fetchFleets();
      if (!sseHealthyRef.current) fetchTimeline();
    };
    window.addEventListener('planetarion:tick', onTick);
    return () => window.removeEventListener('planetarion:tick', onTick);
  }, [fetchFleets, fetchTimeline]);

  const planetLookupList = useMemo(() => {
    const byId = new Map();
    [...(planets || []), ...(allPlanets || [])].forEach((planet) => {
      if (!planet || planet.id == null) return;
      if (!byId.has(planet.id)) byId.set(planet.id, planet);
    });
    return Array.from(byId.values());
  }, [planets, allPlanets]);

  const fleetsByPlanet = useMemo(() => {
    return normalizedFleets.reduce((acc, fleet) => {
      const planetId = fleet.start_planet_id;
      if (!acc[planetId]) {
        acc[planetId] = [];
      }
      acc[planetId].push(fleet);
      return acc;
    }, {});
  }, [normalizedFleets]);

  // UI should not treat the inventory fleet as a "real fleet" for management tiles.
  const visibleFleetsByPlanet = useMemo(() => {
    return Object.fromEntries(
      Object.entries(fleetsByPlanet).map(([planetId, list]) => [
        planetId,
        (Array.isArray(list) ? list : []).filter((f) => f?.mission !== 'inventory'),
      ]),
    );
  }, [fleetsByPlanet]);

  const availableShipsByPlanetId = useMemo(() => {
    const map = {};
    (userPlanets || []).forEach((p) => {
      map[p.id] = computeAvailableShipsForPlanet({ planet: p, fleets: fleetsByPlanet[p.id] || [] });
    });
    return map;
  }, [userPlanets, fleetsByPlanet]);

  const hasArrivedPendingTick = useMemo(() => {
    const now = Date.now();
    return normalizedFleets.some((fleet) => {
      if (!fleet?.arrival_time) return false;
      if (fleet.status !== 'traveling' && fleet.status !== 'returning') return false;
      const arrival = new Date(fleet.arrival_time).getTime();
      return Number.isFinite(arrival) && arrival <= now;
    });
  }, [normalizedFleets]);

  const handleCreateFleet = async (fleetData) => {
    try {
      const response = await axios.post('/api/fleet', fleetData);
      setFleets(prev => [...prev, response.data.fleet]);
      setShowCreateForm(false);
      showSuccess('Fleet created successfully!');
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to create fleet');
    }
  };

  const handleSendFleet = useCallback(async (sendData) => {
    // Optimistic update - immediately update UI
    const optimisticFleet = {
      ...selectedFleet,
      status: 'traveling',
      mission: sendData.mission,
      target_planet_id: sendData.target_planet_id || null
    };

    setFleets(prev => prev.map(fleet =>
      fleet.id === sendData.fleet_id ? optimisticFleet : fleet
    ));

    try {
      const response = await axios.post('/api/fleet/send', sendData);
      console.log('DEBUG: Fleet send response:', response.data); // API response validation

      // Server truth update - replace optimistic update with actual server response
      setFleets(prev => prev.map(fleet =>
        fleet.id === sendData.fleet_id
          ? {
              // Preserve fields the send endpoint may not return (e.g. start_planet_id),
              // so traveling fleets don't "disappear" from the per-planet view.
              ...fleet,
              ...response.data.fleet,
              ships: response.data.fleet?.ships || fleet.ships || {}
            }
          : fleet
      ));

      setShowSendForm(false);
      setSelectedFleet(null);
      showSuccess('Fleet sent successfully!');
      fetchTimeline();
    } catch (error) {
      console.error('Fleet send error:', error);

      // Revert optimistic update on error
      setFleets(prev => prev.map(fleet =>
        fleet.id === sendData.fleet_id ? selectedFleet : fleet
      ));

      showError(error.response?.data?.error || 'Failed to send fleet');
    }
  }, [selectedFleet, showError]);

  const handleRecallFleet = async (fleetId) => {
    try {
      const response = await axios.post(`/api/fleet/recall/${fleetId}`);
      setFleets(prev => prev.map(fleet =>
        fleet.id === fleetId
          ? {
              // Preserve routing/grouping fields like start/target planet ids.
              ...fleet,
              ...response.data.fleet,
              ships: response.data.fleet?.ships || fleet.ships || {}
            }
          : fleet
      ));
      showSuccess('Fleet recalled successfully!');
      fetchTimeline();
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to recall fleet');
    }
  };

  const handleDissolveFleet = async (fleetId) => {
    try {
      await axios.post(`/api/fleet/${fleetId}/dissolve`);
      showSuccess('Fleet dissolved (ships returned to inventory).');
      fetchFleets();
      fetchTimeline();
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to dissolve fleet');
    }
  };

  const formatTimeRemaining = (arrivalTime, status) => {
    // Only show a countdown for in-flight missions. Stationary fleets should not display
    // a countdown even if their DB timestamps are stale or were restored from snapshots.
    const isInFlight =
      status === 'traveling' ||
      status === 'returning' ||
      (typeof status === 'string' && (status.startsWith('exploring:') || status.startsWith('colonizing:')));

    if (!arrivalTime || !isInFlight) return '—';

    const now = new Date();
    const arrival = new Date(arrivalTime);
    const diff = arrival - now;

    if (diff <= 0) {
      if (status === 'traveling' || status === 'returning') return 'Arrived (pending tick)';
      return 'Arrived';
    }

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-center text-white">Loading fleets...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6" data-testid="fleet-management">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-white">🚀 Fleet Management</h3>
        <button
          onClick={() => setShowCreateForm(true)}
          data-testid="fleet-create-button"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          Create Fleet
        </button>
      </div>

      {hasArrivedPendingTick && (
        <div className="mb-6 bg-yellow-900/40 border border-yellow-700 text-yellow-200 rounded p-4" data-testid="fleet-pending-tick-banner">
          One or more fleets have arrived but are awaiting tick processing. Use the Dashboard “Run tick” button to process arrivals/combat.
        </div>
      )}

      {/* Planet Selection Header */}
      <div className="mb-6">
        <h4 className="text-white font-medium mb-3">Select Planet:</h4>
        <div className="flex flex-wrap gap-2" data-testid="fleet-planet-selector">
          {userPlanets.map(planet => (
            <button
              key={planet.id}
              onClick={() => setSelectedPlanetId(planet.id)}
              data-testid="fleet-planet-button"
              className={`px-4 py-2 rounded whitespace-nowrap ${
                selectedPlanet?.id === planet.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {planet.is_home_planet ? '🏠' : '🌍'} {planet.name} ({planet.x}:{planet.y}:{planet.z})
            </button>
          ))}
        </div>
      </div>

      {/* Planet Overview Cards */}
      {selectedPlanet && (
        <div className="mb-6">
          <PlanetOverviewCard
            planet={selectedPlanet}
            fleets={visibleFleetsByPlanet[selectedPlanet.id] || []}
            onCreateFleet={() => setShowCreateForm(true)}
          />
        </div>
      )}

      {/* Ship Availability Dashboard */}
      {selectedPlanet && (
        <div className="mb-6">
          <ShipAvailabilityDashboard
            planet={selectedPlanet}
            fleets={fleetsByPlanet[selectedPlanet.id] || []}
          />
        </div>
      )}

      {/* Fleet Management Tiles */}
      {selectedPlanet && (
        <div className="mb-6">
          <h4 className="text-white font-medium mb-3">Fleets at {selectedPlanet.name}:</h4>
          <div className="space-y-4">
            {(visibleFleetsByPlanet[selectedPlanet.id] || []).length === 0 ? (
              <div className="text-center text-gray-400 py-8 bg-gray-700 rounded" data-testid="fleet-empty-state">
                No fleets at this planet. Create your first fleet!
              </div>
            ) : (
              (visibleFleetsByPlanet[selectedPlanet.id] || []).map(fleet => (
                <FleetTile
                  key={fleet.id}
                  fleet={fleet}
                  planets={planetLookupList}
                  onSend={(fleet) => {
                    setSelectedFleet(fleet);
                    setActiveSendPreset(null);
                    setShowSendForm(true);
                  }}
                  onRecall={handleRecallFleet}
                  onDissolve={handleDissolveFleet}
                  formatTimeRemaining={formatTimeRemaining}
                />
              ))
            )}
          </div>
        </div>
      )}

      {/* Fleet Timeline */}
      <div className="mb-6" data-testid="fleet-timeline">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <h4 className="text-white font-medium">Recent Fleet Events</h4>
            {timelineLoading && <span className="text-xs text-gray-300">Updating…</span>}
          </div>
          <button
            onClick={fetchTimeline}
            className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm"
            data-testid="fleet-timeline-refresh"
          >
            Refresh
          </button>
        </div>
        <div className="bg-gray-700 rounded p-4">
          {timelineEvents.length === 0 ? (
            <div className="text-gray-400">No recent events yet.</div>
          ) : (
            <div className={`space-y-2 ${timelineLoading ? 'opacity-80' : ''}`}>
              {timelineEvents.slice(0, 10).map((evt) => {
                const type = evt.event_type || 'event';
                const icon =
                  type === 'combat' ? '⚔️' :
                  type === 'planet_capture' ? '🏴‍☠️' :
                  type === 'planet_rename' ? '✏️' :
                  type === 'colonization' ? '🌍' :
                  type === 'recycle' ? '♻️' :
                  type === 'fleet_sent' ? '🚀' :
                  type === 'fleet_recalled' ? '↩️' :
                  type === 'fleet_returned' ? '✅' :
                  '📝';

                const planetLabel = evt.planet?.name
                  ? `${evt.planet.name}${evt.planet.coordinates ? ` (${evt.planet.coordinates})` : ''}`
                  : null;
                const when = evt.timestamp ? new Date(evt.timestamp).toLocaleString() : '';

                return (
                  <div key={evt.id} className="flex items-start gap-3 text-sm" data-testid="fleet-timeline-event">
                    <div className="text-lg leading-none">{icon}</div>
                    <div className="flex-1">
                      <div className="text-white">{evt.event_description || type}</div>
                      <div className="text-gray-400">
                        {planetLabel ? `${planetLabel} • ` : ''}{when}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Fallback: Show all fleets if no planet selected */}
      {!selectedPlanet && (
        <div className="text-center text-gray-400 py-8">
          Select a planet above to view and manage your fleets
        </div>
      )}

      {/* Create Fleet Modal */}
      {showCreateForm && (
        <CreateFleetModal
          planets={userPlanets}
          selectedPlanet={selectedPlanet}
          availableShipsByPlanetId={availableShipsByPlanetId}
          onCreate={handleCreateFleet}
          onClose={() => setShowCreateForm(false)}
        />
      )}

      {/* Send Fleet Modal */}
      {showSendForm && selectedFleet && (
        <SendFleetModal
          fleet={selectedFleet}
          planets={allPlanets.length > 0 ? allPlanets : planets}
          user={user}
          preset={activeSendPreset}
          onSend={handleSendFleet}
          onClose={() => {
            setShowSendForm(false);
            setSelectedFleet(null);
            setSendPreset(null);
            setActiveSendPreset(null);
            localStorage.removeItem('fleetSendPreset');
          }}
        />
      )}
    </div>
  );
}

  function CreateFleetModal({ planets, selectedPlanet, availableShipsByPlanetId, onCreate, onClose }) {
  const { showError } = useToast();
  const [formData, setFormData] = useState({
    start_planet_id: selectedPlanet?.id ? String(selectedPlanet.id) : '',
    ships: Object.fromEntries(FLEET_SHIP_KEYS.map((k) => [k, 0]))
  });

  const handleShipChange = (shipType, value) => {
    setFormData(prev => ({
      ...prev,
      ships: {
        ...prev.ships,
        [shipType]: parseInt(value) || 0
      }
    }));
  };

  const setShipToMax = (shipType) => {
    if (!available) {
      showError('Select a starting planet first');
      return;
    }
    setFormData((prev) => ({
      ...prev,
      ships: {
        ...prev.ships,
        [shipType]: available[shipType] || 0,
      },
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const totalShips = Object.values(formData.ships).reduce((sum, count) => sum + count, 0);
    if (totalShips === 0) {
      showError('Fleet must contain at least one ship');
      return;
    }
    onCreate(formData);
  };

  const selectedPlanetId = formData.start_planet_id ? parseInt(formData.start_planet_id, 10) : null;
  const available = (selectedPlanetId && availableShipsByPlanetId?.[selectedPlanetId]) ? availableShipsByPlanetId[selectedPlanetId] : null;

  const fillAllShips = () => {
    if (!available) {
      showError('Select a starting planet first');
      return;
    }
    setFormData((prev) => ({
      ...prev,
      ships: Object.fromEntries(FLEET_SHIP_KEYS.map((k) => [k, available[k] || 0])),
    }));
  };

  const clearShips = () => {
    setFormData((prev) => ({
      ...prev,
      ships: Object.fromEntries(FLEET_SHIP_KEYS.map((k) => [k, 0])),
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" data-testid="fleet-create-modal">
      <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md">
        <h3 className="text-xl font-bold text-white mb-4">Create New Fleet</h3>

        <form onSubmit={handleSubmit} data-testid="fleet-create-form">
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">Starting Planet</label>
            <select
              value={formData.start_planet_id}
              onChange={(e) => setFormData(prev => ({ ...prev, start_planet_id: e.target.value }))}
              data-testid="fleet-start-planet-select"
              className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              required
            >
              <option value="">Select a planet</option>
              {planets.map(planet => (
                <option key={planet.id} value={planet.id}>
                  {planet.name} ({planet.coordinates})
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-gray-300">Ships</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={fillAllShips}
                  className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm"
                  data-testid="fleet-create-fill-all"
                >
                  Add all
                </button>
                <button
                  type="button"
                  onClick={clearShips}
                  className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm"
                  data-testid="fleet-create-clear"
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {FLEET_SHIP_KEYS.map((shipType) => (
                <div key={shipType}>
                  <div className="flex items-center justify-between mb-1 gap-2">
                    <label className="block text-xs text-gray-400">
                      {shipType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      {available ? ` (max ${available[shipType] || 0})` : ''}
                    </label>
                    <button
                      type="button"
                      className="text-xs px-2 py-0.5 rounded bg-gray-700 hover:bg-gray-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={!available}
                      onClick={() => setShipToMax(shipType)}
                      data-testid={`fleet-ship-max-${shipType}`}
                      title="Set to max available"
                    >
                      max
                    </button>
                  </div>
                  <input
                    type="number"
                    min="0"
                    value={formData.ships[shipType] || 0}
                    onChange={(e) => handleShipChange(shipType, e.target.value)}
                    data-testid={`fleet-ship-${shipType}`}
                    className="w-full p-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              type="submit"
              data-testid="fleet-create-submit"
              className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none"
            >
              Create Fleet
            </button>
            <button
              type="button"
              onClick={onClose}
              data-testid="fleet-create-cancel"
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SendFleetModal({ fleet, planets, user, preset, onSend, onClose }) {
  const [formData, setFormData] = useState(() => ({
    fleet_id: fleet.id,
    target_planet_id: preset?.target_planet_id ? String(preset.target_planet_id) : '',
    target_x: preset?.target_x != null ? String(preset.target_x) : '',
    target_y: preset?.target_y != null ? String(preset.target_y) : '',
    target_z: preset?.target_z != null ? String(preset.target_z) : '',
    mission: preset?.mission || 'attack',
    recycle_focus: preset?.recycle_focus || 'proportional',
  }));
  const [debrisTargets, setDebrisTargets] = useState([]);
  const [debrisLoading, setDebrisLoading] = useState(false);

  // Get current user ID from user prop
  const getCurrentUserId = () => {
    return user?.id || 1; // Fallback to 1 if user not available
  };

  useEffect(() => {
    // If the selected fleet changes while the modal is open, keep fleet_id in sync.
    setFormData((prev) => ({ ...prev, fleet_id: fleet.id }));
  }, [fleet.id]);

  useEffect(() => {
    if (!preset) return;
    setFormData((prev) => ({
      ...prev,
      mission: preset.mission || prev.mission,
      target_planet_id: preset.target_planet_id ? String(preset.target_planet_id) : prev.target_planet_id,
      target_x: preset.target_x != null ? String(preset.target_x) : prev.target_x,
      target_y: preset.target_y != null ? String(preset.target_y) : prev.target_y,
      target_z: preset.target_z != null ? String(preset.target_z) : prev.target_z,
      recycle_focus: preset.recycle_focus || prev.recycle_focus,
    }));
  }, [preset]);

  // Filter planets based on mission type
  const getFilteredPlanets = () => {
    const userId = getCurrentUserId();

    switch (formData.mission) {
      case 'attack':
        // Show only enemy planets (owned by other users)
        return planets.filter(planet =>
          planet.id !== fleet.start_planet_id &&
          planet.user_id !== null &&
          planet.user_id !== userId
        );

      case 'colonize':
        // Show only unowned planets
        return planets.filter(planet =>
          planet.id !== fleet.start_planet_id &&
          planet.user_id === null
        );

      case 'recycle': {
        const debrisPlanetIds = new Set(debrisTargets.map((d) => d?.planet?.id).filter(Boolean));
        return planets.filter((planet) => debrisPlanetIds.has(planet.id));
      }

      case 'transport':
      case 'deploy':
        // Show only own planets
        return planets.filter(planet =>
          planet.id !== fleet.start_planet_id &&
          planet.user_id === userId
        );

      case 'espionage':
        // Spy only enemy planets
        return planets.filter(planet =>
          planet.id !== fleet.start_planet_id &&
          planet.user_id !== null &&
          planet.user_id !== userId
        );

      default:
        // Default: show all planets except start planet
        return planets.filter(planet => planet.id !== fleet.start_planet_id);
    }
  };

  useEffect(() => {
    const loadDebrisTargets = async () => {
      if (formData.mission !== 'recycle') return;
      setDebrisLoading(true);
      try {
        const res = await axios.get('/api/combat/debris');
        const fields = Array.isArray(res.data?.debris_fields) ? res.data.debris_fields : [];
        setDebrisTargets(fields);
      } catch (e) {
        console.warn('Failed to load debris targets:', e);
        setDebrisTargets([]);
      } finally {
        setDebrisLoading(false);
      }
    };
    loadDebrisTargets();
  }, [formData.mission]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSend(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" data-testid="fleet-send-modal">
      <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md">
        <h3 className="text-xl font-bold text-white mb-4">Send Fleet</h3>

        <form onSubmit={handleSubmit} data-testid="fleet-send-form">
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">Target Planet</label>
            <select
              value={formData.target_planet_id}
              onChange={(e) => setFormData(prev => ({ ...prev, target_planet_id: e.target.value }))}
              data-testid="fleet-target-planet-select"
              className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              required
            >
              <option value="">Select target planet</option>
              {getFilteredPlanets().map(planet => (
                <option key={planet.id} value={planet.id}>
                  {planet.name} ({planet.coordinates})
                  {planet.user_id === getCurrentUserId() ? ' 🏠' :
                   planet.user_id === null ? ' 🌌' : ' ⚔️'}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">
              {formData.mission === 'attack' && 'Shows enemy planets only'}
              {formData.mission === 'colonize' && 'Shows unowned planets only'}
              {formData.mission === 'recycle' && (debrisLoading ? 'Loading debris targets…' : 'Shows planets with debris fields only')}
              {formData.mission === 'transport' && 'Shows your planets only'}
              {formData.mission === 'deploy' && 'Shows your planets only'}
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-gray-300 mb-2">Mission</label>
            <select
              value={formData.mission}
              onChange={(e) => setFormData(prev => ({ ...prev, mission: e.target.value }))}
              data-testid="fleet-mission-select"
              className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            >
              <option value="attack">Attack</option>
              <option value="transport">Transport</option>
              <option value="deploy">Deploy</option>
              <option value="espionage">Espionage</option>
              <option value="recycle">Recycle</option>
              <option value="colonize">Colonize</option>
            </select>
          </div>

          {formData.mission === 'recycle' && (
            <div className="mb-4">
              <label className="block text-gray-300 mb-2">Recycling focus</label>
              <select
                value={formData.recycle_focus || 'proportional'}
                onChange={(e) => setFormData((prev) => ({ ...prev, recycle_focus: e.target.value }))}
                data-testid="fleet-recycle-focus"
                className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="proportional">Proportional (recommended)</option>
                <option value="metal">Metal only</option>
                <option value="crystal">Crystal only</option>
                <option value="deuterium">Deuterium only</option>
              </select>
              <p className="text-xs text-gray-400 mt-1">
                Proportional splits recycler capacity across available debris. “Only” focuses all capacity into one resource.
              </p>
            </div>
          )}

          {/* Coordinates for colonization */}
          {formData.mission === 'colonize' && (
            <div className="mb-4">
              <label className="block text-gray-300 mb-2">Target Coordinates</label>
              <div className="grid grid-cols-3 gap-2">
                <input
                  type="number"
                  placeholder="X"
                  value={formData.target_x}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_x: e.target.value }))}
                  data-testid="fleet-target-x"
                  className="p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  required
                />
                <input
                  type="number"
                  placeholder="Y"
                  value={formData.target_y}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_y: e.target.value }))}
                  data-testid="fleet-target-y"
                  className="p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  required
                />
                <input
                  type="number"
                  placeholder="Z"
                  value={formData.target_z}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_z: e.target.value }))}
                  data-testid="fleet-target-z"
                  className="p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <p className="text-xs text-gray-400 mt-1">Enter coordinates for colonization (must be empty)</p>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              type="submit"
              data-testid="fleet-send-submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none"
            >
              Send Fleet
            </button>
            <button
              type="button"
              onClick={onClose}
              data-testid="fleet-send-cancel"
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function PlanetOverviewCard({ planet, fleets, onCreateFleet }) {
  const totalShips = fleets.reduce((total, fleet) => {
    const ships = fleet.ships || {};
    return total + (ships.small_cargo || 0) + (ships.large_cargo || 0) +
           (ships.light_fighter || 0) + (ships.heavy_fighter || 0) +
           (ships.cruiser || 0) + (ships.battleship || 0) +
           (ships.colony_ship || 0) + (ships.recycler || 0);
  }, 0);

  const activeFleets = fleets.filter(fleet =>
    fleet.status === 'traveling' || fleet.status === 'returning'
  ).length;

  const stationedFleets = fleets.filter(fleet =>
    fleet.status === 'stationed'
  ).length;

  return (
    <div className="bg-gray-700 p-4 rounded">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-white font-medium text-lg">
            {planet.is_home_planet ? '🏠' : '🌍'} {planet.name}
          </h4>
          <p className="text-gray-400 text-sm">
            Coordinates: {planet.x}:{planet.y}:{planet.z}
          </p>
        </div>
        <button
          onClick={onCreateFleet}
          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
        >
          + Create Fleet
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-400">{planet.resources?.metal || 0}</div>
          <div className="text-xs text-gray-400">Metal</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-400">{planet.resources?.crystal || 0}</div>
          <div className="text-xs text-gray-400">Crystal</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-400">{planet.resources?.deuterium || 0}</div>
          <div className="text-xs text-gray-400">Deuterium</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-400">{totalShips}</div>
          <div className="text-xs text-gray-400">Total Ships</div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-600">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Active Fleets:</span>
          <span className="text-orange-400">{activeFleets}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Stationed Fleets:</span>
          <span className="text-green-400">{stationedFleets}</span>
        </div>
      </div>
    </div>
  );
}

function ShipAvailabilityDashboard({ planet, fleets }) {
  // Calculate available ships (not in active fleets) - prevent negative values
  const availableShips = useMemo(() => {
    // Prefer the "inventory" stationed fleet if present (shipyard builds into it and /api/fleet splits from it).
    const inventoryFleet =
      (fleets || []).find((f) => f?.status === 'stationed' && f?.mission === 'inventory' && f?.start_planet_id === planet?.id) ||
      // Backwards-compat for older DB snapshots.
      (fleets || []).find((f) => f?.status === 'stationed' && f?.mission === 'stationed' && f?.start_planet_id === planet?.id) ||
      (fleets || []).find((f) => f?.status === 'stationed' && f?.start_planet_id === planet?.id) ||
      null;
    const inventoryShips = inventoryFleet?.ships || null;
    const usesFleetInventory = Boolean(inventoryShips);

    const available = {
      small_cargo: (inventoryShips?.small_cargo ?? planet.ships?.small_cargo) || 0,
      large_cargo: (inventoryShips?.large_cargo ?? planet.ships?.large_cargo) || 0,
      light_fighter: (inventoryShips?.light_fighter ?? planet.ships?.light_fighter) || 0,
      heavy_fighter: (inventoryShips?.heavy_fighter ?? planet.ships?.heavy_fighter) || 0,
      cruiser: (inventoryShips?.cruiser ?? planet.ships?.cruiser) || 0,
      battleship: (inventoryShips?.battleship ?? planet.ships?.battleship) || 0,
      colony_ship: (inventoryShips?.colony_ship ?? planet.ships?.colony_ship) || 0,
      recycler: (inventoryShips?.recycler ?? planet.ships?.recycler) || 0
    };

    // Only subtract active fleets when we're using planet-level inventory, not the stationed inventory fleet.
    if (!usesFleetInventory) {
      (fleets || []).forEach(fleet => {
        if (fleet.status === 'traveling' || fleet.status === 'returning') {
          const ships = fleet.ships || {};
          Object.keys(available).forEach(shipType => {
            available[shipType] = Math.max(0, available[shipType] - (ships[shipType] || 0));
          });
        }
      });
    }

    return available;
  }, [planet, fleets]);

  const shipTypes = [
    { key: 'small_cargo', name: 'Small Cargo', icon: '📦' },
    { key: 'large_cargo', name: 'Large Cargo', icon: '🚛' },
    { key: 'light_fighter', name: 'Light Fighter', icon: '🚀' },
    { key: 'heavy_fighter', name: 'Heavy Fighter', icon: '✈️' },
    { key: 'cruiser', name: 'Cruiser', icon: '🛳️' },
    { key: 'battleship', name: 'Battleship', icon: '🚢' },
    { key: 'colony_ship', name: 'Colony Ship', icon: '🏘️' },
    { key: 'recycler', name: 'Recycler', icon: '♻️' }
  ];

  return (
    <div className="bg-gray-700 p-4 rounded">
      <h4 className="text-white font-medium mb-4">Available Ships at {planet.name}</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {shipTypes.map(shipType => (
          <div key={shipType.key} className="bg-gray-600 p-3 rounded text-center">
            <div className="text-2xl mb-1">{shipType.icon}</div>
            <div className="text-white font-medium text-sm">{shipType.name}</div>
            <div className={`text-lg font-bold ${
              availableShips[shipType.key] > 0 ? 'text-green-400' : 'text-gray-500'
            }`}>
              {availableShips[shipType.key]}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FleetTile({ fleet, planets, onSend, onRecall, onDissolve, formatTimeRemaining }) {
  const startPlanet = fleet.start_planet || planets.find(p => p.id === fleet.start_planet_id) || null;
  const rawTargetPlanet = fleet.target_planet || planets.find(p => p.id === fleet.target_planet_id) || null;
  const displayTargetPlanet = (fleet.status === 'returning' || fleet.mission === 'return') ? startPlanet : rawTargetPlanet;

  return (
    <div className="bg-gray-700 p-4 rounded" data-testid="fleet-tile">
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="text-white font-medium">
            Fleet #{fleet.id} - {fleet.mission}
          </div>
          <div className="text-sm text-gray-400">
            Status: <span className={`font-medium ${
              fleet.status === 'stationed' ? 'text-green-400' :
              fleet.status === 'traveling' ? 'text-yellow-400' :
              fleet.status === 'returning' ? 'text-blue-400' : 'text-gray-400'
            }`} data-testid="fleet-status-value">
              {fleet.status}
            </span>
          </div>
        </div>
        <div className="flex space-x-2">
          {fleet.status === 'stationed' && fleet.mission !== 'inventory' && (
            <button
              onClick={() => onSend(fleet)}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
            >
              Send
            </button>
          )}
          {fleet.status === 'stationed' && fleet.mission !== 'inventory' && (
            <button
              onClick={() => onDissolve(fleet.id)}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
              data-testid="fleet-dissolve-button"
            >
              Dissolve
            </button>
          )}
          {(fleet.status === 'traveling' || fleet.status === 'returning') && (
            <button
              onClick={() => onRecall(fleet.id)}
              className="bg-orange-600 hover:bg-orange-700 text-white px-3 py-1 rounded text-sm"
            >
              Recall
            </button>
          )}
        </div>
      </div>

      {/* Fleet Details */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-3">
        <div>
          <div className="text-gray-400">Ships</div>
          <div className="text-white">
            {(() => {
              const ships = fleet.ships || {};
              const totalShips = (ships.small_cargo || 0) +
                                (ships.large_cargo || 0) +
                                (ships.light_fighter || 0) +
                                (ships.heavy_fighter || 0) +
                                (ships.cruiser || 0) +
                                (ships.battleship || 0) +
                                (ships.colony_ship || 0) +
                                (ships.recycler || 0);
              return totalShips + ' total';
            })()}
          </div>
        </div>
        <div>
          <div className="text-gray-400">From</div>
          <div className="text-white" data-testid="fleet-from-value">{startPlanet?.name || 'Unknown'}</div>
        </div>
        <div>
          <div className="text-gray-400">To</div>
          <div className="text-white" data-testid="fleet-to-value">{displayTargetPlanet?.name || 'N/A'}</div>
        </div>
        <div>
          <div className="text-gray-400">ETA</div>
          <div className="text-white" data-testid="fleet-eta-value">{formatTimeRemaining(fleet.arrival_time, fleet.status)}</div>
        </div>
      </div>

      {/* Ship Breakdown */}
      <div className="pt-3 border-t border-gray-600">
        <div className="text-xs text-gray-400 mb-2">Ship Composition:</div>
        <div className="flex flex-wrap gap-2 text-xs">
          {(() => {
            const ships = fleet.ships || {};
            return Object.entries(ships).map(([shipType, count]) => (
              count > 0 && (
                <span key={shipType} className="bg-gray-600 px-2 py-1 rounded">
                  {shipType.replace('_', ' ')}: {count}
                </span>
              )
            ));
          })()}
        </div>
      </div>
    </div>
  );
}

export default FleetManagement;
