# app.py
#
# A complete Python application to simulate live sensor data stream with API endpoints.
# This script can run as a server, client, or both in one integrated application.
#
# --- Project Structure ---
# To run this, you should have a structure like this:
# /your_project_folder
# |--- app.py (this file)
# |--- your_sensor_data.parquet (or .csv, the dataset file)
#
# --- How to Run ---
# 1. Install necessary libraries:
#    pip install -r requirements.txt
#
# 2. Place your data file (e.g., '1.csv' or your larger .parquet file)
#    in the same directory as this script.
#
# 3. Update the `DATA_FILE_PATH` variable below to match your file name.
#
# 4. Run the script with different modes:
#    - Server only: python app.py --mode server
#    - Client only: python app.py --mode client
#    - Both (default): python app.py or python app.py --mode both
#    - Monitor specific sensor: python app.py --mode monitor --sensor temperature
#
# 5. Access the application:
#    - Web interface: http://127.0.0.1:5000
#    - API endpoints available when server is running

import eventlet
# We patch the standard library to be non-blocking for eventlet to work correctly.
eventlet.monkey_patch()

import pandas as pd
import time
import argparse
import sys
import json
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
sensor_data = None
data_columns = []

# --- Client functionality ---
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

# --- Server functionality (existing code) ---
def load_sensor_data(file_path):
    """Loads sensor data from a file."""
    global data_loaded, sensor_data, data_columns
    
    print(f"Attempting to load data from: {file_path}")
    try:
        if file_path.endswith('.parquet'):
            df = pd.read_parquet(file_path)
            print("Successfully loaded Parquet file.")
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, delimiter=';')
            print("Successfully loaded CSV file.")
        else:
            print(f"Error: Unsupported file format for {file_path}. Please use .parquet or .csv.")
            return None
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        print(f"Data loaded successfully. Shape: {df.shape}")
        sensor_data = df
        data_columns = df.columns.tolist()
        data_loaded = True
        return df
    except FileNotFoundError:
        print(f"Error: The data file was not found at '{file_path}'.")
        print("Please make sure the file exists and the DATA_FILE_PATH is correct.")
        return None
    except Exception as e:
        print(f"An error occurred while loading the data: {e}")
        return None

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
    """Background thread for sensor data simulation."""
    print("Starting sensor data simulation...")
    sensor_df = load_sensor_data(DATA_FILE_PATH)

    if sensor_df is None:
        print("Simulation stopped because data could not be loaded.")
        return

    while not thread_stop_event.is_set():
        for index, row in sensor_df.iterrows():
            if thread_stop_event.is_set():
                break
            
            data_point = row.to_dict()
            if 'timestamp' in data_point and pd.notna(data_point['timestamp']):
                 data_point['timestamp'] = data_point['timestamp'].isoformat()

            update_current_reading(data_point)
            print(f"Sending data: {data_point}")
            socketio.emit('new_data', {'data': data_point})
            socketio.sleep(DATA_INTERVAL_SECONDS)

    print("Simulation stopped.")

