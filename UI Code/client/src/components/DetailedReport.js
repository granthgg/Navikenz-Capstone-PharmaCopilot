import React, { useEffect } from 'react';
import './DetailedReport.css';

const DetailedReport = ({ onBackToHome }) => {
  useEffect(() => {
    // Tab functionality
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    const handleTabClick = (e) => {
      const tab = e.currentTarget;
      tabs.forEach(item => item.classList.remove('active'));
      tab.classList.add('active');
      const target = document.getElementById(tab.dataset.tab);
      tabContents.forEach(content => content.classList.add('hidden'));
      target.classList.remove('hidden');
    };

    tabs.forEach(tab => {
      tab.addEventListener('click', handleTabClick);
    });

    // Animate counters when section comes into view
    function animateCounters() {
      const counters = document.querySelectorAll('.kpi-card h3');
      const speed = 200; 

      counters.forEach(counter => {
        const updateCount = () => {
          const target = +counter.getAttribute('data-target');
          const count = +counter.innerText;
          const inc = target / speed;

          if (count < target) {
            counter.innerText = Math.ceil(count + inc);
            setTimeout(updateCount, 10);
          } else {
            counter.innerText = target;
          }
        };
        updateCount();
      });
    }

    const impactSection = document.getElementById('impact');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounters();
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    
    if (impactSection) {
      observer.observe(impactSection);
    }

    // Cleanup
    return () => {
      tabs.forEach(tab => {
        tab.removeEventListener('click', handleTabClick);
      });
      if (impactSection) {
        observer.unobserve(impactSection);
      }
    };
  }, []);

  useEffect(() => {
    // Chart.js integration
    const loadCharts = async () => {
      if (window.Chart) {
        const classificationData = {
          labels: ['Quality Classification', 'Defect Detection'],
          datasets: [{
            label: 'Model Accuracy',
            data: [82.8, 91.4],
            backgroundColor: ['rgba(79, 70, 229, 0.7)', 'rgba(20, 184, 166, 0.7)'],
            borderColor: ['rgb(79, 70, 229)', 'rgb(20, 184, 166)'],
            borderWidth: 2,
            borderRadius: 5,
          }]
        };

        const forecastingData = {
          labels: ['Waste', 'Produced', 'Ejection', 'Stiffness', 'Main Comp.'],
          datasets: [{
            label: 'R² Score',
            data: [0.9937, 0.9973, 0.8160, 0.9733, 0.9606],
            backgroundColor: 'rgba(20, 184, 166, 0.7)',
            borderColor: 'rgb(20, 184, 166)',
            borderWidth: 2,
            borderRadius: 5,
          }]
        };

        const chartOptions = {
          maintainAspectRatio: false,
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: 'rgba(203, 213, 225, 0.3)' },
              ticks: { color: '#475569' }
            },
            x: {
              grid: { display: false },
              ticks: { color: '#475569' }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              enabled: true,
              backgroundColor: '#1e293b',
              titleColor: '#f1f5f9',
              bodyColor: '#cbd5e1',
              cornerRadius: 6,
              displayColors: false,
              callbacks: {
                label: function(context) {
                  let label = context.dataset.label || '';
                  if (label) {
                    label += ': ';
                  }
                  if (context.parsed.y !== null) {
                    label += context.parsed.y;
                  }
                  return label;
                }
              }
            }
          }
        };

        const classificationCtx = document.getElementById('classificationChart');
        const forecastingCtx = document.getElementById('forecastingChart');

        if (classificationCtx && forecastingCtx) {
          new window.Chart(classificationCtx.getContext('2d'), {
            type: 'bar',
            data: classificationData,
            options: { ...chartOptions, scales: { ...chartOptions.scales, y: { ...chartOptions.scales.y, max: 100 } } }
          });

          new window.Chart(forecastingCtx.getContext('2d'), {
            type: 'bar',
            data: forecastingData,
            options: { ...chartOptions, scales: { ...chartOptions.scales, y: { ...chartOptions.scales.y, max: 1 } } }
          });
        }
      }
    };

    // Wait a bit for the component to fully mount
    setTimeout(loadCharts, 100);
  }, []);

  return (
    <div className="detailed-report">
      <header id="header" className="report-header">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold text-indigo-600">PharmaCopilot AI</span>
            </div>
            <div className="flex items-center">
              <button 
                onClick={onBackToHome}
                className="back-to-home-btn-mobile md:hidden bg-slate-800 text-white px-3 py-1 rounded text-xs font-medium hover:bg-slate-900 transition-colors"
              >
                Home
              </button>
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <a href="#problem" className="nav-link text-sm font-medium text-slate-600">The Challenge</a>
              <a href="#solution" className="nav-link text-sm font-medium text-slate-600">Our Solution</a>
              <a href="#performance" className="nav-link text-sm font-medium text-slate-600">Performance</a>
              <a href="#impact" className="nav-link text-sm font-medium text-slate-600">Business Impact</a>
              <button 
                onClick={onBackToHome}
                className="back-to-home-btn bg-slate-800 text-white px-4 py-2 rounded-lg hover:bg-slate-900 transition-colors text-sm font-medium"
              >
                Home
              </button>
            </nav>
          </div>
        </div>
      </header>

      <main>
        <section id="hero" className="hero-section">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900">
              Intelligent Manufacturing Analytics & Quality Control
            </h1>
            <p className="mt-6 max-w-3xl mx-auto text-lg md:text-xl text-slate-600">
              An advanced AI-powered platform designed to revolutionize pharmaceutical manufacturing through real-time monitoring, predictive analytics, and intelligent process optimization.
            </p>
            <div className="mt-10">
              <a href="#problem" className="inline-block bg-indigo-600 text-white font-semibold px-8 py-3 rounded-lg shadow-lg hover:bg-indigo-700 transition-colors">
                Discover The Impact
              </a>
            </div>
          </div>
        </section>

        <section id="problem" className="problem-section">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">The High Cost of Reactive Quality Control</h2>
              <p className="mt-4 max-w-2xl mx-auto text-lg text-slate-600">
                Traditional manufacturing processes face significant financial and operational challenges due to their reactive nature. These inefficiencies lead to waste, delays, and missed opportunities.
              </p>
            </div>
            <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <div className="bg-white p-8 rounded-xl shadow-lg">
                <div className="text-5xl font-extrabold text-indigo-600">$1.2M</div>
                <p className="mt-2 text-lg font-semibold">Annual Loss Per Plant</p>
                <p className="mt-1 text-slate-500">From batches rejected during final lab testing.</p>
              </div>
              <div className="bg-white p-8 rounded-xl shadow-lg">
                <div className="text-5xl font-extrabold text-indigo-600">22%</div>
                <p className="mt-2 text-lg font-semibold">High-Risk Periods Under-Tested</p>
                <p className="mt-1 text-slate-500">Due to inefficient 10% sampling methods.</p>
              </div>
              <div className="bg-white p-8 rounded-xl shadow-lg">
                <div className="text-5xl font-extrabold text-indigo-600">48 Hours</div>
                <p className="mt-2 text-lg font-semibold">Average Batch Release Time</p>
                <p className="mt-1 text-slate-500">Creating significant operational bottlenecks.</p>
              </div>
            </div>
          </div>
        </section>

        <section id="solution" className="solution-section">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">A Proactive, AI-Powered Platform</h2>
              <p className="mt-4 max-w-2xl mx-auto text-lg text-slate-600">
                PharmaCopilot AI shifts manufacturing from reactive to proactive control by fusing proven AI levers for end-to-end intelligence and optimization.
              </p>
            </div>
            <div className="mt-12 max-w-4xl mx-auto">
              <div className="flex justify-center border-b border-slate-200">
                <button data-tab="forecast" className="tab-btn active flex-1 md:flex-none px-4 py-3 text-sm md:text-base font-medium text-slate-700 rounded-t-lg transition-colors">Forecast-then-Act</button>
                <button data-tab="control" className="tab-btn flex-1 md:flex-none px-4 py-3 text-sm md:text-base font-medium text-slate-700 rounded-t-lg transition-colors">RL-Powered Control</button>
                <button data-tab="report" className="tab-btn flex-1 md:flex-none px-4 py-3 text-sm md:text-base font-medium text-slate-700 rounded-t-lg transition-colors">GenAI Reporting</button>
              </div>
              <div className="mt-8">
                <div id="forecast" className="tab-content">
                  <h3 className="text-2xl font-bold text-indigo-600">Predictive Quality Forecasts</h3>
                  <p className="mt-2 text-slate-600">Anticipate and prevent quality deviations before they occur. Our platform uses advanced time-series models to provide a 60-minute forecast of key quality parameters, giving operators a crucial window to act and prevent batch loss.</p>
                </div>
                <div id="control" className="tab-content hidden">
                  <h3 className="text-2xl font-bold text-indigo-600">Autonomous Process Adjustments</h3>
                  <p className="mt-2 text-slate-600">A safe Reinforcement Learning (RL) agent makes autonomous, real-time process adjustments. Trained on over 1 million simulated episodes, the system optimizes for throughput while ensuring all actions remain within strict safety and compliance limits.</p>
                </div>
                <div id="report" className="tab-content hidden">
                  <h3 className="text-2xl font-bold text-indigo-600">Automated Compliance Reporting</h3>
                  <p className="mt-2 text-slate-600">Instantly generate comprehensive, 21 CFR 11-compliant reports. Our Retrieval-Augmented Generation (RAG) model, powered by Gemini 2.5 Flash, pulls data from batch logs and regulatory guidelines to create accurate, grounded reports in minutes, not hours.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="performance" className="performance-section">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Methodology & Model Performance</h2>
              <p className="mt-4 max-w-2xl mx-auto text-lg text-slate-600">
                Our platform is built on a foundation of robust, state-of-the-art machine learning models. Each component is designed for maximum accuracy and reliability in a real-world manufacturing environment.
              </p>
            </div>
            <div className="mt-16 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div className="bg-white p-8 rounded-xl shadow-lg">
                <h3 className="text-xl font-bold text-center mb-4">Quality & Defect Classification (XGBoost)</h3>
                <div className="chart-container">
                  <canvas id="classificationChart"></canvas>
                </div>
                <p className="text-center text-sm text-slate-500 mt-4">Accuracy scores for identifying product quality and detecting defects.</p>
              </div>
              <div className="bg-white p-8 rounded-xl shadow-lg">
                <h3 className="text-xl font-bold text-center mb-4">Sensor Forecasting Performance (LSTM R²)</h3>
                <div className="chart-container">
                  <canvas id="forecastingChart"></canvas>
                </div>
                <p className="text-center text-sm text-slate-500 mt-4">R² scores indicating the predictive accuracy of our LSTM model across key sensors.</p>
              </div>
            </div>
          </div>
        </section>

        <section id="impact" className="impact-section">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Transforming Manufacturing Efficiency</h2>
              <p className="mt-4 max-w-2xl mx-auto text-lg text-indigo-200">
                By implementing PharmaCopilot AI, manufacturers can achieve dramatic improvements across key performance indicators, leading to significant cost savings and enhanced compliance.
              </p>
            </div>
            <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="kpi-card text-center bg-indigo-600/50 p-6 rounded-xl">
                <h3 className="text-5xl font-extrabold text-teal-300" data-target="94">0</h3>
                <p className="mt-2 text-lg font-semibold">Defect Detection Rate (%)</p>
                <p className="mt-1 text-indigo-200">From 72% to 94%</p>
              </div>
              <div className="kpi-card text-center bg-indigo-600/50 p-6 rounded-xl">
                <h3 className="text-5xl font-extrabold text-teal-300" data-target="87">0</h3>
                <p className="mt-2 text-lg font-semibold">Reduction in Release Time (%)</p>
                <p className="mt-1 text-indigo-200">From 48 hours to 6 hours</p>
              </div>
              <div className="kpi-card text-center bg-indigo-600/50 p-6 rounded-xl">
                <h3 className="text-5xl font-extrabold text-teal-300" data-target="90">0</h3>
                <p className="mt-2 text-lg font-semibold">Reduction in Report Prep (%)</p>
                <p className="mt-1 text-indigo-200">From 8 hours to 45 mins</p>
              </div>
              <div className="kpi-card text-center bg-indigo-600/50 p-6 rounded-xl">
                <h3 className="text-5xl font-extrabold text-teal-300" data-target="33">0</h3>
                <p className="mt-2 text-lg font-semibold">Reduction in Sampling Costs (%)</p>
                <p className="mt-1 text-indigo-200">From $18k to $12k per batch</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="report-footer">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold">PharmaCopilot</h2>
          <p className="mt-4 max-w-2xl mx-auto text-slate-400">
            Created by <span className="text-white font-semibold">Granth Gaurav</span>
          </p>
          <p className="mt-2 text-slate-400">
            Powered by <span className="text-white font-semibold">Navikenz</span>
          </p>
          <p className="mt-8 text-sm text-slate-500">&copy; 2025 PharmaCopilot AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default DetailedReport;
