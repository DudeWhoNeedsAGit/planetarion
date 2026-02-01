import React from 'react';

function Navigation({ activeSection, onSectionChange }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: '🏠' },
    { id: 'planets', label: 'Planets', icon: '🪐' },
    { id: 'galaxy', label: 'Galaxy Map', icon: '🌌' },
    { id: 'fleets', label: 'Fleets', icon: '🚀' },
    { id: 'combat', label: 'Combat', icon: '⚔️' },
    { id: 'wheel', label: 'Lucky Wheel', icon: '🎰' },
    { id: 'shipyard', label: 'Shipyard', icon: '⚙️' },
    { id: 'research', label: 'Research', icon: '🔬' },
    { id: 'alliance', label: 'Alliance', icon: '🤝' },
    { id: 'messages', label: 'Messages', icon: '💬' }
  ];

  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="container mx-auto px-6">
        <div className="flex space-x-1 overflow-x-auto">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              data-testid={`nav-${item.id}`}
              className={`flex items-center space-x-2 px-4 py-3 rounded-t-lg font-medium whitespace-nowrap transition-colors ${
                activeSection === item.id
                  ? 'bg-space-blue text-white border-b-2 border-blue-400'
                  : 'text-gray-300 hover:text-white hover:bg-gray-700'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}

export default Navigation;
