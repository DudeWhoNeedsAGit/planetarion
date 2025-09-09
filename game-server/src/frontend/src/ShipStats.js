import React from 'react';

const ShipStats = ({ shipType, stats, compact = false }) => {
  if (!stats) return null;

  const formatNumber = (num) => {
    if (num === undefined || num === null) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const getRoleColor = (role) => {
    const colors = {
      'cargo': 'text-blue-400',
      'fighter': 'text-red-400',
      'capital': 'text-purple-400',
      'special': 'text-green-400',
      'bomber': 'text-orange-400',
      'ultimate': 'text-yellow-400'
    };
    return colors[role] || 'text-gray-400';
  };

  const getRoleIcon = (role) => {
    const icons = {
      'cargo': '📦',
      'fighter': '⚔️',
      'capital': '🚢',
      'special': '🔧',
      'bomber': '💣',
      'ultimate': '⭐'
    };
    return icons[role] || '🚀';
  };

  if (compact) {
    return (
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="flex items-center space-x-1">
          <span className="text-red-400">⚔️</span>
          <span>{stats.firepower}</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-blue-400">🛡️</span>
          <span>{stats.defense}</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-green-400">💨</span>
          <span>{formatNumber(stats.speed)}</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-yellow-400">📦</span>
          <span>{formatNumber(stats.cargo)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Ship Role */}
      <div className="flex items-center space-x-2">
        <span className="text-lg">{getRoleIcon(stats.role)}</span>
        <span className={`font-medium capitalize ${getRoleColor(stats.role)}`}>
          {stats.role} Ship
        </span>
      </div>

      {/* Combat Stats */}
      <div className="bg-gray-700 rounded-lg p-3">
        <h4 className="text-white font-medium mb-2 flex items-center">
          <span className="mr-2">⚔️</span>
          Combat Statistics
        </h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Firepower:</span>
            <span className="text-red-400 font-medium">{formatNumber(stats.firepower)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Defense:</span>
            <span className="text-blue-400 font-medium">{stats.defense}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Shield:</span>
            <span className="text-green-400 font-medium">{stats.shield}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Speed:</span>
            <span className="text-purple-400 font-medium">{formatNumber(stats.speed)}</span>
          </div>
        </div>
      </div>

      {/* Capacity Stats */}
      <div className="bg-gray-700 rounded-lg p-3">
        <h4 className="text-white font-medium mb-2 flex items-center">
          <span className="mr-2">📦</span>
          Capacity & Fuel
        </h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Cargo:</span>
            <span className="text-yellow-400 font-medium">{formatNumber(stats.cargo)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Fuel Use:</span>
            <span className="text-orange-400 font-medium">{stats.fuel}/unit</span>
          </div>
        </div>
      </div>

      {/* Ship Description */}
      <div className="bg-gray-700 rounded-lg p-3">
        <h4 className="text-white font-medium mb-2">📋 Description</h4>
        <p className="text-gray-300 text-sm leading-relaxed">
          {stats.description}
        </p>
      </div>
    </div>
  );
};

export default ShipStats;
