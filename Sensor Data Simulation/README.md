# PharmaCopilot Sensor Data Simulation

FastAPI-based sensor data simulation service for pharmaceutical manufacturing processes with real-time WebSocket streaming.

## Features

- Real-time sensor data simulation from historical pharmaceutical manufacturing data
- WebSocket streaming for live data feeds
- REST API endpoints for sensor data access
- Memory-optimized streaming with batch processing
- Heroku-ready deployment with automatic memory management
- Thread-safe concurrent data access

## Architecture

- **Data Source**: Historical time-series data from `processed_timeseries.parquet`
- **Streaming**: WebSocket-based real-time data broadcasting
- **API**: FastAPI with automatic OpenAPI documentation
- **Memory Management**: Configurable batch processing for efficient memory usage

## Quick Start

### Prerequisites
- Python 3.8+
- `processed_timeseries.parquet` data file

### Installation

```bash
cd "Sensor Data Simulation"
pip install -r requirements.txt
```

### Running the Service

```bash
# Start both server and WebSocket client
python app_streaming.py

# Server only
python app_streaming.py --mode server --port 8002

# Custom configuration
python app_streaming.py --mode server --host 0.0.0.0 --port 8002 --interval 5
```

## API Endpoints

- **GET /health**: Service health check
- **GET /api/status**: System status and memory usage
- **GET /api/current**: Current sensor reading
- **GET /api/sensor/{sensor_name}**: Specific sensor value
- **GET /api/latest/{count}**: Latest N readings (max 20)
- **GET /api/all**: All historical readings
- **GET /api/sensors**: Available sensor names
- **WebSocket /ws**: Real-time streaming connection

## WebSocket Usage

```javascript
const socket = new WebSocket('ws://localhost:8002/ws');
socket.onmessage = function(event) {
    const message = JSON.parse(event.data);
    if (message.type === 'sensor_data') {
        console.log('New sensor data:', message.data);
    }
};
```

## Configuration

- **Data File**: `processed_timeseries.parquet` (configurable via `DATA_FILE_PATH`)
- **Update Interval**: 10 seconds (configurable via `--interval`)
- **Batch Size**: Auto-optimized based on environment (500-2000 rows)
- **Memory Management**: Automatic Heroku detection and optimization

## Integration

The Sensor Data Simulation integrates with:
- **Prediction API**: Provides real-time sensor data for model inference
- **UI Dashboard**: WebSocket streaming for live sensor visualization
- **Report Generation**: Historical data for compliance reporting

For complete setup instructions, see the main project README.

## Features

- ** FastAPI-powered** with high performance and automatic API documentation
- ** Pharmaceutical Manufacturing Focus** - Cholesterol-lowering drug production monitoring
- ** Memory-Optimized Streaming** with configurable batch processing (500-2000 rows)
- ** Native WebSocket streaming** for real-time data visualization
- ** REST API endpoints** with automatic OpenAPI/Swagger documentation
- ** Thread-safe data handling** for concurrent access with proper locking
- ** Historical data storage** with configurable retention (1000-2000 readings)
- ** Modern web interface** with interactive API documentation
- ** Heroku-ready deployment** with automatic memory constraint detection
- ** Aggressive garbage collection** for memory efficiency
- ** Real Data Only** - Works exclusively with parquet/CSV sensor data files

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure your sensor data file is available:**
   - The app expects `processed_timeseries.parquet` by default
   - You can modify `DATA_FILE_PATH` in `app_streaming.py` to use a different file
   - Supports both `.parquet` and `.csv` files
   - **Required**: The application will not start without real data files

## Usage

### Starting the Server

```bash
# Run both server and client (recommended)
python app_streaming.py

# Or start server only
python app_streaming.py --mode server

# Or with custom configuration
python app_streaming.py --mode server --port 8000 --interval 5
```

The server will start on `http://127.0.0.1:5000` (or the specified port)

### Web Interface & Documentation

Visit these URLs in your browser:

- **Main Interface**: `http://127.0.0.1:5000` - Real-time data visualization
- **Interactive API Docs**: `http://127.0.0.1:5000/docs` - Swagger UI with live testing
- **Alternative Docs**: `http://127.0.0.1:5000/redoc` - ReDoc documentation

### API Endpoints

