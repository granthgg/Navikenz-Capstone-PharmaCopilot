import pandas as pd
import time
import argparse
import sys
import json
import os
import gc  # For garbage collection
import asyncio
from threading import Thread, Event, Lock
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from collections import deque
from datetime import datetime
import requests
from typing import List
import uvicorn

# --- Configuration ---
DATA_FILE_PATH = 'timeseries_small_data.csv'
# The time interval in seconds between sending data points.
DATA_INTERVAL_SECONDS = 10
# Maximum number of historical readings to keep in memory
MAX_HISTORICAL_READINGS = 1000
# Server configuration (will be updated by command line args)
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
API_BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/api"

# --- FastAPI Initialization ---
app = FastAPI(
    title="Cholesterol-Lowering Drug Manufacturing Sensor Data API",
    description="Real-time streaming from CSV sensor data files",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global variables for the simulation ---
simulation_thread = None
thread_stop_event = Event()
restart_event = Event()
current_reading = {}
current_reading_lock = Lock()
historical_readings = deque(maxlen=MAX_HISTORICAL_READINGS)
historical_readings_lock = Lock()
data_loaded = False
data_columns = []
all_data = None
current_data_index = 0
data_lock = Lock()

# --- WebSocket connection management ---
active_connections: List[WebSocket] = []

class CSVDataLoader:
    """Simple CSV data loader that loads all data at startup."""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.columns = []
        self.initialized = False
        self.current_index = 0
        
        # Initialize data
        self._load_data()
    
    def _load_data(self):
        """Load all CSV data at startup."""
        try:
            print(f"Loading CSV data from: {self.file_path}")
            
            if not os.path.exists(self.file_path):
                print(f"Error: Data file {self.file_path} not found.")
                self.initialized = False
                return
            
            # Load all CSV data with semicolon delimiter
            self.data = pd.read_csv(self.file_path, delimiter=';')
            self.columns = self.data.columns.tolist()
            
            # Process timestamp if exists
            if 'timestamp' in self.data.columns:
                self.data['timestamp'] = pd.to_datetime(self.data['timestamp'], errors='coerce')
            
            print(f"Successfully loaded {len(self.data)} rows with {len(self.columns)} columns")
            print(f"Columns: {self.columns}")
            
            self.initialized = True
            
        except Exception as e:
            print(f"Error loading CSV data: {e}")
            self.initialized = False
    
    def get_next_row(self):
        """Get the next data row, cycling through all data."""
        if not self.initialized or self.data is None:
            return None
        
        if self.current_index >= len(self.data):
            self.current_index = 0  # Reset to start
            print("Reached end of data, cycling back to beginning")
        
        row = self.data.iloc[self.current_index]
        self.current_index += 1
        
        return row
    
    def restart_stream(self):
        """Restart streaming from the beginning."""
        self.current_index = 0
        print("Stream restarted from beginning")
    
    def get_columns(self):
        """Get column names."""
        return self.columns
    
    def get_total_rows(self):
        """Get total number of rows."""
        return len(self.data) if self.data is not None else 0

# Global data loader instance
data_loader = None

# --- Data management functions ---
def initialize_data_loader():
    """Initialize the CSV data loader."""
    global data_loader, data_loaded, data_columns, all_data
    
    try:
        data_loader = CSVDataLoader(DATA_FILE_PATH)
        if data_loader.initialized:
            data_columns = data_loader.get_columns()
            all_data = data_loader.data
            data_loaded = True
            print("CSV data loader initialized successfully")
            print(f"Total rows available: {data_loader.get_total_rows()}")
            return True
        else:
            print("Failed to initialize CSV data loader")
            return False
    except Exception as e:
        print(f"Error initializing CSV data loader: {e}")
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

def simulate_sensor_data():
    """Background thread function for continuous sensor data simulation."""
    global current_data_index
    
    print("Starting sensor data simulation...")
    
    # Initialize data loader
    if not initialize_data_loader():
        print("Failed to initialize data loader. Stopping simulation.")
        return
    
    print(f"Simulation started. Updating every {DATA_INTERVAL_SECONDS} seconds.")
    
    while not thread_stop_event.is_set():
        try:
            # Check if restart was requested
            if restart_event.is_set():
                print("Restart requested - resetting to beginning of data")
                data_loader.restart_stream()
                with historical_readings_lock:
                    historical_readings.clear()
                restart_event.clear()
                
                # Broadcast restart notification
                if active_connections:
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    message = {"type": "stream_restarted", "message": "Data stream restarted from beginning"}
                    loop.run_until_complete(broadcast_to_websockets(message))
            
            # Get next data point
            row = data_loader.get_next_row()
            
            if row is not None:
                # Convert to dictionary
                data_point = row.to_dict()
                
                # Handle timestamp formatting
                if 'timestamp' in data_point and pd.notna(data_point['timestamp']):
                    if hasattr(data_point['timestamp'], 'isoformat'):
                        data_point['timestamp'] = data_point['timestamp'].isoformat()
                    else:
                        data_point['timestamp'] = str(data_point['timestamp'])
                
                # Convert any NaN values to None and optimize data types
                optimized_point = {}
                for key, value in data_point.items():
                    if pd.isna(value):
                        optimized_point[key] = None
                    elif isinstance(value, (int, float)):
                        if abs(value) > 1e10:
                            optimized_point[key] = None  # Handle extreme values
                        else:
                            # Round floats to reduce memory usage
                            if isinstance(value, float):
                                optimized_point[key] = round(float(value), 4)
                            else:
                                optimized_point[key] = int(value)
                    else:
                        optimized_point[key] = str(value) if value is not None else None
                
                data_point = optimized_point
                
                # Update current reading
                update_current_reading(data_point)
                
                # Store current index for tracking
                with data_lock:
                    current_data_index = data_loader.current_index
                
                # Broadcast to WebSocket clients
                if active_connections:
                    try:
                        # Create event loop if needed
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        # Broadcast the data
                        message = {
                            "type": "sensor_data", 
                            "data": data_point,
                            "index": data_loader.current_index - 1,
                            "total": data_loader.get_total_rows()
                        }
                        loop.run_until_complete(broadcast_to_websockets(message))
                    except Exception as e:
                        print(f"Error broadcasting to WebSocket clients: {e}")
                
                print(f"Updated sensor data: {data_point.get('timestamp', 'N/A')} - Row {data_loader.current_index - 1}/{data_loader.get_total_rows()}")
            else:
                print("No data available from loader")
            
            # Wait for the specified interval
            time.sleep(DATA_INTERVAL_SECONDS)
            
        except Exception as e:
            print(f"Error in sensor simulation: {e}")
            time.sleep(DATA_INTERVAL_SECONDS)
    
    print("Sensor data simulation stopped.")

async def broadcast_to_websockets(message):
    """Broadcast message to all WebSocket connections."""
    if active_connections:
        disconnected = []
        for websocket in active_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            if websocket in active_connections:
                active_connections.remove(websocket)

# --- API Endpoints ---
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {
        "status": "healthy",
        "service": "cholesterol-sensor-api",
        "version": "2.1.0-csv-streaming",
        "data_source": "csv_file",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def api_status():
    """Get API status and data information."""
    with current_reading_lock:
        has_current_data = bool(current_reading)
    
    with historical_readings_lock:
        historical_count = len(historical_readings)
    
    with data_lock:
        current_index = current_data_index
    
    # Get data loader info
    loader_info = {}
    if data_loader:
        loader_info = {
            'total_rows': data_loader.get_total_rows(),
            'current_index': current_index,
            'progress_percentage': round((current_index / data_loader.get_total_rows()) * 100, 2) if data_loader.get_total_rows() > 0 else 0
        }
    
    return {
        'status': 'active',
        'data_loaded': data_loaded,
        'has_current_reading': has_current_data,
        'historical_readings_count': historical_count,
        'data_interval_seconds': DATA_INTERVAL_SECONDS,
        'available_columns': data_columns if data_loaded else [],
        'max_historical_readings': MAX_HISTORICAL_READINGS,
        'simulation_running': simulation_thread is not None and simulation_thread.is_alive(),
        'websocket_connections': len(active_connections),
        'loader_info': loader_info,
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/current")
async def api_current():
    """Get the current sensor reading."""
    with current_reading_lock:
        if not current_reading:
            if not data_loaded:
                return {"error": "No current reading available", "message": "CSV data file not loaded. Check if file exists and is accessible."}
            else:
                return {"error": "No current reading available", "message": "Wait for the simulation to start processing data"}
        
        with data_lock:
            index_info = {
                "current_index": current_data_index,
                "total_rows": data_loader.get_total_rows() if data_loader else 0
            }
        
        return {
            "status": "success", 
            "data": current_reading.copy(), 
            "index_info": index_info,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/all")
async def api_all():
    """Get all historical sensor readings (last 1000)."""
    with historical_readings_lock:
        if not historical_readings:
            if not data_loaded:
                return {"error": "No historical readings available", "message": "CSV data file not loaded. Check if file exists and is accessible."}
            else:
                return {"error": "No historical readings available", "message": "Wait for the simulation to generate data"}
        
        return {
            "status": "success", 
            "count": len(historical_readings), 
            "data": list(historical_readings), 
            "max_capacity": MAX_HISTORICAL_READINGS,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/latest/{count}")
async def api_latest(count: int):
    """Get the latest N sensor readings."""
    if count <= 0:
        return {"error": "Count must be a positive integer"}
    
    # Limit count for memory efficiency
    count = min(count, MAX_HISTORICAL_READINGS)
    
    with historical_readings_lock:
        if not historical_readings:
            if not data_loaded:
                return {"error": "No historical readings available", "message": "CSV data file not loaded. Check if file exists and is accessible."}
            else:
                return {"error": "No historical readings available", "message": "Wait for the simulation to generate data"}
        
        latest_readings = list(historical_readings)[-count:]
        
        return {
            "status": "success", 
            "requested_count": count, 
            "returned_count": len(latest_readings), 
            "data": latest_readings, 
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/sensor/{sensor_name}")
async def api_sensor_value(sensor_name: str):
    """Get the current value of a specific sensor."""
    with current_reading_lock:
        if not current_reading:
            if not data_loaded:
                return {"error": "No current reading available", "message": "CSV data file not loaded. Check if file exists and is accessible."}
            else:
                return {"error": "No current reading available", "message": "Wait for the simulation to start processing data"}
        
        if sensor_name not in current_reading:
            available_sensors = list(current_reading.keys())
            return {"error": f'Sensor "{sensor_name}" not found', "available_sensors": available_sensors}
        
        return {
            "status": "success", 
            "sensor_name": sensor_name, 
            "value": current_reading[sensor_name], 
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/sensors")
async def api_available_sensors():
    """Get list of available sensors."""
    with current_reading_lock:
        if not current_reading:
            if data_loaded:
                return {"status": "success", "available_sensors": data_columns, "message": "Data loaded but no current reading yet"}
            else:
                return {"error": "No data loaded", "message": "CSV data file not loaded. Check if file exists and is accessible."}
        
        return {
            "status": "success", 
            "available_sensors": list(current_reading.keys()), 
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/restart")
async def api_restart():
    """Restart the data stream from the beginning."""
    global restart_event
    
    if not data_loaded:
        return {"error": "No data loaded", "message": "CSV data file not loaded. Cannot restart stream."}
    
    restart_event.set()
    
    return {
        "status": "success",
        "message": "Stream restart requested. Data will restart from beginning.",
        "timestamp": datetime.now().isoformat()
    }

# --- WebSocket Endpoints ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time sensor data streaming."""
    await websocket.accept()
    active_connections.append(websocket)
    print(f"WebSocket connected. Total connections: {len(active_connections)}")
    
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            
            # Handle restart command
            if data == "restart":
                restart_event.set()
                await websocket.send_json({
                    "type": "restart_acknowledged", 
                    "message": "Stream restart requested", 
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Send keep-alive response
                await websocket.send_json({
                    "type": "keepalive", 
                    "message": "Connection active", 
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# --- Web Interface ---
@app.get("/")
async def root():
    """Serves the main HTML page."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cholesterol-Lowering Drug Manufacturing Live Sensor Data</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; margin: 0; padding: 2rem; }
            .container { max-width: 1200px; margin: auto; background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
            h1, h2 { color: #0b57d0; border-bottom: 2px solid #e7e9ec; padding-bottom: 0.5rem; }
            .badge { color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-left: 0.5rem; }
            .streaming-badge { background-color: #1e8e3e; }
            .csv-badge { background-color: #ff6b35; }
            #status { font-weight: bold; margin-bottom: 1rem; padding: 0.75rem; border-radius: 8px; }
            .connected { color: #1e8e3e; background-color: #e6f4ea; }
            .disconnected { color: #d93025; background-color: #fce8e6; }
            #data-container { margin-top: 1.5rem; background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border: 1px solid #e0e0e0; min-height: 200px; font-family: monospace; overflow-y: auto; max-height: 400px; }
            .controls { margin: 1rem 0; }
            .restart-btn { background: #d93025; color: white; padding: 0.5rem 1rem; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; }
            .restart-btn:hover { background: #b71c1c; }
            .restart-btn:disabled { background: #ccc; cursor: not-allowed; }
            .progress-info { background: #e3f2fd; padding: 0.5rem; border-radius: 4px; margin: 0.5rem 0; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem; }
            .endpoint { background: #fff; padding: 1rem; margin: 0.5rem 0; border-radius: 6px; border-left: 4px solid #0b57d0; }
            .endpoint code { background: #f1f3f4; padding: 0.2rem 0.4rem; border-radius: 4px; }
            .api-docs-link { background: #0b57d0; color: white; padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; display: inline-block; margin: 0.5rem 0.5rem 0 0; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Cholesterol Drug Manufacturing Live Sensor Data<span class="streaming-badge badge">LIVE STREAMING</span><span class="csv-badge badge">CSV DATA</span></h1>
            <p><strong>Real-time FastAPI streaming from CSV sensor data</strong> - Complete data loaded and streaming</p>
            <p>
                <a href="/docs" class="api-docs-link" target="_blank">API Documentation</a>
                <a href="/redoc" class="api-docs-link" target="_blank">ReDoc Documentation</a>
                <a href="/api/status" class="api-docs-link" target="_blank">API Status</a>
            </p>
            
            <div class="grid">
                <div>
                    <h2>Real-time Data Stream</h2>
                    <div id="status" class="disconnected">Status: Connecting...</div>
                    <div class="controls">
                        <button id="restartBtn" class="restart-btn" onclick="restartStream()">Restart Stream</button>
                    </div>
                    <div id="progress" class="progress-info">Progress: Connecting...</div>
                    <div id="data-container">Connecting to real-time sensor data from CSV file...</div>
                </div>
                
                <div>
                    <h2>API Endpoints</h2>
                    <div class="endpoint"><strong>Health Check:</strong><br><code>GET /health</code></div>
                    <div class="endpoint"><strong>Current Reading:</strong><br><code>GET /api/current</code></div>
                    <div class="endpoint"><strong>Latest 1000 Readings:</strong><br><code>GET /api/all</code></div>
                    <div class="endpoint"><strong>Latest N Readings:</strong><br><code>GET /api/latest/10</code></div>
                    <div class="endpoint"><strong>All Sensors:</strong><br><code>GET /api/sensors</code></div>
                    <div class="endpoint"><strong>Restart Stream:</strong><br><code>POST /api/restart</code></div>
                    <div class="endpoint"><strong>WebSocket:</strong><br><code>WS /ws</code></div>
                </div>
            </div>
        </div>

        <script>
            let socket = null;
            let reconnectAttempts = 0;
            const maxReconnects = 5;

            function connect() {
                const statusDiv = document.getElementById('status');
                const dataContainer = document.getElementById('data-container');
                const progressDiv = document.getElementById('progress');
                
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                socket = new WebSocket(wsUrl);

                socket.onopen = function() {
                    console.log('Connected to WebSocket');
                    statusDiv.textContent = 'Status: Connected (Real-time Streaming)';
                    statusDiv.className = 'connected';
                    document.getElementById('restartBtn').disabled = false;
                    reconnectAttempts = 0;
                };

                socket.onclose = function() {
                    console.log('WebSocket disconnected');
                    statusDiv.textContent = 'Status: Disconnected';
                    statusDiv.className = 'disconnected';
                    document.getElementById('restartBtn').disabled = true;
                    
                    if (reconnectAttempts < maxReconnects) {
                        reconnectAttempts++;
                        setTimeout(connect, 3000);
                    }
                };

                socket.onmessage = function(event) {
                    try {
                        const message = JSON.parse(event.data);
                        
                        if (message.type === 'sensor_data' && message.data) {
                            const formattedData = JSON.stringify(message.data, null, 2);
                            dataContainer.innerHTML = `<pre>${formattedData}</pre>`;
                            
                            // Update progress if available
                            if (message.index !== undefined && message.total !== undefined) {
                                const progress = ((message.index / message.total) * 100).toFixed(1);
                                progressDiv.textContent = `Progress: Row ${message.index + 1}/${message.total} (${progress}%)`;
                            }
                        } else if (message.type === 'stream_restarted') {
                            progressDiv.textContent = 'Progress: Stream restarted - starting from beginning';
                            dataContainer.innerHTML = '<pre>Stream restarted - waiting for new data...</pre>';
                        } else if (message.type === 'restart_acknowledged') {
                            console.log('Restart acknowledged by server');
                        }
                    } catch (error) {
                        console.error('Error parsing message:', error);
                    }
                };

                socket.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }

            function restartStream() {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send('restart');
                    document.getElementById('restartBtn').disabled = true;
                    setTimeout(() => {
                        document.getElementById('restartBtn').disabled = false;
                    }, 2000);
                } else {
                    // Try API restart if WebSocket is not available
                    fetch('/api/restart', { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            console.log('Restart response:', data);
                            document.getElementById('progress').textContent = 'Progress: Restart requested via API';
                        })
                        .catch(error => {
                            console.error('Error restarting stream:', error);
                        });
                }
            }

            document.addEventListener('DOMContentLoaded', connect);
            
            // Keep-alive ping
            setInterval(() => {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send('ping');
                }
            }, 30000);
        </script>
    </body>
    </html>
    """)

# --- FastAPI Event Handlers ---
@app.on_event("startup")
async def startup_event():
    """Start background streaming when FastAPI starts."""
    global simulation_thread
    print("FastAPI startup: Starting CSV sensor data simulation...")
    
    # Start simulation thread
    if simulation_thread is None or not simulation_thread.is_alive():
        simulation_thread = Thread(target=simulate_sensor_data, daemon=True)
        simulation_thread.start()
        print("Background simulation thread started!")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown."""
    print("Shutting down sensor simulation...")
    thread_stop_event.set()
    if simulation_thread and simulation_thread.is_alive():
        simulation_thread.join(timeout=3)

# --- Client functionality ---
class SensorAPIClient:
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        
    def check_api_status(self):
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                print("FastAPI is available!")
                print(json.dumps(response.json(), indent=2))
                return True
            return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect: {e}")
            return False

    def get_current_reading(self):
        try:
            response = requests.get(f"{self.base_url}/current", timeout=5)
            if response.status_code == 200:
                print("\nCurrent Reading:")
                print(json.dumps(response.json(), indent=2))
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def restart_stream(self):
        try:
            response = requests.post(f"{self.base_url}/restart", timeout=5)
            if response.status_code == 200:
                print("\nStream Restart:")
                print(json.dumps(response.json(), indent=2))
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def run_demo(self):
        print("FastAPI Sensor Data API Demo")
        print("=" * 40)
        
        if not self.check_api_status():
            print("API not available!")
            return False
        
        self.get_current_reading()
        
        # Demo restart functionality
        print("\n--- Testing Restart Functionality ---")
        self.restart_stream()
        
        return True

# --- Server functions ---
def run_server(host=SERVER_HOST, port=SERVER_PORT):
    print("Starting CSV streaming FastAPI server...")
    print(f"Navigate to http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    uvicorn.run(app, host='0.0.0.0', port=port, log_level="info")

def run_client(api_base_url=API_BASE_URL):
    time.sleep(3)  # Wait for server
    client = SensorAPIClient(api_base_url)
    client.run_demo()

def run_both(host=SERVER_HOST, port=SERVER_PORT, api_base_url=API_BASE_URL):
    print("Starting integrated FastAPI server and client...")
    
    server_thread = Thread(target=lambda: run_server(host=host, port=port), daemon=True)
    server_thread.start()
    
    time.sleep(5)
    
    try:
        client = SensorAPIClient(api_base_url)
        if client.check_api_status():
            print("\nServer and client running successfully!")
            client.run_demo()
            
            print("\nServer continues running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        thread_stop_event.set()

# --- Main execution ---
def main():
    global DATA_INTERVAL_SECONDS
    
    parser = argparse.ArgumentParser(description='CSV Sensor Data Streaming API')
    parser.add_argument('--mode', choices=['server', 'client', 'both'], default='both')
    parser.add_argument('--host', type=str, default=SERVER_HOST)
    parser.add_argument('--port', type=int, default=None)
    parser.add_argument('--interval', type=int, default=DATA_INTERVAL_SECONDS)
    
    args = parser.parse_args()
    
    server_host = args.host
    server_port = args.port if args.port else int(os.environ.get('PORT', SERVER_PORT))
    DATA_INTERVAL_SECONDS = args.interval
    
    api_base_url = f"http://{server_host}:{server_port}/api"
    
    print("=" * 60)
    print("CHOLESTEROL DRUG MANUFACTURING SENSOR DATA API")
    print("=" * 60)
    print(f"CSV Streaming FastAPI | Interval: {DATA_INTERVAL_SECONDS}s")
    
    if args.mode == 'server':
        run_server(host=server_host, port=server_port)
    elif args.mode == 'client':
        run_client(api_base_url=api_base_url)
    else:
        run_both(host=server_host, port=server_port, api_base_url=api_base_url)

if __name__ == '__main__':
    main() 