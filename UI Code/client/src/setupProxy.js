const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests to the Express server with extended timeouts
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:3001',
      changeOrigin: true,
      timeout: 300000, // 5 minutes timeout
      proxyTimeout: 300000,
      onError: (err, req, res) => {
        console.error('React dev server proxy error:', err.message);
        if (!res.headersSent) {
          res.writeHead(500, {
            'Content-Type': 'application/json',
          });
          res.end(JSON.stringify({
            error: 'Proxy Error',
            message: err.message,
            timestamp: new Date().toISOString()
          }));
        }
      },
      onProxyReq: (proxyReq, req, res) => {
        console.log(`React dev server proxying: ${req.method} ${req.url} -> http://localhost:3001${req.url}`);
        
        // Set longer timeout for report generation requests
        if (req.url.includes('/api/reports/generate')) {
          proxyReq.setTimeout(300000); // 5 minutes for report generation
        } else {
          proxyReq.setTimeout(60000); // 1 minute for other requests
        }
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log(`React dev server proxy response: ${proxyRes.statusCode} for ${req.url}`);
      },
      logLevel: 'warn'
    })
  );
};
