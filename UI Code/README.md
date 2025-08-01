# Smart Pharmaceutical Manufacturing Copilot - UI Dashboard

A comprehensive real-time dashboard for pharmaceutical manufacturing process monitoring, AI-powered predictions, and Overall Equipment Effectiveness (OEE) tracking.

## 🏭 Overview

This React-based dashboard integrates with a FastAPI prediction service to provide:

- **Real-time sensor monitoring** with 7 key pharmaceutical parameters
- **AI-powered forecasting** using LSTM models for 60-minute predictions
- **Defect probability prediction** using XGBoost classifiers
- **Quality class prediction** with confidence scoring
- **Reinforcement Learning control recommendations** for process optimization
- **Comprehensive OEE calculations** with availability, performance, and quality metrics
- **Professional pharmaceutical-grade UI** with real-time updates

## 🏗️ Architecture

### Backend Services
- **FastAPI Prediction API** (`localhost:8000`) - AI models and predictions
- **External Sensor API** - Real-time pharmaceutical sensor data
- **Express Proxy Server** (`localhost:3001`) - API routing and static file serving

### Frontend Components
- **LiveSensors** - Real-time pharmaceutical sensor monitoring
- **ForecastPanel** - AI predictions with tabbed interface (Forecast/Defect/Quality)
- **RLControl** - Reinforcement learning action recommendations
- **OEEDisplay** - Comprehensive OEE metrics with historical trends
- **ReportsView** - Future GenAI integration for automated reporting

### Key Features
- **Dual API Integration**: Primary prediction API with sensor API fallback
- **Real-time Updates**: 5-8 second polling intervals for live data
- **Advanced OEE Calculation**: Pharmaceutical-specific metrics using AI predictions
- **Professional UI**: Gradient styling, animations, and responsive design
- **Error Handling**: Graceful degradation with fallback data sources

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- Python 3.8+ (for prediction API)
- FastAPI server running on localhost:8000

### Installation

1. **Install Dependencies**
   ```bash
   cd "UI Code"
   npm install
   npm run client:install  # Install React dependencies
   ```

2. **Start the Prediction API**
   ```bash
   cd "../Model Run Code"
   python prediction_api.py
   # Ensure it's running on localhost:8000
   ```

3. **Start the Dashboard**
   ```bash
   cd "../UI Code"
   npm run dev
   # Or separately:
   # npm run server  # Express server on :3001
   # npm run client  # React dev server on :3000
   ```

4. **Access Dashboard**
   - Dashboard: http://localhost:3000
   - Health Check: http://localhost:3001/health
   - API Status: http://localhost:3001/api-status

## 📊 Dashboard Panels

### 1. Live Sensor Monitoring
- **Data Source**: `/api/prediction/current` (primary) or `/api/current` (fallback)
- **Update Frequency**: Every 5 seconds
- **Key Metrics**: 
  - Main Compression Force, Tablet Speed, Stiffness, SREL Parameter
  - Production Output, Waste Material, Ejection Force
- **Features**: 
  - Interactive gauges with color-coded status
  - Grid layout for numerical values
  - API status indicators
  - Real-time data source switching

### 2. Quality Forecast (Multi-tab)
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

## 🔧 API Integration

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

## 🎨 Styling & UI

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

## 📱 Real-time Features

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

## 🔍 OEE Calculation Details

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

## 🛠️ Configuration

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

## 🔧 Troubleshooting

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

## 📈 Future Enhancements

### Planned Features
- WebSocket real-time connections
- Advanced analytics and trending
- Mobile app integration
- GenAI report automation
- Multi-language support
- Advanced alerting system

### Integration Opportunities
- SCADA system connectivity
- ERP system integration
- Laboratory information systems
- Quality management systems
- Regulatory compliance tracking

## 🤝 Contributing

When making changes:
1. Update component tests
2. Maintain API compatibility
3. Follow pharmaceutical UI guidelines
4. Test fallback mechanisms
5. Update documentation

## 📄 License

MIT License - Pharmaceutical Manufacturing Copilot

---

**Smart Pharmaceutical Manufacturing Copilot v1.0**  
Real-time AI-powered manufacturing optimization for the pharmaceutical industry. 