| Endpoint | Method | Description | Example Response |
|----------|--------|-------------|------------------|
| `/health` | GET | Health check for monitoring | `{"status": "healthy", "service": "cholesterol-sensor-api"}` |
| `/api/status` | GET | Get API status and streaming info | `{"status": "active", "data_loaded": true, "memory_usage_mb": 45.2}` |
| `/api/current` | GET | Get current sensor reading | `{"status": "success", "data": {...}, "timestamp": "..."}` |
| `/api/sensor/{sensor_name}` | GET | Get specific sensor value | `{"status": "success", "sensor_name": "temp", "value": 25.3}` |
| `/api/latest/{count}` | GET | Get latest N readings (max 20) | `{"status": "success", "data": [...], "returned_count": 5}` |
| `/api/all` | GET | Get all historical readings | `{"status": "success", "data": [...], "count": 100}` |
| `/api/sensors` | GET | Get available sensor names | `{"status": "success", "available_sensors": [...]}` |
| `/ws` | WebSocket | Real-time streaming connection | Native WebSocket with JSON messages |

### WebSocket Usage

Connect to the WebSocket endpoint for real-time streaming:

```javascript
// Browser JavaScript
const wsUrl = 'ws://127.0.0.1:5000/ws';
const socket = new WebSocket(wsUrl);

socket.onmessage = function(event) {
    const message = JSON.parse(event.data);
    if (message.type === 'sensor_data' && message.data) {
        console.log('New sensor data:', message.data);
    }
};
```

```python
# Python with websockets library
import asyncio
import websockets
import json

async def listen_to_sensors():
    uri = "ws://127.0.0.1:5000/ws"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            if data.get('type') == 'sensor_data':
                print("New sensor reading:", data['data'])

asyncio.run(listen_to_sensors())
```

### Example API Usage

#### Python with requests library:

```python
import requests

# Get current sensor reading
response = requests.get("http://127.0.0.1:5000/api/current")
if response.status_code == 200:
    data = response.json()
    if data.get('status') == 'success':
        sensor_values = data['data']
        print(f"Current temperature: {sensor_values.get('temperature')}")

# Get specific sensor value
response = requests.get("http://127.0.0.1:5000/api/sensor/temperature")
if response.status_code == 200:
    data = response.json()
    if data.get('status') == 'success':
        print(f"Temperature: {data['value']}")
```

#### cURL examples:

```bash
# Get health status
curl http://127.0.0.1:5000/health

# Get API status with memory usage
curl http://127.0.0.1:5000/api/status

# Get current reading
curl http://127.0.0.1:5000/api/current

# Get specific sensor
curl http://127.0.0.1:5000/api/sensor/temperature

# Get latest 5 readings
curl http://127.0.0.1:5000/api/latest/5
```

### Running Different Modes

The application supports multiple run modes:

```bash
# Run both server and client together (default)
python app_streaming.py

# Run FastAPI server only
python app_streaming.py --mode server

# Run client only (requires server to be running separately)
python app_streaming.py --mode client

# Custom configuration
python app_streaming.py --mode server --host 0.0.0.0 --port 8000 --interval 5
```

## Configuration

### Key Configuration Variables in `app_streaming.py`:

- `DATA_FILE_PATH`: Path to your sensor data file (default: `'processed_timeseries.parquet'`)
- `DATA_INTERVAL_SECONDS`: Time between data updates (default: 10 seconds)
- `MAX_HISTORICAL_READINGS`: Maximum historical readings to keep in memory
  - Local: 2000 readings
  - Heroku: 1000 readings (automatic detection)
- **Memory-Efficient Batch Processing**:
  - Local: 2000 rows per batch
  - Heroku: 500 rows per batch (automatic optimization)

### Command Line Options

```bash
python app_streaming.py --help
```

Available options:
- `--mode`: Run mode (`server`, `client`, `both`) - default: `both`
- `--host`: Server host (default: `127.0.0.1`)
- `--port`: Server port (default: 5000, or `PORT` environment variable)
- `--interval`: Data interval in seconds (default: 10)

## Memory Optimization Features

### Automatic Memory Management
- **Batch Processing**: Loads data in configurable chunks (500-2000 rows)
- **Heroku Detection**: Automatically optimizes for Heroku memory constraints
- **Aggressive Garbage Collection**: More frequent on Heroku (every 3 cycles vs 10)
- **Thread-Safe Operations**: Proper locking mechanisms for concurrent access
- **Memory Monitoring**: Real-time memory usage tracking via `/api/status`

### MemoryEfficientDataStreamer Class
```python
# Automatic optimization based on environment
batch_size = 500 if 'PORT' in os.environ else 2000  # Heroku vs Local
```

### Memory Usage Monitoring
The `/api/status` endpoint provides detailed memory information:
```json
{
  "memory_usage_mb": 45.2,
  "memory_percent": 12.3,
  "memory_optimized": true,
  "ultra_minimal_mode": true,
  "heroku_mode": true,
  "streamer_info": {
    "current_batch_size": 500,
    "batch_size_limit": 500,
    "current_file_batch": 3
  }
}
```

## FastAPI Benefits

### Automatic API Documentation
- **Swagger UI** at `/docs` - Interactive API testing interface
- **ReDoc** at `/redoc` - Clean, organized documentation
- **OpenAPI Schema** - Machine-readable API specification