# --- API Endpoints ---
@app.route('/api/status')
def api_status():
    """Get API status and data information."""
    with current_reading_lock:
        has_current_data = bool(current_reading)
    
    with historical_readings_lock:
        historical_count = len(historical_readings)
    
    return jsonify({
        'status': 'active',
        'data_loaded': data_loaded,
        'has_current_reading': has_current_data,
        'historical_readings_count': historical_count,
        'data_interval_seconds': DATA_INTERVAL_SECONDS,
        'available_columns': data_columns if data_loaded else [],
        'max_historical_readings': MAX_HISTORICAL_READINGS,
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

# --- Web Routes ---
@app.route('/')
def index():
    """Serves the main HTML page with live data and API documentation."""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cholessterol-Lowering Drug Manufacturing Live Sensor Data</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f0f2f5; color: #1c1e21; margin: 0; padding: 2rem; }
            .container { max-width: 1200px; margin: auto; background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
            h1, h2 { color: #0b57d0; border-bottom: 2px solid #e7e9ec; padding-bottom: 0.5rem; }
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
            <h1>Cholessterol-Lowering Drug Manufacturing Live Sensor Data</h1>
            
            <div class="grid">
                <div>
                    <h2>Real-time Data Stream</h2>
                    <div id="status" class="disconnected">Status: Disconnected</div>
                    <div id="data-container">
                        <p>Waiting for data...</p>
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
                        Returns API status and information
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
                    console.log('Successfully connected to the server!');
                    statusDiv.textContent = 'Status: Connected';
                    statusDiv.className = 'connected';
                });

                socket.on('disconnect', () => {
                    console.log('Disconnected from the server.');
                    statusDiv.textContent = 'Status: Disconnected';
                    statusDiv.className = 'disconnected';
                });

                socket.on('new_data', (msg) => {
                    console.log('Received new data:', msg.data);
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
    print('Client connected')
    
    if thread is None or not thread.is_alive():
        print("Starting background thread for data simulation.")
        thread = Thread(target=simulate_sensor_stream)
        thread.daemon = True
        thread.start()

@socketio.on('disconnect')
def handle_disconnect():
    """Called when a client disconnects."""
    print('Client disconnected')

# --- Combined Mode Functions ---
def run_server(host=SERVER_HOST, port=SERVER_PORT):
    """Run the Flask-SocketIO server."""
    print("Starting Flask-SocketIO server with API endpoints...")
    print(f"Navigate to http://{host}:{port} in your browser.")
    print("\nAPI Endpoints available:")
    print("  GET /api/current - Get current sensor reading")
    print("  GET /api/sensor/<sensor_name> - Get specific sensor value")
    print("  GET /api/latest/<count> - Get latest N readings")
    print("  GET /api/all - Get all historical readings")
    print("  GET /api/sensors - Get available sensors")
    print("  GET /api/status - Get API status")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False)

def run_client(api_base_url=API_BASE_URL, sensor_name=None):
    """Run the client to access the API."""
    print("Running API client...")
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
    print("Starting integrated server and client...")
    
    # Start server in a separate thread
    server_thread = Thread(target=lambda: run_server(host=host, port=port))
    server_thread.daemon = True
    server_thread.start()
    
    # Wait a moment for server to start
    print("Waiting for server to initialize...")
    time.sleep(5)
    
    # Run client demo
    try:
        client = SensorAPIClient(api_base_url)
        if client.check_api_status():
            print("\nBoth server and client are running successfully!")
            print("Running client demo...")
            client.run_client_demo()
            
            # Keep both running
            print("\nServer continues running. Press Ctrl+C to stop both.")
            while True:
                time.sleep(1)
        else:
            print("Failed to connect to server")
    except KeyboardInterrupt:
        print("\nStopping server and client...")
        thread_stop_event.set()

# --- Main Execution ---
def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Sensor Data Simulation with API')
    parser.add_argument('--mode', choices=['server', 'client', 'both', 'monitor'], 
                       default='both', help='Run mode (default: both)')
    parser.add_argument('--sensor', type=str, 
                       help='Sensor name to monitor (used with --mode monitor)')
    parser.add_argument('--host', type=str, default=SERVER_HOST,
                       help=f'Server host (default: {SERVER_HOST})')
    parser.add_argument('--port', type=int, default=SERVER_PORT,
                       help=f'Server port (default: {SERVER_PORT})')
    
    args = parser.parse_args()
    
    # Update configuration
    server_host = args.host
    server_port = args.port
    api_base_url = f"http://{server_host}:{server_port}/api"
    
    print("=" * 60)
    print("CHOLESSTEROL-LOWERING DRUG MANUFACTURING SENSOR DATA SIMULATION & API")
    print("=" * 60)
    
    if args.mode == 'server':
        print("Running in SERVER mode only")
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
        print("Running in COMBINED mode (server + client)")
        run_both(host=server_host, port=server_port, api_base_url=api_base_url)

if __name__ == '__main__':
    main()
