import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GaugeChart from 'react-gauge-chart';
import LoadingSpinner from './LoadingSpinner';

const LiveSensors = () => {
  const [sensorData, setSensorData] = useState(null);
  const [predictionApiStatus, setPredictionApiStatus] = useState(null);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

  // Mock data generator for when all APIs fail
  const generateMockData = () => {
    return {
      waste: Math.random() * 3 + 1,
      produced: Math.random() * 500 + 800,
      ejection: Math.random() * 40 + 100,
      tbl_speed: Math.random() * 30 + 90,
      stiffness: Math.random() * 50 + 75,
      SREL: Math.random() * 3 + 2.5,
      main_comp: Math.random() * 8 + 12,
      timestamp: new Date().toISOString()
    };
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (!hasLoadedOnce) {
          setIsLoading(true);
        }
        
        // Try prediction API first
        try {
          const predictionResponse = await axios.get('/api/prediction/current', { timeout: 8000 });
          
          if (predictionResponse.data && predictionResponse.data.sensors) {
            setSensorData(predictionResponse.data.sensors);
            setLastUpdate(new Date().toLocaleTimeString());
            setError(null);
            setPredictionApiStatus('connected');
            return;
          }
        } catch (predictionErr) {
          console.warn('Prediction API unavailable:', predictionErr.message);
          setPredictionApiStatus('error');
        }

        // Try direct endpoints if prediction API prefix fails
        try {
          const directResponse = await axios.get('/api/current', { timeout: 8000 });
          
          if (directResponse.data && directResponse.data.status === 'success' && directResponse.data.data) {
            setSensorData(directResponse.data.data);
            setLastUpdate(new Date().toLocaleTimeString());
            setError('Using sensor API - Sensors unavailable');
            setPredictionApiStatus('fallback');
            return;
          }
        } catch (sensorErr) {
          console.warn('Sensor API unavailable:', sensorErr.message);
        }

        // Try mock data endpoint as last resort
        try {
          const mockResponse = await axios.get('/api/mock/current', { timeout: 5000 });
          
          if (mockResponse.data && mockResponse.data.status === 'success') {
            setSensorData(mockResponse.data.data);
            setLastUpdate(new Date().toLocaleTimeString());
            setError('Using mock data - Both APIs unavailable');
            setPredictionApiStatus('mock');
            return;
          }
        } catch (mockErr) {
          console.warn('Mock API unavailable:', mockErr.message);
        }

        // If all APIs fail, generate local mock data
        const mockData = generateMockData();
        setSensorData(mockData);
        setLastUpdate(new Date().toLocaleTimeString());
        setError('Using local simulation - All APIs unavailable');
        setPredictionApiStatus('offline');

      } catch (err) {
        console.error('Complete data fetch failure:', err);
        
        // Generate emergency mock data
        const mockData = generateMockData();
        setSensorData(mockData);
        setLastUpdate(new Date().toLocaleTimeString());
        setError('Emergency mode - Using simulated data');
        setPredictionApiStatus('offline');
      } finally {
        if (!hasLoadedOnce) {
          setIsLoading(false);
          setHasLoadedOnce(true);
        }
      }
    };

    // Fetch immediately on component mount
    fetchData();
    
    // Poll every 6 seconds for real-time updates
    const intervalId = setInterval(fetchData, 6000);

    return () => clearInterval(intervalId);
  }, [hasLoadedOnce]);

  const getStatusIndicator = () => {
    switch (predictionApiStatus) {
      case 'connected':
        return { class: 'status-healthy', text: 'Sensors Connected' };
      case 'fallback':
        return { class: 'status-warning', text: 'Sensor API Fallback Active' };
      case 'mock':
        return { class: 'status-warning', text: 'Mock Data Mode' };
      case 'offline':
        return { class: 'status-critical', text: 'Simulation Mode' };
      default:
        return { class: 'status-offline', text: 'System Initializing' };
    }
  };

  if (isLoading && !hasLoadedOnce) {
    return (
      <div className="panel loading-panel-modern live-sensors-panel" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '300px',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <LoadingSpinner size="large" color="#000000" message="Connecting to sensor systems" />
        <div style={{ fontSize: '0.75rem', color: '#666666', textAlign: 'center', maxWidth: '250px' }}>
          Establishing connection to live pharmaceutical sensors
        </div>
      </div>
    );
  }

  const statusInfo = getStatusIndicator();

  // Calculate gauge percentages for main pharmaceutical parameters
  const speedPercent = Math.min((sensorData?.tbl_speed || 0) / 150, 1);
  const stiffnessPercent = Math.min((sensorData?.stiffness || 0) / 200, 1);
  const srelPercent = Math.min((sensorData?.SREL || 0) / 10, 1);
  const mainCompPercent = Math.min((sensorData?.main_comp || 0) / 25, 1);

  return (
    <div className="panel live-sensors-panel">
      <div className={`status-indicator ${statusInfo.class}`}>
        {statusInfo.text} - Last Update: {lastUpdate}
      </div>

      {error && (
        <div style={{ 
          background: predictionApiStatus === 'offline' ? '#f8d7da' : '#fff3cd', 
          color: predictionApiStatus === 'offline' ? '#721c24' : '#856404', 
          padding: '0.75rem', 
          borderRadius: '6px', 
          marginBottom: '1rem',
          fontSize: '0.8rem',
          border: `1px solid ${predictionApiStatus === 'offline' ? '#f5c6cb' : '#ffeaa7'}`
        }}>
          <strong>Notice:</strong> {error}
          {predictionApiStatus === 'offline' && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem' }}>
              • Check if sensor service is running on localhost:8000<br/>
              • Verify network connectivity to sensor API<br/>
              • Data shown is simulated for demonstration purposes
            </div>
          )}
        </div>
      )}

      <div className="gauges-container">
        <div className="gauge">
          <h4>Main Compression Force</h4>
          <GaugeChart
            id="gauge-main-comp"
            nrOfLevels={20}
            percent={mainCompPercent}
            textColor="#333"
            colors={['#28a745', '#ffc107', '#dc3545']}
            arcWidth={0.3}
            hideText={true}
          />
          <p>{(sensorData?.main_comp || 0).toFixed(2)} kN</p>
        </div>
        
        <div className="gauge">
          <h4>Tablet Speed</h4>
          <GaugeChart
            id="gauge-tbl-speed"
            nrOfLevels={20}
            percent={speedPercent}
            textColor="#333"
            colors={['#dc3545', '#ffc107', '#28a745']}
            arcWidth={0.3}
            hideText={true}
          />
          <p>{(sensorData?.tbl_speed || 0).toFixed(1)} RPM</p>
        </div>

        <div className="gauge">
          <h4>Tablet Stiffness</h4>
          <GaugeChart
            id="gauge-stiffness"
            nrOfLevels={20}
            percent={stiffnessPercent}
            textColor="#333"
            colors={['#dc3545', '#ffc107', '#28a745']}
            arcWidth={0.3}
            hideText={true}
          />
          <p>{(sensorData?.stiffness || 0).toFixed(2)} N/mm</p>
        </div>

        <div className="gauge">
          <h4>SREL Parameter</h4>
          <GaugeChart
            id="gauge-srel"
            nrOfLevels={20}
            percent={srelPercent}
            textColor="#333"
            colors={['#28a745', '#ffc107', '#dc3545']}
            arcWidth={0.3}
            hideText={true}
          />
          <p>{(sensorData?.SREL || 0).toFixed(2)}</p>
        </div>
      </div>

      <div className="numeric-data">
        <div className="data-grid">
          <div className="data-item">
            <span className="data-label">Production Output</span>
            <span className="data-value">{(sensorData?.produced || 0).toFixed(0)} units</span>
          </div>
          
          <div className="data-item">
            <span className="data-label">Waste Material</span>
            <span className="data-value">{(sensorData?.waste || 0).toFixed(2)} g</span>
          </div>

          <div className="data-item">
            <span className="data-label">Ejection Force</span>
            <span className="data-value">{(sensorData?.ejection || 0).toFixed(2)} N</span>
          </div>

          <div className="data-item">
            <span className="data-label">Tablet Speed</span>
            <span className="data-value">{(sensorData?.tbl_speed || 0).toFixed(1)} RPM</span>
          </div>

          <div className="data-item">
            <span className="data-label">Stiffness</span>
            <span className="data-value">{(sensorData?.stiffness || 0).toFixed(2)} N/mm</span>
          </div>

          <div className="data-item">
            <span className="data-label">SREL Parameter</span>
            <span className="data-value">{(sensorData?.SREL || 0).toFixed(2)}</span>
          </div>

          <div className="data-item">
            <span className="data-label">Main Compression</span>
            <span className="data-value">{(sensorData?.main_comp || 0).toFixed(2)} kN</span>
          </div>
        </div>
      </div>

      {/* API Status Information */}
      <div style={{ 
        fontSize: '0.7rem', 
        color: '#6c757d', 
        marginTop: '1.5rem', 
        padding: '0.75rem',
        background: predictionApiStatus === 'connected' ? '#d4edda' : 
                   predictionApiStatus === 'fallback' ? '#fff3cd' : '#f8d7da',
        borderRadius: '6px',
        border: `1px solid ${predictionApiStatus === 'connected' ? '#c3e6cb' : 
                             predictionApiStatus === 'fallback' ? '#ffeaa7' : '#f5c6cb'}`
      }}>
        <div style={{ marginBottom: '0.5rem', fontWeight: 'bold' }}>
          System Status: {statusInfo.text}
        </div>
        <div style={{ marginBottom: '0.25rem' }}>
          <strong>Data Source:</strong> {
            predictionApiStatus === 'connected' ? 'Sensors (Primary)' :
            predictionApiStatus === 'fallback' ? 'Sensor API (Fallback)' :
            predictionApiStatus === 'mock' ? 'Mock Data Service' : 'Local Simulation'
          }
        </div>
        <div style={{ marginBottom: '0.25rem' }}>
          <strong>Update Frequency:</strong> Every 6 seconds
        </div>
        <div style={{ marginBottom: '0.25rem' }}>
          <strong>Monitored Parameters:</strong> 7 key pharmaceutical sensors
        </div>
        <div>
          <strong>Data Quality:</strong> {
            predictionApiStatus === 'connected' ? 'Real-time production data' :
            predictionApiStatus === 'fallback' ? 'Real-time sensor data' :
            'Simulated pharmaceutical data'
          }
        </div>
      </div>

      {sensorData?.timestamp && (
        <div style={{ 
          fontSize: '0.75rem', 
          color: '#6c757d', 
          marginTop: '0.5rem', 
          textAlign: 'center',
          fontStyle: 'italic'
        }}>
          Data timestamp: {new Date(sensorData.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default LiveSensors; 