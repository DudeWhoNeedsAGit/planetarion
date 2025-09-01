import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Login from './Login';
import Register from './Register';
import Dashboard from './Dashboard';

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



export default App;
