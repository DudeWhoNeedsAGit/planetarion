import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Navigation from './Navigation';
import Overview from './Overview';
import FleetManagement from './FleetManagement';
import LuckyWheel from './LuckyWheel';
import GalaxyMap from './GalaxyMap';
import ChatPanel from './ChatPanel';
import { useToast } from './ToastContext';
import AnimatedButton from './AnimatedButton';

function Dashboard({ user, onLogout }) {
  const [activeSection, setActiveSection] = useState('overview');
  const [planets, setPlanets] = useState([]);
  const [selectedPlanet, setSelectedPlanet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [pollingInterval, setPollingInterval] = useState(null);
  const [chatMinimized, setChatMinimized] = useState(false);
  const { showSuccess, showError } = useToast();

  useEffect(() => {
    fetchPlanets(); // Initial fetch

    // Start polling every 10 seconds for real-time updates
    const interval = setInterval(fetchPlanets, 10000);
    setPollingInterval(interval);

    // Cleanup interval on unmount
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, []);

  // Update selected planet when planets data changes
  useEffect(() => {
    if (planets.length > 0 && !selectedPlanet) {
      setSelectedPlanet(planets[0]);
    } else if (selectedPlanet) {
      // Update selected planet with latest data
      const updatedPlanet = planets.find(p => p.id === selectedPlanet.id);
      if (updatedPlanet) {
        setSelectedPlanet(updatedPlanet);
      }
    }
  }, [planets, selectedPlanet]);

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

      showSuccess('Building upgraded successfully!');
    } catch (error) {
      showError(error.response?.data?.error || 'Upgrade failed');
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

  const calculateProductionRate = (buildingType, level) => {
    // Calculate production per tick (5 seconds) using divisor 72
    const baseRate = buildingType === 'metal_mine' ? 30 :
                     buildingType === 'crystal_mine' ? 20 :
                     buildingType === 'deuterium_synthesizer' ? 10 : 0;

    const hourlyRate = level * baseRate * Math.pow(1.1, level);
    const perTickRate = Math.max(1, Math.floor(hourlyRate / 72));

    return {
      perTick: perTickRate,
      perHour: Math.floor(hourlyRate)
    };
  };

  const getProductionIncrease = (buildingType, currentLevel) => {
    const current = calculateProductionRate(buildingType, currentLevel);
    const next = calculateProductionRate(buildingType, currentLevel + 1);

    return {
      current: current.perTick,
      next: next.perTick,
      increase: next.perTick - current.perTick,
      currentHourly: current.perHour,
      nextHourly: next.perHour,
      increaseHourly: next.perHour - current.perHour
    };
  };

  const getAllProductionChanges = (buildingType, currentLevel) => {
    const changes = {
      metal: { current: 0, next: 0, increase: 0 },
      crystal: { current: 0, next: 0, increase: 0 },
      deuterium: { current: 0, next: 0, increase: 0 }
    };

    // Calculate production for each resource type
    const resourceTypes = ['metal_mine', 'crystal_mine', 'deuterium_synthesizer'];

    resourceTypes.forEach(resourceType => {
      const production = getProductionIncrease(resourceType, currentLevel);

      if (resourceType === 'metal_mine') {
        changes.metal = {
          current: production.currentHourly,
          next: production.nextHourly,
          increase: production.increaseHourly
        };
      } else if (resourceType === 'crystal_mine') {
        changes.crystal = {
          current: production.currentHourly,
          next: production.nextHourly,
          increase: production.increaseHourly
        };
      } else if (resourceType === 'deuterium_synthesizer') {
        changes.deuterium = {
          current: production.currentHourly,
          next: production.nextHourly,
          increase: production.increaseHourly
        };
      }
    });

    return changes;
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

  const handleBuildShip = async (shipType, quantity) => {
    if (!selectedPlanet) return;

    setUpgrading(true);
    try {
      const response = await axios.post('/api/shipyard/build', {
        planet_id: selectedPlanet.id,
        ship_type: shipType,
        quantity: quantity
      });

      // Update the selected planet with new resources
      setSelectedPlanet(prev => ({
        ...prev,
        resources: response.data.planet_resources
      }));

      // Update planets list
      setPlanets(prev => prev.map(p =>
        p.id === selectedPlanet.id
          ? { ...p, resources: response.data.planet_resources }
          : p
      ));

      showSuccess(response.data.message);
    } catch (error) {
      showError(error.response?.data?.error || 'Ship building failed');
    } finally {
      setUpgrading(false);
    }
  };

  const canAffordShip = (shipType, quantity) => {
    if (!selectedPlanet) return false;

    const costs = {
      'colony_ship': {
        metal: 10000 * quantity,
        crystal: 20000 * quantity,
        deuterium: 10000 * quantity
      }
    };

    const cost = costs[shipType];
    return (
      selectedPlanet.resources.metal >= cost.metal &&
      selectedPlanet.resources.crystal >= cost.crystal &&
      selectedPlanet.resources.deuterium >= cost.deuterium
    );
  };

  // Energy calculation functions
  const calculateEnergyStats = (planet) => {
    if (!planet) return null;

    const energyProduction = planet.structures.solar_plant * 20 + planet.structures.fusion_reactor * 50;
    const energyConsumption = (
      planet.structures.metal_mine * 10 +
      planet.structures.crystal_mine * 10 +
      planet.structures.deuterium_synthesizer * 20
    );

    const energyRatio = energyConsumption > 0 ? energyProduction / energyConsumption : 1;
    const status = energyRatio >= 1.2 ? 'surplus' :
                   energyRatio >= 1.0 ? 'balanced' : 'deficit';

    return {
      production: energyProduction,
      consumption: energyConsumption,
      ratio: energyRatio,
      status: status,
      efficiency: Math.min(1.0, energyRatio)
    };
  };

  const calculateUpgradeEnergyImpact = (buildingType, currentLevel, planet) => {
    if (!planet) return null;

    const newLevel = currentLevel + 1;
    const currentConsumption = (
      planet.structures.metal_mine * 10 +
      planet.structures.crystal_mine * 10 +
      planet.structures.deuterium_synthesizer * 20
    );

    let additionalConsumption = 0;
    if (buildingType === 'metal_mine' || buildingType === 'crystal_mine') {
      additionalConsumption = 10;
    } else if (buildingType === 'deuterium_synthesizer') {
      additionalConsumption = 20;
    }

    const newConsumption = currentConsumption + additionalConsumption;
    const energyProduction = planet.structures.solar_plant * 20 + planet.structures.fusion_reactor * 50;
    const newRatio = newConsumption > 0 ? energyProduction / newConsumption : 1;

    return {
      additionalConsumption: additionalConsumption,
      newConsumption: newConsumption,
      newRatio: newRatio,
      status: newRatio >= 1.2 ? 'surplus' :
              newRatio >= 1.0 ? 'balanced' : 'deficit'
    };
  };

  const getEnergyStatusIcon = (status) => {
    switch (status) {
      case 'surplus': return '🟢';
      case 'balanced': return '🟡';
      case 'deficit': return '🔴';
      default: return '⚪';
    }
  };

  const getEnergyStatusColor = (status) => {
    switch (status) {
      case 'surplus': return 'text-green-400';
      case 'balanced': return 'text-yellow-400';
      case 'deficit': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const calculateTheoreticalProduction = (buildingType, level) => {
    const baseRate = buildingType === 'metal_mine' ? 30 :
                     buildingType === 'crystal_mine' ? 20 :
                     buildingType === 'deuterium_synthesizer' ? 10 : 0;
    return level * baseRate * Math.pow(1.1, level);
  };

  const calculateActualProduction = (theoreticalRate, energyEfficiency) => {
    return theoreticalRate * energyEfficiency;
  };

  const renderSection = () => {
    switch (activeSection) {
      case 'overview':
        return <Overview user={user} planets={planets} />;
      case 'galaxy':
        return <GalaxyMap user={user} planets={planets} onClose={() => setActiveSection('overview')} />;
      case 'planets':
        return (
          <div className="space-y-6">
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

                  {/* Current Energy Status Overview */}
                  {(() => {
                    const energyStats = calculateEnergyStats(selectedPlanet);
                    return energyStats ? (
                      <div className="mb-6 p-4 bg-gray-700 rounded-lg border border-gray-600">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-white font-medium flex items-center">
                            <span className="mr-2">⚡</span>
                            Energy Status
                          </h4>
                          <span className={`text-sm font-bold px-2 py-1 rounded ${getEnergyStatusColor(energyStats.status)} bg-opacity-20`}>
                            {getEnergyStatusIcon(energyStats.status)} {energyStats.status.toUpperCase()}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="text-gray-400">Production</div>
                            <div className="text-green-400 font-medium">{energyStats.production}</div>
                          </div>
                          <div>
                            <div className="text-gray-400">Consumption</div>
                            <div className="text-red-400 font-medium">{energyStats.consumption}</div>
                          </div>
                        </div>

                        <div className="mt-3 pt-3 border-t border-gray-600">
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-gray-400">Efficiency Ratio</span>
                            <span className={`${getEnergyStatusColor(energyStats.status)} font-medium`}>
                              {(energyStats.ratio * 100).toFixed(1)}%
                            </span>
                          </div>
                          {energyStats.status === 'deficit' && (
                            <div className="mt-2 text-orange-400 text-xs">
                              ⚠️ Your mines are operating at reduced efficiency due to insufficient energy
                            </div>
                          )}
                        </div>
                      </div>
                    ) : null;
                  })()}

                  <div className="space-y-4">
                    {[
                      { key: 'metal_mine', name: 'Metal Mine', icon: '⛏️' },
                      { key: 'crystal_mine', name: 'Crystal Mine', icon: '💎' },
                      { key: 'deuterium_synthesizer', name: 'Deuterium Synthesizer', icon: '⚡' },
                      { key: 'solar_plant', name: 'Solar Plant', icon: '☀️' },
                      { key: 'fusion_reactor', name: 'Fusion Reactor', icon: '🔥' }
                    ].map(building => {
                      const currentLevel = selectedPlanet.structures[building.key];
                      const energyStats = calculateEnergyStats(selectedPlanet);
                      const energyImpact = calculateUpgradeEnergyImpact(building.key, currentLevel, selectedPlanet);

                      // Enhanced production calculations with energy awareness
                      const isProductionBuilding = ['metal_mine', 'crystal_mine', 'deuterium_synthesizer'].includes(building.key);
                      let productionInfo = null;

                      if (isProductionBuilding) {
                        const currentTheoretical = calculateTheoreticalProduction(building.key, currentLevel);
                        const nextTheoretical = calculateTheoreticalProduction(building.key, currentLevel + 1);
                        const currentActual = calculateActualProduction(currentTheoretical, energyStats?.efficiency || 1);
                        const nextActual = calculateActualProduction(nextTheoretical, energyImpact?.newRatio || 1);

                        productionInfo = {
                          current: {
                            theoretical: Math.floor(currentTheoretical),
                            actual: Math.floor(currentActual)
                          },
                          next: {
                            theoretical: Math.floor(nextTheoretical),
                            actual: Math.floor(nextActual)
                          },
                          increase: {
                            theoretical: Math.floor(nextTheoretical - currentTheoretical),
                            actual: Math.floor(nextActual - currentActual)
                          }
                        };
                      }

                      return (
                        <div key={building.key} className="bg-gray-700 p-4 rounded group relative">
                          {/* Building Header */}
                          <div className="flex justify-between items-center mb-3">
                            <span className="text-white font-medium">
                              {building.icon} {building.name}
                            </span>
                            <span className="text-gray-300">
                              Level {currentLevel} → {currentLevel + 1}
                            </span>
                          </div>

                          {/* Energy Impact Warning */}
                          {energyImpact && energyImpact.additionalConsumption > 0 && (
                            <div className="mb-3 p-2 bg-yellow-900/30 border border-yellow-600/30 rounded">
                              <div className="flex items-center text-yellow-400 text-xs mb-1">
                                ⚠️ Energy Impact
                              </div>
                              <div className="text-xs text-gray-300">
                                +{energyImpact.additionalConsumption} energy consumption
                                <span className={`ml-2 ${getEnergyStatusColor(energyImpact.status)}`}>
                                  → {getEnergyStatusIcon(energyImpact.status)} {energyImpact.status.toUpperCase()}
                                </span>
                              </div>
                            </div>
                          )}

                          {/* Production Information */}
                          {productionInfo && (
                            <div className="mb-3 p-2 bg-blue-900/20 border border-blue-600/30 rounded">
                              <div className="text-xs text-blue-400 mb-1">📊 Production Rates</div>
                              <div className="text-xs text-gray-300 space-y-1">
                                <div>
                                  Current: {productionInfo.current.actual}/hour
                                  <span className="text-gray-500"> ({productionInfo.current.theoretical} theoretical)</span>
                                </div>
                                <div>
                                  After Upgrade: {productionInfo.next.actual}/hour
                                  <span className="text-gray-500"> ({productionInfo.next.theoretical} theoretical)</span>
                                  <span className="text-green-400 ml-1">+{productionInfo.increase.actual}</span>
                                </div>
                                {energyImpact && energyImpact.newRatio < 1 && (
                                  <div className="text-orange-400">
                                    ⚠️ Reduced by {(100 - energyImpact.newRatio * 100).toFixed(1)}% due to energy shortage
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Upgrade Cost */}
                          <div className="mb-3">
                            <div className="text-xs text-gray-400 mb-1">💰 Upgrade Cost</div>
                            <div className="text-xs text-yellow-400">
                              {Object.entries(calculateUpgradeCost(building.key, currentLevel))
                                .filter(([_, cost]) => cost > 0)
                                .map(([resource, cost]) => `${resource}: ${cost.toLocaleString()}`)
                                .join(' | ')}
                            </div>
                          </div>

                          {/* Upgrade Button */}
                          <div className="flex justify-end">
                            <button
                              onClick={() => handleBuildingUpgrade(building.key, currentLevel + 1)}
                              disabled={upgrading || !canAffordUpgrade(building.key, currentLevel)}
                              className={`px-4 py-2 text-white text-sm rounded hover:scale-105 transition-transform ${
                                energyImpact?.status === 'deficit'
                                  ? 'bg-orange-600 hover:bg-orange-700'
                                  : 'bg-green-600 hover:bg-green-700'
                              } disabled:bg-gray-600`}
                              title={
                                energyImpact?.status === 'deficit'
                                  ? 'Warning: This upgrade will cause energy deficit!'
                                  : 'Upgrade building'
                              }
                            >
                              {upgrading ? 'Upgrading...' : 'Upgrade'}
                            </button>
                          </div>

                          {/* Enhanced Tooltip on Hover */}
                          <div className="absolute left-full ml-2 top-0 w-80 bg-gray-900 border border-gray-600 rounded-lg p-3 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10 shadow-lg">
                            <div className="text-white font-medium mb-2">{building.icon} {building.name} Upgrade</div>

                            {/* Detailed Energy Analysis */}
                            {energyImpact && (
                              <div className="mb-3">
                                <div className="text-blue-400 text-sm font-medium mb-1">⚡ Energy Analysis</div>
                                <div className="text-xs text-gray-300 space-y-1">
                                  <div>Current: {energyStats?.production || 0} produced, {energyStats?.consumption || 0} consumed</div>
                                  <div>After Upgrade: {energyStats?.production || 0} produced, {energyImpact.newConsumption} consumed</div>
                                  <div className={getEnergyStatusColor(energyImpact.status)}>
                                    Status: {energyImpact.status.toUpperCase()} ({(energyImpact.newRatio * 100).toFixed(1)}% efficiency)
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Production Breakdown */}
                            {productionInfo && (
                              <div className="mb-3">
                                <div className="text-green-400 text-sm font-medium mb-1">📈 Production Impact</div>
                                <div className="text-xs text-gray-300 space-y-1">
                                  <div>Theoretical: +{productionInfo.increase.theoretical}/hour</div>
                                  <div>Actual: +{productionInfo.increase.actual}/hour</div>
                                  {energyImpact && energyImpact.newRatio < 1 && (
                                    <div className="text-orange-400">
                                      ⚠️ Production will be reduced by {(100 - energyImpact.newRatio * 100).toFixed(1)}% due to insufficient energy
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Strategic Advice */}
                            <div className="text-purple-400 text-sm font-medium mb-1">💡 Strategic Advice</div>
                            <div className="text-xs text-gray-300">
                              {energyImpact?.status === 'deficit'
                                ? 'Consider upgrading solar plants or fusion reactors first to avoid production penalties.'
                                : 'This upgrade looks good! Your energy production can handle it.'}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      case 'fleets':
        return <FleetManagement user={user} planets={planets} />;
      case 'wheel':
        return (
          <div className="max-w-md mx-auto">
            <LuckyWheel
              planets={planets}
              selectedPlanet={selectedPlanet}
              onBuffApplied={(multiplier, duration) => {
                // For now, just show a success message
                // In the future, this could apply actual buffs to production
                showSuccess(`🎉 Production boosted by ${multiplier}x for ${Math.floor(duration / 60000)} minutes!`);
              }}
            />
          </div>
        );
      case 'research':
        return (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-4 text-white">🔬 Research Lab</h3>
            <div className="text-center text-gray-400 py-8">
              Research system coming soon! This will include technologies like:
              <ul className="mt-4 space-y-2">
                <li>• Energy Technology</li>
                <li>• Laser Technology</li>
                <li>• Ion Technology</li>
                <li>• Hyperspace Technology</li>
                <li>• Plasma Technology</li>
              </ul>
            </div>
          </div>
        );
      case 'shipyard':
        return (
          <div className="space-y-6">
            {/* Shipyard Header */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-bold mb-4 text-white">🚀 Shipyard</h3>
              <p className="text-gray-400">Build ships to expand your fleet and colonize new planets</p>
            </div>

            {/* Planet Selection for Shipyard */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h4 className="text-lg font-semibold mb-4 text-white">Select Planet</h4>
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

            {/* Ship Construction */}
            {selectedPlanet && (
              <div className="bg-gray-800 rounded-lg p-6">
                <h4 className="text-lg font-semibold mb-4 text-white">Build Ships</h4>

                {/* Colony Ship */}
                <div className="bg-gray-700 p-4 rounded mb-4">
                  <div className="flex justify-between items-center mb-3">
                    <div>
                      <h5 className="text-white font-medium">🚁 Colony Ship</h5>
                      <p className="text-gray-400 text-sm">Essential for establishing new colonies</p>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-400">Cost per ship:</div>
                      <div className="text-yellow-400 text-sm">
                        10,000 Metal<br/>
                        20,000 Crystal<br/>
                        10,000 Deuterium
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <div className="text-sm text-gray-300">
                      Available Resources: {selectedPlanet.resources.metal.toLocaleString()} Metal, {selectedPlanet.resources.crystal.toLocaleString()} Crystal, {selectedPlanet.resources.deuterium.toLocaleString()} Deuterium
                    </div>
                    <button
                      onClick={() => handleBuildShip('colony_ship', 1)}
                      disabled={upgrading || !canAffordShip('colony_ship', 1)}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded"
                    >
                      {upgrading ? 'Building...' : 'Build 1 Colony Ship'}
                    </button>
                  </div>
                </div>

                {/* Build Multiple */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {[5, 10, 25, 50].map(quantity => (
                    <button
                      key={quantity}
                      onClick={() => handleBuildShip('colony_ship', quantity)}
                      disabled={upgrading || !canAffordShip('colony_ship', quantity)}
                      className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white text-sm rounded"
                    >
                      Build {quantity}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      case 'alliance':
        return (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-4 text-white">🤝 Alliance Center</h3>
            <div className="text-center text-gray-400 py-8">
              Alliance system coming soon! This will include:
              <ul className="mt-4 space-y-2">
                <li>• Alliance creation and management</li>
                <li>• Member recruitment</li>
                <li>• Internal messaging</li>
                <li>• Alliance diplomacy</li>
                <li>• Shared resources</li>
              </ul>
            </div>
          </div>
        );
      case 'messages':
        return (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-4 text-white">💬 Messages</h3>
            <div className="text-center text-gray-400 py-8">
              Messaging system coming soon! This will include:
              <ul className="mt-4 space-y-2">
                <li>• Private messages</li>
                <li>• Alliance messages</li>
                <li>• System notifications</li>
                <li>• Battle reports</li>
                <li>• Espionage reports</li>
              </ul>
            </div>
          </div>
        );
      default:
        return <Overview user={user} planets={planets} />;
    }
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

      <Navigation activeSection={activeSection} onSectionChange={setActiveSection} />

      <main className="container mx-auto p-6">
        {renderSection()}
      </main>

      {/* Global Chat Panel */}
      <ChatPanel
        isMinimized={chatMinimized}
        onToggleMinimize={() => setChatMinimized(!chatMinimized)}
      />
    </div>
  );
}

export default Dashboard;
