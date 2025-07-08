# Sensor Data Simulation API

A Flask-based application that simulates live sensor data streams and provides REST API endpoints for accessing sensor values in real-time.

## Features

- **Real-time WebSocket streaming** for live data visualization
- **REST API endpoints** for programmatic access to sensor data
- **Thread-safe data handling** for concurrent access
- **Historical data storage** with configurable retention
- **Web interface** with API documentation

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure your sensor data file is in the same directory:**
   - The app expects `processed_timeseries.parquet` by default
   - You can modify `DATA_FILE_PATH` in `app.py` to use a different file
   - Supports both `.parquet` and `.csv` files

## Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://127.0.0.1:5000`

### Web Interface

Visit `http://127.0.0.1:5000` in your browser to see:
- Real-time sensor data visualization
- API endpoint documentation
- Connection status

### API Endpoints

| Endpoint | Method | Description | Example Response |
|----------|--------|-------------|------------------|
| `/api/status` | GET | Get API status and information | `{"status": "active", "data_loaded": true, ...}` |
| `/api/current` | GET | Get current sensor reading | `{"status": "success", "data": {...}, "timestamp": "..."}` |
| `/api/sensor/<name>` | GET | Get specific sensor value | `{"status": "success", "sensor_name": "temp", "value": 25.3}` |
| `/api/latest/<count>` | GET | Get latest N readings | `{"status": "success", "data": [...], "count": 5}` |
| `/api/all` | GET | Get all historical readings | `{"status": "success", "data": [...], "count": 100}` |
| `/api/sensors` | GET | Get available sensor names | `{"status": "success", "available_sensors": [...]}` |

### Example API Usage

#### Python with requests library:

```python
import requests

# Get current sensor reading
response = requests.get("http://127.0.0.1:5000/api/current")
if response.status_code == 200:
    data = response.json()
    sensor_values = data['data']
    print(f"Current temperature: {sensor_values.get('temperature')}")

# Get specific sensor value
response = requests.get("http://127.0.0.1:5000/api/sensor/temperature")
if response.status_code == 200:
    data = response.json()
    print(f"Temperature: {data['value']}")
```

#### cURL examples:

```bash
# Get API status
curl http://127.0.0.1:5000/api/status

# Get current reading
curl http://127.0.0.1:5000/api/current

# Get specific sensor
curl http://127.0.0.1:5000/api/sensor/temperature

# Get latest 5 readings
curl http://127.0.0.1:5000/api/latest/5
```

### Running Different Modes

The application now has integrated client functionality with multiple run modes:

```bash
# Run both server and client together (default)
python app.py

# Run server only
python app.py --mode server

# Run client only (requires server to be running separately)
python app.py --mode client

# Monitor a specific sensor continuously
python app.py --mode monitor --sensor temperature
```

This demonstrates:
- Checking API availability
- Fetching current and historical data
- Monitoring specific sensors
- Processing sensor data
- All in one integrated application

## Configuration

Edit these variables in `app.py`:

- `DATA_FILE_PATH`: Path to your sensor data file
- `DATA_INTERVAL_SECONDS`: Time between data updates (default: 10 seconds)
- `MAX_HISTORICAL_READINGS`: Maximum historical readings to keep in memory (default: 1000)

## Integration Examples

### Real-time Monitoring Dashboard

```python
import requests
import time

def monitor_sensors():
    while True:
        response = requests.get("http://127.0.0.1:5000/api/current")
        if response.status_code == 200:
            data = response.json()['data']
            
            # Check for alerts
            if data.get('temperature', 0) > 80:
                print("ALERT: High temperature detected!")
            
            # Log to database, send notifications, etc.
            
        time.sleep(5)  # Check every 5 seconds
```

### Data Collection Service

```python
import requests
import json

def collect_sensor_data():
    response = requests.get("http://127.0.0.1:5000/api/latest/10")
    if response.status_code == 200:
        readings = response.json()['data']
        
        # Store in database
        for reading in readings:
            # save_to_database(reading)
            pass
        
        return readings
```

### Machine Learning Input

```python
import requests
import numpy as np

def get_features_for_ml():
    response = requests.get("http://127.0.0.1:5000/api/current")
    if response.status_code == 200:
        data = response.json()['data']
        
        # Extract numeric features
        features = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                features.append(value)
        
        return np.array(features)
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `404`: Resource not found (no data available)
- `400`: Bad request (invalid parameters)
- `500`: Server error

Error responses include descriptive messages:

```json
{
  "error": "No current reading available",
  "message": "Wait for the simulation to start or check if data is loaded"
}
```

## Thread Safety

The application is designed for concurrent access:
- Current readings are protected with locks
- Historical data uses thread-safe collections
- Multiple clients can access the API simultaneously

## Deployment

For production deployment:

1. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn --worker-class eventlet -w 1 app:app
   ```

2. **Configure environment variables:**
   - Set `FLASK_ENV=production`
   - Use proper secret keys
   - Configure logging

3. **Set up reverse proxy** (nginx, Apache) for SSL termination

4. **Monitor resource usage** - adjust `MAX_HISTORICAL_READINGS` based on memory constraints

## License

This project is provided as-is for demonstration purposes. 