import React, { useState, useEffect } from 'react';
import axios from 'axios';

function GalaxyMap({ user, planets, onClose }) {
  const [systems, setSystems] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [loading, setLoading] = useState(false);

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
    fetchNearbySystems();
  }, [centerX, centerY, centerZ]);

  const fetchNearbySystems = async () => {
    try {
      console.log('🌌 Fetching nearby systems:', `http://localhost:5000/api/galaxy/nearby/${centerX}/${centerY}/${centerZ}`);

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
      console.log('✅ Systems fetched successfully:', data);
      setSystems(data);
    } catch (error) {
      console.error('❌ Error fetching systems:', {
        message: error.message,
        status: error.status,
        url: `http://localhost:5000/api/galaxy/nearby/${centerX}/${centerY}/${centerZ}`
      });

      // Add fallback data for testing (following fleet pattern)
      console.log('🔧 Using fallback test data');
      setSystems([
        { x: centerX + 10, y: centerY + 20, z: centerZ + 30, explored: false, planets: 0 },
        { x: centerX - 15, y: centerY - 25, z: centerZ - 35, explored: true, planets: 0 },
        { x: centerX + 40, y: centerY + 50, z: centerZ + 60, explored: false, planets: 0 }
      ]);
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full max-h-96 overflow-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-white">Galaxy Map</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        <div className="mb-4 text-sm text-gray-300">
          Center: {centerX}:{centerY}:{centerZ} | Exploration Range: 50 units
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {systems.map((system, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                system.explored
                  ? 'bg-blue-900 border-blue-600 hover:bg-blue-800'
                  : 'bg-gray-700 border-gray-600 hover:bg-gray-600'
              }`}
              onClick={() => handleExploreSystem(system)}
            >
              <div className="text-white font-medium">
                {system.x}:{system.y}:{system.z}
              </div>
              <div className="text-sm text-gray-300">
                {system.explored ? (
                  `${system.planets} planets discovered`
                ) : (
                  'Unexplored system'
                )}
              </div>
              <div className="mt-2">
                <button
                  className={`px-3 py-1 text-xs rounded ${
                    system.explored
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-yellow-600 hover:bg-yellow-700'
                  }`}
                  disabled={loading}
                >
                  {system.explored ? 'View System' : 'Explore'}
                </button>
              </div>
            </div>
          ))}
        </div>

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

function SystemDetails({ system, onClose, onColonize, loading }) {
  const [planets, setPlanets] = useState([]);

  useEffect(() => {
    fetchSystemPlanets();
  }, [system]);

  const fetchSystemPlanets = async () => {
    try {
      console.log('🌌 Fetching system planets:', `http://localhost:5000/api/galaxy/system/${system.x}/${system.y}/${system.z}`);

      // Get JWT token from localStorage (following fleet pattern)
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

      // Add fallback empty array for testing
      console.log('🔧 Using fallback empty planets data');
      setPlanets([]);
    }
  };

  return (
    <div className="mt-6 p-4 bg-gray-700 rounded-lg">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-white">
          System {system.x}:{system.y}:{system.z}
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white"
        >
          ✕
        </button>
      </div>

      {planets.length === 0 ? (
        <div className="text-gray-400">No planets discovered yet</div>
      ) : (
        <div className="space-y-2">
          {planets.map(planet => (
            <div key={planet.id} className="flex justify-between items-center p-2 bg-gray-600 rounded">
              <div>
                <div className="text-white font-medium">{planet.name}</div>
                <div className="text-sm text-gray-300">
                  {planet.owner_name ? `Owned by ${planet.owner_name}` : 'Unowned'}
                </div>
              </div>
              {!planet.user_id && (
                <button
                  onClick={() => onColonize(planet)}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded"
                  disabled={loading}
                >
                  Colonize
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default GalaxyMap;
