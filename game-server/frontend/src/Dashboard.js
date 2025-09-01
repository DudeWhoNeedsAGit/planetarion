import React, { useState, useEffect } from 'react';
import axios from 'axios';
import FleetManagement from './FleetManagement';

function Dashboard({ user, onLogout }) {
  const [planets, setPlanets] = useState([]);
  const [selectedPlanet, setSelectedPlanet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    fetchPlanets();
  }, []);

  const fetchPlanets = async () => {
    try {
      const response = await axios.get('/api/planet');
      setPlanets(response.data);
      if (response.data.length > 0 && !selectedPlanet) {
        setSelectedPlanet(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching planets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBuildingUpgrade = async (buildingType, newLevel) => {
    if (!selectedPlanet) return;

    setUpgrading(true);
    try {
      const response = await axios.put('/api/planet/buildings', {
        planet_id: selectedPlanet.id,
        buildings: {
          [buildingType]: newLevel
        }
      });

      // Update the selected planet with new data
      setSelectedPlanet(prev => ({
        ...prev,
        resources: response.data.resources,
        structures: response.data.structures
      }));

      // Update planets list
      setPlanets(prev => prev.map(p =>
        p.id === selectedPlanet.id
          ? { ...p, resources: response.data.resources, structures: response.data.structures }
          : p
      ));

      alert('Building upgraded successfully!');
    } catch (error) {
      alert(error.response?.data?.error || 'Upgrade failed');
    } finally {
      setUpgrading(false);
    }
  };

  const calculateUpgradeCost = (buildingType, currentLevel) => {
    const newLevel = currentLevel + 1;
    const costMultiplier = 1.5 ** (newLevel - 1);

    switch (buildingType) {
      case 'metal_mine':
      case 'crystal_mine':
        return {
          metal: Math.floor(60 * costMultiplier),
          crystal: Math.floor(15 * costMultiplier),
          deuterium: 0
        };
      case 'deuterium_synthesizer':
        return {
          metal: Math.floor(225 * costMultiplier),
          crystal: Math.floor(75 * costMultiplier),
          deuterium: 0
        };
      case 'solar_plant':
        return {
          metal: Math.floor(75 * costMultiplier),
          crystal: Math.floor(30 * costMultiplier),
          deuterium: 0
        };
      case 'fusion_reactor':
        return {
          metal: Math.floor(900 * costMultiplier),
          crystal: Math.floor(360 * costMultiplier),
          deuterium: Math.floor(180 * costMultiplier)
        };
      default:
        return { metal: 0, crystal: 0, deuterium: 0 };
    }
  };

  const canAffordUpgrade = (buildingType, currentLevel) => {
    if (!selectedPlanet) return false;

    const cost = calculateUpgradeCost(buildingType, currentLevel);
    return (
      selectedPlanet.resources.metal >= cost.metal &&
      selectedPlanet.resources.crystal >= cost.crystal &&
      selectedPlanet.resources.deuterium >= cost.deuterium
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-space-dark flex items-center justify-center">
        <div className="text-xl">Loading your empire...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-space-dark">
      <header className="bg-space-blue p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-3xl font-bold">🌌 Planetarion</h1>
          <div className="flex items-center space-x-4">
            <span className="text-white">Welcome, {user.username}!</span>
            <button
              onClick={onLogout}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto p-6">
        {/* Planet Selection */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-4 text-white">Your Planets</h2>
          <div className="flex space-x-4 overflow-x-auto">
            {planets.map(planet => (
              <button
                key={planet.id}
                onClick={() => setSelectedPlanet(planet)}
                className={`px-4 py-2 rounded whitespace-nowrap ${
                  selectedPlanet?.id === planet.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {planet.name} ({planet.coordinates})
              </button>
            ))}
          </div>
        </div>

        {selectedPlanet && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Resources */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-bold mb-4 text-white">Resources</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-metal">Metal:</span>
                  <span className="text-metal font-bold">
                    {selectedPlanet.resources.metal.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-crystal">Crystal:</span>
                  <span className="text-crystal font-bold">
                    {selectedPlanet.resources.crystal.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-deuterium">Deuterium:</span>
                  <span className="text-deuterium font-bold">
                    {selectedPlanet.resources.deuterium.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Production Rates */}
              <div className="mt-6">
                <h4 className="text-lg font-semibold mb-3 text-white">Production Rates</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-metal">Metal/hour:</span>
                    <span className="text-metal">{selectedPlanet.production_rates?.metal_per_hour || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-crystal">Crystal/hour:</span>
                    <span className="text-crystal">{selectedPlanet.production_rates?.crystal_per_hour || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-deuterium">Deuterium/hour:</span>
                    <span className="text-deuterium">{selectedPlanet.production_rates?.deuterium_per_hour || 0}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Buildings */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-bold mb-4 text-white">Buildings</h3>
              <div className="space-y-4">
                {[
                  { key: 'metal_mine', name: 'Metal Mine', icon: '⛏️' },
                  { key: 'crystal_mine', name: 'Crystal Mine', icon: '💎' },
                  { key: 'deuterium_synthesizer', name: 'Deuterium Synthesizer', icon: '⚡' },
                  { key: 'solar_plant', name: 'Solar Plant', icon: '☀️' },
                  { key: 'fusion_reactor', name: 'Fusion Reactor', icon: '🔥' }
                ].map(building => (
                  <div key={building.key} className="bg-gray-700 p-3 rounded">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-white font-medium">
                        {building.icon} {building.name}
                      </span>
                      <span className="text-gray-300">
                        Level {selectedPlanet.structures[building.key]}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <div className="text-xs text-gray-400">
                        Cost: {Object.entries(calculateUpgradeCost(building.key, selectedPlanet.structures[building.key]))
                          .filter(([_, cost]) => cost > 0)
                          .map(([resource, cost]) => `${resource}: ${cost.toLocaleString()}`)
                          .join(', ')}
                      </div>
                      <button
                        onClick={() => handleBuildingUpgrade(building.key, selectedPlanet.structures[building.key] + 1)}
                        disabled={upgrading || !canAffordUpgrade(building.key, selectedPlanet.structures[building.key])}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white text-sm rounded"
                      >
                        {upgrading ? 'Upgrading...' : 'Upgrade'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Fleet Management */}
        <div className="mt-8">
          <FleetManagement user={user} planets={planets} />
        </div>

        {/* Universe Stats */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4 text-deuterium">📊 Universe Stats</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-metal">{planets.length}</div>
              <div className="text-sm text-gray-400">Your Planets</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-crystal">
                {planets.reduce((sum, p) => sum + p.resources.metal + p.resources.crystal + p.resources.deuterium, 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-400">Total Resources</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-deuterium">
                {planets.reduce((sum, p) => sum + p.production_rates?.metal_per_hour + p.production_rates?.crystal_per_hour + p.production_rates?.deuterium_per_hour || 0, 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-400">Hourly Production</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
