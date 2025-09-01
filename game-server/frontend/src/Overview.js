import React from 'react';

function Overview({ user, planets }) {
  const totalResources = planets.reduce((sum, planet) => ({
    metal: sum.metal + planet.resources.metal,
    crystal: sum.crystal + planet.resources.crystal,
    deuterium: sum.deuterium + planet.resources.deuterium
  }), { metal: 0, crystal: 0, deuterium: 0 });

  const totalProduction = planets.reduce((sum, planet) => ({
    metal: sum.metal + (planet.production_rates?.metal_per_hour || 0),
    crystal: sum.crystal + (planet.production_rates?.crystal_per_hour || 0),
    deuterium: sum.deuterium + (planet.production_rates?.deuterium_per_hour || 0)
  }), { metal: 0, crystal: 0, deuterium: 0 });

  const totalBuildings = planets.reduce((sum, planet) => ({
    metal_mine: sum.metal_mine + planet.structures.metal_mine,
    crystal_mine: sum.crystal_mine + planet.structures.crystal_mine,
    deuterium_synthesizer: sum.deuterium_synthesizer + planet.structures.deuterium_synthesizer,
    solar_plant: sum.solar_plant + planet.structures.solar_plant,
    fusion_reactor: sum.fusion_reactor + planet.structures.fusion_reactor
  }), { metal_mine: 0, crystal_mine: 0, deuterium_synthesizer: 0, solar_plant: 0, fusion_reactor: 0 });

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-space-blue to-blue-600 rounded-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">Welcome back, {user.username}!</h2>
        <p className="text-blue-100">Your empire spans {planets.length} planet{planets.length !== 1 ? 's' : ''} across the galaxy.</p>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Planets */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🪐</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Planets</h3>
              <p className="text-gray-400">Colonies</p>
            </div>
          </div>
          <div className="text-3xl font-bold text-blue-400">{planets.length}</div>
        </div>

        {/* Total Resources */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">💰</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Resources</h3>
              <p className="text-gray-400">Total Value</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-green-400">
            {(totalResources.metal + totalResources.crystal + totalResources.deuterium).toLocaleString()}
          </div>
        </div>

        {/* Production */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">⚡</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Production</h3>
              <p className="text-gray-400">Per Hour</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-yellow-400">
            {(totalProduction.metal + totalProduction.crystal + totalProduction.deuterium).toLocaleString()}
          </div>
        </div>

        {/* Buildings */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🏗️</span>
            <div>
              <h3 className="text-lg font-semibold text-white">Buildings</h3>
              <p className="text-gray-400">Total Level</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-purple-400">
            {Object.values(totalBuildings).reduce((sum, level) => sum + level, 0)}
          </div>
        </div>
      </div>

      {/* Resource Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4 text-metal">Metal Resources</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Current:</span>
              <span className="text-metal font-bold">{totalResources.metal.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Production:</span>
              <span className="text-metal">{totalProduction.metal.toLocaleString()}/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Mines:</span>
              <span className="text-metal">{totalBuildings.metal_mine} total</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4 text-crystal">Crystal Resources</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Current:</span>
              <span className="text-crystal font-bold">{totalResources.crystal.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Production:</span>
              <span className="text-crystal">{totalProduction.crystal.toLocaleString()}/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Mines:</span>
              <span className="text-crystal">{totalBuildings.crystal_mine} total</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4 text-deuterium">Deuterium Resources</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Current:</span>
              <span className="text-deuterium font-bold">{totalResources.deuterium.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Production:</span>
              <span className="text-deuterium">{totalProduction.deuterium.toLocaleString()}/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Synthesizers:</span>
              <span className="text-deuterium">{totalBuildings.deuterium_synthesizer} total</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Placeholder */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4 text-white">Recent Activity</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3 p-3 bg-gray-700 rounded">
            <span className="text-green-400">✅</span>
            <div>
              <p className="text-white">Empire initialized successfully</p>
              <p className="text-gray-400 text-sm">Just now</p>
            </div>
          </div>
          <div className="text-center text-gray-400 py-4">
            More activity will appear here as you play the game
          </div>
        </div>
      </div>
    </div>
  );
}

export default Overview;
