import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Navigation from './Navigation';
import Overview from './Overview';
import FleetManagement from './FleetManagement';
import LuckyWheel from './LuckyWheel';
import GalaxyMap from './GalaxyMap';
import CombatDashboard from './CombatDashboard';
import ChatPanel from './ChatPanel';
import ShipStats from './ShipStats';
import ResearchDashboard from './ResearchDashboard';
import { useToast } from './ToastContext';
import AnimatedButton from './AnimatedButton';
import planetarionLogo from './assets/branding/planetarion-logo.png';
import CommanderPortrait from './CommanderPortrait';
import BackgroundMusicToggle from './BackgroundMusicToggle';

function Dashboard({ user, onLogout, onUserRefresh = null }) {
  const [activeSection, setActiveSection] = useState('overview');
  const [planets, setPlanets] = useState([]);
  const [selectedPlanet, setSelectedPlanet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [upgrading, setUpgrading] = useState(false);
  const [pollingInterval, setPollingInterval] = useState(null);
  const [chatMinimized, setChatMinimized] = useState(false);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [renaming, setRenaming] = useState(false);
  const { showSuccess, showError } = useToast();
  const idleGains = user?.idle_gains || null;
  const [portraitKey, setPortraitKey] = useState(() => user?.portrait_key || 'male');
  const [portraitSize, setPortraitSize] = useState(() => (window.innerWidth < 640 ? 72 : 108));

  useEffect(() => {
    setPortraitKey(user?.portrait_key || 'male');
  }, [user?.portrait_key]);

  useEffect(() => {
    const onResize = () => setPortraitSize(window.innerWidth < 640 ? 72 : 108);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const updatePortraitKey = async (nextKey) => {
    const key = String(nextKey || '').toLowerCase();
    setPortraitKey(key);
    try {
      await axios.patch('/api/auth/me', { portrait_key: key });
      if (typeof onUserRefresh === 'function') await onUserRefresh();
      showSuccess('Commander portrait updated.');
    } catch (e) {
      showError('Failed to update commander portrait.');
    }
  };

  const formatDuration = (seconds) => {
    const s = Math.max(0, Number(seconds || 0));
    const m = Math.floor(s / 60);
    const h = Math.floor(m / 60);
    if (h > 0) return `${h}h ${m % 60}m`;
    if (m > 0) return `${m}m`;
    return `${Math.floor(s)}s`;
  };

		  const shouldShowIdleSummary = () => {
		    if (!idleGains) return false;
		    if (Number(idleGains.duration_seconds || 0) < 120) return false;
		    const r = idleGains.resources || {};
		    const hasRes = (r.metal || 0) + (r.crystal || 0) + (r.deuterium || 0) > 0;
		    const hasRp = Number(idleGains.research_points || 0) > 0;
		    const ev = idleGains.events || {};
		    const hasEvents = Number(ev.fleets_resolved || 0) + Number(ev.research_completed || 0) > 0;
		    return hasRes || hasRp || hasEvents;
		  };

		  const renderCommanderXpBar = () => {
		    const xpProgress = user?.commander_xp_progress || null;
		    if (!xpProgress) return null;
		    const into = Math.max(0, Number(xpProgress.into_level ?? 0));
		    const toNext = Math.max(0, Number(xpProgress.to_next ?? 0));
		    if (!(toNext > 0)) return null;
		    const pct = Math.max(0, Math.min(100, Math.floor((into / toNext) * 100)));

		    return (
		      <div className="mt-1.5" data-testid="commander-xp-bar">
		        <div className="flex items-center justify-between text-[11px] text-slate-300/80">
		          <span>XP</span>
		          <span className="text-slate-100/90 font-semibold">
		            {into.toLocaleString()} / {toNext.toLocaleString()} • {pct}%
		          </span>
		        </div>
		        <div className="mt-1 h-2 rounded-full bg-slate-900/60 border border-slate-200/10 overflow-hidden">
		          <div
		            className="h-full rounded-full"
		            style={{
		              width: `${pct}%`,
		              background: 'rgba(37, 99, 235, 0.85)',
		              boxShadow: '0 0 16px rgba(37, 99, 235, 0.35)',
		            }}
		          />
		        </div>
		      </div>
		    );
		  };

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
      setLoadError(null);
      const response = await axios.get('/api/planet', { timeout: 10000 });
      setPlanets(response.data);
      if (response.data.length > 0 && !selectedPlanet) {
        setSelectedPlanet(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching planets:', error);
      const message = error.response?.data?.error || error.message || 'Failed to load planets';
      setLoadError(message);
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
      case 'research_lab':
        return {
          metal: Math.floor(200 * costMultiplier),
          crystal: Math.floor(100 * costMultiplier),
          deuterium: Math.floor(50 * costMultiplier)
        };
      case 'metal_storage':
      case 'crystal_storage':
      case 'deuterium_tank':
        return {
          metal: Math.floor(100 * costMultiplier),
          crystal: Math.floor(50 * costMultiplier),
          deuterium: 0
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

  const [shipCosts, setShipCosts] = useState({});
  const [shipStats, setShipStats] = useState({});
  const [shipRoles, setShipRoles] = useState([]);
  const [selectedShipRole, setSelectedShipRole] = useState('all');
  const [shipBuildQuantities, setShipBuildQuantities] = useState({});

  // Fetch ship data on component mount
  useEffect(() => {
    const fetchShipData = async () => {
      try {
        // Fetch ship costs
        const costsResponse = await axios.get('/api/shipyard/costs');
        setShipCosts(costsResponse.data);

        // Fetch ship statistics
        const statsResponse = await axios.get('/api/shipyard/stats');
        setShipStats(statsResponse.data);

        // Fetch ship roles
        const rolesResponse = await axios.get('/api/shipyard/roles');
        setShipRoles(rolesResponse.data.roles || []);
      } catch (error) {
        console.error('Error fetching ship data:', error);
      }
    };
    fetchShipData();
  }, []);

  const canAffordShip = (shipType, quantity) => {
    if (!selectedPlanet || !shipCosts[shipType]) return false;

    const cost = shipCosts[shipType];
    return (
      selectedPlanet.resources.metal >= (cost.metal * quantity) &&
      selectedPlanet.resources.crystal >= (cost.crystal * quantity) &&
      selectedPlanet.resources.deuterium >= (cost.deuterium * quantity)
    );
  };

  const getMaxBuildableShipCount = (shipType) => {
    if (!selectedPlanet || !shipCosts[shipType]) return 0;
    const cost = shipCosts[shipType];
    const resources = selectedPlanet.resources || { metal: 0, crystal: 0, deuterium: 0 };

    const limits = [];
    if ((cost.metal || 0) > 0) limits.push(Math.floor((resources.metal || 0) / cost.metal));
    if ((cost.crystal || 0) > 0) limits.push(Math.floor((resources.crystal || 0) / cost.crystal));
    if ((cost.deuterium || 0) > 0) limits.push(Math.floor((resources.deuterium || 0) / cost.deuterium));

    if (limits.length === 0) return 0;
    const raw = Math.max(0, Math.min(...limits));
    // Guard against absurd sizes in UI; backend can still accept large numbers if desired.
    return Math.min(raw, 10_000_000);
  };

  const formatShipName = (shipType) => {
    return shipType.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const getShipIcon = (shipType) => {
    const icons = {
      'small_cargo': '🚚',
      'large_cargo': '🚛',
      'light_fighter': '🚀',
      'heavy_fighter': '✈️',
      'cruiser': '🚢',
      'battleship': '🛳️',
      'colony_ship': '🚁',
      'recycler': '♻️',
      'espionage_probe': '🛰️',
      'bomber': '💣',
      'destroyer': '💥',
      'deathstar': '⭐',
      'battlecruiser': '⚔️'
    };
    return icons[shipType] || '🚀';
  };

  // Energy calculation functions
  const calculateEnergyStats = (planet) => {
    if (!planet) return null;

    const energyProduction = planet.structures.solar_plant * 20 + planet.structures.fusion_reactor * 50;
    const energyConsumption = (
      planet.structures.metal_mine * 10 +
      planet.structures.crystal_mine * 10 +
      planet.structures.deuterium_synthesizer * 20 +
      (planet.structures.research_lab || 0) * 15
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
      planet.structures.deuterium_synthesizer * 20 +
      (planet.structures.research_lab || 0) * 15
    );

    let additionalConsumption = 0;
    if (buildingType === 'metal_mine' || buildingType === 'crystal_mine') {
      additionalConsumption = 10;
    } else if (buildingType === 'deuterium_synthesizer') {
      additionalConsumption = 20;
    } else if (buildingType === 'research_lab') {
      additionalConsumption = 15;
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
        return (
          <div data-testid="section-overview">
            <Overview user={user} planets={planets} onNavigateSection={setActiveSection} />
          </div>
        );
	      case 'planets':
	        return (
	          <div className="space-y-6" data-testid="section-planets">
	            {/* Planet Selection */}
	            <div className="mb-6">
	              <div className="flex items-center justify-between gap-4 mb-4">
	                <h2 className="text-2xl font-bold text-white flex items-center">
	                  🪐 Your Planets ({planets.length})
	                </h2>
	                <button
	                  type="button"
	                  className="pa-btn-secondary px-4 py-2"
	                  disabled={!selectedPlanet || renaming}
	                  onClick={() => {
	                    if (!selectedPlanet) return;
	                    setRenameValue(selectedPlanet.name || '');
	                    setShowRenameModal(true);
	                  }}
	                  data-testid="planet-rename-open"
	                >
	                  Rename
	                </button>
	              </div>
              {planets.length > 6 ? (
                <div className="pa-card p-4">
                  <label className="block text-sm text-slate-200/90 mb-2">Select planet</label>
                  <select
                    className="pa-input"
                    data-testid="planet-selector-dropdown"
                    value={selectedPlanet?.id ?? ''}
                    onChange={(e) => {
                      const id = parseInt(e.target.value, 10);
                      const p = planets.find((pl) => pl.id === id);
                      if (p) setSelectedPlanet(p);
                    }}
                  >
                    {planets.map((planet) => (
                      <option key={planet.id} value={planet.id}>
                        {(planet.is_home_planet ? '🏠 ' : '🌍 ') + planet.name} ({planet.x}:{planet.y}:{planet.z})
                      </option>
                    ))}
                  </select>
                  <div className="mt-2 text-xs text-slate-300/70">
                    Tip: You have {planets.length} planets — use the dropdown to switch quickly.
                  </div>
                </div>
              ) : (
                <div className="flex space-x-4 overflow-x-auto overflow-y-hidden max-w-full pb-1" data-testid="planet-selector-buttons">
                  {planets.map(planet => {
                    const isHomePlanet = planet.is_home_planet;
                    return (
                      <button
                        key={planet.id}
                        onClick={() => setSelectedPlanet(planet)}
                        className={`whitespace-nowrap transition-colors duration-150 ${
                          selectedPlanet?.id === planet.id
                            ? 'pa-btn-primary shadow-lg'
                            : 'pa-btn-secondary'
                        } ${isHomePlanet ? 'ring-2 ring-yellow-400' : 'ring-2 ring-green-400'}`}
                        title={isHomePlanet ? '🏠 Home Planet' : '🌍 Colony'}
                      >
                        <span className="flex items-center space-x-2">
                          <span>{isHomePlanet ? '🏠' : '🌍'}</span>
                          <span>{planet.name}</span>
                          <span className="text-xs opacity-75">({planet.x}:{planet.y}:{planet.z})</span>
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Planet Summary */}
              <div className="mt-4 flex items-center space-x-6 text-sm text-slate-300/70">
                <span className="flex items-center space-x-1">
                  <span className="w-3 h-3 bg-yellow-400 rounded-full"></span>
                  <span>Home Planet: {planets.filter(p => p.is_home_planet).length}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span className="w-3 h-3 bg-green-400 rounded-full"></span>
                  <span>Colonies: {planets.filter(p => !p.is_home_planet).length}</span>
                </span>
              </div>
            </div>

            {selectedPlanet && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
	                {/* Resources */}
	                <div className="pa-card p-6">
	                  <h3 className="text-xl font-bold mb-4 text-white">Resources</h3>
	                  <div className="space-y-3">
	                    <div className="flex justify-between items-center">
	                      <span className="text-metal">Metal:</span>
	                      <span className="text-metal font-bold">
	                        {selectedPlanet.resources.metal.toLocaleString()}
	                        {selectedPlanet.storage?.metal != null && (
	                          <span className="text-slate-300/70 text-xs font-normal ml-2">
	                            / {selectedPlanet.storage.metal.toLocaleString()}
	                          </span>
	                        )}
	                      </span>
	                    </div>
	                    <div className="flex justify-between items-center">
	                      <span className="text-crystal">Crystal:</span>
	                      <span className="text-crystal font-bold">
	                        {selectedPlanet.resources.crystal.toLocaleString()}
	                        {selectedPlanet.storage?.crystal != null && (
	                          <span className="text-slate-300/70 text-xs font-normal ml-2">
	                            / {selectedPlanet.storage.crystal.toLocaleString()}
	                          </span>
	                        )}
	                      </span>
	                    </div>
	                    <div className="flex justify-between items-center">
	                      <span className="text-deuterium">Deuterium:</span>
	                      <span className="text-deuterium font-bold">
	                        {selectedPlanet.resources.deuterium.toLocaleString()}
	                        {selectedPlanet.storage?.deuterium != null && (
	                          <span className="text-slate-300/70 text-xs font-normal ml-2">
	                            / {selectedPlanet.storage.deuterium.toLocaleString()}
	                          </span>
	                        )}
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
                <div className="pa-card p-6">
                  <h3 className="text-xl font-bold mb-4 text-white">Buildings</h3>

                  {/* Current Energy Status Overview */}
                  {(() => {
                    const energyStats = calculateEnergyStats(selectedPlanet);
                    return energyStats ? (
                      <div className="mb-6 p-4 pa-panel">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-white font-medium flex items-center">
                            <span className="mr-2">⚡</span>
                            Energy Status
                          </h4>
                          <span className={`text-sm font-bold px-2 py-1 rounded ${getEnergyStatusColor(energyStats.status)} bg-black/20`}>
                            {getEnergyStatusIcon(energyStats.status)} {energyStats.status.toUpperCase()}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="text-slate-300/70">Production</div>
                            <div className="text-green-400 font-medium">{energyStats.production}</div>
                          </div>
                          <div>
                            <div className="text-slate-300/70">Consumption</div>
                            <div className="text-red-400 font-medium">{energyStats.consumption}</div>
                          </div>
                        </div>

                        <div className="mt-3 pt-3 border-t border-slate-500/30">
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-slate-300/70">Efficiency Ratio</span>
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
                        { key: 'fusion_reactor', name: 'Fusion Reactor', icon: '🔥' },
                        { key: 'research_lab', name: 'Research Lab', icon: '🔬' },
                        { key: 'metal_storage', name: 'Metal Storage', icon: '🏪' },
                        { key: 'crystal_storage', name: 'Crystal Storage', icon: '🏪' },
                        { key: 'deuterium_tank', name: 'Deuterium Tank', icon: '🧪' }
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
                        <div key={building.key} className="pa-panel p-4 group relative">
                          {/* Building Header */}
                          <div className="flex justify-between items-center mb-3">
                            <span className="text-white font-medium">
                              {building.icon} {building.name}
                            </span>
                            <span className="text-slate-200/80">
                              Level {currentLevel} → {currentLevel + 1}
                            </span>
                          </div>

                          {/* Energy Impact Warning */}
                          {energyImpact && energyImpact.additionalConsumption > 0 && (
                            <div className="mb-3 p-2 bg-yellow-900/30 border border-yellow-600/30 rounded">
                              <div className="flex items-center text-yellow-400 text-xs mb-1">
                                ⚠️ Energy Impact
                              </div>
                              <div className="text-xs text-slate-200/80">
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
                              <div className="text-xs text-slate-200/80 space-y-1">
                                <div>
                                  Current: {productionInfo.current.actual}/hour
                                  <span className="text-slate-300/60"> ({productionInfo.current.theoretical} theoretical)</span>
                                </div>
                                <div>
                                  After Upgrade: {productionInfo.next.actual}/hour
                                  <span className="text-slate-300/60"> ({productionInfo.next.theoretical} theoretical)</span>
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
                            <div className="text-xs text-slate-300/70 mb-1">💰 Upgrade Cost</div>
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
                              className={`px-4 py-2 text-sm hover:scale-105 transition-transform ${
                                energyImpact?.status === 'deficit'
                                  ? 'pa-btn-secondary bg-amber-500/15 hover:bg-amber-500/20 border-amber-500/40 text-amber-100'
                                  : 'pa-btn-primary'
                              }`}
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
                          <div className="absolute left-full ml-2 top-0 w-80 pa-modal p-3 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10 shadow-lg">
                            <div className="text-white font-medium mb-2">{building.icon} {building.name} Upgrade</div>

                            {/* Detailed Energy Analysis */}
                            {energyImpact && (
                              <div className="mb-3">
                                <div className="text-blue-400 text-sm font-medium mb-1">⚡ Energy Analysis</div>
                                <div className="text-xs text-slate-200/80 space-y-1">
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
                                <div className="text-xs text-slate-200/80 space-y-1">
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
                            <div className="text-xs text-slate-200/80">
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
        return (
          <div data-testid="section-fleets">
            <FleetManagement user={user} planets={planets} />
          </div>
        );
      case 'combat':
        return (
          <div data-testid="section-combat">
            <CombatDashboard user={user} planets={planets} onNavigateSection={setActiveSection} />
          </div>
        );
      case 'wheel':
        return (
          <div className="max-w-md mx-auto" data-testid="section-wheel">
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
          <ResearchDashboard />
        );
      case 'shipyard':
        // Filter ships based on selected role
        const filteredShips = selectedShipRole === 'all'
          ? Object.keys(shipCosts)
          : Object.entries(shipStats)
              .filter(([_, stats]) => stats.role === selectedShipRole)
              .map(([shipType, _]) => shipType);

        return (
          <div className="space-y-6" data-testid="section-shipyard">
            {/* Shipyard Header */}
            <div className="pa-card p-6">
              <h3 className="text-xl font-bold mb-4 text-white">🚀 Shipyard</h3>
              <p className="text-slate-300/80">Build ships to expand your fleet and colonize new planets</p>
            </div>

            {/* Planet Selection for Shipyard */}
            <div className="pa-card p-6">
              <h4 className="text-lg font-semibold mb-4 text-white">Select Planet</h4>
              {planets.length > 6 ? (
                <select
                  className="pa-input"
                  data-testid="shipyard-planet-dropdown"
                  value={selectedPlanet?.id ?? ''}
                  onChange={(e) => {
                    const id = parseInt(e.target.value, 10);
                    const p = planets.find((pl) => pl.id === id);
                    if (p) setSelectedPlanet(p);
                  }}
                >
                  {planets.map((planet) => (
                    <option key={planet.id} value={planet.id}>
                      {(planet.is_home_planet ? '🏠 ' : '🌍 ') + planet.name} ({planet.x}:{planet.y}:{planet.z})
                    </option>
                  ))}
                </select>
              ) : (
                <div className="flex space-x-4 overflow-x-auto overflow-y-hidden max-w-full pb-1">
                  {planets.map(planet => (
                    <button
                      key={planet.id}
                      onClick={() => setSelectedPlanet(planet)}
                      className={`whitespace-nowrap ${
                        selectedPlanet?.id === planet.id
                          ? 'pa-btn-primary'
                          : 'pa-btn-secondary'
                      }`}
                    >
                      {planet.name} ({planet.coordinates})
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Ship Construction */}
            {selectedPlanet && Object.keys(shipCosts).length > 0 && Object.keys(shipStats).length > 0 && (
              <div className="space-y-6">
                {/* Available Resources Display */}
                <div className="pa-card p-6">
                  <h4 className="text-lg font-semibold mb-4 text-white">Available Resources</h4>
                  <div className="grid grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-metal text-2xl font-bold">
                        {selectedPlanet.resources.metal.toLocaleString()}
                      </div>
                      <div className="text-metal text-sm">Metal</div>
                    </div>
                    <div className="text-center">
                      <div className="text-crystal text-2xl font-bold">
                        {selectedPlanet.resources.crystal.toLocaleString()}
                      </div>
                      <div className="text-crystal text-sm">Crystal</div>
                    </div>
                    <div className="text-center">
                      <div className="text-deuterium text-2xl font-bold">
                        {selectedPlanet.resources.deuterium.toLocaleString()}
                      </div>
                      <div className="text-deuterium text-sm">Deuterium</div>
                    </div>
                  </div>
                </div>

                {/* Ship Role Filter */}
                <div className="pa-card p-6">
                  <h4 className="text-lg font-semibold mb-4 text-white">Filter by Ship Type</h4>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => setSelectedShipRole('all')}
                      className={`px-4 py-2 text-sm font-medium transition-colors ${
                        selectedShipRole === 'all'
                          ? 'pa-btn-primary'
                          : 'pa-btn-secondary'
                      }`}
                    >
                      All Ships ({Object.keys(shipCosts).length})
                    </button>
                    {shipRoles.map(role => {
                      const roleShips = Object.values(shipStats).filter(stats => stats.role === role).length;
                      return (
                        <button
                          key={role}
                          onClick={() => setSelectedShipRole(role)}
                          className={`px-4 py-2 text-sm font-medium transition-colors capitalize ${
                            selectedShipRole === role
                              ? 'pa-btn-primary'
                              : 'pa-btn-secondary'
                          }`}
                        >
                          {role} ({roleShips})
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Ship List */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {filteredShips.map(shipType => {
                    const costs = shipCosts[shipType];
                    const stats = shipStats[shipType];
                    const canAfford = canAffordShip(shipType, 1);
                    const shipName = formatShipName(shipType);
                    const shipIcon = getShipIcon(shipType);

                    return (
                      <div key={shipType} className="pa-card p-6 group relative">
                        {/* Ship Header */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center space-x-3">
                            <span className="text-3xl">{shipIcon}</span>
                            <div>
                              <h5 className="text-white font-bold text-lg">{shipName}</h5>
                              <div className={`text-sm font-medium capitalize ${
                                stats?.role === 'cargo' ? 'text-blue-400' :
                                stats?.role === 'fighter' ? 'text-red-400' :
                                stats?.role === 'capital' ? 'text-purple-400' :
                                stats?.role === 'special' ? 'text-green-400' :
                                stats?.role === 'bomber' ? 'text-orange-400' :
                                stats?.role === 'ultimate' ? 'text-yellow-400' :
                                'text-slate-300/70'
                              }`}>
                                {stats?.role || 'unknown'} Ship
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-slate-300/70 mb-1">Cost per ship</div>
                            <div className="text-yellow-400 font-medium">
                              {costs?.metal > 0 && `${costs.metal.toLocaleString()}M`}
                              {costs?.crystal > 0 && ` ${costs.crystal.toLocaleString()}C`}
                              {costs?.deuterium > 0 && ` ${costs.deuterium.toLocaleString()}D`}
                            </div>
                          </div>
                        </div>

                        {/* Ship Stats - Compact View */}
                        {stats && (
                          <div className="mb-4">
                            <ShipStats shipType={shipType} stats={stats} compact={true} />
                          </div>
                        )}

	                        {/* Build Buttons */}
	                        <div className="flex flex-col space-y-3">
	                          {/* Custom quantity input (scales to late game) */}
	                          <div className="pa-panel p-3">
	                            <div className="flex items-center justify-between mb-2">
	                              <div className="text-sm text-slate-200/90 font-medium">Custom amount</div>
	                              <button
	                                type="button"
	                                className="pa-btn-ghost text-xs px-3 py-1"
	                                onClick={() => {
	                                  const max = getMaxBuildableShipCount(shipType);
	                                  setShipBuildQuantities((prev) => ({ ...prev, [shipType]: String(max) }));
	                                }}
	                                data-testid={`shipyard-max-${shipType}`}
	                              >
	                                Max
	                              </button>
	                            </div>
	                            <div className="flex items-center gap-2">
	                              <input
	                                type="number"
	                                min="0"
	                                inputMode="numeric"
	                                className="pa-input flex-1 p-2"
	                                value={shipBuildQuantities?.[shipType] ?? ''}
	                                onChange={(e) => {
	                                  const next = e.target.value;
	                                  setShipBuildQuantities((prev) => ({ ...prev, [shipType]: next }));
	                                }}
	                                placeholder="e.g. 1000"
	                                data-testid={`shipyard-qty-${shipType}`}
	                              />
	                              <button
	                                type="button"
	                                className="pa-btn-primary px-4 py-2"
	                                disabled={upgrading || !(() => {
	                                  const q = parseInt(shipBuildQuantities?.[shipType] || '0', 10);
	                                  return Number.isFinite(q) && q > 0 && canAffordShip(shipType, q);
	                                })()}
	                                onClick={() => {
	                                  const q = parseInt(shipBuildQuantities?.[shipType] || '0', 10);
	                                  if (!Number.isFinite(q) || q <= 0) {
	                                    showError('Enter a valid ship quantity');
	                                    return;
	                                  }
	                                  handleBuildShip(shipType, q);
	                                }}
	                                data-testid={`shipyard-build-${shipType}`}
	                              >
	                                Build
	                              </button>
	                            </div>
	                            <div className="mt-2 text-xs text-slate-300/70">
	                              Max buildable: {getMaxBuildableShipCount(shipType).toLocaleString()}
	                            </div>
	                          </div>

	                          <div className="flex justify-between items-center">
	                            <button
	                              onClick={() => handleBuildShip(shipType, 1)}
	                              disabled={upgrading || !canAfford}
                              className={`${canAfford ? 'pa-btn-primary' : 'pa-btn-secondary'} px-4 py-2`}
                            >
                              {upgrading ? 'Building...' : 'Build 1'}
                            </button>
                            <span className="text-xs text-slate-300/70">
                              {canAfford ? '✅ Can afford' : '❌ Insufficient resources'}
                            </span>
                          </div>

                          {/* Build Multiple Buttons */}
                          <div className="grid grid-cols-4 gap-2">
                            {[5, 10, 25, 50].map(quantity => {
                              const canAffordMultiple = canAffordShip(shipType, quantity);
                              return (
                                <button
                                  key={quantity}
                                  onClick={() => handleBuildShip(shipType, quantity)}
                                  disabled={upgrading || !canAffordMultiple}
                                  className={`${canAffordMultiple ? 'pa-btn-primary' : 'pa-btn-secondary'} px-3 py-2 text-sm`}
                                  title={`Build ${quantity} ships`}
                                >
                                  {quantity}
                                </button>
                              );
                            })}
                          </div>
                        </div>

                        {/* Detailed Stats Tooltip */}
                        {stats && (
                          <div className="absolute left-full ml-4 top-0 w-96 pa-modal p-4 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10 shadow-xl">
                            <div className="text-white font-bold text-lg mb-3 flex items-center">
                              <span className="mr-2">{shipIcon}</span>
                              {shipName}
                            </div>
                            <ShipStats shipType={shipType} stats={stats} compact={false} />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* No ships found message */}
                {filteredShips.length === 0 && (
                  <div className="pa-card p-8 text-center">
                    <div className="text-slate-300/80 text-lg mb-2">No ships found</div>
                    <div className="text-slate-300/60 text-sm">
                      Try selecting a different ship role or check if ship data is loading.
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Loading state */}
            {selectedPlanet && (Object.keys(shipCosts).length === 0 || Object.keys(shipStats).length === 0) && (
              <div className="pa-card p-8 text-center">
                <div className="text-slate-300/80 text-lg mb-2">Loading shipyard data…</div>
                <div className="text-slate-300/60 text-sm">
                  Fetching ship costs and statistics from the server.
                </div>
              </div>
            )}
          </div>
        );
      case 'alliance':
        return (
          <div className="pa-card p-6" data-testid="section-alliance">
            <h3 className="text-xl font-bold mb-4 text-white">🤝 Alliance Center</h3>
            <div className="text-center text-slate-300/70 py-8">
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
          <div className="pa-card p-6" data-testid="section-messages">
            <h3 className="text-xl font-bold mb-4 text-white">💬 Messages</h3>
            <div className="text-center text-slate-300/70 py-8">
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
        return (
          <div data-testid="section-overview">
            <Overview user={user} planets={planets} onNavigateSection={setActiveSection} />
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="pa-card p-6 text-center">
          <div className="text-xl font-semibold text-white">Loading your empire…</div>
          <div className="text-sm text-slate-300/90 mt-2">Syncing colonies and fleet telemetry</div>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="pa-card p-6 text-center max-w-lg w-full">
          <div className="text-xl font-semibold text-white">Couldn’t load your empire</div>
          <div className="text-sm text-slate-300/90 mt-2">{loadError}</div>
          <div className="mt-4 flex justify-center gap-3">
            <button type="button" className="pa-btn-secondary px-4 py-2" onClick={fetchPlanets} data-testid="dashboard-retry">
              Retry
            </button>
            <button type="button" className="pa-btn-danger px-4 py-2" onClick={onLogout}>
              Logout
            </button>
          </div>
          <div className="mt-4 text-xs text-slate-300/70">
            Tip: for local dev, confirm backend is reachable at <span className="text-slate-200">http://localhost:5000/health</span>.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="dashboard">
      <header className="pa-panel rounded-none border-x-0 border-t-0">
        <div className="container mx-auto px-6 py-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
          <div className="flex items-center gap-3">
            <img
              src={planetarionLogo}
              alt="Planetarion"
              className="h-12 sm:h-14 md:h-16 w-auto select-none"
              draggable={false}
            />
            <h1 className="text-2xl sm:text-3xl font-bold text-white">Planetarion</h1>
          </div>
	          <div className="flex items-center gap-4 flex-wrap justify-between sm:justify-end w-full sm:w-auto">
	            <div className="flex items-center gap-3 min-w-[260px]">
		              <CommanderPortrait
		                username={user.username}
		                level={user.commander_level || 1}
		                xp={user.commander_xp || 0}
		                xpProgress={user.commander_xp_progress || null}
		                portraitKey={portraitKey}
		                size={portraitSize}
		              />
		              <div className="min-w-0">
		                <div className="flex items-center gap-2 min-w-0">
		                  <span
		                    className="px-2 py-0.5 rounded-full text-[11px] font-extrabold tracking-wide uppercase"
		                    style={{
		                      background: 'rgba(2, 6, 23, 0.65)',
		                      border: '1px solid rgba(148, 163, 184, 0.20)',
		                      color: 'rgba(226, 232, 240, 0.92)',
		                      boxShadow: '0 10px 24px rgba(0,0,0,0.35)',
		                    }}
		                  >
		                    Commander
		                  </span>
		                  <div className="text-slate-100/95 font-semibold truncate">{user.username}</div>
		                </div>
		                {renderCommanderXpBar()}
		                {shouldShowIdleSummary() && (
	                  <div className="text-xs text-slate-300/80 mt-0.5" data-testid="idle-summary">
	                    While you were away ({formatDuration(idleGains.duration_seconds)}):{' '}
	                    <span className="text-slate-100/95 font-semibold">
	                      +{Number(idleGains.resources?.metal || 0).toLocaleString()}M
                    </span>{' '}
                    <span className="text-slate-100/95 font-semibold">
                      +{Number(idleGains.resources?.crystal || 0).toLocaleString()}C
                    </span>{' '}
                    <span className="text-slate-100/95 font-semibold">
                      +{Number(idleGains.resources?.deuterium || 0).toLocaleString()}D
                    </span>
                    {Number(idleGains.research_points || 0) > 0 && (
                      <>
                        {' • '}
                        <span className="text-slate-100/95 font-semibold">
                          +{Number(idleGains.research_points || 0).toLocaleString()} RP
                        </span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>

	            <div className="flex items-center gap-3 flex-wrap">
	              <label className="flex items-center gap-2 text-xs text-slate-200/80">
	                <span className="hidden sm:inline">Commander</span>
	                <select
	                  className="pa-input py-2 px-3 text-sm"
	                  value={portraitKey || 'male'}
	                  onChange={(e) => updatePortraitKey(e.target.value)}
	                  data-testid="commander-portrait-select"
	                  aria-label="Commander portrait"
	                  title="Commander portrait"
	                >
	                  <option value="male">Male</option>
	                  <option value="female">Female</option>
	                </select>
	              </label>
	              <BackgroundMusicToggle />
	              <button
	                onClick={onLogout}
	                data-testid="logout-button"
	                className="pa-btn-danger px-4 py-2"
	              >
                Logout
              </button>
            </div>
          </div>
          </div>
        </header>

      <Navigation activeSection={activeSection} onSectionChange={setActiveSection} />

      <main className="container mx-auto px-6 py-6">
        {renderSection()}
      </main>

	      {showRenameModal && selectedPlanet && (
	        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-6" data-testid="planet-rename-modal">
	          <div className="pa-modal p-6 w-full max-w-md">
	            <div className="flex items-center justify-between mb-4">
	              <h3 className="text-xl font-bold text-white">Rename Planet</h3>
	              <button
	                type="button"
	                className="pa-btn-ghost px-3 py-2 text-sm"
	                onClick={() => setShowRenameModal(false)}
	                aria-label="Close"
	              >
	                Close
	              </button>
	            </div>

	            <div className="text-sm text-slate-300/90 mb-3">
	              Planet: <span className="text-white font-medium">{selectedPlanet.name}</span>
	            </div>

	            <label className="block text-slate-200/90 mb-2">New name (one-time)</label>
	            <input
	              className="pa-input"
	              value={renameValue}
	              maxLength={32}
	              onChange={(e) => setRenameValue(e.target.value)}
	              data-testid="planet-rename-input"
	              placeholder="e.g. New Terra"
	            />
	            <div className="mt-2 text-xs text-slate-300/70">Max 32 characters. Renaming is allowed once per planet.</div>

	            <div className="flex gap-3 mt-5">
	              <button
	                type="button"
	                className="flex-1 pa-btn-primary py-3"
	                disabled={renaming || !renameValue.trim()}
	                data-testid="planet-rename-submit"
	                onClick={async () => {
	                  const newName = renameValue.trim();
	                  if (!newName) return;
	                  setRenaming(true);
	                  try {
	                    const res = await axios.put('/api/planet/rename', { planet_id: selectedPlanet.id, new_name: newName });
	                    const updated = res.data?.planet;
	                    if (updated?.id) {
	                      setPlanets((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
	                      setSelectedPlanet((prev) => (prev?.id === updated.id ? updated : prev));
	                    }
	                    showSuccess('Planet renamed');
	                    setShowRenameModal(false);
	                  } catch (e) {
	                    showError(e.response?.data?.error || 'Rename failed');
	                  } finally {
	                    setRenaming(false);
	                  }
	                }}
	              >
	                {renaming ? 'Renaming…' : 'Rename'}
	              </button>
	              <button
	                type="button"
	                className="flex-1 pa-btn-secondary py-3"
	                data-testid="planet-rename-cancel"
	                onClick={() => setShowRenameModal(false)}
	              >
	                Cancel
	              </button>
	            </div>
	          </div>
	        </div>
	      )}
	
		      {/* Galaxy Map Modal */}
		      {activeSection === 'galaxy' && (
		        <GalaxyMap
		          user={user}
	          planets={planets}
	          onNavigateSection={setActiveSection}
	          onClose={() => setActiveSection('overview')}
	        />
	      )}

      {/* Global Chat Panel */}
      <ChatPanel
        isMinimized={chatMinimized}
        onToggleMinimize={() => setChatMinimized(!chatMinimized)}
      />
    </div>
  );
}

export default Dashboard;
