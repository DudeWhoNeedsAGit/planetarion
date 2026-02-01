import React, { useState, useEffect } from 'react';
import axios from 'axios';
import planetImage from './images/p4.png';
import { useToast } from './ToastContext';

// Enhanced Debug Infrastructure for E2E Testing
const DEBUG_MODE = process.env.NODE_ENV === 'development' || process.env.REACT_APP_DEBUG_MODE === 'true';

const debugLog = (message, data = null) => {
  if (DEBUG_MODE) {
    const timestamp = new Date().toISOString();
    console.log(`[GalaxyMap Debug ${timestamp}] ${message}`, data);
  }
};

// Test-specific debug markers for E2E test identification
const TEST_DEBUG = {
  consoleMessages: true,
  systemMarkers: true,
  fogOverlay: true,
  apiCalls: true,
  eventHandling: true
};

// Event Handling System for proper click management
const EventHandlingSystem = {
  setupSystemMarkerEvents: (element) => {
    if (!element) return;

    element.style.pointerEvents = 'auto';
    element.style.zIndex = '20';
    element.setAttribute('data-test-marker', 'system-marker');

    if (TEST_DEBUG.eventHandling) {
      debugLog('System marker event setup', {
        pointerEvents: element.style.pointerEvents,
        zIndex: element.style.zIndex,
        testMarker: element.getAttribute('data-test-marker')
      });
    }
  },

  setupFogOverlayEvents: (element) => {
    if (!element) return;

    element.style.pointerEvents = 'none';
    element.style.zIndex = '5';
    element.setAttribute('data-test-fog', 'fog-overlay');

    if (TEST_DEBUG.eventHandling) {
      debugLog('Fog overlay event setup', {
        pointerEvents: element.style.pointerEvents,
        zIndex: element.style.zIndex,
        testFog: element.getAttribute('data-test-fog')
      });
    }
  }
};

// Coordinate System Utilities
const CoordinateUtils = {
  // Validate coordinate bounds
  isValidCoordinate: (x, y, z) => {
    return (
      typeof x === 'number' && !isNaN(x) && x >= -10000 && x <= 10000 &&
      typeof y === 'number' && !isNaN(y) && y >= -10000 && y <= 10000 &&
      typeof z === 'number' && !isNaN(z) && z >= -10000 && z <= 10000
    );
  },

  // Format coordinates for display
  formatCoordinates: (x, y, z) => {
    return `${x}:${y}:${z}`;
  },

  // Calculate distance between two coordinate points
  calculateDistance: (x1, y1, z1, x2, y2, z2) => {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const dz = z2 - z1;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  },

  // Check if coordinates are within exploration range
  isWithinRange: (centerX, centerY, centerZ, targetX, targetY, targetZ, range = 50) => {
    const distance = CoordinateUtils.calculateDistance(centerX, centerY, centerZ, targetX, targetY, targetZ);
    return distance <= range;
  },

  // Generate relative coordinates for display
  getRelativeCoordinates: (centerX, centerY, centerZ, targetX, targetY, targetZ) => {
    return {
      relativeX: targetX - centerX,
      relativeY: targetY - centerY,
      relativeZ: targetZ - centerZ
    };
  }
};

const DEFAULT_GALAXY_RANGE = 2000;
const WORLD_SCALE = 0.1; // convert coordinate units -> pixels (higher = more spread out)

