# Smart Pharma Copilot - Web Interface

A professional React/Node.js web interface for intelligent pharmaceutical manufacturing monitoring and control. Features real-time sensor data visualization, AI-powered forecasting, reinforcement learning control recommendations, and comprehensive reporting capabilities.

## Features

- **Real-time Sensor Monitoring** - Live data from pharmaceutical manufacturing sensors
- **AI-Powered Quality Forecasting** - LSTM-based defect probability predictions  
- **RL Control System** - Intelligent action recommendations with human-in-the-loop feedback
- **OEE Dashboard** - Overall Equipment Effectiveness monitoring and analysis
- **AI Reports Center** - Placeholder for future GenAI report generation integration
- **Professional UI** - Clean, materialistic black and white design theme
- **Responsive Design** - Optimized for desktop and mobile devices

## Technology Stack

### Backend
- **Node.js** with Express.js
- **API Proxy** to Heroku sensor data endpoint
- **CORS** enabled for cross-origin requests

### Frontend  
- **React 18** with functional components and hooks
- **Axios** for API communication
- **Recharts** for data visualization
- **React Gauge Chart** for real-time gauges
- **Responsive CSS Grid** layout

## Quick Start

### Prerequisites
- Node.js (version 16 or higher)
- npm or yarn package manager

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd pharma-copilot-ui
   ```

2. **Install backend dependencies:**
   ```bash
   npm install
   ```

3. **Install frontend dependencies:**
   ```bash
   cd client
   npm install
   cd ..
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

   This will start both the backend server (port 3001) and React development server (port 3000).

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend health check: http://localhost:3001/health

### Production Build

```bash
# Build the React app
cd client
npm run build
cd ..

# Start production server
npm start
```

## API Integration

The application integrates with your pharmaceutical sensor API:

- **Endpoint:** `https://cholesterol-sensor-api-4ad950146578.herokuapp.com/api/current`
- **Proxy:** Backend Express server handles CORS and API proxying
- **Data Source:** Real-time pharmaceutical manufacturing sensor data
- **Update Frequency:** 5-second polling for live sensor readings

### Available Sensor Data

The interface displays the following sensor metrics:
- Compression Force (kN)
- Tablet Hardness (N)  
- Moisture Content (%)
- Air Temperature (°C)
- Air Humidity (%)
- Relative Humidity (%)
- Machine Speed (RPM)
- Production Rate (units/hr)

## Component Architecture

### Main Dashboard (`App.js`)
- Central container managing all dashboard components
- Responsive grid layout for optimal viewing
- Professional header with branding

### LiveSensors (`LiveSensors.js`)
- Real-time sensor data visualization
- Interactive gauges for key metrics
- Numeric displays for all sensor values
- Error handling and offline status

### ForecastPanel (`ForecastPanel.js`)
- LSTM-based quality forecasting (simulated)
- Defect probability predictions
- 60-minute forecast charts with threshold indicators
- Status-based color coding (Nominal/Warning/Critical)

### RLControl (`RLControl.js`)
- Reinforcement learning action recommendations
- Human-in-the-loop operator feedback
- Safety layer status monitoring
- Action reasoning and confidence scores

### OEEDisplay (`OEEDisplay.js`)
- Overall Equipment Effectiveness calculation
- Availability, Performance, and Quality breakdown
- Color-coded status indicators
- Performance insights and recommendations

### ReportsView (`ReportsView.js`)
- Placeholder for GenAI report integration
- Mock report data and generation options
- 21 CFR 11 compliance features preview
- Future integration roadmap

## Customization

### Styling
- Modify `client/src/App.css` for global styles
- Professional black/white materialistic theme
- Responsive design with CSS Grid
- Hover animations and transitions

### API Configuration
- Update proxy target in `server.js`
- Modify polling intervals in component files
- Add authentication headers if required

### Data Processing
- Customize sensor data mapping in `LiveSensors.js`
- Adjust forecast algorithms in `ForecastPanel.js`
- Modify RL logic in `RLControl.js`
- Update OEE calculations in `OEEDisplay.js`

## Model Integration

The interface is designed to integrate with your trained models:

### Forecasting Models
- **LSTM Model:** `lstm_sensor_forecasting_model.h5`
- **Scalers:** `lstm_scalers.pkl`
- **Features:** Based on real-time sensor data

### Classification Models  
- **XGBoost Defect Classifier:** `xgboost_defect_classifier.pkl`
- **Quality Classifier:** `xgboost_quality_class_classifier.pkl`
- **Feature Processing:** `feature_scaler.pkl`, `feature_names.txt`

### Reinforcement Learning
- **CQL Models:** `pharma_cql_*.pt` files
- **Hyperparameters:** `best_hyperparameters_*.json`
- **Action Space:** Speed, compression, temperature adjustments

## Environment Variables

Create a `.env` file in the root directory for configuration:

```env
# Server Configuration
PORT=3001
NODE_ENV=production

# API Configuration  
SENSOR_API_URL=https://cholesterol-sensor-api-4ad950146578.herokuapp.com
API_TIMEOUT=10000

# Security
CORS_ORIGIN=http://localhost:3000
```

## Deployment

### Heroku Deployment

1. **Prepare for deployment:**
   ```bash
   git add .
   git commit -m "Deploy Smart Pharma Copilot"
   ```

2. **Create Heroku app:**
   ```bash
   heroku create your-pharma-copilot-app
   ```

3. **Deploy:**
   ```bash
   git push heroku main
   ```

The `heroku-postbuild` script will automatically build the React app.

### Docker Deployment

```dockerfile
FROM node:16-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
WORKDIR /app/client
RUN npm install && npm run build

WORKDIR /app
EXPOSE 3001
CMD ["npm", "start"]
```

## Development Scripts

```bash
# Start both backend and frontend in development
npm run dev

# Start backend only
npm run server

# Start frontend only  
npm run client

# Build for production
cd client && npm run build

# Run production server
npm start
```

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (iOS Safari, Android Chrome)

## Performance Optimization

- **Component memoization** for expensive operations
- **Efficient polling** with cleanup on unmount
- **Responsive images** and optimized assets
- **Code splitting** for faster load times
- **Progressive Web App** features ready

## Security Considerations

- **API proxy** prevents CORS issues and hides endpoints
- **Input validation** on all user interactions
- **Error boundaries** for graceful failure handling
- **Secure headers** in production deployment

## Future Enhancements

- **WebSocket integration** for real-time data streaming
- **GenAI report generation** with LangChain/RAG integration
- **Advanced analytics** and trend analysis
- **Multi-language support** for global operations
- **Mobile app** development with React Native
- **Advanced authentication** and role-based access

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check if sensor API is accessible
   - Verify proxy configuration in `server.js`
   - Check network connectivity

2. **Components Not Loading**
   - Ensure all dependencies are installed
   - Check browser console for errors
   - Verify React version compatibility

3. **Styling Issues**
   - Clear browser cache
   - Check CSS conflicts
   - Verify font loading from Google Fonts

### Debug Mode

Set `NODE_ENV=development` for detailed error messages and debugging information.

## Support

For technical support or questions about integration:
- Review the component documentation in source files
- Check the browser developer console for errors
- Verify API endpoint accessibility and data format

## License

This project is developed for pharmaceutical manufacturing monitoring and control. All rights reserved.

---

**Smart Pharma Copilot** - Intelligent Pharmaceutical Manufacturing Control System 