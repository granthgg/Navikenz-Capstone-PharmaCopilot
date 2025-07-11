const express = require('express');
const path = require('path');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3001;

// Enable CORS for all routes
app.use(cors());

// Parse JSON bodies
app.use(express.json());

app.use('/api', createProxyMiddleware({
  target: 'https://cholesterol-sensor-api-4ad950146578.herokuapp.com',
  changeOrigin: true,
  pathRewrite: {
    '^/api': '/api',
  },
  onError: (err, req, res) => {
    console.error('Proxy error:', err);
    res.status(500).json({ 
      error: 'Sensor API unavailable',
      message: 'Unable to connect to sensor data stream'
    });
  },
  logLevel: 'debug'
}));

// Serve static files from the React app build directory
app.use(express.static(path.join(__dirname, 'client/build')));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'smart-pharma-copilot-ui',
    timestamp: new Date().toISOString()
  });
});

// Catch all handler: send back React's index.html file for client-side routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'client/build', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Smart Pharma Copilot UI server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Dashboard: http://localhost:${PORT}`);
}); 