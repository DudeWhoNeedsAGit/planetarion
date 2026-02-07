function resolveBackendBaseUrl() {
  const fromEnv = (process.env.REACT_APP_BACKEND_URL || '').replace(/\/$/, '');
  if (fromEnv) return fromEnv;

  // Dev ergonomics: if the frontend runs on :3000 and backend on :5000,
  // default to localhost:5000 so SSE does not 404 on the React dev server.
  // In production we expect REACT_APP_BACKEND_URL to be set (or served behind the same origin).
  if (typeof window !== 'undefined' && window.location?.hostname) {
    const host = window.location.hostname;
    return `http://${host}:5000`;
  }

  return '';
}

export const backendBaseUrl = resolveBackendBaseUrl();
