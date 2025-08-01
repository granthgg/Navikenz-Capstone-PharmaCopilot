# PharmaCopilot - AI-Powered Pharmaceutical Manufacturing Optimization System

PharmaCopilot is a comprehensive AI-driven platform designed to revolutionize pharmaceutical manufacturing through intelligent forecasting, autonomous control, and automated compliance reporting. The system integrates advanced machine learning models with real-time monitoring to prevent batch defects, optimize production efficiency, and ensure regulatory compliance.

## System Architecture

PharmaCopilot implements a "Forecast-then-Act" methodology with three core AI capabilities:

1. **Time-Series Forecasting & Classification**: LSTM-based sensor forecasting with XGBoost classifiers for quality and defect prediction
2. **Reinforcement Learning Control**: Safe RL agents for autonomous process optimization using Conservative Q-Learning (CQL)
3. **Generative AI Reporting**: RAG-powered automated compliance reporting with regulatory knowledge base
<img width="897" height="590" alt="PharmaCopilot drawio" src="https://github.com/user-attachments/assets/d31753db-ae4c-4cc3-92c9-169abd843155" />


## Key Features

- **Real-time Sensor Monitoring**: Live data collection and processing from manufacturing sensors
- **Predictive Quality Control**: 60-minute ahead forecasting with 97.2% accuracy
- **Defect Prevention**: Early defect detection with 94.8% F1-score
- **Autonomous Process Control**: RL-based parameter adjustments within safety constraints
- **Compliance Automation**: 21 CFR 11 compliant report generation
- **OEE Dashboard**: Real-time Overall Equipment Effectiveness monitoring
- **Interactive Web Interface**: Comprehensive dashboard for monitoring and control

## Project Structure

### Core Directories

#### `/Data`
Contains the primary datasets used for model training and validation:
- `Laboratory.csv` - Quality control and batch analysis data (1,005 batches)
- `Process.csv` - Aggregated process parameters and manufacturing features
- `Normalization.csv` - Product-specific normalization factors
- `processed_timeseries.parquet` - Pre-processed time-series data for real-time inference

#### `/Model Train Code`
Model development and training implementations:
- `Phase-1 F+C.ipynb` - Forecasting and Classification model training
  - LSTM sensor forecasting model (TensorFlow/Keras)
  - XGBoost quality and defect classifiers
  - Feature engineering and model validation
- `Phase-2 RL.ipynb` - Reinforcement Learning model training
  - Conservative Q-Learning (CQL) implementation using d3rlpy
  - Safe exploration and policy optimization
  - Multi-model training (baseline, current, new)
- `Models/` - Trained RL model checkpoints
- `New Output/` - Saved model artifacts and scalers

#### `/Model Run Code`
Production API for model inference and real-time predictions:
- `prediction_api.py` - FastAPI server providing ML model endpoints
- `requirements.txt` - Python dependencies (TensorFlow, PyTorch, d3rlpy, XGBoost)
- `Models/` - RL model files and hyperparameters
- `New Output/` - Production model artifacts
  - `lstm_sensor_forecasting_model.h5` - LSTM forecasting model
  - `gradientboosting_defect_classifier.pkl` - Defect detection model
  - `gradientboosting_quality_class_classifier.pkl` - Quality classification model
  - `feature_scaler.pkl`, `lstm_scalers.pkl` - Data preprocessing scalers

**API Endpoints:**
- `/api/forecast` - LSTM sensor predictions (60-minute horizon)
- `/api/defect` - Defect probability classification
- `/api/quality` - Quality class prediction
- `/api/rl_action/{model}` - RL-based process recommendations

#### `/Sensor Data Simulation`
Real-time sensor data simulation and streaming:
- `app_streaming.py` - WebSocket-based streaming sensor simulation
- `app.py` - REST API sensor simulation
- `processed_timeseries.parquet` - Historical sensor data for simulation
- `requirements.txt` - Streaming dependencies (FastAPI, WebSockets, PyArrow)

**Features:**
- Realistic sensor data simulation based on historical patterns
- WebSocket streaming for real-time data feeds
- Configurable simulation parameters and noise injection

#### `/UI Code`
React-based web dashboard with Express.js proxy server:
- `server.js` - Express proxy server with API routing and fallback mechanisms
- `client/` - React application with comprehensive monitoring interface
- `package.json` - Node.js dependencies and build scripts

