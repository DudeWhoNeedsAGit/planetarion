import React, { useState } from 'react';
import axios from 'axios';
import planetarionLogo from './assets/branding/planetarion-logo.png';

function Login({ onLogin }) {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/auth/login', formData);
      localStorage.setItem('token', response.data.access_token);
      // Fetch enriched user payload (level/idle gains/etc).
      const me = await axios.get('/api/auth/me');
      onLogin(me.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="pa-card p-8 w-full max-w-md">
        <div className="flex justify-center mb-4">
          <img
            src={planetarionLogo}
            alt="Planetarion"
            className="h-9 w-auto select-none"
            draggable={false}
          />
        </div>
        <h2 className="text-2xl font-bold text-center mb-2 text-white">Login to Planetarion</h2>
        <div className="text-center text-sm text-slate-300/90 mb-6">
          Command your empire. Explore, fight, and colonize.
        </div>

        {error && (
          <div data-testid="auth-error" className="bg-red-950/60 border border-red-500/30 text-red-100 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-slate-200/90 mb-2">Username</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="pa-input"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-slate-200/90 mb-2">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="pa-input"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full pa-btn-primary py-3"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="text-center mt-4">
          <p className="text-slate-300/70">
            Don't have an account?{' '}
            <button
              onClick={() => window.location.hash = '#register'}
              className="text-blue-300 hover:text-blue-200 underline underline-offset-4"
            >
              Register here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
