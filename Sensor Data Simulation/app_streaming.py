# app_streaming.py
#
# Memory-optimized streaming version for Heroku deployment
# Loads data in chunks to stay within 512MB memory limit
#
# This version loads only small chunks of data at a time and automatically
# loads the next chunk when the current one is exhausted, ensuring continuous
# operation while maintaining low memory usage.

import eventlet
# We patch the standard library to be non-blocking for eventlet to work correctly.
eventlet.monkey_patch()

import pandas as pd
import time
import argparse
import sys
import json
import os
import gc  # For garbage collection
from threading import Thread, Event, Lock, Timer
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
from collections import deque
from datetime import datetime
import requests

# --- Configuration ---
# Update this path to your Parquet or CSV file.
DATA_FILE_PATH = 'processed_timeseries.parquet'
# The time interval in seconds between sending data points.
DATA_INTERVAL_SECONDS = 10
# Maximum number of historical readings to keep in memory
MAX_HISTORICAL_READINGS = 1000
# Chunk size for memory-efficient loading (rows per chunk)
CHUNK_SIZE = 500  # Adjust based on your data size and memory needs
# Server configuration (will be updated by command line args)
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
API_BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/api"

# --- Flask & SocketIO Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key!'
socketio = SocketIO(app, async_mode='eventlet')

# --- Global variables for the simulation ---
thread = None
thread_stop_event = Event()
current_reading = {}
current_reading_lock = Lock()
historical_readings = deque(maxlen=MAX_HISTORICAL_READINGS)
historical_readings_lock = Lock()
data_loaded = False
data_columns = []

# --- Streaming data management ---
data_streamer = None
data_streamer_lock = Lock()

