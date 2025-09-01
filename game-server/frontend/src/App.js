import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Login from './Login';
import Register from './Register';

// Set up axios defaults
axios.defaults.baseURL = 'http://localhost:5000';

// Add token to requests if available
const token = localStorage.getItem('token');
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

function App() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
    handleHashChange();

    // Listen for hash changes
    window.addEventListener('hashchange', handleHashChange);

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        const response = await axios.get('/api/auth/me');
        setUser(response.data);
        setCurrentView('dashboard');
      } catch (error) {
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
        setCurrentView('login');
      }
    } else {
      setCurrentView('login');
    }
    setLoading(false);
  };

  const handleHashChange = () => {
    const hash = window.location.hash.substring(1);
    if (hash === 'register') {
      setCurrentView('register');
    } else if (hash === 'login' || !user) {
      setCurrentView('login');
    } else {
      setCurrentView('dashboard');
    }
  };

  const handleLogin = (userData) => {
    setUser(userData);
    setCurrentView('dashboard');
    window.location.hash = '';
  };

  const handleRegister = (userData) => {
    setUser(userData);
    setCurrentView('dashboard');
    window.location.hash = '';
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setCurrentView('login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-space-dark flex items-center justify-center">
        <div className="text-xl">Loading Planetarion...</div>
      </div>
    );
  }

  if (currentView === 'login') {
    return <Login onLogin={handleLogin} />;
  }

  if (currentView === 'register') {
    return <Register onRegister={handleRegister} />;
  }

  return (
    <Dashboard user={user} onLogout={handleLogout} />
  );
}

function Dashboard({ user, onLogout }) {
  const [users, setUsers] = useState([]);
  const [planets, setPlanets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [usersRes, planetsRes] = await Promise.all([
        axios.get('/users'),
        axios.get('/api/planet')
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
