import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import axios from 'axios';
import { useToast } from './ToastContext';
import AnimatedButton from './AnimatedButton';
import { backendBaseUrl } from './apiBase';
import { deriveFleetDisplayState } from './fleetStateView';

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

function formatShipLabel(shipType) {
  return String(shipType || '')
    .split('_')
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(' ');
}

function summarizeFleetShips(ships) {
  const entries = FLEET_SHIP_KEYS.map((k) => [k, Number(ships?.[k] || 0)]).filter(([, v]) => v > 0);
  const total = entries.reduce((sum, [, v]) => sum + v, 0);
  const top = entries
    .slice()
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([k, v]) => `${formatShipLabel(k)} ${v}`)
    .join(', ');
  return { total, top, entries };
}

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
  const [showSplitForm, setShowSplitForm] = useState(false);
  const [showTransferForm, setShowTransferForm] = useState(false);
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
  const [fleetTemplates, setFleetTemplates] = useState([]);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const sseHealthyRef = useRef(false);
  const lastAutoTickAtRef = useRef(0);
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
  const templateStorageKey = useMemo(() => {
    const userId = user?.id ?? 'anon';
    const planetId = selectedPlanetId ?? 'none';
    return `planetarion:fleet:templates:v1:${userId}:${planetId}`;
  }, [user?.id, selectedPlanetId]);

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

    const findStationedFleetWithColonyShip = ({ planetId }) =>
      normalizedFleets.find((f) => {
        if (f.status !== 'stationed') return false;
        if (f.mission === 'inventory') return false;
        if (planetId != null && f.start_planet_id !== planetId) return false;
        return (f?.ships?.colony_ship || 0) > 0;
      });

    const findInventoryFleetWithRecyclers = ({ planetId }) =>
      normalizedFleets.find((f) => {
        if (f.status !== 'stationed') return false;
        if (f.mission !== 'inventory') return false;
        if (planetId != null && f.start_planet_id !== planetId) return false;
        return (f?.ships?.recycler || 0) > 0;
      });

    const findInventoryFleetWithColonyShip = ({ planetId }) =>
      normalizedFleets.find((f) => {
        if (f.status !== 'stationed') return false;
        if (f.mission !== 'inventory') return false;
        if (planetId != null && f.start_planet_id !== planetId) return false;
        return (f?.ships?.colony_ship || 0) > 0;
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

      // Colonize presets: ensure we use (or create) a fleet with colony ships.
      if (sendPreset.mission === 'colonize') {
        const eligible =
          findStationedFleetWithColonyShip({ planetId: preferredPlanetId }) ||
          findStationedFleetWithColonyShip({ planetId: null });

        if (eligible) {
          openSendForFleet(eligible);
          return;
        }

        const inv =
          findInventoryFleetWithColonyShip({ planetId: preferredPlanetId }) ||
          findInventoryFleetWithColonyShip({ planetId: null });

        if (!inv) {
          showError('No colony ships available. Build colony ships first (Shipyard) or create a colony fleet.');
          setSendPreset(null);
          return;
        }

        try {
          const resp = await axios.post('/api/fleet', {
            start_planet_id: inv.start_planet_id,
            ships: { colony_ship: 1 }
          });
          const created = resp.data?.fleet;
          if (!created) throw new Error('Missing fleet in response');
          await fetchFleets();
          openSendForFleet(created);
          return;
        } catch (e) {
          console.error('Failed to auto-create colony fleet:', e);
          showError(e.response?.data?.error || 'Failed to create colony fleet automatically.');
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

  useEffect(() => {
    try {
      const raw = localStorage.getItem(templateStorageKey);
      if (!raw) {
        setFleetTemplates([]);
        return;
      }
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        setFleetTemplates([]);
        return;
      }
      setFleetTemplates(parsed.filter((t) => t && typeof t === 'object' && t.id && t.name && t.preset));
    } catch (e) {
      setFleetTemplates([]);
    }
  }, [templateStorageKey]);

  useEffect(() => {
    try {
      localStorage.setItem(templateStorageKey, JSON.stringify(fleetTemplates));
    } catch (e) {
      // ignore
    }
  }, [fleetTemplates, templateStorageKey]);

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
    return normalizedFleets.some((fleet) => {
      return (
        deriveFleetDisplayState({
          status: fleet?.status,
          arrivalTime: fleet?.arrival_time,
        }) === 'arrived_pending_processing'
      );
    });
  }, [normalizedFleets]);

  // Dev-only helper: in manual testing environments where the server scheduler is disabled,
  // allow the UI to trigger a tick when we detect "Arrived (pending tick)" fleets.
  // This is intentionally gated by an env var to avoid affecting E2E determinism.
  useEffect(() => {
    const enabled = process.env.REACT_APP_DEV_AUTO_TICK_ON_PENDING === 'true';
    if (!enabled) return;
    if (!hasArrivedPendingTick) return;

    const now = Date.now();
    if (now - (lastAutoTickAtRef.current || 0) < 2000) return;
    lastAutoTickAtRef.current = now;

    let cancelled = false;
    (async () => {
      try {
        await axios.post('/api/tick');
        if (cancelled) return;
        try {
          window.dispatchEvent(new CustomEvent('planetarion:tick'));
        } catch (e) {
          // ignore
        }
      } catch (e) {
        // Non-fatal. If the endpoint is disabled in prod, we simply won't auto-resolve.
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [hasArrivedPendingTick]);

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

  const handleSplitFleet = async ({ fleetId, ships }) => {
    try {
      await axios.post(`/api/fleet/${fleetId}/split`, { ships });
      showSuccess('Fleet split successfully.');
      setShowSplitForm(false);
      setSelectedFleet(null);
      fetchFleets();
      fetchTimeline();
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to split fleet');
    }
  };

  const handleTransferFleet = async ({ sourceFleetId, targetFleetId, ships }) => {
    try {
      await axios.post(`/api/fleet/${sourceFleetId}/transfer`, {
        target_fleet_id: targetFleetId,
        ships,
      });
      showSuccess('Fleet transfer completed.');
      setShowTransferForm(false);
      setSelectedFleet(null);
      fetchFleets();
      fetchTimeline();
    } catch (error) {
      showError(error.response?.data?.error || 'Failed to transfer ships');
    }
  };

  const saveTemplate = useCallback((preset) => {
    if (!preset || typeof preset !== 'object') return;
    const defaultName = `${String(preset.mission || 'mission').replace(/_/g, ' ')} template`;
    const input = window.prompt('Template name', defaultName);
    const name = String(input || '').trim();
    if (!name) return;
    const next = {
      id: `${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      name,
      preset: { ...preset, start_planet_id: selectedPlanetId ?? preset.start_planet_id ?? null },
      created_at: new Date().toISOString(),
    };
    setFleetTemplates((prev) => [next, ...(Array.isArray(prev) ? prev : [])].slice(0, 20));
    showSuccess(`Saved template: ${name}`);
  }, [selectedPlanetId, showSuccess]);

  const applyTemplate = useCallback((template) => {
    if (!template?.preset) return;
    setSendPreset({ ...template.preset, start_planet_id: selectedPlanetId ?? template.preset.start_planet_id ?? null });
  }, [selectedPlanetId]);

  const deleteTemplate = useCallback((templateId) => {
    setFleetTemplates((prev) => (Array.isArray(prev) ? prev.filter((t) => t.id !== templateId) : []));
  }, []);

  const renameTemplate = useCallback((templateId) => {
    setFleetTemplates((prev) => {
      const list = Array.isArray(prev) ? prev : [];
      const target = list.find((t) => t.id === templateId);
      if (!target) return list;
      const input = window.prompt('Rename template', target.name);
      const nextName = String(input || '').trim();
      if (!nextName) return list;
      return list.map((t) => (t.id === templateId ? { ...t, name: nextName } : t));
    });
  }, []);

  const formatTimeRemaining = (arrivalTime, status) => {
    const displayState = deriveFleetDisplayState({ status, arrivalTime });
    if (displayState === 'resolved') return '—';
    if (!arrivalTime) return '—';

    const now = new Date();
    const arrival = new Date(arrivalTime);
    const diff = arrival - now;

    if (diff <= 0) {
      if (displayState === 'arrived_pending_processing') return 'Arrived (pending tick)';
      return 'Arrived';
    }

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="pa-card p-6">
        <div className="text-center text-white">Loading fleets…</div>
      </div>
    );
  }

  return (
    <div className="pa-card p-6" data-testid="fleet-management">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-white">🚀 Fleet Management</h3>
        <button
          onClick={() => setShowCreateForm(true)}
          data-testid="fleet-create-button"
          className="pa-btn-primary px-4 py-2"
        >
          Create Fleet
        </button>
      </div>

      {hasArrivedPendingTick && (
        <div className="mb-6 bg-yellow-900/40 border border-yellow-700 text-yellow-200 rounded p-4" data-testid="fleet-pending-tick-banner">
          One or more fleets have arrived and are awaiting server processing. Auto-ticks should resolve this shortly.
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
              className={`px-4 py-2 whitespace-nowrap ${
                selectedPlanet?.id === planet.id
                  ? 'pa-btn-primary'
                  : 'pa-btn-secondary'
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

      {selectedPlanet && (
        <div className="mb-6 pa-panel p-4" data-testid="fleet-templates-panel">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-white font-medium">Mission Templates</h4>
            <span className="text-xs text-slate-300/70">Planet-local presets</span>
          </div>
          {fleetTemplates.length === 0 ? (
            <div className="text-sm text-slate-300/70">No templates yet. Open Send Fleet and click “Save as template”.</div>
          ) : (
            <div className="space-y-2">
              {fleetTemplates.map((t) => (
                <div key={t.id} className="flex items-center justify-between gap-3 p-2 rounded border border-slate-500/25">
                  <div className="min-w-0">
                    <div className="text-sm text-white truncate">{t.name}</div>
                    <div className="text-xs text-slate-300/70">
                      {String(t?.preset?.mission || 'mission')}
                      {t?.preset?.target_planet_id ? ` • planet #${t.preset.target_planet_id}` : ''}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="pa-btn-primary px-2 py-1 text-xs"
                      onClick={() => applyTemplate(t)}
                      data-testid="fleet-template-apply"
                    >
                      Apply
                    </button>
                    <button
                      type="button"
                      className="pa-btn-secondary px-2 py-1 text-xs"
                      onClick={() => renameTemplate(t.id)}
                      data-testid="fleet-template-rename"
                    >
                      Rename
                    </button>
                    <button
                      type="button"
                      className="pa-btn-secondary px-2 py-1 text-xs"
                      onClick={() => deleteTemplate(t.id)}
                      data-testid="fleet-template-delete"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
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
              <div className="text-center text-slate-300/70 py-8 pa-panel" data-testid="fleet-empty-state">
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
                  onSplit={(fleet) => {
                    setSelectedFleet(fleet);
                    setShowSplitForm(true);
                  }}
                  onTransfer={(fleet) => {
                    const transferTargets = normalizedFleets.filter((f) =>
                      f?.id !== fleet.id &&
                      f?.status === 'stationed' &&
                      f?.start_planet_id === fleet.start_planet_id
                    );
                    if (transferTargets.length === 0) {
                      showError('No other stationed fleet available on this planet for transfer.');
                      return;
                    }
                    setSelectedFleet(fleet);
                    setShowTransferForm(true);
                  }}
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
            {timelineLoading && <span className="text-xs text-slate-200/80">Updating…</span>}
          </div>
          <button
            onClick={fetchTimeline}
            className="pa-btn-secondary px-3 py-1 text-sm"
            data-testid="fleet-timeline-refresh"
          >
            Refresh
          </button>
        </div>
        <div className="pa-panel p-4">
          {timelineEvents.length === 0 ? (
            <div className="text-slate-300/70">No recent events yet.</div>
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
                      <div className="text-slate-300/70">
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
        <div className="text-center text-slate-300/70 py-8">
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
          fleetOptions={
            selectedPlanet
              ? (visibleFleetsByPlanet[selectedPlanet.id] || []).filter((f) => f?.status === 'stationed' && f?.mission !== 'inventory')
              : normalizedFleets.filter((f) => f?.status === 'stationed' && f?.mission !== 'inventory')
          }
          onSelectFleet={(fleetId) => {
            const next = normalizedFleets.find((f) => String(f.id) === String(fleetId));
            if (next) setSelectedFleet(next);
          }}
          onCreateFleet={() => {
            setShowSendForm(false);
            setSelectedFleet(null);
            setShowCreateForm(true);
          }}
          planets={allPlanets.length > 0 ? allPlanets : planets}
          user={user}
          preset={activeSendPreset}
          onSend={handleSendFleet}
          onSaveTemplate={saveTemplate}
          onClose={() => {
            setShowSendForm(false);
            setSelectedFleet(null);
            setSendPreset(null);
            setActiveSendPreset(null);
            localStorage.removeItem('fleetSendPreset');
          }}
        />
      )}

      {showSplitForm && selectedFleet && (
        <SplitFleetModal
          fleet={selectedFleet}
          onSplit={handleSplitFleet}
          onClose={() => {
            setShowSplitForm(false);
            setSelectedFleet(null);
          }}
        />
      )}

      {showTransferForm && selectedFleet && (
        <TransferFleetModal
          sourceFleet={selectedFleet}
          targetFleets={normalizedFleets.filter((f) =>
            f?.id !== selectedFleet.id &&
            f?.status === 'stationed' &&
            f?.start_planet_id === selectedFleet.start_planet_id
          )}
          onTransfer={handleTransferFleet}
          onClose={() => {
            setShowTransferForm(false);
            setSelectedFleet(null);
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
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-6" data-testid="fleet-create-modal">
      <div className="pa-modal p-6 w-full max-w-md">
        <h3 className="text-xl font-bold text-white mb-4">Create New Fleet</h3>

        <form onSubmit={handleSubmit} data-testid="fleet-create-form">
          <div className="mb-4">
            <label className="block text-slate-200/90 mb-2">Starting Planet</label>
            <select
              value={formData.start_planet_id}
              onChange={(e) => setFormData(prev => ({ ...prev, start_planet_id: e.target.value }))}
              data-testid="fleet-start-planet-select"
              className="pa-input"
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
              <label className="block text-slate-200/90">Ships</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={fillAllShips}
                  className="pa-btn-secondary px-3 py-1 text-sm"
                  data-testid="fleet-create-fill-all"
                >
                  Add all
                </button>
                <button
                  type="button"
                  onClick={clearShips}
                  className="pa-btn-secondary px-3 py-1 text-sm"
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
                    <label className="block text-xs text-slate-300/70">
                      {shipType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      {available ? ` (max ${available[shipType] || 0})` : ''}
                    </label>
                    <button
                      type="button"
                      className="pa-btn-ghost text-xs px-2 py-0.5"
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
                    className="pa-input p-2"
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              type="submit"
              data-testid="fleet-create-submit"
              className="flex-1 pa-btn-primary py-2 px-4"
            >
              Create Fleet
            </button>
            <button
              type="button"
              onClick={onClose}
              data-testid="fleet-create-cancel"
              className="flex-1 pa-btn-secondary py-2 px-4"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SendFleetModal({ fleet, fleetOptions = [], onSelectFleet, onCreateFleet, planets, user, preset, onSend, onSaveTemplate, onClose }) {
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

  const handleSaveTemplate = () => {
    if (typeof onSaveTemplate !== 'function') return;
    onSaveTemplate({
      mission: formData.mission,
      target_planet_id: formData.target_planet_id ? parseInt(formData.target_planet_id, 10) : null,
      target_x: formData.target_x ? parseInt(formData.target_x, 10) : null,
      target_y: formData.target_y ? parseInt(formData.target_y, 10) : null,
      target_z: formData.target_z ? parseInt(formData.target_z, 10) : null,
      recycle_focus: formData.recycle_focus || 'proportional',
    });
  };

  const fleetSummary = useMemo(() => summarizeFleetShips(fleet?.ships || {}), [fleet?.ships]);

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-6" data-testid="fleet-send-modal">
      <div className="pa-modal p-6 w-full max-w-md">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <h3 className="text-xl font-bold text-white">Send Fleet</h3>
            <div className="text-xs text-slate-300/70 mt-1">
              Fleet #{fleet.id} • {fleetSummary.total.toLocaleString()} ships{fleetSummary.top ? ` • ${fleetSummary.top}` : ''}
            </div>
          </div>
          {typeof onCreateFleet === 'function' && (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleSaveTemplate}
                className="pa-btn-secondary px-3 py-1 text-sm"
                data-testid="fleet-send-save-template"
                title="Save current mission/target as template"
              >
                Save as template
              </button>
              <button
                type="button"
                onClick={onCreateFleet}
                className="pa-btn-secondary px-3 py-1 text-sm"
                data-testid="fleet-send-create-fleet"
                title="Create a new fleet (change composition)"
              >
                Create fleet
              </button>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} data-testid="fleet-send-form">
          {Array.isArray(fleetOptions) && fleetOptions.length > 1 && (
            <div className="mb-4">
              <label className="block text-slate-200/90 mb-2">Fleet</label>
              <select
                value={String(fleet.id)}
                onChange={(e) => onSelectFleet?.(e.target.value)}
                data-testid="fleet-send-fleet-select"
                className="pa-input"
              >
                {fleetOptions.map((f) => (
                  <option key={f.id} value={f.id}>
                    {(() => {
                      const s = summarizeFleetShips(f?.ships || {});
                      return `Fleet #${f.id} • ${s.total} ships${s.top ? ` • ${s.top}` : ''}`;
                    })()}
                  </option>
                ))}
              </select>
              {formData.mission === 'colonize' && (
                <p className="text-xs text-slate-300/70 mt-1">Colonize requires a fleet with colony ships.</p>
              )}
            </div>
          )}

          <div className="mb-4 pa-panel p-3" data-testid="fleet-send-composition">
            <div className="flex items-center justify-between mb-2">
              <div className="text-slate-200/90 text-sm font-semibold">Fleet composition</div>
              <div className="text-slate-300/70 text-xs">{fleetSummary.total.toLocaleString()} total</div>
            </div>
            {fleetSummary.entries.length === 0 ? (
              <div className="text-xs text-slate-300/70">No ships in this fleet.</div>
            ) : (
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                {fleetSummary.entries.map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between text-slate-200/90">
                    <span className="text-slate-200/80">{formatShipLabel(k)}</span>
                    <span className="font-semibold text-white">{Number(v).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mb-4">
            <label className="block text-slate-200/90 mb-2">Target Planet</label>
            <select
              value={formData.target_planet_id}
              onChange={(e) => setFormData(prev => ({ ...prev, target_planet_id: e.target.value }))}
              data-testid="fleet-target-planet-select"
              className="pa-input"
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
            <p className="text-xs text-slate-300/70 mt-1">
              {formData.mission === 'attack' && 'Shows enemy planets only'}
              {formData.mission === 'colonize' && 'Shows unowned planets only'}
              {formData.mission === 'recycle' && (debrisLoading ? 'Loading debris targets…' : 'Shows planets with debris fields only')}
              {formData.mission === 'transport' && 'Shows your planets only'}
              {formData.mission === 'deploy' && 'Shows your planets only'}
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-slate-200/90 mb-2">Mission</label>
            <select
              value={formData.mission}
              onChange={(e) => setFormData(prev => ({ ...prev, mission: e.target.value }))}
              data-testid="fleet-mission-select"
              className="pa-input"
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
              <label className="block text-slate-200/90 mb-2">Recycling focus</label>
              <select
                value={formData.recycle_focus || 'proportional'}
                onChange={(e) => setFormData((prev) => ({ ...prev, recycle_focus: e.target.value }))}
                data-testid="fleet-recycle-focus"
                className="pa-input"
              >
                <option value="proportional">Proportional (recommended)</option>
                <option value="metal">Metal only</option>
                <option value="crystal">Crystal only</option>
                <option value="deuterium">Deuterium only</option>
              </select>
              <p className="text-xs text-slate-300/70 mt-1">
                Proportional splits recycler capacity across available debris. “Only” focuses all capacity into one resource.
              </p>
            </div>
          )}

          {/* Coordinates for colonization */}
          {formData.mission === 'colonize' && (
            <div className="mb-4">
              <label className="block text-slate-200/90 mb-2">Target Coordinates</label>
              <div className="grid grid-cols-3 gap-2">
                <input
                  type="number"
                  placeholder="X"
                  value={formData.target_x}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_x: e.target.value }))}
                  data-testid="fleet-target-x"
                  className="pa-input p-3"
                  required
                />
                <input
                  type="number"
                  placeholder="Y"
                  value={formData.target_y}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_y: e.target.value }))}
                  data-testid="fleet-target-y"
                  className="pa-input p-3"
                  required
                />
                <input
                  type="number"
                  placeholder="Z"
                  value={formData.target_z}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_z: e.target.value }))}
                  data-testid="fleet-target-z"
                  className="pa-input p-3"
                  required
                />
              </div>
              <p className="text-xs text-slate-300/70 mt-1">Enter coordinates for colonization (must be empty)</p>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              type="submit"
              data-testid="fleet-send-submit"
              className="flex-1 pa-btn-primary py-2 px-4"
            >
              Send Fleet
            </button>
            <button
              type="button"
              onClick={onClose}
              data-testid="fleet-send-cancel"
              className="flex-1 pa-btn-secondary py-2 px-4"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SplitFleetModal({ fleet, onSplit, onClose }) {
  const { showError } = useToast();
  const [ships, setShips] = useState(() => Object.fromEntries(FLEET_SHIP_KEYS.map((k) => [k, 0])));

  const setShipAmount = (shipType, value) => {
    setShips((prev) => ({ ...prev, [shipType]: Math.max(0, parseInt(value, 10) || 0) }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {};
    let total = 0;

    FLEET_SHIP_KEYS.forEach((shipType) => {
      const amount = Math.max(0, parseInt(ships[shipType], 10) || 0);
      const available = Math.max(0, parseInt(fleet?.ships?.[shipType], 10) || 0);
      if (amount <= 0) return;
      if (amount > available) {
        showError(`Cannot split more than available ${formatShipLabel(shipType)} (${available}).`);
        total = -1;
        return;
      }
      payload[shipType] = amount;
      total += amount;
    });

    if (total <= 0) {
      showError(total === 0 ? 'Select at least one ship to split.' : 'Invalid split amounts.');
      return;
    }

    onSplit({ fleetId: fleet.id, ships: payload });
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-6" data-testid="fleet-split-modal">
      <div className="pa-modal p-6 w-full max-w-lg">
        <h3 className="text-xl font-bold text-white mb-4">Split Fleet #{fleet.id}</h3>
        <form onSubmit={handleSubmit} data-testid="fleet-split-form">
          <div className="grid grid-cols-2 gap-2 mb-4">
            {FLEET_SHIP_KEYS.map((shipType) => {
              const available = Math.max(0, parseInt(fleet?.ships?.[shipType], 10) || 0);
              return (
                <div key={shipType}>
                  <label className="block text-xs text-slate-300/70 mb-1">
                    {formatShipLabel(shipType)} (max {available})
                  </label>
                  <input
                    type="number"
                    min="0"
                    max={available}
                    value={ships[shipType] || 0}
                    onChange={(e) => setShipAmount(shipType, e.target.value)}
                    data-testid={`fleet-split-ship-${shipType}`}
                    className="pa-input p-2"
                  />
                </div>
              );
            })}
          </div>

          <div className="flex space-x-3">
            <button type="submit" className="flex-1 pa-btn-primary py-2 px-4" data-testid="fleet-split-submit">
              Split Fleet
            </button>
            <button type="button" onClick={onClose} className="flex-1 pa-btn-secondary py-2 px-4" data-testid="fleet-split-cancel">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function TransferFleetModal({ sourceFleet, targetFleets, onTransfer, onClose }) {
  const { showError } = useToast();
  const [targetFleetId, setTargetFleetId] = useState(() => {
    if (!Array.isArray(targetFleets) || targetFleets.length === 0) return '';
    return String(targetFleets[0].id);
  });
  const [ships, setShips] = useState(() => Object.fromEntries(FLEET_SHIP_KEYS.map((k) => [k, 0])));

  useEffect(() => {
    if (!Array.isArray(targetFleets) || targetFleets.length === 0) {
      setTargetFleetId('');
      return;
    }
    if (!targetFleets.some((f) => String(f.id) === String(targetFleetId))) {
      setTargetFleetId(String(targetFleets[0].id));
    }
  }, [targetFleets, targetFleetId]);

  const setShipAmount = (shipType, value) => {
    setShips((prev) => ({ ...prev, [shipType]: Math.max(0, parseInt(value, 10) || 0) }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!targetFleetId) {
      showError('Select a target fleet.');
      return;
    }

    const payload = {};
    let total = 0;
    FLEET_SHIP_KEYS.forEach((shipType) => {
      const amount = Math.max(0, parseInt(ships[shipType], 10) || 0);
      const available = Math.max(0, parseInt(sourceFleet?.ships?.[shipType], 10) || 0);
      if (amount <= 0) return;
      if (amount > available) {
        showError(`Cannot transfer more than available ${formatShipLabel(shipType)} (${available}).`);
        total = -1;
        return;
      }
      payload[shipType] = amount;
      total += amount;
    });

    if (total <= 0) {
      showError(total === 0 ? 'Select at least one ship to transfer.' : 'Invalid transfer amounts.');
      return;
    }

    onTransfer({
      sourceFleetId: sourceFleet.id,
      targetFleetId: parseInt(targetFleetId, 10),
      ships: payload,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-6" data-testid="fleet-transfer-modal">
      <div className="pa-modal p-6 w-full max-w-lg">
        <h3 className="text-xl font-bold text-white mb-4">Transfer From Fleet #{sourceFleet.id}</h3>
        <form onSubmit={handleSubmit} data-testid="fleet-transfer-form">
          <div className="mb-4">
            <label className="block text-slate-200/90 mb-2">Target Fleet</label>
            <select
              value={targetFleetId}
              onChange={(e) => setTargetFleetId(e.target.value)}
              data-testid="fleet-transfer-target-select"
              className="pa-input"
              required
            >
              {Array.isArray(targetFleets) && targetFleets.map((fleet) => (
                <option key={fleet.id} value={fleet.id}>
                  Fleet #{fleet.id} ({fleet.mission})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-2 mb-4">
            {FLEET_SHIP_KEYS.map((shipType) => {
              const available = Math.max(0, parseInt(sourceFleet?.ships?.[shipType], 10) || 0);
              return (
                <div key={shipType}>
                  <label className="block text-xs text-slate-300/70 mb-1">
                    {formatShipLabel(shipType)} (max {available})
                  </label>
                  <input
                    type="number"
                    min="0"
                    max={available}
                    value={ships[shipType] || 0}
                    onChange={(e) => setShipAmount(shipType, e.target.value)}
                    data-testid={`fleet-transfer-ship-${shipType}`}
                    className="pa-input p-2"
                  />
                </div>
              );
            })}
          </div>

          <div className="flex space-x-3">
            <button type="submit" className="flex-1 pa-btn-primary py-2 px-4" data-testid="fleet-transfer-submit">
              Transfer Ships
            </button>
            <button type="button" onClick={onClose} className="flex-1 pa-btn-secondary py-2 px-4" data-testid="fleet-transfer-cancel">
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
    <div className="pa-panel p-4">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-white font-medium text-lg">
            {planet.is_home_planet ? '🏠' : '🌍'} {planet.name}
          </h4>
          <p className="text-slate-300/70 text-sm">
            Coordinates: {planet.x}:{planet.y}:{planet.z}
          </p>
        </div>
        <button
          onClick={onCreateFleet}
          className="pa-btn-primary px-3 py-1 text-sm"
        >
          + Create Fleet
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-400">{planet.resources?.metal || 0}</div>
          <div className="text-xs text-slate-300/70">Metal</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-400">{planet.resources?.crystal || 0}</div>
          <div className="text-xs text-slate-300/70">Crystal</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-400">{planet.resources?.deuterium || 0}</div>
          <div className="text-xs text-slate-300/70">Deuterium</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-400">{totalShips}</div>
          <div className="text-xs text-slate-300/70">Total Ships</div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-slate-500/25">
        <div className="flex justify-between text-sm">
          <span className="text-slate-300/70">Active Fleets:</span>
          <span className="text-orange-400">{activeFleets}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-300/70">Stationed Fleets:</span>
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
    <div className="pa-panel p-4">
      <h4 className="text-white font-medium mb-4">Available Ships at {planet.name}</h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {shipTypes.map(shipType => (
          <div key={shipType.key} className="pa-surface p-3 text-center">
            <div className="text-2xl mb-1">{shipType.icon}</div>
            <div className="text-white font-medium text-sm">{shipType.name}</div>
            <div className={`text-lg font-bold ${
              availableShips[shipType.key] > 0 ? 'text-green-400' : 'text-slate-300/50'
            }`}>
              {availableShips[shipType.key]}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FleetTile({ fleet, planets, onSend, onRecall, onDissolve, onSplit, onTransfer, formatTimeRemaining }) {
  const startPlanet = fleet.start_planet || planets.find(p => p.id === fleet.start_planet_id) || null;
  const rawTargetPlanet = fleet.target_planet || planets.find(p => p.id === fleet.target_planet_id) || null;
  // Keep From/To stable (start -> target) even while returning; the status already communicates direction.
  const displayTargetPlanet = rawTargetPlanet;
  const upkeepPerHour = Number(fleet?.upkeep?.deuterium_per_hour || 0);

  return (
    <div className="pa-panel p-4" data-testid="fleet-tile">
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="text-white font-medium">
            Fleet #{fleet.id} - {fleet.mission}
          </div>
          <div className="text-sm text-slate-300/70">
            Status: <span className={`font-medium ${
              fleet.status === 'stationed' ? 'text-green-400' :
              fleet.status === 'traveling' ? 'text-yellow-400' :
              fleet.status === 'returning' ? 'text-blue-400' : 'text-slate-300/70'
            }`} data-testid="fleet-status-value">
              {fleet.status}
            </span>
          </div>
        </div>
        <div className="flex space-x-2">
          {fleet.status === 'stationed' && fleet.mission !== 'inventory' && (
            <button
              onClick={() => onSend(fleet)}
              className="pa-btn-primary px-3 py-1 text-sm"
              data-testid="fleet-send-button"
            >
              Send
            </button>
          )}
          {fleet.status === 'stationed' && fleet.mission !== 'inventory' && (
            <button
              onClick={() => onSplit(fleet)}
              className="pa-btn-secondary px-3 py-1 text-sm"
              data-testid="fleet-split-button"
            >
              Split
            </button>
          )}
          {fleet.status === 'stationed' && fleet.mission !== 'inventory' && (
            <button
              onClick={() => onTransfer(fleet)}
              className="pa-btn-secondary px-3 py-1 text-sm"
              data-testid="fleet-transfer-button"
            >
              Transfer
            </button>
          )}
          {fleet.status === 'stationed' && fleet.mission !== 'inventory' && (
            <button
              onClick={() => onDissolve(fleet.id)}
              className="pa-btn-danger px-3 py-1 text-sm"
              data-testid="fleet-dissolve-button"
            >
              Dissolve
            </button>
          )}
          {(fleet.status === 'traveling' || fleet.status === 'returning') && (
            <button
              onClick={() => onRecall(fleet.id)}
              className="pa-btn-secondary px-3 py-1 text-sm bg-amber-500/20 hover:bg-amber-500/25 border-amber-500/30 text-amber-100"
              data-testid="fleet-recall-button"
            >
              Recall
            </button>
          )}
        </div>
      </div>

      {/* Fleet Details */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm mb-3">
        <div>
          <div className="text-slate-300/70">Ships</div>
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
          <div className="text-slate-300/70">From</div>
          <div className="text-white" data-testid="fleet-from-value">{startPlanet?.name || 'Unknown'}</div>
        </div>
        <div>
          <div className="text-slate-300/70">To</div>
          <div className="text-white" data-testid="fleet-to-value">{displayTargetPlanet?.name || 'N/A'}</div>
        </div>
        <div>
          <div className="text-slate-300/70">ETA</div>
          <div className="text-white" data-testid="fleet-eta-value">{formatTimeRemaining(fleet.arrival_time, fleet.status)}</div>
        </div>
        <div>
          <div className="text-slate-300/70">Upkeep</div>
          <div className="text-amber-300" data-testid="fleet-upkeep-value">-{upkeepPerHour.toLocaleString()} D/h</div>
        </div>
      </div>

      {/* Ship Breakdown */}
      <div className="pt-3 border-t border-slate-500/25">
        <div className="text-xs text-slate-300/70 mb-2">Ship Composition:</div>
        <div className="flex flex-wrap gap-2 text-xs">
          {(() => {
            const ships = fleet.ships || {};
            return Object.entries(ships).map(([shipType, count]) => (
              count > 0 && (
                <span key={shipType} className="pa-surface px-2 py-1 rounded">
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
