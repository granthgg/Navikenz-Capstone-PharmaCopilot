import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import HomePage from './components/HomePage';
import LiveSensors from './components/LiveSensors';
import ForecastPanel from './components/ForecastPanel';
import RLControl from './components/RLControl';
import ReportsView from './components/ReportsView';
import OEEDisplay from './components/OEEDisplay';
import DetailedReport from './components/DetailedReport';

function App() {
  const [currentPanelIndex, setCurrentPanelIndex] = useState(0);
  const [showHomePage, setShowHomePage] = useState(true);
  const [showDetailedReport, setShowDetailedReport] = useState(false);

  const panels = [
    {
      id: 'live-sensors',
      title: 'Live Sensor Monitoring',
      component: <LiveSensors />,
      description: 'Real-time pharmaceutical manufacturing sensor data'
    },
    {
      id: 'forecast',
      title: 'Quality Forecast',
      component: <ForecastPanel />,
      description: 'AI-powered defect probability predictions'
    },
    {
      id: 'rl-control',
      title: 'RL Control System',
      component: <RLControl />,
      description: 'Intelligent process optimization recommendations'
    },
    {
      id: 'oee-dashboard',
      title: 'OEE Dashboard',
      component: <OEEDisplay />,
      description: 'Overall Equipment Effectiveness monitoring'
    },
    {
      id: 'reports',
      title: 'AI Reports Center',
      component: <ReportsView />,
      description: 'Automated compliance and analysis reports'
    }
  ];

  const goToPrevious = useCallback(() => {
    setCurrentPanelIndex((prev) => 
      prev === 0 ? panels.length - 1 : prev - 1
    );
  }, [panels.length]);

  const goToNext = useCallback(() => {
    setCurrentPanelIndex((prev) => 
      prev === panels.length - 1 ? 0 : prev + 1
    );
  }, [panels.length]);

  const goToPanel = (index) => {
    setCurrentPanelIndex(index);
    setShowHomePage(false);
    setShowDetailedReport(false);
  };

  const goToDetailedReport = () => {
    setShowDetailedReport(true);
    setShowHomePage(false);
  };

  const backToHome = () => {
    setShowDetailedReport(false);
    setShowHomePage(true);
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (event) => {
      if (event.key === 'ArrowLeft') {
        goToPrevious();
      } else if (event.key === 'ArrowRight') {
        goToNext();
      } else if (event.key >= '1' && event.key <= '5') {
        const index = parseInt(event.key) - 1;
        if (index < panels.length) {
          goToPanel(index);
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [panels.length, goToNext, goToPrevious]);

  const currentPanel = panels[currentPanelIndex];

  return (
    <div className="App">
      {showDetailedReport ? (
        <DetailedReport onBackToHome={backToHome} />
      ) : (
        <>
          <header className="App-header">
            <div className="floating-nav">
              <div className="app-branding">
                <h1 onClick={() => {
                  setShowHomePage(true);
                  setShowDetailedReport(false);
                }} style={{ cursor: 'pointer' }}>PHARMA COPILOT</h1>
              </div>
              
              <div className="panel-navigation">
                {panels.map((panel, index) => (
                  <button
                    key={panel.id}
                    className={`nav-btn ${index === currentPanelIndex ? 'active' : ''}`}
                    onClick={() => goToPanel(index)}
                    title={panel.description}
                  >
                    <span className="nav-btn-text">{panel.title}</span>
                  </button>
                ))}
              </div>
            </div>
          </header>

          <main className="dashboard-container">
            {showHomePage ? (
              <HomePage onNavigateToPanel={goToPanel} onNavigateToDetailedReport={goToDetailedReport} />
            ) : (
              <>
                {/* Current Panel */}
                <div className="panel-container">
                  <div className="panel-header">
                    <div className="panel-title">
                      <h2>{currentPanel.title}</h2>
                      <p className="panel-description">{currentPanel.description}</p>
                    </div>
                    <div className="panel-counter">
                      {currentPanelIndex + 1} / {panels.length}
                    </div>
                  </div>
                  
                  <div className="panel-content">
                    {currentPanel.component}
                  </div>
                </div>
              </>
            )}
          </main>

          {/* Floating Navigation Arrows - Only show when not on home page and not on detailed report */}
          {!showHomePage && !showDetailedReport && (
            <>
              {/* Navigation Arrow - Left */}
              <button 
                className="nav-arrow nav-arrow-left nav-arrow-floating"
                onClick={goToPrevious}
                title="Previous Panel"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
                </svg>
              </button>

              {/* Navigation Arrow - Right */}
              <button 
                className="nav-arrow nav-arrow-right nav-arrow-floating"
                onClick={goToNext}
                title="Next Panel"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z"/>
                </svg>
              </button>
            </>
          )}

          {/* Bottom Navigation - Only show when not on home page and not on detailed report */}
          {!showHomePage && !showDetailedReport && (
            <footer className="bottom-navigation">
              <div className="nav-dots">
                {panels.map((panel, index) => (
                  <button
                    key={panel.id}
                    className={`nav-dot ${index === currentPanelIndex ? 'active' : ''}`}
                    onClick={() => goToPanel(index)}
                    title={panel.title}
                  />
                ))}
              </div>
              
              <div className="keyboard-hint">
                Navigate: Arrow Keys | Direct Access: 1-5
              </div>
            </footer>
          )}
        </>
      )}
    </div>
  );
}

export default App; 