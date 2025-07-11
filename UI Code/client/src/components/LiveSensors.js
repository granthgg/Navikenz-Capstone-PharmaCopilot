import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GaugeChart from 'react-gauge-chart';

const LiveSensors = () => {
  const [sensorData, setSensorData] = useState(null);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('/api/current');
        
        if (response.data && response.data.status === 'success' && response.data.data) {
          setSensorData(response.data.data);
          setLastUpdate(new Date().toLocaleTimeString());
          setError(null);
        } else {
          throw new Error('Invalid data format received');
        }
      } catch (err) {
        console.error('Error fetching sensor data:', err);
        setError('Failed to fetch sensor data. Checking connection...');
      } finally {
        setIsLoading(false);
      }
    };

    // Fetch immediately on component mount
    fetchData();
    
    // Poll every 10 seconds for real-time updates
    const intervalId = setInterval(fetchData, 10000);

    return () => clearInterval(intervalId);
  }, []);

  if (error) {
    return (
      <div className="panel error-panel live-sensors-panel">
        <div className="status-indicator status-offline">
          System Offline
        </div>
        <p>{error}</p>
      </div>
    );
  }

  if (isLoading && !sensorData) {
    return (
      <div className="panel loading-panel live-sensors-panel">
        <div className="loading">Loading sensor data...</div>
      </div>
    );
  }

  if (!sensorData) {
    return (
      <div className="panel live-sensors-panel">
        <div className="status-indicator status-offline">
          No Data Available
        </div>
      </div>
    );
  }

  // Calculate gauge percentages for main pharmaceutical parameters
  const mainCompForcePercent = Math.min((sensorData.main_comp || 0) / 25, 1);
  const tabletFillPercent = Math.min((sensorData.tbl_fill || 0) / 10, 1);

  return (
    <div className="panel live-sensors-panel">
      <div className="status-indicator status-healthy">
        System Active - Last Update: {lastUpdate}
      </div>

      <div className="gauges-container">
        <div className="gauge">
          <h4>Main Compression Force</h4>
          <GaugeChart
            id="gauge-main-comp"
            nrOfLevels={20}
            percent={mainCompForcePercent}
            textColor="#333"
            colors={['#28a745', '#ffc107', '#dc3545']}
            arcWidth={0.3}
            hideText={true}
          />
          <p>{(sensorData.main_comp || 0).toFixed(2)} kN</p>
        </div>
        
        <div className="gauge">
          <h4>Tablet Fill Weight</h4>
          <GaugeChart
            id="gauge-tbl-fill"
            nrOfLevels={20}
            percent={tabletFillPercent}
            textColor="#333"
            colors={['#28a745', '#ffc107', '#dc3545']}
            arcWidth={0.3}
            hideText={true}
          />
          <p>{(sensorData.tbl_fill || 0).toFixed(3)} g</p>
        </div>
      </div>

      <div className="numeric-data">
        <p>
          <strong>Tablet Speed</strong>
          {(sensorData.tbl_speed || 0).toFixed(1)} RPM
        </p>
        <p>
          <strong>Force of Mix (FOM)</strong>
          {(sensorData.fom || 0).toFixed(2)} N
        </p>
        <p>
          <strong>SREL Parameter</strong>
          {(sensorData.SREL || 0).toFixed(2)}
        </p>
        <p>
          <strong>Pre-Compression</strong>
          {(sensorData.pre_comp || 0).toFixed(2)} kN
        </p>
        <p>
          <strong>Tablet Stiffness</strong>
          {(sensorData.stiffness || 0).toFixed(2)} N/mm
        </p>
        <p>
          <strong>Ejection Force</strong>
          {(sensorData.ejection || 0).toFixed(2)} N
        </p>
        <p>
          <strong>Production Output</strong>
          {(sensorData.produced || 0).toFixed(0)} units
        </p>
        <p>
          <strong>Waste Material</strong>
          {(sensorData.waste || 0).toFixed(2)} g
        </p>
        <p>
          <strong>Batch ID</strong>
          {sensorData.batch || 'N/A'}
        </p>
        <p>
          <strong>Campaign</strong>
          {sensorData.campaign || 'N/A'}
        </p>
        <p>
          <strong>Process Code</strong>
          {sensorData.code || 'N/A'}
        </p>
        <p>
          <strong>Data Index</strong>
          {(sensorData.index || 0).toFixed(1)}
        </p>
      </div>

      {sensorData.timestamp && (
        <div style={{ 
          fontSize: '0.75rem', 
          color: '#6c757d', 
          marginTop: '1rem', 
          textAlign: 'center',
          fontStyle: 'italic'
        }}>
          Sensor timestamp: {new Date(sensorData.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default LiveSensors; 