class DataStreamer:
    """Memory-efficient data streamer that loads data in chunks."""
    
    def __init__(self, file_path, chunk_size=CHUNK_SIZE):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.current_chunk = None
        self.current_index = 0
        self.chunk_start_row = 0
        self.total_rows = None
        self.is_parquet = file_path.endswith('.parquet')
        self.data_columns = []
        self.end_of_data = False
        
        # Initialize first chunk and get metadata
        self._load_metadata()
        self._load_next_chunk()
    
    def _load_metadata(self):
        """Load file metadata without loading all data."""
        try:
            if self.is_parquet:
                # For parquet, use a more memory-efficient approach
                print("Loading parquet metadata efficiently...")
                
                # Check if we're on Heroku (memory constrained environment)
                is_heroku = 'PORT' in os.environ
                
                if is_heroku:
                    # On Heroku: Load smaller sample and estimate total rows
                    print("Heroku detected - using memory-efficient parquet loading")
                    try:
                        # Try to use PyArrow for metadata if available
                        import pyarrow.parquet as pq
                        parquet_file = pq.ParquetFile(self.file_path)
                        self.total_rows = parquet_file.metadata.num_rows
                        # Get schema for column names
                        schema = parquet_file.schema.to_arrow_schema()
                        self.data_columns = schema.names
                        print(f"PyArrow metadata: {self.total_rows} rows, {len(self.data_columns)} columns")
                    except ImportError:
                        # Fallback: Load small chunk and estimate
                        print("PyArrow not available, using pandas estimation")
                        sample_df = pd.read_parquet(self.file_path)
                        # Take only first few rows to reduce memory usage
                        sample_size = min(1000, len(sample_df))
                        sample_df = sample_df.head(sample_size)
                        self.data_columns = sample_df.columns.tolist()
                        # Estimate total based on file size (rough approximation)
                        file_size = os.path.getsize(self.file_path)
                        estimated_rows = max(10000, file_size // 1000)  # Rough estimate
                        self.total_rows = estimated_rows
                        print(f"Estimated {estimated_rows} rows from {file_size} byte file")
                        del sample_df
                else:
                    # Local development: Load full file for accurate metadata
                    full_df = pd.read_parquet(self.file_path)
                    self.data_columns = full_df.columns.tolist()
                    self.total_rows = len(full_df)
                    print(f"Full parquet loaded: {self.total_rows} rows, {len(self.data_columns)} columns")
                    del full_df
                    
            else:
                # For CSV, we can count rows more efficiently
                with open(self.file_path, 'r') as f:
                    self.total_rows = sum(1 for line in f) - 1  # Subtract header
                # Load small sample to get columns
                sample_df = pd.read_csv(self.file_path, delimiter=';', nrows=1)
                self.data_columns = sample_df.columns.tolist()
                del sample_df
            
            print(f"Data metadata loaded: {len(self.data_columns)} columns, ~{self.total_rows} total rows")
            
        except Exception as e:
            print(f"Error loading metadata: {e}")
            raise
    
    def _load_next_chunk(self):
        """Load the next chunk of data."""
        try:
            if self.chunk_start_row >= self.total_rows:
                self.end_of_data = True
                print("Reached end of data. Will restart from beginning.")
                self.chunk_start_row = 0
            
            print(f"Loading chunk starting at row {self.chunk_start_row}")
            
            if self.is_parquet:
                # Check if we're on Heroku for memory-efficient loading
                is_heroku = 'PORT' in os.environ
                
                if is_heroku:
                    # Memory-efficient approach for Heroku
                    print("Using memory-efficient parquet chunking for Heroku")
                    try:
                        # Try PyArrow for efficient chunking
                        import pyarrow.parquet as pq
                        parquet_file = pq.ParquetFile(self.file_path)
                        
                        # Read only the chunk we need
                        table = parquet_file.read_row_group(
                            min(self.chunk_start_row // 1000, parquet_file.num_row_groups - 1)
                        )
                        chunk_df = table.to_pandas()
                        
                        # Slice to get exact chunk
                        start_idx = self.chunk_start_row % 1000
                        end_idx = min(start_idx + self.chunk_size, len(chunk_df))
                        self.current_chunk = chunk_df.iloc[start_idx:end_idx].copy()
                        
                        del chunk_df  # Free memory
                        
                    except (ImportError, Exception) as e:
                        print(f"PyArrow chunking failed ({e}), using fallback")
                        # Fallback: Load full file and slice (not ideal but works)
                        full_df = pd.read_parquet(self.file_path)
                        end_row = min(self.chunk_start_row + self.chunk_size, len(full_df))
                        self.current_chunk = full_df.iloc[self.chunk_start_row:end_row].copy()
                        del full_df
                else:
                    # Local development: Load full file and slice
                    full_df = pd.read_parquet(self.file_path)
                    end_row = min(self.chunk_start_row + self.chunk_size, len(full_df))
                    self.current_chunk = full_df.iloc[self.chunk_start_row:end_row].copy()
                    del full_df
            else:
                # For CSV, we can skip rows more efficiently
                self.current_chunk = pd.read_csv(
                    self.file_path, 
                    delimiter=';',
                    skiprows=range(1, self.chunk_start_row + 1),  # Skip header + previous rows
                    nrows=self.chunk_size
                )
            
            # Process timestamp column if it exists
            if 'timestamp' in self.current_chunk.columns:
                self.current_chunk['timestamp'] = pd.to_datetime(self.current_chunk['timestamp'])
            
            self.current_index = 0
            self.chunk_start_row += len(self.current_chunk)
            
            print(f"Loaded chunk with {len(self.current_chunk)} rows. Memory usage optimized.")
            
            # Force garbage collection to free memory
            gc.collect()
            
        except Exception as e:
            print(f"Error loading chunk: {e}")
            self.end_of_data = True
    
    def get_next_row(self):
        """Get the next row of data."""
        if self.current_chunk is None or self.current_index >= len(self.current_chunk):
            # Need to load next chunk
            self._load_next_chunk()
            
            if self.current_chunk is None or len(self.current_chunk) == 0:
                # If we still have no data, restart from beginning
                self.chunk_start_row = 0
                self._load_next_chunk()
                
                if self.current_chunk is None or len(self.current_chunk) == 0:
                    print("No data available")
                    return None
        
        # Get current row
        row = self.current_chunk.iloc[self.current_index]
        self.current_index += 1
        
        return row
    
    def get_columns(self):
        """Get the column names."""
        return self.data_columns

# --- Client functionality (same as before) ---
class SensorAPIClient:
    """Client class for accessing sensor data API."""
    
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        
    def pretty_print_json(self, data):
        """Helper function to print JSON data in a readable format."""
        print(json.dumps(data, indent=2))

    def check_api_status(self):
        """Check if the API is available and get status information."""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                print("API is available!")
                self.pretty_print_json(response.json())
                return True
            else:
                print(f"API status check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to API: {e}")
            return False

    def get_current_sensor_reading(self):
        """Get the current sensor reading."""
        try:
            response = requests.get(f"{self.base_url}/current", timeout=5)
            if response.status_code == 200:
                print("\nCurrent Sensor Reading:")
                self.pretty_print_json(response.json())
                return response.json()
            else:
                print(f"Failed to get current reading: {response.status_code}")
                print(response.text)
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def get_available_sensors(self):
        """Get list of available sensors."""
        try:
            response = requests.get(f"{self.base_url}/sensors", timeout=5)
            if response.status_code == 200:
                print("\nAvailable Sensors:")
                self.pretty_print_json(response.json())
                return response.json().get('available_sensors', [])
            else:
                print(f"Failed to get sensors: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return []

    def get_specific_sensor_value(self, sensor_name):
        """Get the current value of a specific sensor."""
        try:
            response = requests.get(f"{self.base_url}/sensor/{sensor_name}", timeout=5)
            if response.status_code == 200:
                print(f"\nSensor '{sensor_name}' Value:")
                self.pretty_print_json(response.json())
                return response.json()
            else:
                print(f"Failed to get sensor '{sensor_name}': {response.status_code}")
                print(response.text)
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def get_latest_readings(self, count=5):
        """Get the latest N sensor readings."""
        try:
            response = requests.get(f"{self.base_url}/latest/{count}", timeout=5)
            if response.status_code == 200:
                print(f"\nLatest {count} Readings:")
                self.pretty_print_json(response.json())
                return response.json()
            else:
                print(f"Failed to get latest readings: {response.status_code}")
                print(response.text)
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def monitor_sensor_continuously(self, sensor_name, interval=15):
        """Continuously monitor a specific sensor value."""
        print(f"\nStarting continuous monitoring of sensor '{sensor_name}' (every {interval} seconds)")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{current_time}] Checking sensor '{sensor_name}'...")
                
                sensor_data = self.get_specific_sensor_value(sensor_name)
                if sensor_data and sensor_data.get('status') == 'success':
                    value = sensor_data.get('value')
                    print(f"Current value: {value}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")

    def run_client_demo(self):
        """Run a comprehensive client demonstration."""
        print("Sensor Data API Client Demo")
        print("=" * 50)
        
        # Check if API is available
        if not self.check_api_status():
            print("\nCannot proceed - API is not available.")
            print("Make sure the server is running first!")
            return False
        
        # Get available sensors
        sensors = self.get_available_sensors()
        
        # Get current reading
        self.get_current_sensor_reading()
        
        # Get latest readings
        self.get_latest_readings(3)
        
        # If we have sensors available, demonstrate specific sensor access
        if sensors:
            first_sensor = sensors[0]
            self.get_specific_sensor_value(first_sensor)
        
        print("\nClient demo completed!")
        return True

# --- Server functionality with streaming ---
def initialize_data_streamer(file_path):
    """Initialize the data streamer."""
    global data_streamer, data_loaded, data_columns
    
    print(f"Initializing data streamer for: {file_path}")
    try:
        with data_streamer_lock:
            data_streamer = DataStreamer(file_path, chunk_size=CHUNK_SIZE)
            data_columns = data_streamer.get_columns()
            data_loaded = True
        
        print(f"Data streamer initialized successfully with {len(data_columns)} columns")
        print(f"Chunk size: {CHUNK_SIZE} rows")
        return True
        
    except FileNotFoundError:
        print(f"Error: The data file was not found at '{file_path}'.")
        print("Please make sure the file exists and the DATA_FILE_PATH is correct.")
        return False
    except Exception as e:
        print(f"An error occurred while initializing data streamer: {e}")
        return False

def update_current_reading(data_point):
    """Thread-safe function to update the current sensor reading."""
    with current_reading_lock:
        current_reading.clear()
        current_reading.update(data_point)
    
    with historical_readings_lock:
        data_point_with_processing_time = data_point.copy()
        data_point_with_processing_time['processing_timestamp'] = datetime.now().isoformat()
        historical_readings.append(data_point_with_processing_time)

def simulate_sensor_stream():
    """Background thread for sensor data simulation with streaming."""
    print("Starting streaming sensor data simulation...")
    
    if not initialize_data_streamer(DATA_FILE_PATH):
        print("Simulation stopped because data streamer could not be initialized.")
        return

    print("Data streamer ready. Starting continuous simulation...")
    
    while not thread_stop_event.is_set():
        with data_streamer_lock:
            if data_streamer is None:
                print("Data streamer not available.")
                break
                
            row = data_streamer.get_next_row()
        
        if row is None:
            print("No data available from streamer.")
            socketio.sleep(DATA_INTERVAL_SECONDS)
            continue
        
        # Convert row to dictionary
        data_point = row.to_dict()
        
        # Handle timestamp formatting
        if 'timestamp' in data_point and pd.notna(data_point['timestamp']):
            data_point['timestamp'] = data_point['timestamp'].isoformat()
        
        # Update current reading and emit data
        update_current_reading(data_point)
        print(f"Streaming data: {list(data_point.keys())[:3]}...") # Show first 3 keys to avoid clutter
        socketio.emit('new_data', {'data': data_point})
        socketio.sleep(DATA_INTERVAL_SECONDS)

    print("Streaming simulation stopped.")

# --- API Endpoints (same as before) ---
@app.route('/api/status')
def api_status():
    """Get API status and data information."""
    with current_reading_lock:
        has_current_data = bool(current_reading)
    
    with historical_readings_lock:
        historical_count = len(historical_readings)
    
    # Add streaming-specific information
    streaming_info = {}
    with data_streamer_lock:
        if data_streamer:
            streaming_info = {
                'chunk_size': CHUNK_SIZE,
                'current_chunk_row': data_streamer.chunk_start_row,
                'estimated_total_rows': data_streamer.total_rows,
                'streaming_enabled': True
            }
        else:
            streaming_info = {'streaming_enabled': False}
    
    return jsonify({
        'status': 'active',
        'data_loaded': data_loaded,
        'has_current_reading': has_current_data,
        'historical_readings_count': historical_count,
        'data_interval_seconds': DATA_INTERVAL_SECONDS,
        'available_columns': data_columns if data_loaded else [],
        'max_historical_readings': MAX_HISTORICAL_READINGS,
        'streaming_info': streaming_info,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/current')
def api_current():
    """Get the current sensor reading."""
    with current_reading_lock:
        if not current_reading:
            return jsonify({
                'error': 'No current reading available',
                'message': 'Wait for the simulation to start or check if data is loaded'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': current_reading.copy(),
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/all')
def api_all():
    """Get all historical sensor readings."""
    with historical_readings_lock:
        if not historical_readings:
            return jsonify({
                'error': 'No historical readings available',
                'message': 'Wait for the simulation to generate some data'
            }), 404
        
        return jsonify({
            'status': 'success',
            'count': len(historical_readings),
            'data': list(historical_readings),
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/latest/<int:count>')
def api_latest(count):
    """Get the latest N sensor readings."""
    if count <= 0:
        return jsonify({'error': 'Count must be a positive integer'}), 400
    
    with historical_readings_lock:
        if not historical_readings:
            return jsonify({
                'error': 'No historical readings available',
                'message': 'Wait for the simulation to generate some data'
            }), 404
        
        latest_readings = list(historical_readings)[-count:]
        
        return jsonify({
            'status': 'success',
            'requested_count': count,
            'returned_count': len(latest_readings),
            'data': latest_readings,
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/sensor/<sensor_name>')
def api_sensor_value(sensor_name):
    """Get the current value of a specific sensor."""
    with current_reading_lock:
        if not current_reading:
            return jsonify({
                'error': 'No current reading available',
                'message': 'Wait for the simulation to start or check if data is loaded'
            }), 404
        
        if sensor_name not in current_reading:
            available_sensors = list(current_reading.keys())
            return jsonify({
                'error': f'Sensor "{sensor_name}" not found',
                'available_sensors': available_sensors
            }), 404
        
        return jsonify({
            'status': 'success',
            'sensor_name': sensor_name,
            'value': current_reading[sensor_name],
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/sensors')
def api_available_sensors():
    """Get list of available sensors."""
    with current_reading_lock:
        if not current_reading:
            if data_loaded:
                return jsonify({
                    'status': 'success',
                    'available_sensors': data_columns,
                    'message': 'Data loaded but no current reading yet'
                })
            else:
                return jsonify({
                    'error': 'No data loaded yet',
                    'message': 'Wait for data to be loaded'
                }), 404
        
        return jsonify({
            'status': 'success',
            'available_sensors': list(current_reading.keys()),
            'timestamp': datetime.now().isoformat()
        })

# --- Web Routes (same as before) ---
@app.route('/')
def index():
    """Serves the main HTML page with live data and API documentation."""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cholesterol-Lowering Drug Manufacturing Live Sensor Data (Streaming)</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f0f2f5; color: #1c1e21; margin: 0; padding: 2rem; }
            .container { max-width: 1200px; margin: auto; background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
            h1, h2 { color: #0b57d0; border-bottom: 2px solid #e7e9ec; padding-bottom: 0.5rem; }
            .streaming-badge { background-color: #1e8e3e; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-left: 1rem; }
            #status { font-weight: bold; margin-bottom: 1rem; padding: 0.75rem; border-radius: 8px; }
            .connected { color: #1e8e3e; background-color: #e6f4ea; }
            .disconnected { color: #d93025; background-color: #fce8e6; }
            #data-container { margin-top: 1.5rem; background-color: #f8f9fa; padding: 1.5rem; border-radius: 8px; border: 1px solid #e0e0e0; min-height: 200px; overflow-wrap: break-word; font-family: "Courier New", Courier, monospace; }
            .api-section { margin-top: 2rem; background-color: #f8f9fa; padding: 1.5rem; border-radius: 8px; border: 1px solid #e0e0e0; }
            .endpoint { background-color: #fff; padding: 1rem; margin: 0.5rem 0; border-radius: 6px; border-left: 4px solid #0b57d0; }
            .endpoint code { background-color: #f1f3f4; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; }
            pre { white-space: pre-wrap; word-wrap: break-word; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.4/socket.io.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>Cholesterol-Lowering Drug Manufacturing Live Sensor Data<span class="streaming-badge">STREAMING</span></h1>
            <p><strong>Memory-optimized streaming version</strong> - Loads data in chunks to stay within memory limits</p>
            
            <div class="grid">
                <div>
                    <h2>Real-time Data Stream</h2>
                    <div id="status" class="disconnected">Status: Disconnected</div>
                    <div id="data-container">
                        <p>Waiting for streaming data...</p>
                    </div>
                </div>
                
                <div class="api-section">
                    <h2>API Endpoints</h2>
                    <p>Use these endpoints to access sensor data programmatically:</p>
                    
                    <div class="endpoint">
                        <strong>Get Current Reading:</strong><br>
                        <code>GET /api/current</code><br>
                        Returns the latest sensor reading
                    </div>
                    
                    <div class="endpoint">
                        <strong>Get Specific Sensor:</strong><br>
                        <code>GET /api/sensor/&lt;sensor_name&gt;</code><br>
                        Returns current value of a specific sensor
                    </div>
                    
                    <div class="endpoint">
                        <strong>Get Latest N Readings:</strong><br>
                        <code>GET /api/latest/&lt;count&gt;</code><br>
                        Returns the latest N sensor readings
                    </div>
                    
                    <div class="endpoint">
                        <strong>Get All Historical Data:</strong><br>
                        <code>GET /api/all</code><br>
                        Returns all stored historical readings
                    </div>
                    
                    <div class="endpoint">
                        <strong>Get Available Sensors:</strong><br>
                        <code>GET /api/sensors</code><br>
                        Returns list of available sensor names
                    </div>
                    
                    <div class="endpoint">
                        <strong>Get API Status:</strong><br>
                        <code>GET /api/status</code><br>
                        Returns API status and streaming information
                    </div>
                </div>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', (event) => {
                const socket = io();
                const statusDiv = document.getElementById('status');
                const dataContainer = document.getElementById('data-container');

                socket.on('connect', () => {
                    console.log('Successfully connected to the streaming server!');
                    statusDiv.textContent = 'Status: Connected (Streaming)';
                    statusDiv.className = 'connected';
                });

                socket.on('disconnect', () => {
                    console.log('Disconnected from the streaming server.');
                    statusDiv.textContent = 'Status: Disconnected';
                    statusDiv.className = 'disconnected';
                });

                socket.on('new_data', (msg) => {
                    console.log('Received streaming data:', msg.data);
                    const formattedData = JSON.stringify(msg.data, null, 4);
                    dataContainer.innerHTML = `<pre>${formattedData}</pre>`;
                });
            });
        </script>
    </body>
    </html>
    """)

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    """Called when a new client connects."""
    global thread
    print('Client connected to streaming server')
    
    if thread is None or not thread.is_alive():
        print("Starting background thread for streaming data simulation.")
        thread = Thread(target=simulate_sensor_stream)
        thread.daemon = True
        thread.start()

@socketio.on('disconnect')
def handle_disconnect():
    """Called when a client disconnects."""
    print('Client disconnected from streaming server')

# --- Combined Mode Functions (same as before) ---
def run_server(host=SERVER_HOST, port=SERVER_PORT):
    """Run the Flask-SocketIO server."""
    print("Starting Flask-SocketIO streaming server with API endpoints...")
    print(f"Navigate to http://{host}:{port} in your browser.")
    print("\nStreaming Configuration:")
    print(f"  Chunk size: {CHUNK_SIZE} rows")
    print(f"  Data interval: {DATA_INTERVAL_SECONDS} seconds")
    print("\nAPI Endpoints available:")
    print("  GET /api/current - Get current sensor reading")
    print("  GET /api/sensor/<sensor_name> - Get specific sensor value")
    print("  GET /api/latest/<count> - Get latest N readings")
    print("  GET /api/all - Get all historical readings")
    print("  GET /api/sensors - Get available sensors")
    print("  GET /api/status - Get API status and streaming info")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False)

def run_client(api_base_url=API_BASE_URL, sensor_name=None):
    """Run the client to access the API."""
    print("Running API client for streaming server...")
    client = SensorAPIClient(api_base_url)
    
    if sensor_name:
        # Wait a bit for server to start if running in combined mode
        print("Waiting 3 seconds for server to start...")
        time.sleep(3)
        client.monitor_sensor_continuously(sensor_name, interval=10)
    else:
        # Wait a bit for server to start if running in combined mode
        print("Waiting 3 seconds for server to start...")
        time.sleep(3)
        client.run_client_demo()

def run_both(host=SERVER_HOST, port=SERVER_PORT, api_base_url=API_BASE_URL):
    """Run both server and client in the same process."""
    print("Starting integrated streaming server and client...")
    
    # Start server in a separate thread
    server_thread = Thread(target=lambda: run_server(host=host, port=port))
    server_thread.daemon = True
    server_thread.start()
    
    # Wait a moment for server to start
    print("Waiting for streaming server to initialize...")
    time.sleep(5)
    
    # Run client demo
    try:
        client = SensorAPIClient(api_base_url)
        if client.check_api_status():
            print("\nBoth streaming server and client are running successfully!")
            print("Running client demo...")
            client.run_client_demo()
            
            # Keep both running
            print("\nStreaming server continues running. Press Ctrl+C to stop both.")
            while True:
                time.sleep(1)
        else:
            print("Failed to connect to streaming server")
    except KeyboardInterrupt:
        print("\nStopping streaming server and client...")
        thread_stop_event.set()

# --- Main Execution ---
def main():
    """Main function with command line argument parsing."""
    global CHUNK_SIZE  # Declare global at the top to avoid syntax error
    
    parser = argparse.ArgumentParser(description='Memory-Optimized Streaming Sensor Data Simulation with API')
    parser.add_argument('--mode', choices=['server', 'client', 'both', 'monitor'], 
                       default='both', help='Run mode (default: both)')
    parser.add_argument('--sensor', type=str, 
                       help='Sensor name to monitor (used with --mode monitor)')
    parser.add_argument('--host', type=str, default=SERVER_HOST,
                       help=f'Server host (default: {SERVER_HOST})')
    parser.add_argument('--port', type=int, default=None,
                       help=f'Server port (default: {SERVER_PORT} or PORT env var)')
    parser.add_argument('--chunk-size', type=int, default=CHUNK_SIZE,
                       help=f'Chunk size for streaming (default: {CHUNK_SIZE})')
    
    args = parser.parse_args()
    
    # Update configuration - prioritize environment variable for Heroku
    server_host = args.host
    if args.port is not None:
        server_port = args.port
    else:
        # Use PORT environment variable if available (for Heroku), otherwise default
        server_port = int(os.environ.get('PORT', SERVER_PORT))
    
    # Update chunk size if specified
    CHUNK_SIZE = args.chunk_size
    
    api_base_url = f"http://{server_host}:{server_port}/api"
    
    print("=" * 70)
    print("CHOLESTEROL-LOWERING DRUG MANUFACTURING SENSOR DATA STREAMING API")
    print("=" * 70)
    print(f"Memory-Optimized Version | Chunk Size: {CHUNK_SIZE} rows")
    
    if args.mode == 'server':
        print("Running in STREAMING SERVER mode only")
        run_server(host=server_host, port=server_port)
    elif args.mode == 'client':
        print("Running in CLIENT mode only")
        run_client(api_base_url=api_base_url)
    elif args.mode == 'monitor':
        if not args.sensor:
            print("Error: --sensor argument required for monitor mode")
            sys.exit(1)
        print(f"Running in MONITOR mode for sensor: {args.sensor}")
        run_client(api_base_url=api_base_url, sensor_name=args.sensor)
    else:  # both
        print("Running in COMBINED mode (streaming server + client)")
        run_both(host=server_host, port=server_port, api_base_url=api_base_url)

if __name__ == '__main__':
    main() 