import React from 'react';
import Lottie from 'lottie-react';
import './HomePage.css';
import lottieAnimation from './assets/Web Design Layout.json';

const HomePage = ({ onNavigateToPanel }) => {
  return (
    <div className="home-page">
      <div className="hero-container">
        <div className="hero-content">
          <div className="text-section">
            <h1 className="main-title">PharmaCopilot AI</h1>
            <p className="powered-by">Powered by Navikenz</p>
            <p className="subtitle">Intelligent Manufacturing Analytics & Quality Control</p>
            <p className="description">
              Advanced AI-powered platform for pharmaceutical manufacturing optimization. 
              Real-time sensor monitoring, predictive quality control, and intelligent 
              process analytics to ensure compliance and maximize efficiency.
            </p>
          </div>
          
          <div className="animation-section">
            <div className="animation-container">
              <div className="illustration-wrapper">
                {lottieAnimation && Object.keys(lottieAnimation).length > 0 ? (
                  <Lottie
                    animationData={lottieAnimation}
                    style={{ height: '500px', width: '500px' }}
                    loop={true}
                    autoplay={true}
                  />
                ) : (
                  <div className="lottie-placeholder">
                    <div className="placeholder-icon">🏭</div>
                    <p>Pharmaceutical Manufacturing Analytics</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="features-section">
        <div className="features-container">
          <div className="features-header">
            <h2 className="features-title">Platform Capabilities</h2>
            <p className="features-subtitle">
              Comprehensive pharmaceutical manufacturing intelligence designed for modern production environments
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <div className="icon-circle">
                  <svg className="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 3v5h5M21 21v-5h-5M21 3l-7 7M3 21l7-7M12 2v20M2 12h20"/>
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">Real-time Analytics</h3>
              <p className="feature-description">
                Monitor production metrics and sensor data in real-time with advanced visualization dashboards
                and customizable alerts for immediate process insights.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <div className="icon-circle">
                  <svg className="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="m9 12 2 2 4-4"/>
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">Predictive Quality Control</h3>
              <p className="feature-description">
                AI-powered quality prediction models that identify potential defects before they occur,
                ensuring consistent product quality and reducing waste.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <div className="icon-circle">
                  <svg className="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M12 1v6m0 6v6"/>
                    <path d="m21 12-6-3-6 3-6-3"/>
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">Process Optimization</h3>
              <p className="feature-description">
                Machine learning algorithms analyze historical data to recommend optimal process parameters
                for maximum efficiency and yield improvement.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <div className="icon-circle">
                  <svg className="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10,9 9,9 8,9"/>
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">Compliance Management</h3>
              <p className="feature-description">
                Automated compliance tracking and reporting tools ensure adherence to regulatory standards
                with comprehensive audit trails and documentation.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <div className="icon-circle">
                  <svg className="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                    <polyline points="3.27,6.96 12,12.01 20.73,6.96"/>
                    <line x1="12" y1="22.08" x2="12" y2="12"/>
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">System Integration</h3>
              <p className="feature-description">
                Seamless integration with existing manufacturing systems, ERP platforms, and laboratory
                information management systems (LIMS).
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <div className="icon-circle">
                  <svg className="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <circle cx="12" cy="16" r="1"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                </div>
              </div>
              <h3 className="feature-title">Secure Infrastructure</h3>
              <p className="feature-description">
                Enterprise-grade security with data encryption, role-based access control, and secure
                cloud infrastructure designed for pharmaceutical environments.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="performance-metrics-section">
        <div className="metrics-container">
          <div className="data-overview">
            <div className="data-stats">
              <div className="stat-item">
                <div className="stat-number">97.2%</div>
                <div className="stat-label">Quality Prediction Accuracy</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">94.8%</div>
                <div className="stat-label">Defect Classification F1-Score</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">92.5%</div>
                <div className="stat-label">Process Forecasting RMSE</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">99.1%</div>
                <div className="stat-label">Sensor Data Reliability</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="data-analysis-section">
        <div className="data-container">
          <div className="data-header">
            <h2 className="data-title">Pharmaceutical Manufacturing Analytics Platform</h2>
            <p className="data-subtitle">
              Advanced AI-driven insights for diabetes medication production with real-time quality monitoring and predictive analytics
            </p>
          </div>

          <div className="data-content">
            <div className="drug-information">
              <div className="drug-description">
                <h3 className="drug-title">Diabetes Medication Manufacturing</h3>
                <p className="drug-text">
                  Our platform monitors the production of advanced diabetes therapeutic tablets designed for optimal 
                  glycemic control. These oral antidiabetic medications are formulated with precise API concentrations 
                  and excipient ratios to ensure consistent bioavailability and patient efficacy. Each batch undergoes 
                  rigorous quality control testing including dissolution profiling, content uniformity, and impurity 
                  analysis to meet FDA and international regulatory standards for diabetes care.
                </p>
              </div>
            </div>

            <div className="data-categories">
              <div className="category-card">
                <div className="category-icon">
                  <svg className="category-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 11H7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2h-2M9 11V9a2 2 0 1 1 4 0v2M9 11h6"/>
                  </svg>
                </div>
                <h3 className="category-title">Pharmaceutical Tablets</h3>
                <div className="category-details">
                  <div className="detail-item">
                    <span className="detail-label">Drug Strengths:</span>
                    <span className="detail-value">5MG, 10MG, 20MG</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Batch Sizes:</span>
                    <span className="detail-value">240K - 1.92M tablets</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">API Content:</span>
                    <span className="detail-value">94.5% - 94.6% purity</span>
                  </div>
                </div>
              </div>

              <div className="category-card">
                <div className="category-icon">
                  <svg className="category-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                  </svg>
                </div>
                <h3 className="category-title">Process Sensors</h3>
                <div className="category-details">
                  <div className="detail-item">
                    <span className="detail-label">Compression Force:</span>
                    <span className="detail-value">Real-time monitoring</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Tablet Speed:</span>
                    <span className="detail-value">99.8-100 RPM</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Fill Depth:</span>
                    <span className="detail-value">Continuous tracking</span>
                  </div>
                </div>
              </div>

              <div className="category-card">
                <div className="category-icon">
                  <svg className="category-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
                    <path d="M12 11h4"/>
                    <path d="M12 16h4"/>
                    <path d="M8 11h.01"/>
                    <path d="M8 16h.01"/>
                  </svg>
                </div>
                <h3 className="category-title">Quality Parameters</h3>
                <div className="category-details">
                  <div className="detail-item">
                    <span className="detail-label">Dissolution Rate:</span>
                    <span className="detail-value">86% - 100%</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Hardness Testing:</span>
                    <span className="detail-value">36-82 N force</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Weight Variation:</span>
                    <span className="detail-value">±2.5% tolerance</span>
                  </div>
                </div>
              </div>

              <div className="category-card">
                <div className="category-icon">
                  <svg className="category-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M8 2v4"/>
                    <path d="M16 2v4"/>
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <path d="M3 10h18"/>
                    <path d="M8 14h.01"/>
                    <path d="M12 14h.01"/>
                    <path d="M16 14h.01"/>
                    <path d="M8 18h.01"/>
                    <path d="M12 18h.01"/>
                    <path d="M16 18h.01"/>
                  </svg>
                </div>
                <h3 className="category-title">Raw Materials</h3>
                <div className="category-details">
                  <div className="detail-item">
                    <span className="detail-label">Active Ingredient:</span>
                    <span className="detail-value">API with batch tracking</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Excipients:</span>
                    <span className="detail-value">SMCC, Lactose, Starch</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Water Content:</span>
                    <span className="detail-value">1.53-1.68% controlled</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
