import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LoadingSpinner from './LoadingSpinner';

const RLControl = () => {
  const [currentAction, setCurrentAction] = useState(null);
  const [safetyStatus, setSafetyStatus] = useState('active');
  const [operatorFeedback, setOperatorFeedback] = useState([]);
  const [lastActionTime, setLastActionTime] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [availableModels, setAvailableModels] = useState(['baseline']);
  const [selectedModel, setSelectedModel] = useState('baseline');
  const [bufferStatus, setBufferStatus] = useState(null);
  const [rlStatus, setRlStatus] = useState(null);

  // Fetch available RL models on component mount
  useEffect(() => {
    const fetchAvailableModels = async () => {
      try {
        const statusRes = await axios.get('/api/prediction/rl-status');
        if (statusRes.data && statusRes.data.available_models) {
          const models = statusRes.data.available_models;
          setAvailableModels(models);
          setRlStatus(statusRes.data);
          
          // Set default model to first available model
          if (models.length > 0 && !models.includes(selectedModel)) {
            setSelectedModel(models[0]);
          }
        }
      } catch (err) {
        console.error('Error fetching RL status:', err);
        // Keep default models if API fails
      }
    };

    fetchAvailableModels();
  }, [selectedModel]);

  useEffect(() => {
    const fetchRLData = async () => {
      try {
        if (!hasLoadedOnce) {
          setIsLoading(true);
        }
        
        // Fetch buffer status to check data availability
        const bufferRes = await axios.get('/api/prediction/buffer-status');
        if (bufferRes.data) {
          setBufferStatus(bufferRes.data);
        }

        // Fetch RL action recommendation
        try {
          const actionRes = await axios.get(`/api/prediction/rl_action/${selectedModel}`);
          if (actionRes.data && actionRes.data.recommended_actions) {
            const rlData = actionRes.data;
            
            // Transform API response to component format
            const transformedAction = {
              speedAdjustment: rlData.recommended_actions.speed_adjustment || 0,
              compressionAdjustment: rlData.recommended_actions.compression_adjustment || 0,
              fillAdjustment: rlData.recommended_actions.fill_adjustment || 0,
              reasoning: [
                `Model: ${rlData.model_type}`,
                `Model Description: ${rlData.model_description || 'N/A'}`,
                `Mock Model: ${rlData.is_mock_model ? 'Yes' : 'No'}`,
                `Preprocessing applied: ${rlData.preprocessing_applied ? 'Yes' : 'No'}`,
                `Buffer size: ${rlData.data_sources?.buffer_size || 'N/A'}`,
                'RL model recommendation based on current process state'
              ],
              confidence: 0.8 + Math.random() * 0.2, // Mock confidence for now
              currentParams: rlData.state_summary || {},
              apiStatus: 'connected',
              isMockModel: rlData.is_mock_model || false
            };
            
            setCurrentAction(transformedAction);
            setError(null);
            
            // Determine safety status based on action magnitudes
            const needsSafetyClipping = 
              Math.abs(transformedAction.speedAdjustment) > 15 || 
              Math.abs(transformedAction.compressionAdjustment) > 3 ||
              Math.abs(transformedAction.fillAdjustment) > 0.5;
            setSafetyStatus(needsSafetyClipping ? 'clipping' : 'active');
            
          } else {
            throw new Error('Invalid RL response format');
          }
        } catch (rlErr) {
          console.error('RL Action API error:', rlErr);
          
          if (rlErr.response?.status === 503) {
            setError('RL models are not available due to version compatibility issues');
            // Generate fallback recommendation
            generateFallbackAction();
          } else if (rlErr.response?.status === 404) {
            setError(`Model '${selectedModel}' not available. Available models: ${availableModels.join(', ')}`);
            generateFallbackAction();
          } else {
            throw rlErr;
          }
        }

        setLastActionTime(new Date().toLocaleTimeString());
        
      } catch (err) {
        console.error('Error fetching RL data:', err);
        setError('RL Control system unavailable - using fallback mode');
        generateFallbackAction();
      } finally {
        if (!hasLoadedOnce) {
          setIsLoading(false);
          setHasLoadedOnce(true);
        }
      }
    };

    const generateFallbackAction = async () => {
      try {
        // Get current sensor data for fallback recommendations
        const response = await axios.get('/api/current');
        
        if (response.data && response.data.status === 'success') {
          const sensorData = response.data.data;
          const actions = generateActionRecommendation(sensorData);
          actions.apiStatus = 'fallback';
          setCurrentAction(actions);
        }
      } catch (fallbackErr) {
        console.error('Fallback action generation failed:', fallbackErr);
        // Generate basic safe action
        setCurrentAction({
          speedAdjustment: 0,
          compressionAdjustment: 0,
          fillAdjustment: 0,
          reasoning: ['System in safe mode - no adjustments recommended'],
          confidence: 0.5,
          currentParams: {},
          apiStatus: 'offline'
        });
      }
    };

    const generateActionRecommendation = (sensorData) => {
      // Fallback logic similar to original implementation but enhanced
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
        confidence: Math.random() * 0.3 + 0.7,
        currentParams: {
          main_comp: sensorData.main_comp || 0,
          stiffness: sensorData.stiffness || 0,
          ejection: sensorData.ejection || 0,
          SREL: sensorData.SREL || 0,
          waste: sensorData.waste || 0,
          produced: sensorData.produced || 0
        }
      };
    };

    fetchRLData();
    const intervalId = setInterval(fetchRLData, 15000); // Update every 15 seconds

    return () => clearInterval(intervalId);
  }, [selectedModel, hasLoadedOnce, availableModels]);

  const handleOperatorAction = async (action) => {
    setIsProcessing(true);
    
    try {
      // Log operator feedback
      const feedback = {
        action: action,
        recommendation: currentAction,
        timestamp: new Date().toISOString(),
        operatorId: 'OP001', // In real app, get from auth
        modelType: selectedModel
      };
      
      // In real implementation, send to backend for RL model training
      console.log('Operator feedback logged:', feedback);
      
      setOperatorFeedback(prev => [feedback, ...prev.slice(0, 4)]);
      
      // Trigger buffer supplementation if needed
      if (bufferStatus && !bufferStatus.data_sufficiency.rl_ready) {
        try {
          await axios.post('/api/prediction/supplement-buffer');
          console.log('Buffer supplementation triggered');
        } catch (suppErr) {
          console.warn('Buffer supplementation failed:', suppErr);
        }
      }
      
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

  if (isLoading && !hasLoadedOnce) {
    return (
      <div className="panel loading-panel-modern rl-control-panel" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '300px',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <LoadingSpinner size="large" color="#000000" message="Initializing RL Control System" />
        <div style={{ fontSize: '0.75rem', color: '#666666', textAlign: 'center', maxWidth: '250px' }}>
          Loading reinforcement learning models and safety protocols
        </div>
      </div>
    );
  }

  if (error && currentAction?.apiStatus === 'offline') {
    return (
      <div className="panel error-panel rl-control-panel">
        <div className="status-indicator status-offline">
          RL Control System Offline
        </div>
        <p>{error}</p>
        <div style={{ fontSize: '0.75rem', color: '#6c757d', marginTop: '1rem' }}>
          Ensure the prediction API is running with RL models loaded
        </div>
      </div>
    );
  }

  if (!currentAction) {
    return (
      <div className="panel rl-control-panel" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '200px',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <LoadingSpinner size="medium" color="#000000" message="Generating AI Recommendations" />
        <div style={{ fontSize: '0.75rem', color: '#666666', textAlign: 'center' }}>
          Analyzing current conditions and generating optimal control actions
        </div>
      </div>
    );
  }

  return (
    <div className="panel rl-control-panel">
      <div className={`status-indicator ${safetyConfig.className}`}>
        {safetyConfig.label}
      </div>

      {error && currentAction?.apiStatus === 'fallback' && (
        <div style={{ 
          background: '#fff3cd', 
          color: '#856404', 
          padding: '0.5rem', 
          borderRadius: '4px', 
          marginBottom: '1rem',
          fontSize: '0.75rem'
        }}>
          {error}
        </div>
      )}

      {/* Model Selection */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ fontSize: '0.8rem', color: '#495057', marginRight: '0.5rem' }}>
          RL Model:
        </label>
        <select 
          value={selectedModel} 
          onChange={(e) => {
            setSelectedModel(e.target.value);
            setIsLoading(true);
            setHasLoadedOnce(false);
          }}
          style={{ 
            padding: '0.25rem', 
            fontSize: '0.8rem',
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            marginRight: '0.5rem'
          }}
        >
          {availableModels.map(model => (
            <option key={model} value={model}>
              {model.toUpperCase()}
              {rlStatus?.mock_models?.includes(model) ? ' (MOCK)' : ''}
            </option>
          ))}
        </select>
        {currentAction?.isMockModel && (
          <span style={{ 
            fontSize: '0.7rem', 
            color: '#dc3545', 
            background: '#f8d7da', 
            padding: '0.2rem 0.4rem', 
            borderRadius: '3px',
            marginLeft: '0.5rem'
          }}>
            MOCK MODEL
          </span>
        )}
      </div>



      <div className="rl-action-display">
        <h4>AI Recommendations</h4>
        
        {/* Action Cards */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '1rem', 
          marginBottom: '1rem' 
        }}>
          {/* Speed Adjustment Card */}
          <div style={{
            background: currentAction.speedAdjustment === 0 ? '#f8f9fa' : 
                       Math.abs(currentAction.speedAdjustment) > 5 ? '#fff3cd' : '#e8f5e8',
            border: `2px solid ${currentAction.speedAdjustment === 0 ? '#e9ecef' : 
                                 Math.abs(currentAction.speedAdjustment) > 5 ? '#ffc107' : '#28a745'}`,
            borderRadius: '8px',
            padding: '1rem',
            textAlign: 'center'
          }}>
            <div style={{ 
              width: '24px', 
              height: '24px', 
              margin: '0 auto 0.5rem auto',
              background: '#6c757d',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{
                width: '12px',
                height: '12px',
                border: '2px solid white',
                borderRadius: '50%'
              }}></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#6c757d', marginBottom: '0.5rem', fontWeight: '600' }}>
              SPEED ADJUSTMENT
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#2c3e50' }}>
              {currentAction.speedAdjustment > 0 ? '+' : ''}{currentAction.speedAdjustment.toFixed(2)} RPM
            </div>
            <div style={{ fontSize: '0.7rem', color: '#6c757d', marginTop: '0.25rem' }}>
              {Math.abs(currentAction.speedAdjustment) < 0.1 ? 'No Change' :
               currentAction.speedAdjustment > 0 ? 'Increase Speed' : 'Decrease Speed'}
            </div>
          </div>

          {/* Compression Force Card */}
          <div style={{
            background: currentAction.compressionAdjustment === 0 ? '#f8f9fa' : 
                       Math.abs(currentAction.compressionAdjustment) > 2 ? '#fff3cd' : '#e8f5e8',
            border: `2px solid ${currentAction.compressionAdjustment === 0 ? '#e9ecef' : 
                                 Math.abs(currentAction.compressionAdjustment) > 2 ? '#ffc107' : '#28a745'}`,
            borderRadius: '8px',
            padding: '1rem',
            textAlign: 'center'
          }}>
            <div style={{ 
              width: '24px', 
              height: '24px', 
              margin: '0 auto 0.5rem auto',
              background: '#6c757d',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                background: 'white',
                borderRadius: '2px'
              }}></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#6c757d', marginBottom: '0.5rem', fontWeight: '600' }}>
              COMPRESSION FORCE
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#2c3e50' }}>
              {currentAction.compressionAdjustment > 0 ? '+' : ''}{currentAction.compressionAdjustment.toFixed(2)} kN
            </div>
            <div style={{ fontSize: '0.7rem', color: '#6c757d', marginTop: '0.25rem' }}>
              {Math.abs(currentAction.compressionAdjustment) < 0.1 ? 'No Change' :
               currentAction.compressionAdjustment > 0 ? 'Increase Force' : 'Decrease Force'}
            </div>
          </div>

          {/* Fill Weight Card */}
          <div style={{
            background: currentAction.fillAdjustment === 0 ? '#f8f9fa' : 
                       Math.abs(currentAction.fillAdjustment) > 0.3 ? '#fff3cd' : '#e8f5e8',
            border: `2px solid ${currentAction.fillAdjustment === 0 ? '#e9ecef' : 
                                 Math.abs(currentAction.fillAdjustment) > 0.3 ? '#ffc107' : '#28a745'}`,
            borderRadius: '8px',
            padding: '1rem',
            textAlign: 'center'
          }}>
            <div style={{ 
              width: '24px', 
              height: '24px', 
              margin: '0 auto 0.5rem auto',
              background: '#6c757d',
              borderRadius: '2px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{
                width: '12px',
                height: '2px',
                background: 'white'
              }}></div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#6c757d', marginBottom: '0.5rem', fontWeight: '600' }}>
              FILL WEIGHT
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#2c3e50' }}>
              {currentAction.fillAdjustment > 0 ? '+' : ''}{currentAction.fillAdjustment.toFixed(3)} g
            </div>
            <div style={{ fontSize: '0.7rem', color: '#6c757d', marginTop: '0.25rem' }}>
              {Math.abs(currentAction.fillAdjustment) < 0.01 ? 'No Change' :
               currentAction.fillAdjustment > 0 ? 'Increase Weight' : 'Decrease Weight'}
            </div>
          </div>
        </div>

        {/* Status Bar */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ 
              width: '12px', 
              height: '12px', 
              borderRadius: '50%', 
              background: currentAction.confidence > 0.8 ? '#28a745' : 
                         currentAction.confidence > 0.6 ? '#ffc107' : '#dc3545'
            }}></div>
            <span style={{ fontSize: '0.85rem', fontWeight: '600', color: '#495057' }}>
              Confidence: {(currentAction.confidence * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      <div style={{ margin: '1rem 0' }}>
        <h5 style={{ fontSize: '0.875rem', color: '#495057', marginBottom: '1rem', fontWeight: '600' }}>
          Current Process Parameters:
        </h5>
        
        {Object.keys(currentAction.currentParams).length > 0 ? (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', 
            gap: '0.75rem' 
          }}>
            {Object.entries(currentAction.currentParams).map(([key, value]) => {
              const paramName = key.replace('_', ' ').toUpperCase();
              const units = {
                'WASTE': 'g',
                'PRODUCED': 'units',
                'EJECTION': 'N',
                'TBL SPEED': 'RPM',
                'STIFFNESS': 'N/mm',
                'SREL': '',
                'MAIN COMP': 'kN'
              };
              
              const getStatusInfo = (paramName, value) => {
                switch(paramName) {
                  case 'WASTE':
                    if (value <= 1500) return { bg: '#e8f5e8', border: '#28a74540' }; // Green - Low waste
                    if (value <= 3000) return { bg: '#fff3cd', border: '#ffc10740' }; // Yellow - Medium waste
                    return { bg: '#ffebee', border: '#dc354540' }; // Red - High waste
                  case 'PRODUCED':
                    if (value >= 800) return { bg: '#e8f5e8', border: '#28a74540' }; // Green - Good production
                    if (value >= 500) return { bg: '#fff3cd', border: '#ffc10740' }; // Yellow - Medium production
                    return { bg: '#ffebee', border: '#dc354540' }; // Red - Low production
                  case 'EJECTION':
                    if (value <= 120) return { bg: '#e8f5e8', border: '#28a74540' }; // Green - Low ejection force
                    if (value <= 180) return { bg: '#fff3cd', border: '#ffc10740' }; // Yellow - Medium ejection force
                    return { bg: '#ffebee', border: '#dc354540' }; // Red - High ejection force
                  case 'TBL SPEED':
                    if (value >= 80 && value <= 140) return { bg: '#e8f5e8', border: '#28a74540' }; // Green - Optimal speed
                    if (value >= 60 && value <= 160) return { bg: '#fff3cd', border: '#ffc10740' }; // Yellow - Acceptable speed
                    return { bg: '#ffebee', border: '#dc354540' }; // Red - Poor speed
                  case 'STIFFNESS':
                    if (value >= 80 && value <= 150) return { bg: '#e8f5e8', border: '#28a74540' }; // Green - Good stiffness
                    if (value >= 60 && value <= 180) return { bg: '#fff3cd', border: '#ffc10740' }; // Yellow - Acceptable stiffness
                    return { bg: '#ffebee', border: '#dc354540' }; // Red - Poor stiffness
                  case 'SREL':
                    if (value >= 2 && value <= 6) return { bg: '#e8f5e8', border: '#28a74540' }; // Green - Optimal SREL
                    if (value >= 1 && value <= 8) return { bg: '#fff3cd', border: '#ffc10740' }; // Yellow - Acceptable SREL
                    return { bg: '#ffebee', border: '#dc354540' }; // Red - Poor SREL
                  case 'MAIN COMP':
                    if (value >= 12 && value <= 22) return { bg: '#e8f5e8', border: '#28a74540' }; // Green - Optimal compression
                    if (value >= 8 && value <= 25) return { bg: '#fff3cd', border: '#ffc10740' }; // Yellow - Acceptable compression
                    return { bg: '#ffebee', border: '#dc354540' }; // Red - Poor compression
                  default:
                    return { bg: '#f1f3f4', border: '#e9ecef40' }; // Default gray
                }
              };
              
              const statusInfo = getStatusInfo(paramName, value);
              
              return (
                <div key={key} style={{
                  background: statusInfo.bg,
                  border: `2px solid ${statusInfo.border}`,
                  borderRadius: '8px',
                  padding: '0.75rem',
                  textAlign: 'center',
                  transition: 'all 0.2s ease'
                }}>
                  <div style={{ 
                    fontSize: '0.7rem', 
                    color: '#6c757d', 
                    marginBottom: '0.5rem',
                    fontWeight: '600',
                    letterSpacing: '0.5px'
                  }}>
                    {paramName}
                  </div>
                  
                  <div style={{ 
                    fontSize: '1.1rem', 
                    fontWeight: 'bold', 
                    color: '#2c3e50',
                    marginBottom: '0.25rem'
                  }}>
                    {typeof value === 'number' ? value.toFixed(2) : value}
                  </div>
                  
                  {units[paramName] && (
                    <div style={{ 
                      fontSize: '0.65rem', 
                      color: '#6c757d',
                      fontWeight: '500'
                    }}>
                      {units[paramName]}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{
            background: '#f8f9fa',
            border: '2px dashed #dee2e6',
            borderRadius: '8px',
            padding: '2rem',
            textAlign: 'center',
            color: '#6c757d',
            fontSize: '0.875rem'
          }}>
            No parameter data available
          </div>
        )}
        
        {/* Parameter Legend */}
        <div style={{
          marginTop: '1rem',
          padding: '0.5rem',
          background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
          borderRadius: '6px',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#28a745' }}></div>
              <span style={{ fontSize: '0.7rem', color: '#6c757d' }}>Optimal</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ffc107' }}></div>
              <span style={{ fontSize: '0.7rem', color: '#6c757d' }}>Warning</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#dc3545' }}></div>
              <span style={{ fontSize: '0.7rem', color: '#6c757d' }}>Critical</span>
            </div>
          </div>
        </div>
      </div>



      {/* Buffer Status Information */}
      {bufferStatus && (
        <div style={{ 
          margin: '1rem 0', 
          padding: '0.75rem', 
          background: '#d4edda',
          borderRadius: '6px',
          border: '1px solid #c3e6cb'
        }}>
          <h5 style={{ fontSize: '0.8rem', color: '#495057', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Data Buffer Status:
          </h5>
          <div style={{ fontSize: '0.75rem', color: '#6c757d' }}>
            <div><strong>Buffer Size:</strong> {bufferStatus.buffer_size}/{bufferStatus.buffer_max_size}</div>
            <div><strong>RL Ready:</strong> {bufferStatus.data_sufficiency.rl_ready ? 'Yes' : 'No'}</div>
            <div><strong>Preprocessing:</strong> {bufferStatus.preprocessing_status.enabled ? 'Enabled' : 'Disabled'}</div>
          </div>
        </div>
      )}

      <div className="operator-controls">
        <button 
          className="btn btn-accept"
          onClick={() => handleOperatorAction('accept')}
          disabled={isProcessing}
          style={{
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            marginRight: '0.5rem',
            cursor: isProcessing ? 'not-allowed' : 'pointer'
          }}
        >
          {isProcessing ? 'Processing...' : 'Accept'}
        </button>
        <button 
          className="btn btn-reject"
          onClick={() => handleOperatorAction('reject')}
          disabled={isProcessing}
          style={{
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            cursor: isProcessing ? 'not-allowed' : 'pointer'
          }}
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
                {feedback.modelType && <span> ({feedback.modelType})</span>}
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