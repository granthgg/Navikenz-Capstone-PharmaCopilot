# PharmaCopilot UI Dashboard

React-based web interface for the PharmaCopilot pharmaceutical manufacturing optimization system.

## Features

- Real-time sensor monitoring and visualization
- AI-powered forecasting and quality predictions
- Reinforcement learning control recommendations
- Overall Equipment Effectiveness (OEE) tracking
- Automated compliance report generation
- Interactive process optimization dashboard

## Architecture

- **Frontend**: React.js with Chart.js visualizations
- **Backend**: Express.js proxy server with API routing
- **Real-time Updates**: WebSocket integration for live sensor data
- **API Integration**: Connects to Prediction API, Report Generation API, and Sensor Simulation

## Quick Start

### Prerequisites
- Node.js 16+
- PharmaCopilot backend services running (see main README)

### Installation

```bash
cd "UI Code"
npm install
cd client && npm install
```

### Running the Dashboard

```bash
# Start the complete system
npm start

# Development mode with auto-reload
npm run dev
```

### API Endpoints

The dashboard connects to these backend services:
- **Prediction API**: `http://localhost:8000` - ML model inference
- **Report Generation API**: `http://localhost:8001` - AI-powered reports
- **Sensor Simulation**: `http://localhost:8002` - Real-time sensor data

### Component Overview

- **HomePage**: System overview and key performance indicators
- **LiveSensors**: Real-time sensor monitoring with WebSocket updates
- **ForecastPanel**: LSTM forecasting and classification predictions
- **RLControl**: Reinforcement learning process recommendations
- **ReportsView**: AI-generated compliance reports
- **OEEDisplay**: Overall Equipment Effectiveness calculations

### Configuration

Update API endpoints in `server.js`:
```javascript
const PREDICTION_API_URL = 'http://localhost:8000';
const REPORT_API_URL = 'http://localhost:8001';
```

## Development

### Testing API Connections
```bash
npm run test-local-report-api
```

### Building for Production
```bash
cd client && npm run build
```

For complete setup instructions, see the main project README.
- **Forecast Tab**: 60-minute LSTM sensor predictions
- **Defect Risk Tab**: AI-powered defect probability analysis
- **Quality Tab**: Quality class prediction with confidence scores
- **Data Sources**: 
  - `/api/prediction/forecast` - LSTM forecasting
  - `/api/prediction/defect` - Defect classification
  - `/api/prediction/quality` - Quality prediction
- **Features**:
  - Interactive charts with Recharts
  - Risk level indicators (Low/Medium/High)
  - Preprocessing status information
  - Fallback simulation mode

### 3. RL Control System
- **Data Source**: `/api/prediction/rl_action/{model_type}`
- **Update Frequency**: Every 15 seconds
- **Features**:
  - Model selection (CQL, etc.)
  - Speed, compression, and fill weight adjustments
  - AI reasoning explanations
  - Operator feedback logging (Accept/Reject)
  - Safety clipping indicators
  - Buffer status monitoring

### 4. OEE Dashboard (Enhanced)
- **Calculation Method**: Real-time pharmaceutical-specific metrics
- **Status Thresholds**: 
  - **Excellent**: ≥75% (Green)
  - **Good**: 65-74% (Light Blue) 
  - **Fair**: 55-64% (Yellow)
  - **Poor**: <55% (Red)
- **Components**:
  - **Availability**: Machine uptime, operational status
  - **Performance**: Speed efficiency, production rates (allows >100%)
  - **Quality**: AI defect/quality predictions + sensor validation
- **Features**:
  - Interactive gauge charts for each component
  - Historical trend analysis (last 20 measurements)
  - Production metrics display
  - AI-powered insights and recommendations
  - Integration with defect and quality predictions

### 5. AI Reports Center
- **Status**: Integration pending with GenAI systems
- **Planned Features**:
  - 21 CFR 11 compliant report generation
  - Automated narrative analysis
  - Regulatory submission formats

##  API Integration

### Prediction API Endpoints
```
GET /api/prediction/current       # Current sensor data
GET /api/prediction/forecast      # 60-minute LSTM forecast
GET /api/prediction/defect        # Defect probability
GET /api/prediction/quality       # Quality classification
GET /api/prediction/rl_action/cql # RL recommendations
GET /api/prediction/buffer-status # Data buffer information
POST /api/prediction/supplement-buffer # Manual buffer refresh
```

