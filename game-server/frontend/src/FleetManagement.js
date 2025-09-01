import React, { useState, useEffect } from 'react';
import axios from 'axios';

function FleetManagement({ user, planets }) {
  const [fleets, setFleets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showSendForm, setShowSendForm] = useState(false);
  const [selectedFleet, setSelectedFleet] = useState(null);

  useEffect(() => {
    fetchFleets();
  }, []);

  const fetchFleets = async () => {
    try {
      const response = await axios.get('/api/fleet');
      setFleets(response.data);
    } catch (error) {
      console.error('Error fetching fleets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFleet = async (fleetData) => {
    try {
      const response = await axios.post('/api/fleet', fleetData);
      setFleets(prev => [...prev, response.data.fleet]);
      setShowCreateForm(false);
      alert('Fleet created successfully!');
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to create fleet');
    }
  };

  const handleSendFleet = async (sendData) => {
    try {
      const response = await axios.post('/api/fleet/send', sendData);
      // Update the fleet in the list
      setFleets(prev => prev.map(fleet =>
        fleet.id === sendData.fleet_id ? response.data.fleet : fleet
      ));
      setShowSendForm(false);
      setSelectedFleet(null);
      alert('Fleet sent successfully!');
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to send fleet');
    }
  };

  const handleRecallFleet = async (fleetId) => {
    try {
      const response = await axios.post(`/api/fleet/recall/${fleetId}`);
      setFleets(prev => prev.map(fleet =>
        fleet.id === fleetId ? response.data.fleet : fleet
      ));
      alert('Fleet recalled successfully!');
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to recall fleet');
    }
  };

  const formatTimeRemaining = (arrivalTime) => {
    if (!arrivalTime) return 'N/A';

    const now = new Date();
    const arrival = new Date(arrivalTime);
    const diff = arrival - now;

    if (diff <= 0) return 'Arrived';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-center text-white">Loading fleets...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-white">🚀 Fleet Management</h3>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          Create Fleet
        </button>
      </div>

      {/* Fleets List */}
      <div className="space-y-4 mb-6">
        {fleets.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            No fleets available. Create your first fleet!
          </div>
        ) : (
          fleets.map(fleet => (
            <div key={fleet.id} className="bg-gray-700 p-4 rounded">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="text-white font-medium">
                    Fleet #{fleet.id} - {fleet.mission}
                  </div>
                  <div className="text-sm text-gray-400">
                    Status: <span className={`font-medium ${
                      fleet.status === 'stationed' ? 'text-green-400' :
                      fleet.status === 'traveling' ? 'text-yellow-400' :
                      fleet.status === 'returning' ? 'text-blue-400' : 'text-gray-400'
                    }`}>
                      {fleet.status}
                    </span>
                  </div>
                </div>
                <div className="flex space-x-2">
                  {fleet.status === 'stationed' && (
                    <button
                      onClick={() => {
                        setSelectedFleet(fleet);
                        setShowSendForm(true);
                      }}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Send
                    </button>
                  )}
                  {(fleet.status === 'traveling' || fleet.status === 'returning') && (
                    <button
                      onClick={() => handleRecallFleet(fleet.id)}
                      className="bg-orange-600 hover:bg-orange-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Recall
                    </button>
                  )}
                </div>
              </div>

              {/* Fleet Details */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-gray-400">Ships</div>
                  <div className="text-white">
                    {fleet.ships.small_cargo + fleet.ships.large_cargo +
                     fleet.ships.light_fighter + fleet.ships.heavy_fighter +
                     fleet.ships.cruiser + fleet.ships.battleship} total
                  </div>
                </div>
                <div>
                  <div className="text-gray-400">From</div>
                  <div className="text-white">{planets.find(p => p.id === fleet.start_planet_id)?.name || 'Unknown'}</div>
                </div>
                <div>
                  <div className="text-gray-400">To</div>
                  <div className="text-white">{planets.find(p => p.id === fleet.target_planet_id)?.name || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-gray-400">ETA</div>
                  <div className="text-white">{formatTimeRemaining(fleet.arrival_time)}</div>
                </div>
              </div>

              {/* Ship Breakdown */}
              <div className="mt-3 pt-3 border-t border-gray-600">
                <div className="text-xs text-gray-400 mb-2">Ship Composition:</div>
                <div className="flex flex-wrap gap-2 text-xs">
                  {Object.entries(fleet.ships).map(([shipType, count]) => (
                    count > 0 && (
                      <span key={shipType} className="bg-gray-600 px-2 py-1 rounded">
                        {shipType.replace('_', ' ')}: {count}
                      </span>
                    )
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Fleet Modal */}
      {showCreateForm && (
        <CreateFleetModal
          planets={planets}
          onCreate={handleCreateFleet}
          onClose={() => setShowCreateForm(false)}
        />
      )}

      {/* Send Fleet Modal */}
      {showSendForm && selectedFleet && (
        <SendFleetModal
          fleet={selectedFleet}
          planets={planets}
          onSend={handleSendFleet}
          onClose={() => {
            setShowSendForm(false);
            setSelectedFleet(null);
          }}
        />
      )}
    </div>
  );
}

function CreateFleetModal({ planets, onCreate, onClose }) {
  const [formData, setFormData] = useState({
    start_planet_id: '',
    ships: {
      small_cargo: 0,
      large_cargo: 0,
      light_fighter: 0,
      heavy_fighter: 0,
      cruiser: 0,
      battleship: 0
    }
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

  const handleSubmit = (e) => {
    e.preventDefault();
    const totalShips = Object.values(formData.ships).reduce((sum, count) => sum + count, 0);
    if (totalShips === 0) {
      alert('Fleet must contain at least one ship');
      return;
    }
    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md">
        <h3 className="text-xl font-bold text-white mb-4">Create New Fleet</h3>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">Starting Planet</label>
            <select
              value={formData.start_planet_id}
              onChange={(e) => setFormData(prev => ({ ...prev, start_planet_id: e.target.value }))}
              className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
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
            <label className="block text-gray-300 mb-2">Ships</label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(formData.ships).map(([shipType, count]) => (
                <div key={shipType}>
                  <label className="block text-xs text-gray-400 mb-1">
                    {shipType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={count}
                    onChange={(e) => handleShipChange(shipType, e.target.value)}
                    className="w-full p-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              ))}
              {/* Colony Ship */}
              <div>
                <label className="block text-xs text-gray-400 mb-1">Colony Ship</label>
                <input
                  type="number"
                  min="0"
                  value={formData.ships.colony_ship || 0}
                  onChange={(e) => handleShipChange('colony_ship', e.target.value)}
                  className="w-full p-2 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              type="submit"
              className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none"
            >
              Create Fleet
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SendFleetModal({ fleet, planets, onSend, onClose }) {
  const [formData, setFormData] = useState({
    fleet_id: fleet.id,
    target_planet_id: '',
    target_x: '',
    target_y: '',
    target_z: '',
    mission: 'attack'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSend(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md">
        <h3 className="text-xl font-bold text-white mb-4">Send Fleet</h3>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-300 mb-2">Target Planet</label>
            <select
              value={formData.target_planet_id}
              onChange={(e) => setFormData(prev => ({ ...prev, target_planet_id: e.target.value }))}
              className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
              required
            >
              <option value="">Select target planet</option>
              {planets.filter(p => p.id !== fleet.start_planet_id).map(planet => (
                <option key={planet.id} value={planet.id}>
                  {planet.name} ({planet.coordinates})
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-gray-300 mb-2">Mission</label>
            <select
              value={formData.mission}
              onChange={(e) => setFormData(prev => ({ ...prev, mission: e.target.value }))}
              className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            >
              <option value="attack">Attack</option>
              <option value="transport">Transport</option>
              <option value="deploy">Deploy</option>
              <option value="espionage">Espionage</option>
              <option value="recycle">Recycle</option>
              <option value="colonize">Colonize</option>
            </select>
          </div>

          {/* Coordinates for colonization */}
          {formData.mission === 'colonize' && (
            <div className="mb-4">
              <label className="block text-gray-300 mb-2">Target Coordinates</label>
              <div className="grid grid-cols-3 gap-2">
                <input
                  type="number"
                  placeholder="X"
                  value={formData.target_x}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_x: e.target.value }))}
                  className="p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  required
                />
                <input
                  type="number"
                  placeholder="Y"
                  value={formData.target_y}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_y: e.target.value }))}
                  className="p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  required
                />
                <input
                  type="number"
                  placeholder="Z"
                  value={formData.target_z}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_z: e.target.value }))}
                  className="p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <p className="text-xs text-gray-400 mt-1">Enter coordinates for colonization (must be empty)</p>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none"
            >
              Send Fleet
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default FleetManagement;
