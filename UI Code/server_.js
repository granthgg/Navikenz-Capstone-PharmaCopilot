const express = require('express');
const path = require('path');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3001;
const PREDICTION_API_PORT = process.env.PREDICTION_API_PORT || 8000;
const PREDICTION_API_URL = process.env.PREDICTION_API_URL || `http://165.22.211.17:8000`;
const REPORT_API_PORT = process.env.REPORT_API_PORT || 8001;
const REPORT_API_URL = process.env.REPORT_API_URL || `http://165.22.211.17:8001`;

// Enhanced CORS configuration
const corsOptions = {
  origin: [
    'http://localhost:3000', // React dev server
    'http://localhost:3001', // Express server
    'http://127.0.0.1:3000',
    'http://127.0.0.1:3001'
  ],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-requested-with'],
  credentials: true
};

app.use(cors(corsOptions));

// Parse JSON bodies with increased limit
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Add request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// ============================================================================
// PREDICTION API PROXIES (HIGHEST PRIORITY)
// ============================================================================

// 1. Proxy for prediction API with /api/prediction prefix
app.use('/api/prediction', createProxyMiddleware({
  target: PREDICTION_API_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api/prediction': '/api',
  },
  timeout: 15000,
  proxyTimeout: 15000,
  onError: (err, req, res) => {
    console.error(`❌ Prediction API (/api/prediction) proxy error:`, err.message);
    if (!res.headersSent) {
      res.status(500).json({ 
        error: 'Prediction API unavailable',
        message: `Unable to connect to prediction service at ${PREDICTION_API_URL}`,
        details: err.message,
        originalUrl: req.originalUrl,
        timestamp: new Date().toISOString()
      });
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`✅ PREDICTION API: ${req.method} ${req.originalUrl} -> ${PREDICTION_API_URL}${req.url.replace('/api/prediction', '/api')}`);
  },
  onProxyRes: (proxyRes, req, res) => {
    console.log(`✅ PREDICTION API RESPONSE: ${proxyRes.statusCode} for ${req.originalUrl}`);
  },
  logLevel: 'info'
}));

// 2. Direct proxy for ALL prediction API endpoints (these take priority over sensor endpoints)
const predictionApiEndpoints = [
  '/api/current',
  '/api/forecast', 
  '/api/defect', 
  '/api/quality', 
  '/api/health', 
  '/api/buffer-status', 
  '/api/supplement-buffer',
  '/api/rl-status',
  '/api/sensor-api/health',
  '/api/sensor-api/status',
  '/api/sensor-api/sensors',
  '/api/sensor-api/latest',
  '/api/sensor-api/all'
];

app.use(predictionApiEndpoints, createProxyMiddleware({
  target: PREDICTION_API_URL,
  changeOrigin: true,
  timeout: 15000,
  proxyTimeout: 15000,
  onError: (err, req, res) => {
    console.error(`❌ Prediction API proxy error for ${req.url}:`, err.message);
    
    // Only fallback to sensor API for /api/current if prediction API fails
    if (req.url === '/api/current') {
      console.log(`🔄 FALLBACK: Trying sensor API for ${req.url}`);
      // Manually proxy to sensor API as fallback
      const axios = require('axios');
      axios.get('https://cholesterol-sensor-api-4ad950146578.herokuapp.com/api/current', { timeout: 10000 })
        .then(response => {
          if (!res.headersSent) {
            console.log(`✅ SENSOR API FALLBACK: Success for ${req.url}`);
            res.json(response.data);
          }
        })
        .catch(sensorErr => {
          console.error(`❌ SENSOR API FALLBACK: Failed for ${req.url}:`, sensorErr.message);
          if (!res.headersSent) {
            // Final fallback to mock data
            const mockData = {
              status: 'success',
              data: {
                waste: Math.random() * 3 + 1,
                produced: Math.random() * 500 + 800,
                ejection: Math.random() * 40 + 100,
                tbl_speed: Math.random() * 30 + 90,
                stiffness: Math.random() * 50 + 75,
                SREL: Math.random() * 3 + 2.5,
                main_comp: Math.random() * 8 + 12,
                timestamp: new Date().toISOString()
              },
              source: 'emergency_fallback_mock',
              note: 'Both Prediction and Sensor APIs unavailable',
              generated_at: new Date().toISOString()
            };
            console.log(`🆘 EMERGENCY FALLBACK: Using mock data for ${req.url}`);
            res.json(mockData);
          }
        });
    } else {
      // For other endpoints, just return error
      if (!res.headersSent) {
        res.status(500).json({ 
          error: 'Prediction API unavailable',
          message: `Unable to connect to prediction service at ${PREDICTION_API_URL}`,
          details: err.message,
          url: req.url,
          timestamp: new Date().toISOString()
        });
      }
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`✅ PREDICTION API: ${req.method} ${req.url} -> ${PREDICTION_API_URL}${req.url}`);
  },
  onProxyRes: (proxyRes, req, res) => {
    console.log(`✅ PREDICTION API RESPONSE: ${proxyRes.statusCode} for ${req.url}`);
  },
  logLevel: 'info'
}));