### Sensor API Endpoints (Fallback)
```
GET /api/current           # Current sensor readings
GET /api/latest/{count}    # Historical data points
GET /api/all              # All available data
```

### Proxy Configuration
The Express server automatically routes:
- `/api/prediction/*` → `localhost:8000/api/*`
- `/api/sensor/*` → External sensor API
- `/api/*` → External sensor API (legacy compatibility)

##  Styling & UI

### Design System
- **Color Scheme**: Professional pharmaceutical blue/green/orange
- **Typography**: Clean, readable fonts with proper hierarchy
- **Animations**: Subtle transitions and real-time pulse effects
- **Responsive**: Mobile-friendly grid layouts

### Key CSS Classes
- `.panel` - Main container with gradient background
- `.status-indicator` - Color-coded status badges
- `.gauge` - Sensor gauge containers
- `.data-grid` - Responsive data layout
- `.forecast-probability` - Large metric displays
- `.btn-accept/.btn-reject` - Operator control buttons

##  Real-time Features

### Update Frequencies
- **Live Sensors**: 5 seconds
- **Forecast Panel**: 10 seconds
- **RL Control**: 15 seconds
- **OEE Dashboard**: 8 seconds

### Performance Optimizations
- Parallel API calls using `Promise.allSettled()`
- Graceful error handling with fallback data
- Efficient state management in React
- Conditional rendering for large datasets
- Chart optimizations with `ResponsiveContainer`

##  OEE Calculation Details

### Availability Calculation
```javascript
// Base availability: 98% (higher baseline)
// Deductions (very lenient):
- Machine stopped (tbl_speed < 5): -12%
- High ejection force (>180): -4%
- High waste (>8): -2%
- No production: -15%
- Insufficient buffer data: -3%
```

### Performance Calculation
```javascript
// Speed efficiency: (actual_speed / 90_RPM_target) * 100
// Production efficiency: (actual_production / 700_target) * 100
// Weighted average: speed(70%) + production(30%)
// Very minor penalties for suboptimal compression/stiffness
// Allows exceeding 100% for exceptional performance
```

### Quality Calculation
```javascript
// Primary: AI defect prediction (1 - defect_probability) * 100
// Fallback: Sensor-based quality checks (very lenient penalties)
// AI quality class multiplier (High: 1.03, Medium: 1.0, Low: 0.95)
// Pharmaceutical standards: minimum 92%, typical 96-99%
// Removed random variation for consistent calculations
```

##  Configuration

### Environment Variables
```bash
# Server Configuration
PORT=3001                    # Express server port
REACT_APP_API_TIMEOUT=10000  # API timeout in ms

# API Endpoints
PREDICTION_API_URL=http://localhost:8000
SENSOR_API_URL=https://cholesterol-sensor-api-4ad950146578.herokuapp.com
```

### Customization
- **Sensor Selection**: Modify `selected_sensors` array in components
- **Update Frequencies**: Adjust `setInterval` timings
- **OEE Thresholds**: Update calculation functions
- **Color Schemes**: Modify CSS custom properties

##  Troubleshooting

### Common Issues

1. **Prediction API Not Available**
   - Ensure FastAPI server is running on localhost:8000
   - Check API health: `curl http://localhost:8000/api/health`
   - Dashboard automatically falls back to sensor API

2. **No Sensor Data**
   - Verify external sensor API connectivity
   - Check buffer status in OEE dashboard
   - Use manual buffer supplementation

3. **Charts Not Rendering**
   - Ensure recharts dependency is installed
   - Check browser console for JavaScript errors
   - Verify data format compatibility

4. **Performance Issues**
   - Reduce update frequencies if needed
   - Monitor network tab for API response times
   - Consider caching strategies for large datasets

### Debug Endpoints
- `/health` - UI server health
- `/api-status` - Check all API connections
- `/api/prediction/buffer-status` - Check data availability






---

**Smart Pharmaceutical Manufacturing Copilot v1.0**  
Real-time AI-powered manufacturing optimization for the pharmaceutical industry. 