**Dashboard Components:**
- **Home Page**: System overview and key metrics
- **Live Sensors**: Real-time sensor monitoring with WebSocket updates
- **Forecast Panel**: LSTM predictions visualization with confidence intervals
- **RL Control**: Reinforcement learning recommendations and manual overrides
- **Reports View**: AI-generated compliance reports with export functionality
- **OEE Display**: Overall Equipment Effectiveness calculations and trends

**Technical Stack:**
- Frontend: React.js with Chart.js for visualizations
- Backend: Express.js with CORS and proxy middleware
- Styling: Custom CSS with responsive design
- Real-time Updates: WebSocket integration for live data

#### `/Report Generation`
AI-powered compliance reporting system with RAG implementation:
- `simple_run.py` - Streamlined FastAPI server for report generation
- `api/` - Report generation endpoints and request handling
- `knowledge_base/` - ChromaDB vector database for regulatory knowledge
- `llm_integration/` - Groq API integration with multiple LLM models
- `report_generators/` - Template-based report generation logic

**Report Types:**
- Quality Control Analysis
- Batch Record Analysis
- Process Deviation Investigation
- OEE Performance Summary
- Regulatory Compliance Review
- Manufacturing Excellence Report

**Features:**
- RAG-based context injection from historical data
- Multiple LLM model support (Llama 3.3-70B, Mixtral-8x7B)
- Vector-based knowledge retrieval using sentence transformers
- 21 CFR 11 compliant output formatting

#### `/EDA`
Exploratory Data Analysis and dataset understanding:
- `EDA.ipynb` - Comprehensive data exploration and visualization
- `Detail_EDA.ipynb` - In-depth statistical analysis and feature engineering
- Dataset copies for analysis
- `Process/` - Individual time-series files (1.csv through 25.csv)

#### `/Documentation`
Project documentation and research materials:
- `Dataset Documentation.pdf` - Detailed dataset specifications
- `Project Documentation.pdf` - System architecture and implementation guide
- `Research Paper.pdf` - Technical methodology and validation results

## Installation and Setup

### Prerequisites
- Python 3.8+ (recommended: 3.9)
- Node.js 16+ and npm
- Git

### Environment Setup

1. **Clone the repository:**
```bash
git clone https://github.com/granthgg/Navikenz-Capstone-PharmaCopilot.git
cd Navikenz-Capstone-PharmaCopilot
```

2. **Set up Python environment:**
```bash
# Create virtual environment
python -m venv pharma_env
source pharma_env/bin/activate  # On Windows: pharma_env\Scripts\activate

# Install core dependencies
pip install fastapi uvicorn tensorflow torch d3rlpy scikit-learn xgboost
```

3. **Install system-specific dependencies:**

**Model Run Code:**
```bash
cd "Model Run Code"
pip install -r requirements.txt
```

**Sensor Data Simulation:**
```bash
cd "Sensor Data Simulation"
pip install -r requirements.txt
```

**Report Generation:**
```bash
cd "Report Generation"
pip install fastapi chromadb groq sentence-transformers uvicorn
```

**UI Code:**
```bash
cd "UI Code"
npm install
cd client && npm install
```

## Running the System

### Full System Deployment

1. **Start the Prediction API (Port 8000):**
```bash
cd "Model Run Code"
python prediction_api.py
```

2. **Start Sensor Data Simulation (Port 8002):**
```bash
cd "Sensor Data Simulation"
python app_streaming.py
```

3. **Start Report Generation API (Port 8001):**
```bash
cd "Report Generation"
python simple_run.py
```

4. **Start UI Dashboard (Port 3001):**
```bash
cd "UI Code"
npm start
```

### Quick Start Scripts

**Windows:**
```bash
# PowerShell
./setup_deployed_environment.ps1

# Command Prompt
setup_deployed_environment.bat
```

### Individual Component Testing

**Test Prediction API:**
```bash
curl http://localhost:8000/api/forecast
curl http://localhost:8000/api/defect
curl http://localhost:8000/api/quality
```

**Test Report Generation:**
```bash
curl -X POST http://localhost:8001/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"report_type": "quality_control", "query": "Generate quality report"}'
```

**Test Sensor Simulation:**
```bash
curl http://localhost:8002/api/current
```

## Model Performance

### LSTM Forecasting Model
- **Architecture**: Multi-layer LSTM with dropout regularization
- **Input**: 60-step sensor sequences (waste, produced, ejection, speed, stiffness, SREL, compression)
- **Forecast Horizon**: 60 minutes
- **Performance**: RMSE < 0.05 on normalized data