function GalaxyMap({ user, planets, onClose, onNavigateSection }) {
  const { showSuccess, showError } = useToast();
  const [systems, setSystems] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [loading, setLoading] = useState(true); // Start with loading true
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [galaxyLoaded, setGalaxyLoaded] = useState(false);
  const [galaxyRange, setGalaxyRange] = useState(DEFAULT_GALAXY_RANGE);
  const [zoom, setZoom] = useState(1);
  const [viewOffset, setViewOffset] = useState({ x: 0, y: 0 });
  const [showGrid, setShowGrid] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

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

  const viewCenterX = React.useMemo(() => {
    return Math.round(centerX - viewOffset.x / (zoom * WORLD_SCALE));
  }, [centerX, viewOffset.x, zoom]);

  const viewCenterY = React.useMemo(() => {
    return Math.round(centerY - viewOffset.y / (zoom * WORLD_SCALE));
  }, [centerY, viewOffset.y, zoom]);

  const lastFetchCenterRef = React.useRef({ x: centerX, y: centerY, z: centerZ });

  useEffect(() => {
    // Load galaxy data once when component mounts
    if (!galaxyLoaded) {
      fetchNearbySystems();
    }

    // Set up polling for real-time galaxy updates
    const interval = setInterval(() => {
      if (galaxyLoaded && !loading && !refreshing && !isDragging) {
        fetchNearbySystems({ background: true });
      }
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(interval);
  }, [galaxyLoaded, loading, refreshing, isDragging]); // Include dependencies

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
      const params = galaxyRange ? { range: galaxyRange } : {};
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

  // Calculate colonization difficulty for a planet
  const calculateColonizationDifficulty = (planet) => {
    if (!planet) return 1;

    // Calculate distance from origin (0,0,0)
    const distanceFromOrigin = Math.sqrt(
      Math.pow(planet.x || 0, 2) +
      Math.pow(planet.y || 0, 2) +
      Math.pow(planet.z || 0, 2)
    ) / 3;

    // Difficulty formula: min(5, max(1, floor(distance / 200)))
    const difficulty = Math.min(5, Math.max(1, Math.floor(distanceFromOrigin / 200)));
    return difficulty;
  };

  // Check if user can colonize a planet
  const canColonizePlanet = (planet) => {
    if (!planet || planet.user_id) return false;

    const difficulty = calculateColonizationDifficulty(planet);
    // Assume user has colonization tech level (in real implementation, this would come from user data)
    const userColonizationLevel = 3; // Placeholder - should come from user research data

    return userColonizationLevel >= difficulty;
  };

  const handleColonizePlanet = async (planet) => {
    if (planet.user_id) {
      showError('Planet is already colonized!');
      return;
    }

    // Check colonization requirements
    const difficulty = calculateColonizationDifficulty(planet);
    const canColonize = canColonizePlanet(planet);

    if (!canColonize) {
      showError(`Colonization difficulty ${difficulty} requires research level ${difficulty}. Upgrade your colonization technology first!`);
      return;
    }

    setLoading(true);
    try {
      // Find a fleet with colony ship
      const fleetResponse = await axios.get('/api/fleet');
      const fleetData = Array.isArray(fleetResponse.data) ? fleetResponse.data : [];
      const colonyFleet = fleetData.find(f =>
        f.status === 'stationed' && f.ships.colony_ship > 0
      );

      if (!colonyFleet) {
        showError('No fleets with colony ships available! Build colony ships in the Shipyard first.');
        return;
      }

      const sendResponse = await axios.post('/api/fleet/send', {
        fleet_id: colonyFleet.id,
        mission: 'colonize',
        target_x: planet.x,
        target_y: planet.y,
        target_z: planet.z
      });

      const result = sendResponse.data || {};

      // Show success message with ETA
      const etaSeconds = result.fleet?.eta || 0;
      const etaMinutes = Math.ceil(etaSeconds / 60);
      showSuccess(`🚀 Colonization fleet sent to ${planet.name}! ETA: ${etaMinutes} minutes`, 5000);

      // Refresh galaxy data immediately to show the fleet is in transit
      await fetchNearbySystems();

    } catch (error) {
      console.error('❌ Error sending colonization fleet:', error);
      showError(`Failed to send colonization fleet: ${error.message}`);
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
    const relativeX = (system.x - centerX) * WORLD_SCALE * zoom + viewOffset.x;
    const relativeY = (system.y - centerY) * WORLD_SCALE * zoom + viewOffset.y;
    return { x: relativeX, y: relativeY };
  };

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
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseLeave}
            onWheel={handleWheel}
          >
            {/* Deep Space Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900">
            {/* Nebula Layer 1 */}
            <div className="absolute inset-0 opacity-30">
              <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-purple-600 rounded-full blur-3xl animate-pulse"></div>
              <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-pink-600 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
            </div>

            {/* Nebula Layer 2 */}
            <div className="absolute inset-0 opacity-20">
              <div className="absolute top-1/2 left-1/4 w-64 h-64 bg-blue-500 rounded-full blur-2xl animate-pulse" style={{animationDelay: '1s'}}></div>
              <div className="absolute bottom-1/4 right-1/3 w-72 h-72 bg-indigo-600 rounded-full blur-2xl animate-pulse" style={{animationDelay: '3s'}}></div>
            </div>

            {/* Animated Starfield */}
            <div className="absolute inset-0">
              {starfield.stars.map((s) => (
                <div
                  key={s.key}
                  className={`absolute rounded-full bg-white ${s.sizeClass}`}
                  style={{
                    left: `${s.left}%`,
                    top: `${s.top}%`,
                    animation: `twinkle ${s.twinkleSeconds}s infinite`,
                    animationDelay: `${s.delaySeconds}s`
                  }}
                />
              ))}
            </div>

            {/* Floating Particles */}
            <div className="absolute inset-0">
              {starfield.particles.map((p) => (
                <div
                  key={p.key}
                  className="absolute w-1 h-1 bg-white rounded-full opacity-20"
                  style={{
                    left: `${p.left}%`,
                    top: `${p.top}%`,
                    animation: `float ${p.floatSeconds}s infinite linear`,
                    animationDelay: `${p.delaySeconds}s`
                  }}
                />
              ))}
            </div>
          </div>
          {/* Grid Background */}
          {showGrid && (
            <div data-test="grid" className="absolute inset-0 opacity-60">
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
            <div className="text-yellow-300">X: {Math.round(centerX - viewOffset.x / (zoom * WORLD_SCALE))}</div>
            <div className="text-green-300">Y: {Math.round(centerY - viewOffset.y / (zoom * WORLD_SCALE))}</div>
            <div className="text-purple-300">Z: {centerZ}</div>
          </div>

          {/* Systems Display */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="relative">

              {systems.map((system, index) => {
                const pos = getSystemPosition(system);
                const systemKey = `${system.x}:${system.y}:${system.z}`;

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

                return (
                  <div key={index} className="absolute" style={{ left: `${pos.x + 200}px`, top: `${pos.y + 150}px`, transform: 'translate(-50%, -50%)' }}>
                    {/* Coordinates above the planet */}
                    <div className="text-center mb-1">
                      <div className={`text-xs font-bold ${textColor} bg-black bg-opacity-70 px-2 py-1 rounded shadow-lg`}>
                        {system.x - centerX}:{system.y - centerY}
                      </div>
                    </div>

                    {/* Planet marker */}
                    <div
                      ref={(el) => el && EventHandlingSystem.setupSystemMarkerEvents(el)}
                      data-test-marker="system-marker"
                      className={`system-marker w-16 h-16 rounded-full border-2 cursor-pointer transition-all duration-200 flex items-center justify-center text-xs font-bold ${borderClass} ${!system.explored ? 'opacity-60' : ''}`}
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
                  left: `${200 + viewOffset.x}px`,
                  top: `${150 + viewOffset.y}px`,
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
          <SystemDetails
            system={selectedSystem}
            onClose={() => setSelectedSystem(null)}
            onColonize={handleColonizePlanet}
            loading={loading}
            userId={user?.id}
            centerX={centerX}
            centerY={centerY}
            centerZ={centerZ}
            onNavigateSection={onNavigateSection}
            onExplore={handleExploreSystem}
          />
        )}
      </div>
    </div>
  );
}

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
  onQuickColonize,
  onColonize = () => {},
}) {
  const isOwnedByUser = planet?.user_id != null && planet.user_id === userId;
  const isUnowned = planet?.user_id == null;
  const isEnemy = planet?.user_id != null && planet.user_id !== userId;

  const debris = planet?.debris || { metal: 0, crystal: 0, deuterium: 0 };
  const debrisTotal = (debris.metal || 0) + (debris.crystal || 0) + (debris.deuterium || 0);

  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <div className="text-white font-bold text-lg">🪐 {planet.name}</div>
          <div className="text-sm text-gray-300">
            {planet.coordinates || `${planet.x}:${planet.y}:${planet.z}`}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Distance: {Math.round(CoordinateUtils.calculateDistance(
              centerX, centerY, centerZ, planet.x, planet.y, planet.z
            ))} units
          </div>
        </div>

        <div className="text-right">
          {isUnowned && (
            <span className="text-green-300 text-xs font-medium px-2 py-1 bg-green-900 rounded">Unowned</span>
          )}
          {isOwnedByUser && (
            <span className="text-blue-300 text-xs font-medium px-2 py-1 bg-blue-900 rounded">Your planet</span>
          )}
          {isEnemy && (
            <span className="text-red-300 text-xs font-medium px-2 py-1 bg-red-900 rounded">
              {planet.owner_name ? `Enemy: ${planet.owner_name}` : 'Enemy'}
            </span>
          )}
        </div>
      </div>

      {debrisTotal > 0 && (
        <div className="mt-3 text-xs text-gray-200 bg-gray-800 border border-gray-600 rounded p-2">
          Debris: {debris.metal.toLocaleString()} metal, {debris.crystal.toLocaleString()} crystal, {debris.deuterium.toLocaleString()} deut
        </div>
      )}

      <div className="flex justify-end gap-2 mt-3">
        {debrisTotal > 0 && (
          <button
            onClick={() => onRecycle(planet)}
            className="px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded text-sm"
            disabled={loading}
          >
            Send recyclers
          </button>
        )}

        {isUnowned && (
          <button
            onClick={() => (onQuickColonize ? onQuickColonize(planet) : onColonize(planet))}
            className="px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded text-sm"
            disabled={loading}
          >
            Colonize
          </button>
        )}

        {isEnemy && (
          <button
            onClick={() => onSpy(planet)}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm"
            disabled={loading}
          >
            Spy
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

// System Statistics Component
function SystemStatistics({ system, planets }) {
  const totalPlanets = planets.length;
  const ownedPlanets = planets.filter(p => p.user_id).length;
  const unownedPlanets = totalPlanets - ownedPlanets;
  const totalDebris = planets.reduce((sum, p) => {
    const d = p?.debris || {};
    return sum + (d.metal || 0) + (d.crystal || 0) + (d.deuterium || 0);
  }, 0);

  return (
    <div className="bg-gray-700 rounded-lg p-4 mb-4 border border-gray-600">
      <h4 className="text-white font-bold mb-3 flex items-center">
        📊 System Statistics
      </h4>
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

// Enhanced System Details Component
function SystemDetails({ system, onClose, onColonize, loading, userId, centerX, centerY, centerZ, onNavigateSection, onExplore }) {
  const [planets, setPlanets] = useState([]);

  useEffect(() => {
    fetchSystemPlanets();
  }, [system]);

  const fetchSystemPlanets = async () => {
    try {
      const res = await axios.get(`/api/galaxy/system/${system.x}/${system.y}/${system.z}`);
      setPlanets(Array.isArray(res.data) ? res.data : []);
    } catch (error) {
      console.error('❌ Error fetching system planets:', error);
      setPlanets([]);
    }
  };

  const goToFleetsWithPreset = (preset) => {
    try {
      localStorage.setItem('fleetSendPreset', JSON.stringify(preset));
    } catch (e) {
      console.warn('Failed to set fleetSendPreset:', e);
    }
    if (typeof onNavigateSection === 'function') onNavigateSection('fleets');
  };

  return (
    <div className="mt-6 bg-gray-800 rounded-lg p-6 max-h-96 overflow-y-auto border border-gray-600">
      {/* System Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex-1">
          <h3 className="text-2xl font-bold text-white flex items-center">
            🌌 System {system.x}:{system.y}:{system.z}
          </h3>
          <div className="text-gray-400 mt-1 flex items-center">
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              system.explored
                ? 'bg-blue-900 text-blue-300'
                : 'bg-gray-900 text-gray-300'
            }`}>
              {system.explored ? '✅ Explored' : '❓ Unexplored'}
            </span>
            <span className="ml-4">
              Distance: {Math.round(CoordinateUtils.calculateDistance(
                centerX, centerY, centerZ, system.x, system.y, system.z
              ))} units from home
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-xl ml-4"
        >
          ✕
        </button>
      </div>

      {/* System Statistics */}
      <SystemStatistics system={system} planets={planets} />

      {/* Exploration CTA for unexplored systems */}
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

      {/* Planets List */}
      <div>
        <h4 className="text-white font-bold mb-4 flex items-center">
          🪐 Planets ({planets.length})
        </h4>

        {planets.length === 0 ? (
          <div className="text-gray-400 text-center py-8 bg-gray-700 rounded-lg">
            <div className="text-4xl mb-2">🌌</div>
            <div>No planets discovered yet</div>
            <div className="text-sm mt-2">Send an exploration fleet to discover planets in this system</div>
          </div>
        ) : (
          <div className="space-y-4">
            {planets.map(planet => (
              <PlanetCard
                key={planet.id}
                planet={planet}
                onColonize={onColonize}
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

export default GalaxyMap;
