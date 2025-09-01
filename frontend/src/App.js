import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [users, setUsers] = useState([]);
  const [planets, setPlanets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [usersRes, planetsRes] = await Promise.all([
        axios.get('http://localhost:5000/users'),
        axios.get('http://localhost:5000/planets')
      ]);
      setUsers(usersRes.data);
      setPlanets(planetsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-space-dark flex items-center justify-center">
        <div className="text-xl">Loading Planetarion...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-space-dark">
      <header className="bg-space-blue p-4">
        <h1 className="text-3xl font-bold text-center">🌌 Planetarion</h1>
      </header>

      <main className="container mx-auto p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Users Section */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl font-bold mb-4 text-metal">👥 Players</h2>
            <div className="space-y-2">
              {users.length === 0 ? (
                <p className="text-gray-400">No players yet</p>
              ) : (
                users.map(user => (
                  <div key={user.id} className="bg-gray-700 p-3 rounded">
                    <div className="font-semibold">{user.username}</div>
                    <div className="text-sm text-gray-400">{user.email}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Planets Section */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-2xl font-bold mb-4 text-crystal">🪐 Planets</h2>
            <div className="space-y-2">
              {planets.length === 0 ? (
                <p className="text-gray-400">No planets colonized yet</p>
              ) : (
                planets.map(planet => (
                  <div key={planet.id} className="bg-gray-700 p-3 rounded">
                    <div className="font-semibold">{planet.name}</div>
                    <div className="text-sm text-gray-400">{planet.coordinates}</div>
                    <div className="text-xs mt-1">
                      <span className="text-metal">Metal: {planet.resources.metal.toLocaleString()}</span>
                      <span className="ml-2 text-crystal">Crystal: {planet.resources.crystal.toLocaleString()}</span>
                      <span className="ml-2 text-deuterium">Deut: {planet.resources.deuterium.toLocaleString()}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Resources Overview */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4 text-deuterium">📊 Universe Stats</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-metal">{users.length}</div>
              <div className="text-sm text-gray-400">Active Players</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-crystal">{planets.length}</div>
              <div className="text-sm text-gray-400">Colonized Planets</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-deuterium">
                {planets.reduce((sum, p) => sum + p.resources.metal + p.resources.crystal + p.resources.deuterium, 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-400">Total Resources</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
