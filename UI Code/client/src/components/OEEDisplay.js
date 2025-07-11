import React, { useState, useEffect } from 'react';
import axios from 'axios';

const OEEDisplay = () => {
  const [oeeData, setOeeData] = useState({
    overall: 85.2,
    availability: 92.1,
    performance: 88.7,
    quality: 93.6
  });
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const calculateOEE = async () => {
      try {
        // Fetch current sensor data to calculate OEE metrics
        const response = await axios.get('/api/current');
        
        if (response.data && response.data.status === 'success') {
          const sensorData = response.data.data;
          
          // Calculate OEE components based on sensor data
          const calculatedOEE = calculateOEEFromSensorData(sensorData);
          setOeeData(calculatedOEE);
          setLastUpdate(new Date().toLocaleTimeString());
          setError(null);
        }
      } catch (err) {
        console.error('Error calculating OEE:', err);
        setError('OEE calculation unavailable');
      }
    };

    calculateOEE();
    const intervalId = setInterval(calculateOEE, 10000); // Update every 10 seconds

    return () => clearInterval(intervalId);
  }, []);

  const calculateOEEFromSensorData = (sensorData) => {
    // Simulate OEE calculation based on pharmaceutical sensor readings
    // In real implementation, this would use historical data and actual production metrics
    
    // Availability: Based on tablet machine operation status
    let availability = 95; // Base availability
    if (sensorData.tbl_speed < 0.5) availability -= 15; // Machine stopped or very slow
    if (sensorData.ejection > 150) availability -= 5; // High ejection force indicating issues
    if (sensorData.waste > 5) availability -= 3; // High waste indicating problems
    
    // Performance: Based on actual vs expected tablet production
    const targetTabletSpeed = 10; // tablets per second
    const actualSpeed = sensorData.tbl_speed || 0;
    let performance = Math.min((actualSpeed / targetTabletSpeed) * 100, 100);
    
    // Adjust performance based on production parameters
    if (sensorData.produced > 0) {
      // Factor in actual production numbers if available
      const productionEfficiency = Math.min(sensorData.produced / 1000, 1) * 100;
      performance = (performance + productionEfficiency) / 2;
    }
    
    // Quality: Based on pharmaceutical process parameters being within spec
    let quality = 98; // Base quality
    
    // Main compression force quality check
    if (sensorData.main_comp > 25 || sensorData.main_comp < 10) quality -= 4;
    
    // Tablet fill weight quality check  
    if (sensorData.tbl_fill > 8 || sensorData.tbl_fill < 3) quality -= 3;
    
    // SREL parameter quality check
    if (sensorData.SREL > 10 || sensorData.SREL < 2) quality -= 2;
    
    // Tablet stiffness quality check
    if (sensorData.stiffness < 50 || sensorData.stiffness > 200) quality -= 3;
    
    // Ejection force quality check
    if (sensorData.ejection > 120) quality -= 2;
    
    // Pre-compression quality check
    if (sensorData.pre_comp > 15 || sensorData.pre_comp < 3) quality -= 2;
    
    // Waste factor into quality
    if (sensorData.waste > 3) quality -= Math.min(sensorData.waste, 5);
    
    // Add some realistic variation
    availability += (Math.random() - 0.5) * 2;
    performance += (Math.random() - 0.5) * 3;
    quality += (Math.random() - 0.5) * 1.5;
    
    // Ensure values are within reasonable bounds
    availability = Math.max(75, Math.min(99, availability));
    performance = Math.max(70, Math.min(100, performance));
    quality = Math.max(85, Math.min(99.5, quality));
    
    // Calculate overall OEE
    const overall = (availability * performance * quality) / 10000;
    
    return {
      overall: Math.round(overall * 10) / 10,
      availability: Math.round(availability * 10) / 10,
      performance: Math.round(performance * 10) / 10,
      quality: Math.round(quality * 10) / 10
    };
  };

  const getOEEStatus = (value) => {
    if (value >= 85) return 'excellent';
    if (value >= 75) return 'good';
    if (value >= 65) return 'fair';
    return 'poor';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'excellent': return '#28a745';
      case 'good': return '#17a2b8';
      case 'fair': return '#ffc107';
      case 'poor': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const overallStatus = getOEEStatus(oeeData.overall);

  if (error) {
    return (
      <div className="panel error-panel oee-display">
        <div className="status-indicator status-offline">
          OEE Calculation Offline
        </div>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="panel oee-display">
      <div className="status-indicator status-healthy">
        Overall Equipment Effectiveness
      </div>

      <div className="oee-metric">
        <div 
          className="oee-percentage" 
          style={{ color: getStatusColor(overallStatus) }}
        >
          {oeeData.overall}%
        </div>
        <div className="oee-label">
          Overall OEE - {overallStatus.toUpperCase()}
        </div>
      </div>

      <div className="oee-breakdown">
        <div className="oee-component">
          <h5>Availability</h5>
          <div 
            className="value" 
            style={{ color: getStatusColor(getOEEStatus(oeeData.availability)) }}
          >
            {oeeData.availability}%
          </div>
          <div style={{ fontSize: '0.7rem', color: '#6c757d', marginTop: '0.25rem' }}>
            Machine Uptime
          </div>
        </div>
        
        <div className="oee-component">
          <h5>Performance</h5>
          <div 
            className="value" 
            style={{ color: getStatusColor(getOEEStatus(oeeData.performance)) }}
          >
            {oeeData.performance}%
          </div>
          <div style={{ fontSize: '0.7rem', color: '#6c757d', marginTop: '0.25rem' }}>
            Production Speed
          </div>
        </div>
        
        <div className="oee-component">
          <h5>Quality</h5>
          <div 
            className="value" 
            style={{ color: getStatusColor(getOEEStatus(oeeData.quality)) }}
          >
            {oeeData.quality}%
          </div>
          <div style={{ fontSize: '0.7rem', color: '#6c757d', marginTop: '0.25rem' }}>
            Tablet Quality
          </div>
        </div>
      </div>

      <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#f8f9fa', borderRadius: '6px', border: '1px solid #e9ecef' }}>
        <h5 style={{ fontSize: '0.875rem', color: '#495057', marginBottom: '0.5rem' }}>
          Performance Insights
        </h5>
        <div style={{ fontSize: '0.75rem', color: '#6c757d' }}>
          {oeeData.overall >= 85 && "Excellent performance - Pharmaceutical manufacturing process operating optimally"}
          {oeeData.overall >= 75 && oeeData.overall < 85 && "Good performance - Minor tablet production optimizations possible"}
          {oeeData.overall >= 65 && oeeData.overall < 75 && "Fair performance - Review compression and fill parameters"}
          {oeeData.overall < 65 && "Performance attention needed - Check tablet equipment and process conditions"}
        </div>
        
        {/* Show specific recommendations based on lowest performing component */}
        <div style={{ fontSize: '0.75rem', color: '#6c757d', marginTop: '0.5rem' }}>
          {Math.min(oeeData.availability, oeeData.performance, oeeData.quality) === oeeData.availability && 
            "Focus area: Tablet machine reliability and maintenance scheduling"}
          {Math.min(oeeData.availability, oeeData.performance, oeeData.quality) === oeeData.performance && 
            "Focus area: Tablet production speed optimization and throughput efficiency"}
          {Math.min(oeeData.availability, oeeData.performance, oeeData.quality) === oeeData.quality && 
            "Focus area: Tablet quality control and pharmaceutical defect reduction"}
        </div>
      </div>

      {lastUpdate && (
        <div style={{ fontSize: '0.75rem', color: '#6c757d', marginTop: '1rem', textAlign: 'center' }}>
          Last calculation: {lastUpdate}
        </div>
      )}
    </div>
  );
};

export default OEEDisplay; 