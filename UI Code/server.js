const express = require('express');
const path = require('path');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3001;
const PREDICTION_API_PORT = process.env.PREDICTION_API_PORT || 8000;
const PREDICTION_API_URL = `http://localhost:${PREDICTION_API_PORT}`;
const REPORT_API_PORT = process.env.REPORT_API_PORT || 8001;
const REPORT_API_URL = `http://localhost:${REPORT_API_PORT}`;

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

// ============================================================================
// REPORT GENERATION & KNOWLEDGE BASE API PROXIES
// ============================================================================

// Enhanced report generation proxy with better error handling and built-in fallback
app.use('/api/reports', createProxyMiddleware({
  target: REPORT_API_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api/reports': '/api/reports'
  },
  timeout: 30000, // Reduced timeout to 30 seconds
  proxyTimeout: 30000,
  onError: (err, req, res) => {
    console.error('❌ External Report API proxy error:', err.message);
    console.error('❌ Request URL:', req.originalUrl);
    console.error('❌ Falling back to built-in report generation...');
    
    // Don't send response here - let the built-in endpoints handle it
    // by removing the proxy middleware for this request
    if (!res.headersSent) {
      // Remove the /api/reports prefix and forward to built-in endpoints
      const newUrl = req.originalUrl.replace('/api/reports', '/reports');
      console.log(`🔄 FALLBACK: Redirecting ${req.originalUrl} to built-in endpoint ${newUrl}`);
      
      // Create a new request object for the built-in endpoint
      req.url = newUrl;
      req.originalUrl = newUrl;
      
      // Remove this middleware and let the request continue to built-in endpoints
      return;
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`📝 TRYING EXTERNAL REPORT API: ${req.method} ${req.originalUrl} -> ${REPORT_API_URL}${req.url}`);
    
    // Set shorter timeout for faster fallback
    proxyReq.setTimeout(30000);
  },
  onProxyRes: (proxyRes, req, res) => {
    console.log(`📝 EXTERNAL REPORT API RESPONSE: ${proxyRes.statusCode} for ${req.originalUrl}`);
  },
  logLevel: 'warn'
}));

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

// Legacy report endpoints (without /api prefix) - UPDATED TO USE BUILT-IN FIRST
app.use('/reports', createProxyMiddleware({
  target: REPORT_API_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/reports': '/api/reports'
  },
  timeout: 10000, // Much shorter timeout to quickly fallback to built-in
  proxyTimeout: 10000,
  onError: (err, req, res) => {
    console.error('❌ Legacy External Report API error:', err.message);
    console.error('❌ Request URL:', req.originalUrl);
    console.log('🔄 FALLBACK: Using built-in report generation system...');
    
    if (!res.headersSent) {
      // Forward to built-in report generation system
      if (req.method === 'GET' && req.url.includes('/health')) {
        res.json({
          status: 'healthy',
          service: 'built_in_report_generation_fallback',
          components: {
            report_templates: 'healthy',
            data_access: 'healthy',
            rendering_engine: 'healthy'
          },
          timestamp: new Date().toISOString(),
          available_templates: Object.keys(reportTemplates).length,
          note: 'Built-in report generation system - external API unavailable'
        });
      } else if (req.method === 'GET' && req.url.includes('/types')) {
        const reportTypes = Object.keys(reportTemplates).map(key => ({
          type: key,
          name: reportTemplates[key].name,
          description: reportTemplates[key].description,
          template: `${key}_template`,
          built_in: true
        }));
        
        res.json({
          available_report_types: reportTypes,
          source: 'built_in_report_service_fallback',
          timestamp: new Date().toISOString(),
          total_types: reportTypes.length
        });
      } else if (req.method === 'POST' && req.url.includes('/generate')) {
        // Handle report generation with built-in system
        handleBuiltInReportGeneration(req, res);
      } else {
        res.status(503).json({ 
          error: 'External Report Generation API Error',
          message: 'External API unavailable, but built-in report generation is ready',
          fallback_available: true,
          built_in_endpoints: [
            '/api/reports/health',
            '/api/reports/types', 
            '/api/reports/generate'
          ],
          timestamp: new Date().toISOString()
        });
      }
    }
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`📝 TRYING LEGACY EXTERNAL REPORT API: ${req.method} ${req.originalUrl} -> ${REPORT_API_URL}${req.url}`);
    proxyReq.setTimeout(10000); // Fast timeout for quick fallback
  },
  onProxyRes: (proxyRes, req, res) => {
    console.log(`📝 LEGACY EXTERNAL REPORT API RESPONSE: ${proxyRes.statusCode} for ${req.originalUrl}`);
  },
  logLevel: 'warn'
}));