### Performance Improvements
- **Async/await support** for better concurrency
- **Native WebSocket support** without external libraries
- **Faster request processing** compared to Flask
- **Better resource utilization**
- **Memory-optimized batch processing**

### Development Experience
- **Automatic request/response validation**
- **Built-in type hints and validation**
- **Better error handling and debugging**
- **Modern Python standards compliance**

## Integration Examples

### Real-time Monitoring Dashboard

```python
import requests
import time

def monitor_pharmaceutical_sensors():
    while True:
        response = requests.get("http://127.0.0.1:5000/api/current")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                sensor_data = data['data']
                
                # Check for pharmaceutical manufacturing alerts
                if sensor_data.get('temperature', 0) > 80:
                    print("ALERT: High temperature in cholesterol production!")
                
                # Log to database, send notifications, etc.
                
        time.sleep(5)  # Check every 5 seconds
```

### WebSocket Real-time Processing

```python
import asyncio
import websockets
import json

async def process_pharmaceutical_data():
    uri = "ws://127.0.0.1:5000/ws"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get('type') == 'sensor_data':
                    sensor_data = data['data']
                    # Process pharmaceutical sensor data in real-time
                    await process_manufacturing_data(sensor_data)
            except json.JSONDecodeError:
                print("Invalid JSON received")

async def process_manufacturing_data(sensor_data):
    # Your pharmaceutical monitoring logic here
    print(f"Processing cholesterol production data: {len(sensor_data)} sensor values")
```

## Deployment

### Local Development

```bash
# Using the built-in server
python app_streaming.py --mode server

# Using uvicorn directly
uvicorn app_streaming:app --host 0.0.0.0 --port 5000 --reload
```

### Production Deployment

#### Option 1: Uvicorn with workers
```bash
pip install uvicorn[standard]
uvicorn app_streaming:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Option 2: Gunicorn with Uvicorn workers
```bash
pip install gunicorn uvicorn[standard]
gunicorn app_streaming:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Heroku Deployment

The app is optimized for Heroku deployment with automatic memory management:

1. **Procfile is already configured:**
   ```
   web: uvicorn app_streaming:app --host 0.0.0.0 --port $PORT --workers 1
   ```

2. **Automatic Heroku Optimization:**
   - Detects `PORT` environment variable
   - Reduces batch size to 500 rows for memory efficiency
   - Limits historical readings to 1000
   - Increases garbage collection frequency

3. **Push to Heroku:**
   ```bash
   git add .
   git commit -m "Deploy pharmaceutical sensor streaming app"
   git push heroku main
   ```

4. **Environment automatically optimized:**
   - Uses `PORT` environment variable
   - Handles memory constraints gracefully
   - Manages missing data files appropriately

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY processed_timeseries.parquet .

EXPOSE 8000
CMD ["uvicorn", "app_streaming:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Error Handling

The API returns appropriate HTTP status codes with detailed pharmaceutical context:

- `200`: Success
- `404`: Resource not found (no data available)
- `400`: Bad request (invalid parameters)
- `422`: Validation error (FastAPI automatic validation)
- `500`: Server error

Error responses include descriptive messages:

```json
{
  "error": "No current reading available",
  "message": "Real data file not loaded. Check if parquet file exists and is accessible."
}
```

## Data Requirements

### Required Data Format
- **Primary**: Parquet files (`.parquet`) - preferred for memory efficiency
- **Alternative**: CSV files (`.csv`) with semicolon delimiter (`;`)
- **Location**: Must be in the same directory as `app_streaming.py`
- **Default filename**: `processed_timeseries.parquet`

### Data Processing
- **Timestamp handling**: Automatic conversion to ISO format
- **NaN handling**: Converted to `None` for JSON compatibility  
- **Float precision**: Rounded to 4 decimal places for memory efficiency
- **Extreme values**: Values > 1e10 are filtered out

## Performance & Memory Optimization

- **Streaming Data Loading**: Loads data in configurable chunks (500-2000 rows)
- **Thread-Safe Operations**: Concurrent access with proper locking mechanisms
- **Heroku Optimization**: Automatic memory constraint detection and optimization
- **WebSocket Management**: Efficient connection handling and cleanup
- **Garbage Collection**: Aggressive memory management with configurable frequency
- **Batch Processing**: Ultra-efficient data streaming for large files



## Use Cases

This API is specifically designed for:
- **Pharmaceutical Manufacturing Monitoring** - Real-time cholesterol drug production
- **Quality Control Systems** - Continuous sensor monitoring during drug synthesis
- **Regulatory Compliance** - Data logging for pharmaceutical regulations
- **Process Optimization** - Real-time analysis of manufacturing parameters
- **Alert Systems** - Immediate notification of production anomalies

