const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Use environment variable or default to localhost for local development
  const target = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
  
  app.use(
    '/api',
    createProxyMiddleware({
      target: target,
      changeOrigin: true,
      logLevel: 'debug',
    })
  );
};
