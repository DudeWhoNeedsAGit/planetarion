import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Login from './Login';
import Register from './Register';
import Dashboard from './Dashboard';
import { ToastProvider, useToast } from './ToastContext';
import { ToastContainer } from './Toast';

// Set up axios defaults - use localhost for development and testing
// Use external IP only for production
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';
axios.defaults.baseURL = backendUrl;

// Axios request interceptor - automatically add JWT token to all requests
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Axios response interceptor - handle token expiration
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - redirect to login
      localStorage.removeItem('token');
      window.location.hash = '#login';
    }
    return Promise.reject(error);
  }
);

function AppContent() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const { toasts, removeToast } = useToast();

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
        const response = await axios.get('/api/auth/me');
        setUser(response.data);
        setCurrentView('dashboard');
      } catch (error) {
        localStorage.removeItem('token');
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
    <>
      <Dashboard user={user} onLogout={handleLogout} />
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </>
  );
}

function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}



export default App;