// 3. RL Action endpoint with dynamic model type
app.use('/api/rl_action', createProxyMiddleware({
  target: PREDICTION_API_URL,
  changeOrigin: true,
  timeout: 15000,
  proxyTimeout: 15000,
  onError: (err, req, res) => {
    console.error(`❌ RL Action API error:`, err.message);
    if (!res.headersSent) {
      res.status(500).json({ 
        error: 'RL Action API unavailable',
        message: 'RL models are not available',
        details: err.message,
        timestamp: new Date().toISOString()
      });
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`✅ RL ACTION API: ${req.method} ${req.url} -> ${PREDICTION_API_URL}${req.url}`);
  },
  logLevel: 'info'
}));

// ============================================================================
// REPORT GENERATION & KNOWLEDGE BASE API PROXIES
// ============================================================================

// Direct API routes for reports (more reliable than proxy)

// Health check endpoint
app.get('/api/reports/health', async (req, res) => {
  try {
    console.log(`🏥 Health check: GET /api/reports/health -> ${REPORT_API_URL}/api/reports/health`);
    const response = await axios.get(`${REPORT_API_URL}/api/reports/health`, { 
      timeout: 10000 
    });
    console.log(`✅ Health check successful: ${response.status}`);
    res.json(response.data);
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    res.status(503).json({
      error: 'Report Generation API unavailable',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Report types endpoint
app.get('/api/reports/types', async (req, res) => {
  try {
    console.log(`📋 Report types: GET /api/reports/types -> ${REPORT_API_URL}/api/reports/types`);
    const response = await axios.get(`${REPORT_API_URL}/api/reports/types`, { 
      timeout: 10000 
    });
    console.log(`✅ Report types successful: ${response.status}`);
    res.json(response.data);
  } catch (error) {
    console.error('❌ Report types failed:', error.message);
    res.status(503).json({
      error: 'Report Generation API unavailable',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Report generation endpoint (POST)
app.post('/api/reports/generate', async (req, res) => {
  try {
    console.log(`📝 Report generation: POST /api/reports/generate -> ${REPORT_API_URL}/api/reports/generate`);
    console.log(`📋 Request body:`, JSON.stringify(req.body, null, 2));
    
    const response = await axios.post(`${REPORT_API_URL}/api/reports/generate`, req.body, {
      timeout: 120000, // 2 minutes
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`✅ Report generation successful: ${response.status}`);
    res.json(response.data);
    
  } catch (error) {
    console.error('❌ Report generation failed:', error.message);
    
    if (error.code === 'ECONNABORTED') {
      res.status(504).json({
        error: 'Report generation timeout',
        message: 'Report generation took too long. Please try again.',
        timestamp: new Date().toISOString()
      });
    } else if (error.response) {
      res.status(error.response.status).json({
        error: 'Report generation error',
        message: error.response.data?.message || error.message,
        details: error.response.data,
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({
        error: 'Report Generation API unavailable',
        message: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
});

// Report generation endpoint (GET for testing)
app.get('/api/reports/generate', async (req, res) => {
  try {
    const { report_type = 'quality_control', query = 'Generate pharmaceutical manufacturing report' } = req.query;
    
    console.log(`📝 Report generation (GET): /api/reports/generate -> ${REPORT_API_URL}/api/reports/generate`);
    console.log(`📋 Query params: report_type=${report_type}, query=${query}`);
    
    const response = await axios.get(`${REPORT_API_URL}/api/reports/generate`, {
      params: { report_type, query },
      timeout: 120000
    });
    
    console.log(`✅ Report generation (GET) successful: ${response.status}`);
    res.json(response.data);
    
  } catch (error) {
    console.error('❌ Report generation (GET) failed:', error.message);
    res.status(503).json({
      error: 'Report Generation API unavailable',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// PDF Download endpoint (POST)
app.post('/api/reports/download-pdf', async (req, res) => {
  try {
    console.log(`📄 PDF Download: POST /api/reports/download-pdf -> ${REPORT_API_URL}/api/reports/download-pdf`);
    console.log(`📋 Request body:`, JSON.stringify(req.body, null, 2));
    
    const response = await axios.post(`${REPORT_API_URL}/api/reports/download-pdf`, req.body, {
      timeout: 300000, // 5 minutes for PDF generation
      responseType: 'arraybuffer', // Important for binary data
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`✅ PDF Download successful: ${response.status}, Content-Length: ${response.data.length}`);
    
    // Set proper headers for PDF download
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Length', response.data.length);
    
    // Extract filename from response headers if available
    const contentDisposition = response.headers['content-disposition'];
    if (contentDisposition) {
      res.setHeader('Content-Disposition', contentDisposition);
    } else {
      // Generate default filename
      const reportId = req.body?.report_id || `RPT-${Date.now()}`;
      res.setHeader('Content-Disposition', `attachment; filename="${reportId}.pdf"`);
    }
    
    // Send binary data
    res.send(response.data);
    
  } catch (error) {
    console.error('❌ PDF Download failed:', error.message);
    
    if (error.code === 'ECONNABORTED') {
      res.status(504).json({
        error: 'PDF generation timeout',
        message: 'PDF generation took too long. Please try again.',
        timestamp: new Date().toISOString()
      });
    } else if (error.response) {
      res.status(error.response.status).json({
        error: 'PDF generation error',
        message: error.response.data?.message || error.message,
        details: error.response.data,
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({
        error: 'Report Generation API unavailable',
        message: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
});

// PDF Download endpoint (GET for testing)
app.get('/api/reports/download-pdf', async (req, res) => {
  try {
    const { report_type = 'quality_control', query = 'Generate pharmaceutical manufacturing report' } = req.query;
    
    console.log(`📄 PDF Download (GET): /api/reports/download-pdf -> ${REPORT_API_URL}/api/reports/download-pdf`);
    console.log(`📋 Query params: report_type=${report_type}, query=${query}`);
    
    const response = await axios.get(`${REPORT_API_URL}/api/reports/download-pdf`, {
      params: { report_type, query },
      timeout: 300000, // 5 minutes for PDF generation
      responseType: 'arraybuffer' // Important for binary data
    });
    
    console.log(`✅ PDF Download (GET) successful: ${response.status}, Content-Length: ${response.data.length}`);
    
    // Set proper headers for PDF download
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Length', response.data.length);
    
    // Extract filename from response headers if available
    const contentDisposition = response.headers['content-disposition'];
    if (contentDisposition) {
      res.setHeader('Content-Disposition', contentDisposition);
    } else {
      // Generate default filename
      const reportId = `RPT-${Date.now()}`;
      res.setHeader('Content-Disposition', `attachment; filename="${reportId}.pdf"`);
    }
    
    // Send binary data
    res.send(response.data);
    
  } catch (error) {
    console.error('❌ PDF Download (GET) failed:', error.message);
    res.status(503).json({
      error: 'Report Generation API unavailable',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Proxy for knowledge base endpoints
app.use('/api/knowledge', createProxyMiddleware({
  target: REPORT_API_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api/knowledge': '/api/knowledge'
  },
  timeout: 30000,
  proxyTimeout: 30000,
  onError: (err, req, res) => {
    console.error('❌ Knowledge API proxy error:', err.message);
    if (!res.headersSent) {
      res.status(503).json({ 
        error: 'Knowledge Base API unavailable',
        message: `Unable to connect to knowledge base service at ${REPORT_API_URL}`,
        details: err.message,
        timestamp: new Date().toISOString()
      });
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`🧠 KNOWLEDGE API: ${req.method} ${req.originalUrl} -> ${REPORT_API_URL}${req.url}`);
  },
  logLevel: 'debug'
}));

// Proxy for data collection endpoints
app.use('/api/data', createProxyMiddleware({
  target: REPORT_API_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api/data': '/api/data'
  },
  timeout: 30000,
  proxyTimeout: 30000,
  onError: (err, req, res) => {
    console.error('❌ Data API proxy error:', err.message);
    if (!res.headersSent) {
      res.status(503).json({ 
        error: 'Data Collection API unavailable',
        message: `Unable to connect to data collection service at ${REPORT_API_URL}`,
        details: err.message,
        timestamp: new Date().toISOString()
      });
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`📊 DATA API: ${req.method} ${req.originalUrl} -> ${REPORT_API_URL}${req.url}`);
  },
  logLevel: 'debug'
}));

// Test endpoint to check prediction API connectivity
app.get('/api/prediction-test', async (req, res) => {
  try {
    const axios = require('axios');
    const response = await axios.get(`${PREDICTION_API_URL}/api/health`, { timeout: 5000 });
    res.json({
      status: 'success',
      prediction_api: 'connected',
      response: response.data,
      url: `${PREDICTION_API_URL}/api/health`
    });
  } catch (error) {
    console.error('Prediction API test failed:', error.message);
    res.status(500).json({
      status: 'error',
      prediction_api: 'disconnected',
      error: error.message,
      url: `${PREDICTION_API_URL}/api/health`
    });
  }
});

// Enhanced test endpoint to check report generation API connectivity
app.get('/api/reports-test', async (req, res) => {
  try {
    const axios = require('axios');
    console.log(`🧪 Testing Report API connection to: ${REPORT_API_URL}/api/reports/health`);
    
    const response = await axios.get(`${REPORT_API_URL}/api/reports/health`, { 
      timeout: 10000,
      headers: {
        'User-Agent': 'Smart-Pharma-Copilot-UI-Test'
      }
    });
    
    console.log(`✅ Report API test successful:`, response.status, response.data);
    
    res.json({
      status: 'success',
      report_api: 'connected',
      response: response.data,
      url: `${REPORT_API_URL}/api/reports/health`,
      test_time: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Report API test failed:', error.message);
    console.error('❌ Error details:', {
      code: error.code,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    });
    
    res.status(500).json({
      status: 'error',
      report_api: 'disconnected',
      error: error.message,
      error_code: error.code,
      url: `${REPORT_API_URL}/api/reports/health`,
      suggestions: [
        `Check if Report Generation service is running on port ${REPORT_API_PORT}`,
        'Verify with: python "Report Generation/run_report_system.py"',
        'Check logs for any startup errors'
      ],
      test_time: new Date().toISOString()
    });
  }
});

// ============================================================================
// EXTERNAL SENSOR API PROXIES (LOWER PRIORITY)
// ============================================================================

// Enhanced sensor API proxy (for /api/sensor/* paths)
app.use('/api/sensor', createProxyMiddleware({
  target: 'https://cholesterol-sensor-api-4ad950146578.herokuapp.com',
  changeOrigin: true,
  pathRewrite: {
    '^/api/sensor': '/api',
  },
  timeout: 20000,
  proxyTimeout: 20000,
  onError: (err, req, res) => {
    console.error('❌ External Sensor API proxy error:', err.message);
    if (!res.headersSent) {
      res.status(500).json({ 
        error: 'External Sensor API unavailable',
        message: 'Unable to connect to external sensor data stream',
        details: err.message,
        url: req.url,
        timestamp: new Date().toISOString()
      });
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`🔄 EXTERNAL SENSOR API: ${req.method} ${req.url}`);
  },
  logLevel: 'warn'
}));

// Handle /api/prediction/rl_action/{model} with dynamic model parameter
app.use('/api/prediction/rl_action', createProxyMiddleware({
  target: PREDICTION_API_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api/prediction/rl_action': '/api/rl_action',
  },
  timeout: 15000,
  proxyTimeout: 15000,
  onError: (err, req, res) => {
    console.error(`❌ RL Action proxy error:`, err.message);
    if (!res.headersSent) {
      res.status(500).json({ 
        error: 'RL Action API unavailable',
        message: 'RL models are not available',
        details: err.message,
        timestamp: new Date().toISOString()
      });
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`🤖 RL ACTION PROXY: ${req.method} ${req.originalUrl} -> ${PREDICTION_API_URL}/api/rl_action${req.url.replace('/api/prediction/rl_action', '')}`);
  },
  logLevel: 'info'
}));

// ============================================================================
// LEGACY ENDPOINT PROXIES (for requests without /api prefix)
// ============================================================================

// Legacy report endpoints (direct routes instead of proxy)
app.post('/reports/generate', async (req, res) => {
  try {
    console.log(`📝 Legacy report generation: POST /reports/generate -> ${REPORT_API_URL}/api/reports/generate`);
    console.log(`📋 Request body:`, JSON.stringify(req.body, null, 2));
    
    const response = await axios.post(`${REPORT_API_URL}/api/reports/generate`, req.body, {
      timeout: 120000, // 2 minutes
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`✅ Legacy report generation successful: ${response.status}`);
    res.json(response.data);
    
  } catch (error) {
    console.error('❌ Legacy report generation failed:', error.message);
    
    if (error.code === 'ECONNABORTED') {
      res.status(504).json({
        error: 'Report generation timeout',
        message: 'Report generation took too long. Please try again.',
        timestamp: new Date().toISOString()
      });
    } else if (error.response) {
      res.status(error.response.status).json({
        error: 'Report generation error',
        message: error.response.data?.message || error.message,
        details: error.response.data,
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({
        error: 'Report Generation API unavailable',
        message: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
});

app.get('/reports/health', async (req, res) => {
  try {
    console.log(`🏥 Legacy health check: GET /reports/health -> ${REPORT_API_URL}/api/reports/health`);
    const response = await axios.get(`${REPORT_API_URL}/api/reports/health`, { 
      timeout: 10000 
    });
    console.log(`✅ Legacy health check successful: ${response.status}`);
    res.json(response.data);
  } catch (error) {
    console.error('❌ Legacy health check failed:', error.message);
    res.status(503).json({
      error: 'Report Generation API unavailable',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

app.get('/reports/types', async (req, res) => {
  try {
    console.log(`📋 Legacy report types: GET /reports/types -> ${REPORT_API_URL}/api/reports/types`);
    const response = await axios.get(`${REPORT_API_URL}/api/reports/types`, { 
      timeout: 10000 
    });
    console.log(`✅ Legacy report types successful: ${response.status}`);
    res.json(response.data);
  } catch (error) {
    console.error('❌ Legacy report types failed:', error.message);
    res.status(503).json({
      error: 'Report Generation API unavailable',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Legacy PDF download endpoints
app.post('/reports/download-pdf', async (req, res) => {
  try {
    console.log(`📄 Legacy PDF Download: POST /reports/download-pdf -> ${REPORT_API_URL}/api/reports/download-pdf`);
    console.log(`📋 Request body:`, JSON.stringify(req.body, null, 2));
    
    const response = await axios.post(`${REPORT_API_URL}/api/reports/download-pdf`, req.body, {
      timeout: 300000, // 5 minutes for PDF generation
      responseType: 'arraybuffer', // Important for binary data
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`✅ Legacy PDF Download successful: ${response.status}, Content-Length: ${response.data.length}`);
    
    // Set proper headers for PDF download
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Length', response.data.length);
    
    // Extract filename from response headers if available
    const contentDisposition = response.headers['content-disposition'];
    if (contentDisposition) {
      res.setHeader('Content-Disposition', contentDisposition);
    } else {
      // Generate default filename
      const reportId = req.body?.report_id || `RPT-${Date.now()}`;
      res.setHeader('Content-Disposition', `attachment; filename="${reportId}.pdf"`);
    }
    
    // Send binary data
    res.send(response.data);
    
  } catch (error) {
    console.error('❌ Legacy PDF Download failed:', error.message);
    
    if (error.code === 'ECONNABORTED') {
      res.status(504).json({
        error: 'PDF generation timeout',
        message: 'PDF generation took too long. Please try again.',
        timestamp: new Date().toISOString()
      });
    } else if (error.response) {
      res.status(error.response.status).json({
        error: 'PDF generation error',
        message: error.response.data?.message || error.message,
        details: error.response.data,
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({
        error: 'Report Generation API unavailable',
        message: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
});

app.get('/reports/download-pdf', async (req, res) => {
  try {
    const { report_type = 'quality_control', query = 'Generate pharmaceutical manufacturing report' } = req.query;
    
    console.log(`📄 Legacy PDF Download (GET): /reports/download-pdf -> ${REPORT_API_URL}/api/reports/download-pdf`);
    console.log(`📋 Query params: report_type=${report_type}, query=${query}`);
    
    const response = await axios.get(`${REPORT_API_URL}/api/reports/download-pdf`, {
      params: { report_type, query },
      timeout: 300000, // 5 minutes for PDF generation
      responseType: 'arraybuffer' // Important for binary data
    });
    
    console.log(`✅ Legacy PDF Download (GET) successful: ${response.status}, Content-Length: ${response.data.length}`);
    
    // Set proper headers for PDF download
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Length', response.data.length);
    
    // Extract filename from response headers if available
    const contentDisposition = response.headers['content-disposition'];
    if (contentDisposition) {
      res.setHeader('Content-Disposition', contentDisposition);
    } else {
      // Generate default filename
      const reportId = `RPT-${Date.now()}`;
      res.setHeader('Content-Disposition', `attachment; filename="${reportId}.pdf"`);
    }
    
    // Send binary data
    res.send(response.data);
    
  } catch (error) {
    console.error('❌ Legacy PDF Download (GET) failed:', error.message);
    res.status(503).json({
      error: 'Report Generation API unavailable',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Handle legacy requests that come without /api prefix (from older client code)
const legacyEndpoints = [
  '/prediction/current',
  '/prediction/defect',
  '/prediction/quality',
  '/prediction/forecast',
  '/prediction/rl-status',
  '/prediction/buffer-status',
  '/prediction/rl_action',
  '/current', 
  '/forecast', 
  '/defect', 
  '/quality',
  '/health',
  '/buffer-status',
  '/rl-status'
];

app.use(legacyEndpoints, createProxyMiddleware({
  target: PREDICTION_API_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/prediction/current': '/api/current',
    '^/prediction/defect': '/api/defect',
    '^/prediction/quality': '/api/quality',
    '^/prediction/forecast': '/api/forecast',
    '^/prediction/rl-status': '/api/rl-status',
    '^/prediction/buffer-status': '/api/buffer-status',
    '^/prediction/rl_action': '/api/rl_action',
    '^/current': '/api/current',
    '^/forecast': '/api/forecast',
    '^/defect': '/api/defect',
    '^/quality': '/api/quality',
    '^/health': '/api/health',
    '^/buffer-status': '/api/buffer-status',
    '^/rl-status': '/api/rl-status'
  },
  timeout: 15000,
  proxyTimeout: 15000,
  onError: (err, req, res) => {
    console.error(`❌ Legacy endpoint proxy error for ${req.url}:`, err.message);
    
    // Fallback for /current endpoint
    if (req.url === '/current' || req.url === '/prediction/current') {
      console.log(`🔄 LEGACY FALLBACK: Trying sensor API for ${req.url}`);
      const axios = require('axios');
      axios.get('https://cholesterol-sensor-api-4ad950146578.herokuapp.com/api/current', { timeout: 10000 })
        .then(response => {
          if (!res.headersSent) {
            console.log(`✅ SENSOR API FALLBACK: Success for ${req.url}`);
            res.json(response.data);
          }
        })
        .catch(sensorErr => {
          console.error(`❌ SENSOR API FALLBACK: Failed for ${req.url}:`, sensorErr.message);
          if (!res.headersSent) {
            // Final fallback to mock data
            const mockData = {
              status: 'success',
              data: {
                waste: Math.random() * 3 + 1,
                produced: Math.random() * 500 + 800,
                ejection: Math.random() * 40 + 100,
                tbl_speed: Math.random() * 30 + 90,
                stiffness: Math.random() * 50 + 75,
                SREL: Math.random() * 3 + 2.5,
                main_comp: Math.random() * 8 + 12,
                timestamp: new Date().toISOString()
              },
              source: 'legacy_emergency_fallback_mock',
              note: 'Both Prediction and Sensor APIs unavailable',
              generated_at: new Date().toISOString()
            };
            console.log(`🆘 LEGACY EMERGENCY FALLBACK: Using mock data for ${req.url}`);
            res.json(mockData);
          }
        });
    } else {
      // For other endpoints, just return error
      if (!res.headersSent) {
        res.status(500).json({ 
          error: 'Prediction API unavailable',
          message: `Unable to connect to prediction service at ${PREDICTION_API_URL}`,
          details: err.message,
          url: req.url,
          suggestion: `Try /api${req.url} instead`,
          timestamp: new Date().toISOString()
        });
      }
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`📜 LEGACY PROXY: ${req.method} ${req.url} -> ${PREDICTION_API_URL}/api${req.url.replace('/prediction', '')}`);
  },
  onProxyRes: (proxyRes, req, res) => {
    console.log(`📜 LEGACY PROXY RESPONSE: ${proxyRes.statusCode} for ${req.url}`);
  },
  logLevel: 'info'
}));

// ============================================================================
// MOCK DATA ENDPOINTS (FALLBACK)
// ============================================================================

// Enhanced mock data endpoint (handle both /api/mock/current and /mock/current)
app.get(['/api/mock/current', '/mock/current'], (req, res) => {
  const mockData = {
    status: 'success',
    data: {
      waste: Math.random() * 3 + 1,
      produced: Math.random() * 500 + 800,
      ejection: Math.random() * 40 + 100,
      tbl_speed: Math.random() * 30 + 90,
      stiffness: Math.random() * 50 + 75,
      SREL: Math.random() * 3 + 2.5,
      main_comp: Math.random() * 8 + 12,
      timestamp: new Date().toISOString()
    },
    source: 'mock_data_service',
    generated_at: new Date().toISOString()
  };
  
  console.log(`🎭 SERVING MOCK DATA for ${req.url}:`, JSON.stringify(mockData.data, null, 2));
  res.json(mockData);
});

// Mock prediction endpoints (handle both /api/mock/* and /mock/* patterns)
app.get(['/api/mock/forecast', '/mock/forecast'], (req, res) => {
  const forecast = [];
  for (let i = 1; i <= 12; i++) {
    forecast.push({
      timestep: i,
      sensors: {
        waste: Math.random() * 3 + 1,
        produced: Math.random() * 500 + 800,
        ejection: Math.random() * 40 + 100,
        tbl_speed: Math.random() * 30 + 90,
        stiffness: Math.random() * 50 + 75,
        SREL: Math.random() * 3 + 2.5,
        main_comp: Math.random() * 8 + 12
      }
    });
  }
  
  console.log(`🎭 SERVING MOCK FORECAST for ${req.url}`);
  res.json({
    forecast_horizon: 12,
    forecast: forecast,
    source: 'mock_prediction_service'
  });
});

app.get(['/api/mock/defect', '/mock/defect'], (req, res) => {
  const defectProb = Math.random() * 0.3 + 0.1; // 10-40% defect probability
  const riskLevel = defectProb > 0.7 ? 'high' : defectProb > 0.3 ? 'medium' : 'low';
  
  // Higher confidence for pharmaceutical defect predictions
  let confidence;
  if (riskLevel === 'low') {
    confidence = 0.88 + Math.random() * 0.10; // 88-98%
  } else if (riskLevel === 'medium') {
    confidence = 0.82 + Math.random() * 0.12; // 82-94%
  } else {
    confidence = 0.85 + Math.random() * 0.11; // 85-96%
  }
  
  console.log(`🎭 SERVING MOCK DEFECT for ${req.url}`);
  res.json({
    defect_probability: defectProb,
    confidence: Math.min(0.98, confidence),
    risk_level: riskLevel,
    preprocessing_applied: false,
    source: 'mock_prediction_service'
  });
});

app.get(['/api/mock/quality', '/mock/quality'], (req, res) => {
  const classes = ['High', 'Medium', 'Low'];
  const selectedClass = classes[Math.floor(Math.random() * classes.length)];
  
  // Generate more realistic confidence values for pharmaceutical applications
  let confidence;
  if (selectedClass === 'High') {
    confidence = 0.85 + Math.random() * 0.12; // 85-97%
  } else if (selectedClass === 'Medium') {
    confidence = 0.78 + Math.random() * 0.15; // 78-93%
  } else {
    confidence = 0.82 + Math.random() * 0.13; // 82-95%
  }
  
  // Generate balanced class probabilities that sum close to 1
  const probabilities = [Math.random(), Math.random(), Math.random()];
  const sum = probabilities.reduce((a, b) => a + b, 0);
  const normalizedProbs = probabilities.map(p => p / sum);
  
  console.log(`🎭 SERVING MOCK QUALITY for ${req.url}`);
  res.json({
    quality_class: selectedClass,
    confidence: Math.min(0.97, confidence),
    class_probabilities: {
      'High': normalizedProbs[0],
      'Medium': normalizedProbs[1], 
      'Low': normalizedProbs[2]
    },
    source: 'mock_prediction_service'
  });
});

// Mock report generation endpoints as fallbacks
app.get(['/api/mock/reports/health', '/mock/reports/health'], (req, res) => {
  console.log(`🎭 SERVING MOCK REPORT HEALTH for ${req.url}`);
  res.json({
    status: 'healthy',
    service: 'mock_report_generation',
    components: {
      llm_service: 'mock_healthy',
      knowledge_base: 'mock_healthy',
      data_collection: 'mock_healthy'
    },
    timestamp: new Date().toISOString(),
    note: 'This is a mock response - actual Report Generation API unavailable'
  });
});

app.get(['/api/mock/reports/types', '/mock/reports/types'], (req, res) => {
  console.log(`🎭 SERVING MOCK REPORT TYPES for ${req.url}`);
  res.json({
    available_report_types: [
      {
        type: 'quality_control',
        name: 'Quality Control Report',
        description: 'Comprehensive quality analysis and control report',
        template: 'quality_control_template'
      },
      {
        type: 'batch_record',
        name: 'Batch Record Analysis',
        description: 'Detailed batch manufacturing record analysis',
        template: 'batch_record_template'
      },
      {
        type: 'process_deviation',
        name: 'Process Deviation Investigation',
        description: 'Investigation report for process deviations',
        template: 'process_deviation_template'
      },
      {
        type: 'oee_performance',
        name: 'OEE Performance Summary',
        description: 'Overall Equipment Effectiveness performance analysis',
        template: 'oee_performance_template'
      },
      {
        type: 'regulatory_compliance',
        name: 'Regulatory Compliance Review',
        description: 'Regulatory compliance assessment report',
        template: 'regulatory_compliance_template'
      },
      {
        type: 'manufacturing_excellence',
        name: 'Manufacturing Excellence Report',
        description: 'Manufacturing excellence and optimization report',
        template: 'manufacturing_excellence_template'
      }
    ],
    source: 'mock_report_service',
    timestamp: new Date().toISOString()
  });
});

app.post(['/api/mock/reports/generate', '/mock/reports/generate'], (req, res) => {
  console.log(`🎭 SERVING MOCK REPORT GENERATION for ${req.url}`);
  const reportType = req.body?.report_type || 'quality_control';
  
  res.json({
    status: 'success',
    report: {
      report_id: `MOCK-RPT-${Date.now()}`,
      report_content: `# ${reportType.toUpperCase().replace(/_/g, ' ')} REPORT (MOCK)\n\nThis is a mock report generated for demonstration purposes.\n\n## Summary\nMock data analysis shows normal operation parameters.\n\n## Recommendations\n- Continue monitoring key metrics\n- Regular maintenance scheduled\n- No immediate actions required\n\n## Technical Details\n- Generated: ${new Date().toISOString()}\n- Data source: Mock simulation\n- Analysis method: Template-based`,
      metadata: {
        report_type: reportType,
        generated_at: new Date().toISOString(),
        source: 'mock_generator'
      },
      generation_details: {
        model_used: 'mock_llm_v1.0',
        processing_time: '2.3s',
        data_points_analyzed: 1000
      },
      generation_timestamp: new Date().toISOString()
    },
    source: 'mock_report_service',
    note: 'This is a mock response - actual Report Generation API unavailable'
  });
});

// Serve static files from the React app build directory
app.use(express.static(path.join(__dirname, 'client/build')));

// Enhanced health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'smart-pharma-copilot-ui',
    timestamp: new Date().toISOString(),
    ports: {
      ui_server: PORT,
      prediction_api: PREDICTION_API_PORT,
      report_api: REPORT_API_PORT,
      react_dev: 3000
    },
    proxies: {
      prediction_api: PREDICTION_API_URL,
      report_api: REPORT_API_URL,
      sensor_api: 'https://cholesterol-sensor-api-4ad950146578.herokuapp.com'
    },
    endpoints: {
      prediction_test: '/api/prediction-test',
      report_test: '/api/reports-test',
      mock_current: '/api/mock/current',
      mock_forecast: '/api/mock/forecast',
      mock_defect: '/api/mock/defect',
      mock_quality: '/api/mock/quality',
      mock_report_health: '/api/mock/reports/health'
    }
  });
});

// Enhanced API status endpoint
app.get('/api-status', async (req, res) => {
  const axios = require('axios');
  
  const checkService = async (url, name, timeout = 5000) => {
    try {
      const response = await axios.get(url, { timeout });
      return { 
        name, 
        status: 'healthy', 
        response_code: response.status,
        url: url,
        response_time: new Date().toISOString()
      };
    } catch (error) {
      return { 
        name, 
        status: 'unhealthy', 
        error: error.message,
        url: url,
        response_time: new Date().toISOString()
      };
    }
  };

  try {
    const [predictionAPI, sensorAPI, reportAPI] = await Promise.all([
      checkService(`${PREDICTION_API_URL}/api/health`, 'Prediction API'),
      checkService('https://cholesterol-sensor-api-4ad950146578.herokuapp.com/health', 'Sensor API'),
      checkService(`${REPORT_API_URL}/api/reports/health`, 'Report Generation API')
    ]);

    res.json({
      timestamp: new Date().toISOString(),
      services: [predictionAPI, sensorAPI, reportAPI],
      mock_available: true,
      ports: {
        ui_server: PORT,
        prediction_api: PREDICTION_API_PORT,
        report_api: REPORT_API_PORT
      },
      urls: {
        prediction_api: PREDICTION_API_URL,
        report_api: REPORT_API_URL,
        ui_server: `http://localhost:${PORT}`,
        react_dev: 'http://localhost:3000'
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Unable to check API status',
      timestamp: new Date().toISOString(),
      mock_available: true,
      details: error.message
    });
  }
});

// Catch all handler: send back React's index.html file for client-side routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'client/build', 'index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message,
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Smart Pharma Copilot UI server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`API status: http://localhost:${PORT}/api-status`);
  console.log(`Prediction API test: http://localhost:${PORT}/api/prediction-test`);
  console.log(`Report API test: http://localhost:${PORT}/api/reports-test`);
  console.log(`Dashboard: http://localhost:${PORT}`);
  console.log('');
  console.log('Port Configuration:');
  console.log(`  UI Server (Express): localhost:${PORT}`);
  console.log(`  Prediction API (FastAPI): ${PREDICTION_API_URL}`);
  console.log(`  Report Generation API (FastAPI): ${REPORT_API_URL}`);
  console.log(`  React Dev Server: localhost:3000`);
  console.log('');
  console.log('Proxy Configuration:');
  console.log(`  /api/prediction/* -> ${PREDICTION_API_URL}/api/*`);
  console.log(`  /api/reports/* -> ${REPORT_API_URL}/api/reports/*`);
  console.log(`  /reports/* -> ${REPORT_API_URL}/api/reports/* (LEGACY)`);
  console.log(`  /api/knowledge/* -> ${REPORT_API_URL}/api/knowledge/*`);
  console.log(`  /api/data/* -> ${REPORT_API_URL}/api/data/*`);
  console.log(`  /api/forecast, /api/defect, etc. -> ${PREDICTION_API_URL}/api/*`);
  console.log('  /api/sensor/* -> https://cholesterol-sensor-api-4ad950146578.herokuapp.com/api/*');
  console.log('  /api/current, /api/latest, /api/all -> https://cholesterol-sensor-api-4ad950146578.herokuapp.com/api/*');
  console.log('  /api/mock/* -> Local mock data services');
  console.log('');
  console.log('Testing endpoints:');
  console.log(`  curl http://localhost:${PORT}/health`);
  console.log(`  curl http://localhost:${PORT}/api-status`);
  console.log(`  curl http://localhost:${PORT}/api/prediction-test`);
  console.log(`  curl http://localhost:${PORT}/api/reports-test`);
  console.log(`  curl http://localhost:${PORT}/api/mock/current`);
  console.log(`  curl http://localhost:${PORT}/reports/health`);
  console.log(`  curl -X POST http://localhost:${PORT}/reports/generate`);
});
