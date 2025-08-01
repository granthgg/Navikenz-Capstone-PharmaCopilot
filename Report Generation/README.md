# PharmaCopilot Report Generation System

AI-powered automated compliance reporting system with RAG-based knowledge retrieval for pharmaceutical manufacturing.

## Features

- RAG-powered LLM integration with Groq API (Llama 3.3-70B, Mixtral-8x7B)
- ChromaDB vector database for regulatory knowledge retrieval
- Multiple report types for comprehensive compliance coverage
- Real-time data integration from PharmaCopilot APIs
- 21 CFR 11 compliant output formatting

## Architecture

- **LLM Integration**: Groq API with multiple model support
- **Knowledge Base**: ChromaDB with sentence transformers
- **Data Collection**: Automated API data gathering
- **Report Engine**: Template-based generation with AI enhancement

## Report Types

- **Quality Control Analysis**: Defect probability and risk assessment
- **Batch Record Analysis**: Production efficiency and quality metrics
- **Process Deviation Investigation**: Root cause analysis and corrective actions
- **OEE Performance Summary**: Equipment effectiveness reporting
- **Regulatory Compliance Review**: Compliance status and recommendations
- **Manufacturing Excellence Report**: Overall performance assessment

## Quick Start

### Prerequisites
- Python 3.8+
- Groq API key
- PharmaCopilot backend services running

### Installation

```bash
cd "Report Generation"
pip install fastapi chromadb groq sentence-transformers uvicorn
```

### Configuration

Set your Groq API key:
```bash
export GROQ_API_KEY=your_api_key_here
```

### Running the Service

```bash
python simple_run.py
```

The service will be available at `http://localhost:8001`

## API Endpoints

### Generate Report
```bash
POST /api/reports/generate
Content-Type: application/json

{
  "report_type": "quality_control",
  "query": "Generate comprehensive quality analysis",
  "additional_context": {}
}
```

### Health Check
```bash
GET /api/reports/health
```

## Integration

The Report Generation system automatically collects data from:
- **Prediction API** (`localhost:8000`): LSTM forecasts and classifications
- **Sensor API** (`localhost:8002`): Real-time sensor data
- **Knowledge Base**: Historical regulatory data and compliance guidelines

For complete setup instructions, see the main project README.
- Loss analysis and categorization
- Benchmark comparisons
- Improvement recommendations

### 5. Regulatory Compliance Review
- 21 CFR Part 11 compliance assessment
- GMP compliance verification
- Data integrity evaluation
- Compliance gap analysis

##  Installation & Setup

### Prerequisites
- Python 3.8+
- Access to PharmaCopilot prediction APIs (localhost:8000)
- Groq API key

### 1. Install Dependencies
```bash
cd "Report Generation"
pip install -r requirements.txt
```

### 2. Set Environment Variables (Optional)
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```
*Note: The system includes a default API key for demo purposes*

### 3. Start the System
```bash
# Start with full functionality (API server + scheduler)
python run_report_system.py

# Start API server only (no automated data collection)
python run_report_system.py --no-scheduler

# Custom configuration
python run_report_system.py --host 0.0.0.0 --port 8001 --api-url http://localhost:8000
```

## 🌐 API Endpoints

### Core Report Generation
- `POST /api/reports/generate` - Generate reports
- `GET /api/reports/types` - Available report types
- `GET /api/reports/health` - System health check

### Knowledge Base Management
- `GET /api/knowledge/status` - Knowledge base statistics
- `POST /api/knowledge/search` - Search knowledge base
- `POST /api/knowledge/add-documentation` - Add documentation
- `POST /api/knowledge/cleanup` - Clean old data

### Data Collection
- `POST /api/data/collect` - Manual data collection
- `GET /api/data/summaries` - Recent data summaries
- `GET /api/reports/quality/metrics` - Quality metrics

### API Documentation
- Interactive docs: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

##  Integration with PharmaCopilot Dashboard

### Frontend Integration
The system integrates seamlessly with the existing React dashboard:

```javascript
// Generate a quality control report
const response = await axios.post('/api/reports/generate', {
  report_type: 'quality_control',
  query: 'Generate comprehensive quality control report',
  additional_context: {
    timestamp: new Date().toISOString(),
    source: 'pharmacopilot_dashboard'
  }
});
```

### UI Features
- Real-time report generation with progress indicators
- Report history and management
- System status monitoring
- Error handling and fallback displays

##  Automated Data Collection

### Scheduling
- **Data Collection**: Every 5 minutes from all API sources
- **Knowledge Base Cleanup**: Daily at 2:00 AM
- **File Cleanup**: Every 6 hours

### Data Sources
1. **Forecasting Data** (`/api/forecast`)
   - LSTM predictions for 60-minute horizon
   - Sensor forecasting data
   - Preprocessing status

2. **Classification Data** (`/api/defect`, `/api/quality`)
   - Defect probability predictions
   - Quality class predictions
   - Confidence scores

3. **RL Action Data** (`/api/rl_action/{model}`)
   - Baseline, current, and new model recommendations
   - Speed, compression, and fill adjustments
   - Model performance metrics

##  RAG System Architecture

### Knowledge Retrieval Process
1. **Query Processing**: Convert user query to embeddings
2. **Context Search**: Find relevant historical data using vector similarity
3. **Context Ranking**: Sort by relevance scores
4. **Prompt Construction**: Build comprehensive prompt with context
5. **LLM Generation**: Generate report using Groq API
6. **Post-processing**: Format and validate output

### Vector Database Schema
```
Collections:
├── historical_data/     # Real-time collected data
├── documentation/       # Regulatory and process docs
└── templates/          # Report templates and examples
```

##  Example Usage

### Generate Quality Control Report
```python
import requests

