const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5000',
      changeOrigin: true,
      logLevel: 'debug',
      onProxyReq: (proxyReq, req, res) => {
        console.log('🔍 API Proxy: Forwarding request to backend:', req.method, req.url);
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log('🔍 API Proxy: Backend response:', proxyRes.statusCode, req.url);
      },
      onError: (err, req, res) => {
        console.error('❌ API Proxy: Proxy error:', err.message);
      }
    })
  );
};
