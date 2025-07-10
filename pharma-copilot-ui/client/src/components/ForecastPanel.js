import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import axios from 'axios';

const ForecastPanel = () => {
  const [forecastData, setForecastData] = useState([]);
  const [currentProbability, setCurrentProbability] = useState(0.15);
  const [status, setStatus] = useState('nominal');
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);

  // Simulate forecast data based on sensor readings
  useEffect(() => {
    const generateForecastData = async () => {
      try {
        // Fetch current sensor data to base predictions on
        const response = await axios.get('/api/current');
        
        if (response.data && response.data.status === 'success') {
          const sensorData = response.data.data;
          
          // Generate mock forecast data based on current sensor readings
          // In real implementation, this would call your LSTM model
          const baseDefectProbability = Math.random() * 0.3 + 0.1; // 0.1 to 0.4
          const mockForecast = [];
          
          for (let i = 0; i < 12; i++) {
            const time = new Date();
            time.setMinutes(time.getMinutes() + (i * 5));
            
            // Simulate probability fluctuation based on actual sensor conditions
            let probability = baseDefectProbability + (Math.random() - 0.5) * 0.1;
            
            // Increase probability if pharmaceutical sensor values are concerning
            if (sensorData.main_comp > 20) probability += 0.1; // High compression force
            if (sensorData.tbl_fill < 3 || sensorData.tbl_fill > 8) probability += 0.05; // Fill weight out of range
            if (sensorData.SREL > 8) probability += 0.05; // SREL parameter high
            if (sensorData.stiffness < 50) probability += 0.03; // Low tablet stiffness
            if (sensorData.ejection > 150) probability += 0.04; // High ejection force
            if (sensorData.waste > 5) probability += 0.02; // High waste
            
            probability = Math.max(0, Math.min(1, probability));
            
            mockForecast.push({
              time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              probability: probability,
              mainComp: sensorData.main_comp + (Math.random() - 0.5) * 2,
              tblFill: sensorData.tbl_fill + (Math.random() - 0.5) * 0.5,
              stiffness: sensorData.stiffness + (Math.random() - 0.5) * 10
            });
          }
          
          setForecastData(mockForecast);
          setCurrentProbability(mockForecast[0].probability);
          
          // Determine status based on probability
          if (mockForecast[0].probability < 0.3) {
            setStatus('nominal');
          } else if (mockForecast[0].probability < 0.7) {
            setStatus('warning');
          } else {
            setStatus('critical');
          }
          
          setLastUpdate(new Date().toLocaleTimeString());
          setError(null);
        }
      } catch (err) {
        console.error('Error generating forecast:', err);
        setError('Forecast model unavailable');
      }
    };

    generateForecastData();
    const intervalId = setInterval(generateForecastData, 10000); // Update every 10 seconds

    return () => clearInterval(intervalId);
  }, []);

  const getStatusConfig = () => {
    switch (status) {
      case 'nominal':
        return {
          className: 'status-healthy',
          label: 'NOMINAL OPERATION',
          message: 'Pharmaceutical manufacturing process within acceptable parameters'
        };
      case 'warning':
        return {
          className: 'status-warning',
          label: 'HIGH DEFECT PROBABILITY',
          message: 'Increased monitoring recommended - Check tablet compression and fill parameters'
        };
      case 'critical':
        return {
          className: 'status-critical',
          label: 'ACTION REQUIRED',
          message: 'High defect probability detected - Immediate pharmaceutical process intervention needed'
        };
      default:
        return {
          className: 'status-offline',
          label: 'UNKNOWN STATUS',
          message: 'Forecast data unavailable'
        };
    }
  };

  const statusConfig = getStatusConfig();

  if (error) {
    return (
      <div className="panel error-panel forecast-panel">
        <div className="status-indicator status-offline">
          Forecast Offline
        </div>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="panel forecast-panel">
      
      <div className={`status-indicator ${statusConfig.className}`}>
        {statusConfig.label}
      </div>

      <div className="forecast-status">
        <div className={`forecast-probability ${status}`}>
          {(currentProbability * 100).toFixed(1)}%
        </div>
        <div className="forecast-message">
          Defect Probability
        </div>
        <p style={{ fontSize: '0.8rem', color: '#6c757d', marginTop: '0.5rem' }}>
          {statusConfig.message}
        </p>
      </div>

      {forecastData.length > 0 && (
        <div style={{ marginTop: '1.5rem', height: '200px' }}>
          <h4 style={{ fontSize: '0.875rem', color: '#495057', marginBottom: '0.5rem' }}>
            60-Minute Forecast
          </h4>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
              <XAxis 
                dataKey="time" 
                fontSize={10}
                stroke="#6c757d"
              />
              <YAxis 
                domain={[0, 1]}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                fontSize={10}
                stroke="#6c757d"
              />
              <Tooltip 
                formatter={(value) => [`${(value * 100).toFixed(1)}%`, 'Defect Probability']}
                labelStyle={{ color: '#495057' }}
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  fontSize: '0.75rem'
                }}
              />
              <ReferenceLine 
                y={0.7} 
                stroke="#dc3545" 
                strokeDasharray="5 5"
                label={{ value: "Action Threshold", position: "insideTopRight", fontSize: 10 }}
              />
              <Line 
                type="monotone" 
                dataKey="probability" 
                stroke="#007bff" 
                strokeWidth={2}
                dot={{ fill: '#007bff', strokeWidth: 2, r: 3 }}
                activeDot={{ r: 5, stroke: '#007bff', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {lastUpdate && (
        <div style={{ fontSize: '0.75rem', color: '#6c757d', marginTop: '1rem', textAlign: 'center' }}>
          Last forecast update: {lastUpdate}
        </div>
      )}
    </div>
  );
};

export default ForecastPanel; 