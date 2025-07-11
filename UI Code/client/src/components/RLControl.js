import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RLControl = () => {
  const [currentAction, setCurrentAction] = useState(null);
  const [safetyStatus, setSafetyStatus] = useState('active');
  const [operatorFeedback, setOperatorFeedback] = useState([]);
  const [lastActionTime, setLastActionTime] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Simulate RL action generation based on sensor data
  useEffect(() => {
    const generateRLAction = async () => {
      try {
        // Fetch current sensor data to inform RL decisions
        const response = await axios.get('/api/current');
        
        if (response.data && response.data.status === 'success') {
          const sensorData = response.data.data;
          
          // Simulate RL action generation based on current conditions
          // In real implementation, this would call your trained RL model
          const actions = generateActionRecommendation(sensorData);
          
          setCurrentAction(actions);
          setLastActionTime(new Date().toLocaleTimeString());
          
          // Simulate safety layer status
          const needsSafetyClipping = Math.abs(actions.speedAdjustment) > 15 || Math.abs(actions.compressionAdjustment) > 3;
          setSafetyStatus(needsSafetyClipping ? 'clipping' : 'active');
        }
      } catch (err) {
        console.error('Error generating RL action:', err);
        setCurrentAction(null);
      }
    };

    generateRLAction();
    const intervalId = setInterval(generateRLAction, 10000); // Update every 10 seconds

    return () => clearInterval(intervalId);
  }, []);

  const generateActionRecommendation = (sensorData) => {
    // Simulate intelligent RL recommendations based on pharmaceutical sensor data
    let speedAdjustment = 0;
    let compressionAdjustment = 0;
    let fillAdjustment = 0;
    let reasoning = [];

    // Main compression force optimization
    if (sensorData.main_comp > 22) {
      compressionAdjustment = -1.5;
      speedAdjustment = -3;
      reasoning.push('High main compression force - reducing to prevent tablet damage');
    } else if (sensorData.main_comp < 12) {
      compressionAdjustment = 1.0;
      reasoning.push('Low main compression force - increasing for better tablet integrity');
    }

    // Tablet fill weight optimization
    if (sensorData.tbl_fill > 7) {
      fillAdjustment = -0.2;
      reasoning.push('High tablet fill weight - reducing to maintain dosage accuracy');
    } else if (sensorData.tbl_fill < 4) {
      fillAdjustment = 0.15;
      reasoning.push('Low tablet fill weight - increasing to meet dosage requirements');
    }

    // Tablet speed optimization based on stiffness and ejection
    if (sensorData.stiffness < 60) {
      speedAdjustment -= 2;
      reasoning.push('Low tablet stiffness - reducing speed for better consolidation');
    }

    if (sensorData.ejection > 120) {
      speedAdjustment -= 1;
      compressionAdjustment = -0.5;
      reasoning.push('High ejection force - reducing speed and compression');
    }

    // SREL parameter optimization
    if (sensorData.SREL > 8) {
      speedAdjustment -= 1;
      reasoning.push('High SREL parameter - reducing processing speed');
    }

    // Waste reduction optimization
    if (sensorData.waste > 3) {
      speedAdjustment -= 1;
      reasoning.push('High waste detected - optimizing process parameters');
    }

    // Production rate considerations
    if (sensorData.produced < 800) {
      speedAdjustment += 1;
      reasoning.push('Production rate below target - optimizing throughput');
    }

    return {
      speedAdjustment: Math.round(speedAdjustment * 10) / 10,
      compressionAdjustment: Math.round(compressionAdjustment * 10) / 10,
      fillAdjustment: Math.round(fillAdjustment * 100) / 100,
      reasoning: reasoning.length > 0 ? reasoning : ['Maintaining optimal pharmaceutical manufacturing conditions'],
      confidence: Math.random() * 0.3 + 0.7, // 0.7 to 1.0
      currentParams: {
        mainComp: sensorData.main_comp || 0,
        tblFill: sensorData.tbl_fill || 0,
        stiffness: sensorData.stiffness || 0,
        ejection: sensorData.ejection || 0
      }
    };
  };

  const handleOperatorAction = async (action) => {
    setIsProcessing(true);
    
    try {
      // Simulate logging operator feedback
      const feedback = {
        action: action,
        recommendation: currentAction,
        timestamp: new Date().toISOString(),
        operatorId: 'OP001' // In real app, get from auth
      };
      
      // In real implementation, send to backend
      console.log('Operator feedback logged:', feedback);
      
      setOperatorFeedback(prev => [feedback, ...prev.slice(0, 4)]);
      
      // Generate new action after feedback
      setTimeout(() => {
        const response = axios.get('/api/current');
        // This would trigger a new RL action generation
      }, 2000);
      
    } catch (err) {
      console.error('Error logging operator feedback:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const getSafetyStatusConfig = () => {
    switch (safetyStatus) {
      case 'active':
        return {
          className: 'status-healthy',
          label: 'SAFETY LAYER ACTIVE',
          message: 'All recommended actions within safe pharmaceutical parameters'
        };
      case 'clipping':
        return {
          className: 'status-warning',
          label: 'SAFETY CLIPPING ENGAGED',
          message: 'Actions adjusted to maintain safe manufacturing limits'
        };
      default:
        return {
          className: 'status-offline',
          label: 'SAFETY STATUS UNKNOWN',
          message: 'Unable to determine safety layer status'
        };
    }
  };

  const safetyConfig = getSafetyStatusConfig();

  if (!currentAction) {
    return (
      <div className="panel rl-control-panel">
        <div className="status-indicator status-offline">
          Generating Recommendations...
        </div>
      </div>
    );
  }

  return (
    <div className="panel rl-control-panel">
      
      <div className={`status-indicator ${safetyConfig.className}`}>
        {safetyConfig.label}
      </div>

      <div className="rl-action-display">
        <h4>Recommended Actions</h4>
        <div style={{ marginBottom: '0.5rem' }}>
          <strong>Speed Adjustment:</strong> {currentAction.speedAdjustment > 0 ? '+' : ''}{currentAction.speedAdjustment} RPM
        </div>
        <div style={{ marginBottom: '0.5rem' }}>
          <strong>Compression Force:</strong> {currentAction.compressionAdjustment > 0 ? '+' : ''}{currentAction.compressionAdjustment} kN
        </div>
        <div style={{ marginBottom: '0.5rem' }}>
          <strong>Fill Weight:</strong> {currentAction.fillAdjustment > 0 ? '+' : ''}{currentAction.fillAdjustment} g
        </div>
        <div style={{ fontSize: '0.75rem', color: '#6c757d', marginTop: '0.5rem' }}>
          Confidence: {(currentAction.confidence * 100).toFixed(1)}%
        </div>
      </div>

      <div style={{ margin: '1rem 0' }}>
        <h5 style={{ fontSize: '0.875rem', color: '#495057', marginBottom: '0.5rem' }}>
          Current Process Parameters:
        </h5>
        <div style={{ fontSize: '0.75rem', color: '#6c757d', background: '#f8f9fa', padding: '0.5rem', borderRadius: '4px' }}>
          <div>Main Compression: {currentAction.currentParams.mainComp.toFixed(2)} kN</div>
          <div>Fill Weight: {currentAction.currentParams.tblFill.toFixed(2)} g</div>
          <div>Tablet Stiffness: {currentAction.currentParams.stiffness.toFixed(1)} N/mm</div>
          <div>Ejection Force: {currentAction.currentParams.ejection.toFixed(1)} N</div>
        </div>
      </div>

      <div style={{ margin: '1rem 0' }}>
        <h5 style={{ fontSize: '0.875rem', color: '#495057', marginBottom: '0.5rem' }}>
          AI Reasoning:
        </h5>
        <ul style={{ fontSize: '0.75rem', color: '#6c757d', paddingLeft: '1rem' }}>
          {currentAction.reasoning.map((reason, index) => (
            <li key={index} style={{ marginBottom: '0.25rem' }}>{reason}</li>
          ))}
        </ul>
      </div>

      <div className="operator-controls">
        <button 
          className="btn btn-accept"
          onClick={() => handleOperatorAction('accept')}
          disabled={isProcessing}
        >
          {isProcessing ? 'Processing...' : 'Accept'}
        </button>
        <button 
          className="btn btn-reject"
          onClick={() => handleOperatorAction('reject')}
          disabled={isProcessing}
        >
          {isProcessing ? 'Processing...' : 'Reject'}
        </button>
      </div>

      {operatorFeedback.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <h5 style={{ fontSize: '0.875rem', color: '#495057', marginBottom: '0.5rem' }}>
            Recent Operator Actions:
          </h5>
          <div style={{ maxHeight: '100px', overflowY: 'auto' }}>
            {operatorFeedback.map((feedback, index) => (
              <div key={index} style={{ 
                fontSize: '0.75rem', 
                color: '#6c757d', 
                padding: '0.25rem 0',
                borderBottom: '1px solid #f8f9fa'
              }}>
                <strong>{feedback.action.toUpperCase()}</strong> - {new Date(feedback.timestamp).toLocaleTimeString()}
              </div>
            ))}
          </div>
        </div>
      )}

      {lastActionTime && (
        <div style={{ fontSize: '0.75rem', color: '#6c757d', marginTop: '1rem', textAlign: 'center' }}>
          Last recommendation: {lastActionTime}
        </div>
      )}
    </div>
  );
};

export default RLControl; 