response = requests.post('http://localhost:8001/api/reports/generate', json={
    'report_type': 'quality_control',
    'query': 'Analyze current quality metrics and defect probability trends',
    'additional_context': {
        'focus_area': 'compression_force_analysis',
        'time_window': '24_hours'
    }
})

report = response.json()['report']
print(report['report_content'])
```

### Search Knowledge Base
```python
response = requests.post('http://localhost:8001/api/knowledge/search', json={
    'query': 'defect probability trends tablet compression',
    'collection': 'historical_data',
    'max_results': 10
})

results = response.json()['results']
```

##  Configuration Options

### Command Line Arguments
- `--host`: API server host (default: 0.0.0.0)
- `--port`: API server port (default: 8001)
- `--api-url`: PharmaCopilot API base URL (default: http://localhost:8000)
- `--no-scheduler`: Disable automated data collection
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Environment Variables
- `GROQ_API_KEY`: Groq API authentication key
- `CHROMADB_PATH`: Custom ChromaDB storage path
- `LOG_LEVEL`: Default logging level

##  System Monitoring

### Health Checks
```bash
curl http://localhost:8001/api/reports/health
```

### Knowledge Base Statistics
```bash
curl http://localhost:8001/api/knowledge/status
```

### Data Collection Status
```bash
curl http://localhost:8001/api/data/summaries?hours=6
```

##  Security & Compliance

### 21 CFR Part 11 Compliance
- Audit trails for all data operations
- Electronic signature capabilities
- Data integrity validation
- Access control and authentication

### Data Security
- Encrypted API communications
- Secure knowledge base storage
- Automated data cleanup
- Access logging and monitoring

##  Troubleshooting

### Common Issues

1. **ChromaDB Connection Errors**
   ```bash
   # Clean up database
   rm -rf Report\ Generation/knowledge_base/embeddings/vector_store/
   ```

2. **Groq API Rate Limits**
   - System includes automatic retry logic
   - Falls back to template-based reports

3. **Memory Issues**
   - Reduce knowledge base retention period
   - Increase cleanup frequency

4. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Debug Mode
```bash
python run_report_system.py --log-level DEBUG
```

##  Performance Optimization

### Recommended Settings
- **Production**: Use `llama-3.3-70b-versatile` for best quality
- **Development**: Use `llama-3.1-8b-instant` for faster responses
- **Memory Constrained**: Enable aggressive cleanup schedules

### Scaling Considerations
- ChromaDB supports distributed deployment
- FastAPI can be deployed with multiple workers
- Knowledge base can be shared across instances

##  Future Enhancements

### Planned Features
- Additional report types (Manufacturing Excellence, Sustainability)
- Multi-language report generation
- Advanced analytics and trend prediction
- Integration with external regulatory systems
- Custom report templates
- Batch report processing

### API Extensions
- WebSocket support for real-time streaming
- GraphQL API for complex queries
- Webhook notifications for report completion
- Export to multiple formats (PDF, Word, Excel)

##  Contributing

### Development Setup
1. Clone the repository
2. Install development dependencies
3. Run tests: `pytest`
4. Follow code style guidelines

### Code Structure
```
Report Generation/
├── api/                 # FastAPI endpoints
├── data_collectors/     # API data collection
├── knowledge_base/      # Vector database management
├── llm_integration/     # Groq client and prompts
├── report_generators/   # Report generation logic
├── requirements.txt     # Dependencies
└── run_report_system.py # Main entry point
```



---

**PharmaCopilot Report Generation System** - Transforming pharmaceutical manufacturing through AI-powered insights and regulatory-compliant reporting. 