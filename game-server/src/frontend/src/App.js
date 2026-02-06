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
// Prevent "infinite spinners" when the backend is down or the browser has a stuck connection.
axios.defaults.timeout = Number(process.env.REACT_APP_AXIOS_TIMEOUT_MS || 10000);

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
  const { toasts, removeToast, showError, showInfo } = useToast();

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
        const status = error.response?.status;
        if (status === 401) {
          localStorage.removeItem('token');
          setUser(null);
          setCurrentView('login');
          showError('Session expired. Please log in again.');
        } else {
          // Backend down / transient failure: keep token so we can recover after a restart.
          showInfo('Backend unreachable. Retrying…');
          try {
            await new Promise((r) => setTimeout(r, 1500));
            const retry = await axios.get('/api/auth/me');
            setUser(retry.data);
            setCurrentView('dashboard');
          } catch (e2) {
            setCurrentView('login');
          }
        }
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

  const refreshUser = async () => {
    const response = await axios.get('/api/auth/me');
    setUser(response.data);
    return response.data;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="pa-card p-6 text-center">
          <div className="text-xl font-semibold text-white">Loading Planetarion…</div>
          <div className="text-sm text-slate-300/90 mt-2">Initializing command systems</div>
        </div>
      </div>
    );
  }

  if (currentView === 'login') {
    return (
      <>
        <Login onLogin={handleLogin} />
        <ToastContainer toasts={toasts} removeToast={removeToast} />
      </>
    );
  }

  if (currentView === 'register') {
    return (
      <>
        <Register onRegister={handleRegister} />
        <ToastContainer toasts={toasts} removeToast={removeToast} />
      </>
    );
  }

  return (
    <>
      <Dashboard user={user} onLogout={handleLogout} onUserRefresh={refreshUser} />
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