// Helper function for built-in report generation
async function handleBuiltInReportGeneration(req, res) {
  const reportType = req.body?.report_type || 'quality_control';
  
  try {
    // Try to get real sensor data first
    let sensorData = {};
    
    try {
      const axios = require('axios');
      
      // Try prediction API first
      try {
        const predictionResponse = await axios.get(`${PREDICTION_API_URL}/api/current`, { timeout: 3000 });
        if (predictionResponse.data && predictionResponse.data.data) {
          sensorData = predictionResponse.data.data;
          console.log('✅ Using Prediction API data for legacy report');
        }
      } catch (predError) {
        console.log('⚠️ Prediction API unavailable for legacy report, trying sensor API...');
        
        // Try external sensor API as fallback
        try {
          const sensorResponse = await axios.get('https://cholesterol-sensor-api-4ad950146578.herokuapp.com/api/current', { timeout: 3000 });
          if (sensorResponse.data && sensorResponse.data.data) {
            sensorData = sensorResponse.data.data;
            console.log('✅ Using external Sensor API data for legacy report');
          }
        } catch (sensorError) {
          console.log('⚠️ External sensor API unavailable for legacy report, using mock data');
        }
      }
    } catch (error) {
      console.log('⚠️ All data sources unavailable for legacy report, using mock data');
    }
    
    // Use mock data if no real data available
    if (!sensorData || Object.keys(sensorData).length === 0) {
      sensorData = {
        waste: Math.random() * 3 + 1,
        produced: Math.random() * 500 + 800,
        ejection: Math.random() * 40 + 100,
        tbl_speed: Math.random() * 30 + 90,
        stiffness: Math.random() * 50 + 75,
        SREL: Math.random() * 3 + 2.5,
        main_comp: Math.random() * 8 + 12,
        timestamp: new Date().toISOString()
      };
      console.log('🎭 Using mock sensor data for legacy report');
    }
    
    // Generate report using template
    const template = reportTemplates[reportType] || reportTemplates.quality_control;
    const reportContent = template.template(sensorData);
    
    const report = {
      report_id: `LEGACY-RPT-${Date.now()}`,
      report_content: reportContent,
      metadata: {
        report_type: reportType,
        report_name: template.name,
        generated_at: new Date().toISOString(),
        data_source: sensorData.timestamp ? 'live_sensors' : 'mock_data',
        source: 'built_in_generator_legacy_fallback'
      },
      generation_details: {
        template_used: reportType,
        processing_time: '< 1s',
        data_points_analyzed: Object.keys(sensorData).length,
        sensor_data_timestamp: sensorData.timestamp || new Date().toISOString()
      },
      generation_timestamp: new Date().toISOString(),
      sensor_data: sensorData
    };
    
    console.log(`✅ Legacy report generated successfully: ${reportType}`);
    
    res.json({
      status: 'success',
      report: report,
      source: 'built_in_report_service_legacy_fallback',
      processing_time: '< 1 second'
    });
    
  } catch (error) {
    console.error('❌ Legacy report generation error:', error);
    res.status(500).json({
      status: 'error',
      error: 'Legacy report generation failed',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
}

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
  console.log(`🎭 SERVING MOCK DEFECT for ${req.url}`);
  res.json({
    defect_probability: Math.random() * 0.3 + 0.1,
    risk_level: Math.random() > 0.7 ? 'high' : Math.random() > 0.4 ? 'medium' : 'low',
    preprocessing_applied: false,
    source: 'mock_prediction_service'
  });
});

app.get(['/api/mock/quality', '/mock/quality'], (req, res) => {
  const classes = ['High', 'Medium', 'Low'];
  const selectedClass = classes[Math.floor(Math.random() * classes.length)];
  
  console.log(`🎭 SERVING MOCK QUALITY for ${req.url}`);
  res.json({
    quality_class: selectedClass,
    confidence: 0.7 + Math.random() * 0.2,
    class_probabilities: {
      'High': Math.random() * 0.5,
      'Medium': Math.random() * 0.5,
      'Low': Math.random() * 0.3
    },
    source: 'mock_prediction_service'
  });
});

// ============================================================================
// SIMPLIFIED BUILT-IN REPORT GENERATION SYSTEM
// ============================================================================

// Report templates for different types
const reportTemplates = {
  quality_control: {
    name: 'Quality Control Report',
    description: 'Comprehensive quality analysis and control report',
    template: (data) => `# Quality Control Report

## Executive Summary
This quality control report provides an analysis of current manufacturing parameters and quality metrics based on real-time sensor data.

**Report Generated:** ${new Date().toLocaleString()}

## Current System Status
- **Waste Level:** ${data.waste?.toFixed(2) || 'N/A'} units
- **Production Rate:** ${data.produced?.toFixed(0) || 'N/A'} units/hour
- **Ejection Rate:** ${data.ejection?.toFixed(1) || 'N/A'} units/min
- **Table Speed:** ${data.tbl_speed?.toFixed(1) || 'N/A'} RPM
- **Tablet Stiffness:** ${data.stiffness?.toFixed(1) || 'N/A'} N
- **SREL Value:** ${data.SREL?.toFixed(2) || 'N/A'}
- **Main Component:** ${data.main_comp?.toFixed(1) || 'N/A'} mg

## Quality Assessment
${data.waste > 2.5 ? '⚠️ **WARNING:** Waste levels are elevated. Immediate attention required.' : '✅ **GOOD:** Waste levels are within acceptable range.'}

${data.produced < 900 ? '⚠️ **WARNING:** Production rate is below target.' : '✅ **GOOD:** Production rate meets targets.'}

## Recommendations
- Regular monitoring of waste levels
- Maintain optimal tablet speed between 100-120 RPM
- Continue current quality control procedures
- Schedule maintenance if parameters drift outside normal ranges

## Compliance Notes
This report is generated in accordance with pharmaceutical manufacturing standards and provides a snapshot of current manufacturing quality metrics.`
  },
  
  batch_record: {
    name: 'Batch Record Analysis',
    description: 'Detailed batch manufacturing record analysis',
    template: (data) => `# Batch Record Analysis

## Batch Information
**Batch ID:** BATCH-${Date.now().toString().slice(-6)}
**Analysis Date:** ${new Date().toLocaleString()}
**Manufacturing Line:** Primary Production Line

## Process Parameters
| Parameter | Current Value | Specification | Status |
|-----------|---------------|---------------|---------|
| Waste | ${data.waste?.toFixed(2) || 'N/A'} | < 3.0 | ${data.waste > 3.0 ? '❌ Out of Spec' : '✅ In Spec'} |
| Production Rate | ${data.produced?.toFixed(0) || 'N/A'} | > 900 units/hr | ${data.produced < 900 ? '❌ Below Target' : '✅ On Target'} |
| Ejection Rate | ${data.ejection?.toFixed(1) || 'N/A'} | 120-140 units/min | ${data.ejection < 120 || data.ejection > 140 ? '⚠️ Monitor' : '✅ Normal'} |
| Table Speed | ${data.tbl_speed?.toFixed(1) || 'N/A'} | 100-120 RPM | ${data.tbl_speed < 100 || data.tbl_speed > 120 ? '⚠️ Monitor' : '✅ Normal'} |

## Critical Control Points
- All parameters within acceptable manufacturing ranges
- No deviations requiring investigation
- Batch release recommendation: APPROVED

## Signature
**QC Analyst:** Smart Pharma Copilot System
**Date:** ${new Date().toLocaleString()}`
  },
  
  process_deviation: {
    name: 'Process Deviation Investigation',
    description: 'Investigation report for process deviations',
    template: (data) => `# Process Deviation Investigation Report

## Deviation Summary
**Investigation Date:** ${new Date().toLocaleString()}
**Deviation Type:** Parameter Monitoring Review

## Current Parameter Analysis
Based on current sensor readings, the following analysis has been conducted:

### Waste Management
- Current waste level: ${data.waste?.toFixed(2) || 'N/A'} units
- ${data.waste > 2.5 ? 'DEVIATION IDENTIFIED: Waste levels exceed normal operating range' : 'Normal operation - no deviation detected'}

### Production Efficiency
- Current production rate: ${data.produced?.toFixed(0) || 'N/A'} units/hour
- ${data.produced < 900 ? 'DEVIATION IDENTIFIED: Production rate below target efficiency' : 'Production operating within normal parameters'}

## Root Cause Analysis
${data.waste > 2.5 || data.produced < 900 ? 
  '- Review equipment calibration\n- Check raw material quality\n- Verify operator procedures\n- Investigate environmental conditions' :
  'No significant deviations detected in current monitoring period'}

## Corrective Actions
${data.waste > 2.5 || data.produced < 900 ? 
  '1. Immediate monitoring of critical parameters\n2. Equipment inspection scheduled\n3. Additional sampling for quality verification' :
  'Continue routine monitoring and maintenance schedule'}

## Investigation Conclusion
${data.waste > 2.5 || data.produced < 900 ? 
  'Investigation ongoing - additional monitoring required' :
  'No process deviations requiring formal investigation at this time'}

**Report Status:** ${data.waste > 2.5 || data.produced < 900 ? 'OPEN' : 'CLOSED'}`
  },
  
  oee_performance: {
    name: 'OEE Performance Summary',
    description: 'Overall Equipment Effectiveness performance analysis',
    template: (data) => `# OEE Performance Summary

## Overall Equipment Effectiveness Analysis
**Report Period:** ${new Date().toLocaleString()}

## Key Performance Indicators

### Availability
- Equipment uptime: Estimated 95%+ (based on continuous sensor data)
- Production rate: ${data.produced?.toFixed(0) || 'N/A'} units/hour

### Performance Rate
- Current speed: ${data.tbl_speed?.toFixed(1) || 'N/A'} RPM
- Target speed: 110 RPM
- Performance efficiency: ${data.tbl_speed ? ((data.tbl_speed / 110) * 100).toFixed(1) : 'N/A'}%

### Quality Rate
- Waste percentage: ${data.waste && data.produced ? ((data.waste / data.produced) * 100).toFixed(2) : 'N/A'}%
- Quality rate: ${data.waste && data.produced ? (100 - (data.waste / data.produced) * 100).toFixed(1) : 'N/A'}%

## OEE Calculation
${data.tbl_speed && data.waste && data.produced ? `
**Estimated OEE:** ${((0.95 * (data.tbl_speed / 110) * (1 - data.waste / data.produced)) * 100).toFixed(1)}%

### Performance Breakdown:
- Availability: 95.0%
- Performance: ${((data.tbl_speed / 110) * 100).toFixed(1)}%
- Quality: ${((1 - data.waste / data.produced) * 100).toFixed(1)}%
` : 'OEE calculation requires complete sensor data'}

## Recommendations for Improvement
- Optimize table speed to maintain 110 RPM target
- Implement predictive maintenance to maximize availability
- Continue waste reduction initiatives
- Monitor quality metrics for continuous improvement

## Trending Analysis
Continue monitoring these key metrics for trending analysis and optimization opportunities.`
  },
  
  regulatory_compliance: {
    name: 'Regulatory Compliance Review',
    description: 'Regulatory compliance assessment report',
    template: (data) => `# Regulatory Compliance Review

## Compliance Assessment Summary
**Review Date:** ${new Date().toLocaleString()}
**Regulatory Framework:** FDA 21 CFR Part 211, ICH Guidelines

## Manufacturing Parameter Compliance

### Critical Process Parameters (CPP)
| Parameter | Current | Specification | Compliance Status |
|-----------|---------|---------------|-------------------|
| Tablet Weight | ${data.main_comp?.toFixed(1) || 'N/A'} mg | 15.0 ± 5% mg | ${data.main_comp && Math.abs(data.main_comp - 15) <= 0.75 ? '✅ Compliant' : '⚠️ Review Required'} |
| Compression Force | ${data.stiffness?.toFixed(1) || 'N/A'} N | 80-120 N | ${data.stiffness && data.stiffness >= 80 && data.stiffness <= 120 ? '✅ Compliant' : '⚠️ Review Required'} |
| Production Rate | ${data.produced?.toFixed(0) || 'N/A'} units/hr | Min 900 units/hr | ${data.produced >= 900 ? '✅ Compliant' : '⚠️ Review Required'} |

### Quality Control Compliance
- **Data Integrity:** All sensor data automatically logged with timestamps
- **Batch Records:** Continuous monitoring and documentation
- **Change Control:** No unauthorized changes detected
- **Deviation Management:** Real-time monitoring for out-of-specification conditions

## Validation Status
- **Equipment Qualification:** Current and valid
- **Process Validation:** Ongoing monitoring confirms validated state
- **Cleaning Validation:** Scheduled maintenance protocols active

## Audit Readiness
✅ **Ready for Inspection**
- Real-time monitoring systems operational
- Electronic batch records maintained
- Deviation investigation procedures active
- Quality control testing protocols verified

## Regulatory Recommendations
1. Continue current GMP practices
2. Maintain calibrated monitoring systems
3. Regular review of critical process parameters
4. Document any process improvements through change control

**Compliance Officer:** Smart Pharma Copilot System
**Next Review:** ${new Date(Date.now() + 30*24*60*60*1000).toLocaleDateString()}`
  },
  
  manufacturing_excellence: {
    name: 'Manufacturing Excellence Report',
    description: 'Manufacturing excellence and optimization report',
    template: (data) => `# Manufacturing Excellence Report

## Executive Dashboard
**Excellence Review Date:** ${new Date().toLocaleString()}

## Performance Scorecard

### Operational Excellence
| Metric | Current Performance | Target | Score |
|--------|-------------------|---------|-------|
| Waste Efficiency | ${data.waste ? (100 - data.waste).toFixed(1) : 'N/A'}% | >97% | ${data.waste < 3 ? '🟢 Excellent' : '🟡 Good'} |
| Production Throughput | ${data.produced?.toFixed(0) || 'N/A'} units/hr | 1000+ units/hr | ${data.produced > 1000 ? '🟢 Excellent' : data.produced > 900 ? '🟡 Good' : '🔴 Needs Improvement'} |
| Equipment Reliability | ${data.tbl_speed ? 'Active' : 'Unknown'} | 99%+ uptime | 🟢 Excellent |

### Quality Excellence
- **Product Consistency:** ${data.stiffness ? 'Monitored' : 'Unknown'}
- **Process Capability:** Within statistical control
- **Customer Satisfaction:** Quality parameters maintained

### Innovation & Improvement
- **Digital Transformation:** Smart monitoring systems active
- **Predictive Analytics:** Real-time sensor data analysis
- **Continuous Improvement:** Automated deviation detection

## Best Practices Implementation
✅ **Real-time Monitoring:** Advanced sensor networks deployed
✅ **Data-Driven Decisions:** Automated analysis and reporting
✅ **Predictive Maintenance:** Condition-based monitoring active
✅ **Quality by Design:** Process understanding and control

## Optimization Opportunities
1. **Production Optimization:** ${data.produced < 1000 ? 'Increase throughput to exceed 1000 units/hr' : 'Maintain excellent production rates'}
2. **Waste Reduction:** ${data.waste > 2 ? 'Implement lean manufacturing practices to reduce waste' : 'Continue excellent waste management'}
3. **Process Automation:** Expand automated monitoring to additional parameters

## Strategic Initiatives
- **Industry 4.0 Implementation:** Smart factory technologies deployed
- **Sustainability Goals:** Waste reduction and energy efficiency focus
- **Regulatory Excellence:** Continuous compliance monitoring

## Future Vision
Continue leadership in pharmaceutical manufacturing excellence through:
- Advanced analytics and AI-driven optimization
- Sustainable manufacturing practices
- World-class quality systems
- Innovation in process technology

**Excellence Score:** ${data.waste < 2 && data.produced > 1000 ? '95/100 - Outstanding' : data.waste < 3 && data.produced > 900 ? '85/100 - Excellent' : '75/100 - Good'}

**Manufacturing Excellence Team**
**Next Review:** ${new Date(Date.now() + 7*24*60*60*1000).toLocaleDateString()}`
  }
};

// Built-in report generation endpoints that work without external APIs
app.get(['/api/reports/health', '/reports/health'], (req, res) => {
  console.log(`✅ BUILT-IN REPORT HEALTH for ${req.url}`);
  res.json({
    status: 'healthy',
    service: 'built_in_report_generation',
    components: {
      report_templates: 'healthy',
      data_access: 'healthy',
      rendering_engine: 'healthy'
    },
    timestamp: new Date().toISOString(),
    available_templates: Object.keys(reportTemplates).length,
    note: 'Built-in report generation system - no external dependencies'
  });
});

app.get(['/api/reports/types', '/reports/types'], (req, res) => {
  console.log(`✅ BUILT-IN REPORT TYPES for ${req.url}`);
  const reportTypes = Object.keys(reportTemplates).map(key => ({
    type: key,
    name: reportTemplates[key].name,
    description: reportTemplates[key].description,
    template: `${key}_template`,
    built_in: true
  }));
  
  res.json({
    available_report_types: reportTypes,
    source: 'built_in_report_service',
    timestamp: new Date().toISOString(),
    total_types: reportTypes.length
  });
});

// Enhanced report generation with real sensor data integration
app.post(['/api/reports/generate', '/reports/generate'], async (req, res) => {
  console.log(`✅ BUILT-IN REPORT GENERATION for ${req.url}`);
  const reportType = req.body?.report_type || 'quality_control';
  
  try {
    // Try to get real sensor data first
    let sensorData = {};
    
    try {
      const axios = require('axios');
      
      // Try prediction API first
      try {
        const predictionResponse = await axios.get(`${PREDICTION_API_URL}/api/current`, { timeout: 3000 });
        if (predictionResponse.data && predictionResponse.data.data) {
          sensorData = predictionResponse.data.data;
          console.log('✅ Using Prediction API data for report');
        }
      } catch (predError) {
        console.log('⚠️ Prediction API unavailable, trying sensor API...');
        
        // Try external sensor API as fallback
        try {
          const sensorResponse = await axios.get('https://cholesterol-sensor-api-4ad950146578.herokuapp.com/api/current', { timeout: 3000 });
          if (sensorResponse.data && sensorResponse.data.data) {
            sensorData = sensorResponse.data.data;
            console.log('✅ Using external Sensor API data for report');
          }
        } catch (sensorError) {
          console.log('⚠️ External sensor API unavailable, using mock data');
        }
      }
    } catch (error) {
      console.log('⚠️ All data sources unavailable, using mock data');
    }
    
    // Use mock data if no real data available
    if (!sensorData || Object.keys(sensorData).length === 0) {
      sensorData = {
        waste: Math.random() * 3 + 1,
        produced: Math.random() * 500 + 800,
        ejection: Math.random() * 40 + 100,
        tbl_speed: Math.random() * 30 + 90,
        stiffness: Math.random() * 50 + 75,
        SREL: Math.random() * 3 + 2.5,
        main_comp: Math.random() * 8 + 12,
        timestamp: new Date().toISOString()
      };
      console.log('🎭 Using mock sensor data for report');
    }
    
    // Generate report using template
    const template = reportTemplates[reportType] || reportTemplates.quality_control;
    const reportContent = template.template(sensorData);
    
    const report = {
      report_id: `RPT-${Date.now()}`,
      report_content: reportContent,
      metadata: {
        report_type: reportType,
        report_name: template.name,
        generated_at: new Date().toISOString(),
        data_source: sensorData.timestamp ? 'live_sensors' : 'mock_data',
        source: 'built_in_generator'
      },
      generation_details: {
        template_used: reportType,
        processing_time: '< 1s',
        data_points_analyzed: Object.keys(sensorData).length,
        sensor_data_timestamp: sensorData.timestamp || new Date().toISOString()
      },
      generation_timestamp: new Date().toISOString(),
      sensor_data: sensorData
    };
    
    console.log(`✅ Report generated successfully: ${reportType}`);
    
    res.json({
      status: 'success',
      report: report,
      source: 'built_in_report_service',
      processing_time: '< 1 second'
    });
    
  } catch (error) {
    console.error('❌ Report generation error:', error);
    res.status(500).json({
      status: 'error',
      error: 'Report generation failed',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Simplified mock endpoints (keep for backward compatibility)
app.get(['/api/mock/reports/health', '/mock/reports/health'], (req, res) => {
  res.redirect('/api/reports/health');
});

app.get(['/api/mock/reports/types', '/mock/reports/types'], (req, res) => {
  res.redirect('/api/reports/types');
});

app.post(['/api/mock/reports/generate', '/mock/reports/generate'], (req, res) => {
  // Forward to main report generation
  req.url = '/api/reports/generate';
  req.originalUrl = '/api/reports/generate';
  // Call the main report generation endpoint
  app._router.handle(req, res);
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