### XGBoost Classification Models
- **Defect Classification**: F1-Score 94.8%, Precision 96.2%
- **Quality Classification**: Accuracy 97.2%, Macro F1-Score 95.8%
- **Features**: 7 key sensor parameters with engineered statistical features

### Reinforcement Learning Models
- **Algorithm**: Conservative Q-Learning (CQL) for safe exploration
- **Action Space**: Speed, compression, and fill adjustments (-10 to +10)
- **Training**: 1M+ simulated episodes with safety constraints
- **Models**: Baseline, current production, and experimental variants

## API Documentation

### Prediction API Endpoints

**GET /api/forecast**
```json
{
  "forecasted_values": [[1.2, 0.8, 120.5, ...]],
  "forecast_horizon": 60,
  "preprocessing_applied": true,
  "model_type": "LSTM"
}
```

**GET /api/defect**
```json
{
  "defect_probability": 0.15,
  "defect_class": "Normal",
  "confidence": 0.85,
  "preprocessing_applied": true
}
```

**GET /api/rl_action/{model}**
```json
{
  "recommended_actions": {
    "speed_adjustment": 2.5,
    "compression_adjustment": -1.0,
    "fill_adjustment": 0.5
  },
  "model_type": "current",
  "confidence": 0.92
}
```

### Report Generation API

**POST /api/reports/generate**
```json
{
  "report_type": "quality_control",
  "query": "Generate batch quality analysis",
  "additional_context": {}
}
```

## Configuration

### Environment Variables
```bash
# API URLs
PREDICTION_API_URL=http://localhost:8000
REPORT_API_URL=http://localhost:8001
SENSOR_API_URL=http://localhost:8002

# ML Models
MODEL_DIR=./New Output/
RL_MODEL_DIR=./Models/

# Report Generation
GROQ_API_KEY=your_groq_api_key
CHROMA_DB_PATH=./knowledge_base/chroma_db
```

### Model Configuration
Models are automatically loaded from their respective directories. Update `MODEL_DIR` and `RL_MODEL_DIR` paths in configuration files if models are stored elsewhere.

## System Integration

PharmaCopilot is designed for integration with existing manufacturing systems:

- **MES Integration**: REST API endpoints for Manufacturing Execution Systems
- **SCADA Compatibility**: Real-time data exchange protocols
- **ERP Integration**: Batch and production data synchronization
- **LIMS Integration**: Laboratory data import and quality parameter sharing

## Troubleshooting

### Common Issues

**Model Loading Errors:**
- Ensure all model files are present in the correct directories
- Check Python environment has all required packages
- Verify TensorFlow/PyTorch compatibility

**API Connection Issues:**
- Confirm all services are running on correct ports
- Check firewall settings and network connectivity
- Review proxy configuration in UI server

**Report Generation Failures:**
- Verify Groq API key is set correctly
- Check ChromaDB database initialization
- Ensure sufficient system memory for LLM operations

### Performance Optimization

- **Memory Usage**: Configure batch sizes based on available system memory
- **Model Inference**: Use GPU acceleration when available
- **Database Operations**: Implement connection pooling for high-throughput scenarios

## Contributing

This project was developed as part of the Navikenz Capstone Program. For contributions or questions:

1. Fork the repository
2. Create a feature branch
3. Implement changes with appropriate tests
4. Submit a pull request with detailed description



## Technical Requirements

- **Minimum System Requirements**: 8GB RAM, 4 CPU cores, 10GB storage
- **Recommended**: 16GB RAM, 8 CPU cores, GPU support for faster inference
- **Operating System**: Windows 10+, Ubuntu 18.04+, macOS 10.15+
- **Browser Support**: Chrome 90+, Firefox 88+, Safari 14+

## Future Enhancements

- **Advanced RL Algorithms**: Implementation of SAC and TD3 for comparison
- **Expanded Sensor Integration**: Support for additional sensor types and protocols
- **Enhanced Reporting**: Custom report templates and advanced analytics
- **Mobile Interface**: Responsive design optimization for mobile monitoring
- **Cloud Deployment**: Containerized deployment with Kubernetes orchestration

---

**PharmaCopilot v1.0** - Transforming pharmaceutical manufacturing through artificial intelligence and predictive analytics.

