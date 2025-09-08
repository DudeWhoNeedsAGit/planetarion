import React, { useState, useEffect } from 'react';
import axios from 'axios';
import planetImage from './images/p4.png';

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

function GalaxyMap({ user, planets, onClose }) {
  const [systems, setSystems] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [loading, setLoading] = useState(true); // Start with loading true
  const [error, setError] = useState(null);
  const [galaxyLoaded, setGalaxyLoaded] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [viewOffset, setViewOffset] = useState({ x: 0, y: 0 });
  const [showGrid, setShowGrid] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Get user's home planet coordinates as center
  const homePlanet = planets.find(p => p.user_id == user.id); // Use loose equality for type safety
  const centerX = homePlanet?.x || 100; // Default to 100 instead of 0
  const centerY = homePlanet?.y || 200;
  const centerZ = homePlanet?.z || 300;



  console.log('Galaxy Map Debug:', {
    userId: user.id,
    userIdType: typeof user.id,
    planetsCount: planets.length,
    planets: planets.map(p => ({
      id: p.id,
      user_id: p.user_id,
      user_id_type: typeof p.user_id,
      coordinates: p.coordinates || `${p.x}:${p.y}:${p.z}`
    })),
    homePlanet: homePlanet ? `${homePlanet.x}:${homePlanet.y}:${homePlanet.z}` : 'Not found',
    center: `${centerX}:${centerY}:${centerZ}`,
    apiUrl: `/api/galaxy/nearby/${centerX}/${centerY}/${centerZ}`
  });

  useEffect(() => {
    // Load galaxy data once when component mounts
    if (!galaxyLoaded) {
      fetchNearbySystems();
    }
  }, []); // Empty dependency array - only run once on mount

  const fetchNearbySystems = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🌌 Fetching complete galaxy data once:', `http://localhost:5000/api/galaxy/nearby/${centerX}/${centerY}/${centerZ}`);

      // Get JWT token from localStorage (following fleet test pattern)
      const token = localStorage.getItem('token');
      console.log('DEBUG: JWT token present for galaxy API:', !!token);

      const response = await fetch(`http://localhost:5000/api/galaxy/nearby/${centerX}/${centerY}/${centerZ}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });

      console.log('DEBUG: Galaxy API response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ Complete galaxy data loaded successfully:', `${data.length} systems`);
      setSystems(data);
      setGalaxyLoaded(true);
    } catch (error) {
      console.error('❌ Error fetching galaxy data:', {
        message: error.message,
        status: error.status,
        url: `http://localhost:5000/api/galaxy/nearby/${centerX}/${centerY}/${centerZ}`
      });

      setError('Failed to load galaxy data');

      // Add fallback data for testing (following fleet pattern)
      console.log('🔧 Using fallback test data with mix of explored/unexplored systems');
      setSystems([
        { x: centerX + 10, y: centerY + 20, z: centerZ + 30, explored: false, planets: 0, owner_id: null },
        { x: centerX - 15, y: centerY - 25, z: centerZ - 35, explored: true, planets: 2, owner_id: user.id },
        { x: centerX + 40, y: centerY + 50, z: centerZ + 60, explored: false, planets: 0, owner_id: null },
        { x: centerX - 30, y: centerY + 15, z: centerZ - 20, explored: false, planets: 0, owner_id: null },
        { x: centerX + 25, y: centerY - 35, z: centerZ + 45, explored: true, planets: 1, owner_id: null }
      ]);
      setGalaxyLoaded(true);
    } finally {
      setLoading(false);
    }
  };

  const handleExploreSystem = async (system) => {
    if (system.explored) {
      // Show system details
      setSelectedSystem(system);
      return;
    }

    // Send exploration fleet
    setLoading(true);
    try {
      // Get JWT token from localStorage (following fleet pattern)
      const token = localStorage.getItem('token');
      console.log('DEBUG: JWT token present for fleet API:', !!token);

      // Find a fleet to send (simplified - use first available)
      const fleetResponse = await fetch('http://localhost:5000/api/fleet', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });

      if (!fleetResponse.ok) {
        throw new Error(`HTTP ${fleetResponse.status}: ${fleetResponse.statusText}`);
      }

      const fleetData = await fleetResponse.json();
      const availableFleet = fleetData.find(f => f.status === 'stationed');

      if (!availableFleet) {
        alert('No available fleets for exploration!');
        return;
      }

      const sendResponse = await fetch('http://localhost:5000/api/fleet/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          fleet_id: availableFleet.id,
          mission: 'explore',
          target_x: system.x,
          target_y: system.y,
          target_z: system.z
        })
      });

      if (!sendResponse.ok) {
        throw new Error(`HTTP ${sendResponse.status}: ${sendResponse.statusText}`);
      }

      alert(`Exploration fleet sent to ${system.x}:${system.y}:${system.z}`);
    } catch (error) {
      console.error('Error sending exploration fleet:', error);
      alert('Failed to send exploration fleet');
    } finally {
      setLoading(false);
    }
  };

  const handleColonizePlanet = async (planet) => {
    if (planet.user_id) {
      alert('Planet is already colonized!');
      return;
    }

    setLoading(true);
    try {
      // Get JWT token from localStorage (following fleet pattern)
      const token = localStorage.getItem('token');
      console.log('DEBUG: JWT token present for colonization API:', !!token);

      // Find a fleet with colony ship
      const fleetResponse = await fetch('http://localhost:5000/api/fleet', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });

      if (!fleetResponse.ok) {
        throw new Error(`HTTP ${fleetResponse.status}: ${fleetResponse.statusText}`);
      }

      const fleetData = await fleetResponse.json();
      const colonyFleet = fleetData.find(f =>
        f.status === 'stationed' && f.ships.colony_ship > 0
      );

      if (!colonyFleet) {
        alert('No fleets with colony ships available!');
        return;
      }

      const sendResponse = await fetch('http://localhost:5000/api/fleet/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          fleet_id: colonyFleet.id,
          mission: 'colonize',
          target_x: planet.x,
          target_y: planet.y,
          target_z: planet.z
        })
      });

      if (!sendResponse.ok) {
        throw new Error(`HTTP ${sendResponse.status}: ${sendResponse.statusText}`);
      }

      alert(`Colonization fleet sent to ${planet.name}`);
    } catch (error) {
      console.error('Error sending colonization fleet:', error);
      alert('Failed to send colonization fleet');
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
    const relativeX = (system.x - centerX) * zoom + viewOffset.x;
    const relativeY = (system.y - centerY) * zoom + viewOffset.y;
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
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-6xl w-full h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-white">Galaxy Map</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl"
          >
            ✕
          </button>
        </div>

        {/* Controls */}
        <div className="flex justify-between items-center mb-4">
          <div className="text-sm text-gray-300">
            Center: {centerX}:{centerY}:{centerZ} | Zoom: {Math.round(zoom * 100)}% | Range: {Math.round(50 / zoom)} units
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
        {loading && (
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
        {!loading && !error && (
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
              {Array.from({ length: 200 }, (_, i) => (
                <div
                  key={i}
                  className={`absolute rounded-full bg-white ${
                    i % 10 === 0 ? 'w-1 h-1' : i % 5 === 0 ? 'w-0.5 h-0.5' : 'w-px h-px'
                  }`}
                  style={{
                    left: `${Math.random() * 100}%`,
                    top: `${Math.random() * 100}%`,
                    animation: `twinkle ${2 + Math.random() * 3}s infinite`,
                    animationDelay: `${Math.random() * 3}s`
                  }}
                />
              ))}
            </div>

            {/* Floating Particles */}
            <div className="absolute inset-0">
              {Array.from({ length: 30 }, (_, i) => (
                <div
                  key={`particle-${i}`}
                  className="absolute w-1 h-1 bg-white rounded-full opacity-20"
                  style={{
                    left: `${Math.random() * 100}%`,
                    top: `${Math.random() * 100}%`,
                    animation: `float ${10 + Math.random() * 20}s infinite linear`,
                    animationDelay: `${Math.random() * 10}s`
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
            <div className="text-yellow-300">X: {Math.round(centerX - viewOffset.x / zoom)}</div>
            <div className="text-green-300">Y: {Math.round(centerY - viewOffset.y / zoom)}</div>
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
                const isOwnedByUser = system.planets && system.planets > 0 && system.owner_id == user.id;
                const isEnemyColony = hasColonies && !isOwnedByUser;

                // Enhanced system marker with planet image background
                let borderClass = '';
                let markerIcon = '';
                let textColor = 'text-white';

                if (system.explored) {
                  if (isOwnedByUser) {
                    borderClass = 'border-green-400 hover:border-green-300';
                    markerIcon = '🏠';
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
                      className={`system-marker w-16 h-16 rounded-full border-2 cursor-pointer transition-all duration-200 flex items-center justify-center text-xs font-bold ${borderClass} ${!system.explored ? 'opacity-60' : ''}`}
                      style={{
                        zIndex: system.explored ? 10 : 5,
                        backgroundImage: `url(${planetImage})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        backgroundRepeat: 'no-repeat'
                      }}
                      onClick={() => handleExploreSystem(system)}
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
                <div className="w-3 h-3 bg-red-600 rounded-full"></div>
                <span>Enemy Colonies</span>
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
          />
        )}
      </div>
    </div>
  );
}

// Enhanced Planet Card Component
function PlanetCard({ planet, onColonize, loading, centerX, centerY, centerZ }) {
  // Generate mock traits for demonstration (in real implementation, this would come from API)
  const mockTraits = planet.user_id ? [] : [
    { name: 'Rich Metal', bonus: 25 },
    { name: 'Crystal Rich', bonus: 15 }
  ];

  return (
    <div className={`bg-gray-600 rounded-lg p-4 border-2 transition-all duration-200 ${
      planet.user_id
        ? 'border-blue-500 bg-gray-600'
        : 'border-green-500 bg-gray-700 hover:bg-gray-650'
    }`}>
      {/* Planet Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h4 className="text-white font-bold text-lg flex items-center">
            🪐 {planet.name}
          </h4>
          <div className="text-sm text-gray-300">
            {planet.coordinates || `${planet.x}:${planet.y}:${planet.z}`}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Distance: {Math.round(CoordinateUtils.calculateDistance(
              centerX, centerY, centerZ, planet.x, planet.y, planet.z
            ))} units
          </div>
        </div>
        <div className="text-right ml-4">
          {planet.owner_name ? (
            <span className="text-blue-400 text-sm font-medium px-2 py-1 bg-blue-900 rounded">
              Owned by {planet.owner_name}
            </span>
          ) : (
            <span className="text-green-400 text-sm font-medium px-2 py-1 bg-green-900 rounded">
              Unowned
            </span>
          )}
        </div>
      </div>

      {/* Planet Traits */}
      {mockTraits.length > 0 && (
        <div className="mb-3">
          <h5 className="text-gray-300 text-sm font-medium mb-2 flex items-center">
            🎯 Planet Traits:
          </h5>
          <div className="flex flex-wrap gap-1">
            {mockTraits.map((trait, index) => (
              <span key={index} className="px-2 py-1 bg-purple-600 text-white text-xs rounded flex items-center">
                {trait.name} (+{trait.bonus}%)
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Resources */}
      <div className="mb-3">
        <h5 className="text-gray-300 text-sm font-medium mb-2 flex items-center">
          💎 Resources:
        </h5>
        <div className="grid grid-cols-3 gap-2 text-sm">
          <div className="bg-gray-700 p-2 rounded text-center border border-yellow-600">
            <div className="text-yellow-400 font-bold text-lg">
              {planet.metal?.toLocaleString() || 0}
            </div>
            <div className="text-gray-400 text-xs">Metal</div>
          </div>
          <div className="bg-gray-700 p-2 rounded text-center border border-blue-600">
            <div className="text-blue-400 font-bold text-lg">
              {planet.crystal?.toLocaleString() || 0}
            </div>
            <div className="text-gray-400 text-xs">Crystal</div>
          </div>
          <div className="bg-gray-700 p-2 rounded text-center border border-green-600">
            <div className="text-green-400 font-bold text-lg">
              {planet.deuterium?.toLocaleString() || 0}
            </div>
            <div className="text-gray-400 text-xs">Deuterium</div>
          </div>
        </div>
      </div>

      {/* Structures */}
      {(planet.metal_mine > 0 || planet.crystal_mine > 0) && (
        <div className="mb-3">
          <h5 className="text-gray-300 text-sm font-medium mb-2 flex items-center">
            🏭 Structures:
          </h5>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex justify-between items-center bg-gray-700 p-2 rounded">
              <span className="text-gray-400">Metal Mine:</span>
              <span className="text-yellow-400 font-bold">Lv.{planet.metal_mine || 0}</span>
            </div>
            <div className="flex justify-between items-center bg-gray-700 p-2 rounded">
              <span className="text-gray-400">Crystal Mine:</span>
              <span className="text-blue-400 font-bold">Lv.{planet.crystal_mine || 0}</span>
            </div>
            <div className="flex justify-between items-center bg-gray-700 p-2 rounded">
              <span className="text-gray-400">Deut. Synth:</span>
              <span className="text-green-400 font-bold">Lv.{planet.deuterium_synthesizer || 0}</span>
            </div>
            <div className="flex justify-between items-center bg-gray-700 p-2 rounded">
              <span className="text-gray-400">Solar Plant:</span>
              <span className="text-orange-400 font-bold">Lv.{planet.solar_plant || 0}</span>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-2 pt-2 border-t border-gray-500">
        {!planet.user_id && (
          <button
            onClick={() => onColonize(planet)}
            className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded text-sm font-medium transition-colors flex items-center"
            disabled={loading}
          >
            🚀 {loading ? 'Colonizing...' : 'Colonize Planet'}
          </button>
        )}
        {planet.user_id && planet.user_id !== 'current_user_id' && (
          <button className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded text-sm font-medium transition-colors flex items-center">
            ⚔️ Attack
          </button>
        )}
        {planet.user_id && planet.user_id === 'current_user_id' && (
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium transition-colors flex items-center">
            📊 View Details
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
  const totalResources = planets.reduce((sum, p) =>
    sum + (p.metal || 0) + (p.crystal || 0) + (p.deuterium || 0), 0
  );

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
          <div className="text-2xl font-bold text-yellow-400">{totalResources.toLocaleString()}</div>
          <div className="text-gray-400 text-xs">Total Resources</div>
        </div>
      </div>
    </div>
  );
}

// Enhanced System Details Component
function SystemDetails({ system, onClose, onColonize, loading }) {
  const [planets, setPlanets] = useState([]);

  // Get user's home coordinates for distance calculation
  const homePlanet = planets.find(p => p.user_id === 'current_user_id');
  const centerX = homePlanet?.x || 100;
  const centerY = homePlanet?.y || 200;
  const centerZ = homePlanet?.z || 300;

  useEffect(() => {
    fetchSystemPlanets();
  }, [system]);

  const fetchSystemPlanets = async () => {
    try {
      console.log('🌌 Fetching system planets:', `http://localhost:5000/api/galaxy/system/${system.x}/${system.y}/${system.z}`);

      // Get JWT token from localStorage (following fleet test pattern)
      const token = localStorage.getItem('token');
      console.log('DEBUG: JWT token present for system planets API:', !!token);

      const response = await fetch(`http://localhost:5000/api/galaxy/system/${system.x}/${system.y}/${system.z}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });

      console.log('DEBUG: System planets API response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ System planets fetched successfully:', data);
      setPlanets(data);
    } catch (error) {
      console.error('❌ Error fetching system planets:', {
        message: error.message,
        status: error.status,
        url: `http://localhost:5000/api/galaxy/system/${system.x}/${system.y}/${system.z}`
      });

      // Add fallback data for testing
      console.log('🔧 Using fallback empty planets data');
      setPlanets([]);
    }
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
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default GalaxyMap;
