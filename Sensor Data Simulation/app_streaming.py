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
DATA_FILE_PATH = 'processed_timeseries.parquet'
# The time interval in seconds between sending data points.
DATA_INTERVAL_SECONDS = 10
# Maximum number of historical readings to keep in memory (ultra-minimal for Heroku)
MAX_HISTORICAL_READINGS = 1000 if 'PORT' in os.environ else 2000  # Extremely small for Heroku
# Server configuration (will be updated by command line args)
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
API_BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/api"

# --- FastAPI Initialization ---
app = FastAPI(
    title="Cholesterol-Lowering Drug Manufacturing Sensor Data API",
    description="Memory-efficient real-time streaming from parquet sensor data files",
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
current_reading = {}
current_reading_lock = Lock()
historical_readings = deque(maxlen=MAX_HISTORICAL_READINGS)
historical_readings_lock = Lock()
data_loaded = False
data_columns = []

# --- WebSocket connection management ---
active_connections: List[WebSocket] = []

class MemoryEfficientDataStreamer:
    """Ultra memory-efficient data streamer that loads data in small batches."""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.current_row_index = 0
        self.current_batch_index = 0
        self.current_batch = None
        self.data_columns = []
        self.is_parquet = file_path.endswith('.parquet')
        self.initialized = False
        
        # Batch configuration - medium size for efficient processing
        self.is_heroku = 'PORT' in os.environ
        self.batch_size = 500 if self.is_heroku else 2000  # 500 rows per batch for Heroku
        self.total_file_rows = 0
        self.current_file_batch = 0
        
        # Initialize with minimal memory footprint
        self._initialize()
    
    def _initialize(self):
        """Initialize with minimal memory usage - only get schema, no data."""
        try:
            print(f"Initializing efficient batch streamer for: {self.file_path}")
            
            if not os.path.exists(self.file_path):
                print(f"Error: Data file {self.file_path} not found. Cannot proceed without real data.")
                self.initialized = False
                return
            
            if self.is_parquet:
                try:
                    # Only read schema and first tiny batch to get column info
                    if self.is_heroku:
                        # For Heroku: Load full batch size efficiently
                        try:
                            # Try to read just schema first using pyarrow
                            import pyarrow.parquet as pq
                            parquet_file = pq.ParquetFile(self.file_path)
                            self.data_columns = parquet_file.schema.names
                            self.total_file_rows = parquet_file.metadata.num_rows
                            
                            # Load first batch efficiently
                            self._load_next_batch()
                            
                            print(f"Heroku mode: PyArrow batch loading - {len(self.current_batch)} rows, {len(self.data_columns)} columns")
                            print(f"Total file rows: {self.total_file_rows}")
                            
                        except ImportError:
                            # Fallback if pyarrow fails
                            first_batch = pd.read_parquet(self.file_path, engine='fastparquet')
                            self.data_columns = first_batch.columns.tolist()
                            self.total_file_rows = len(first_batch)
                            
                            # Take first batch_size rows
                            batch_size = min(self.batch_size, len(first_batch))
                            self.current_batch = first_batch.head(batch_size).copy()
                            
                            print(f"Heroku fallback mode: {batch_size} rows, {len(self.data_columns)} columns")
                            
                            del first_batch
                            gc.collect()
                        
                    else:
                        # Local development: Still be very careful
                        try:
                            # Try to get just the schema first
                            import pyarrow.parquet as pq
                            parquet_file = pq.ParquetFile(self.file_path)
                            self.data_columns = parquet_file.schema.names
                            self.total_file_rows = parquet_file.metadata.num_rows
                            
                            # Load first small batch
                            self._load_next_batch()
                            
                            print(f"Local mode: Schema-first loading - Total: {self.total_file_rows} rows, {len(self.data_columns)} columns")
                            
                        except ImportError:
                            # Fallback if pyarrow not available
                            first_batch = pd.read_parquet(self.file_path, engine='fastparquet')
                            self.data_columns = first_batch.columns.tolist()
                            self.total_file_rows = len(first_batch)
                            
                            # Keep only first batch
                            self.current_batch = first_batch.head(self.batch_size).copy()
                            del first_batch
                            gc.collect()
                        
                except Exception as e:
                    print(f"Error with parquet loading: {e}")
                    print("Cannot proceed without valid parquet data.")
                    self.initialized = False
                    return
            else:
                # CSV handling - ultra minimal
                try:
                    # Read just a few rows to get schema
                    schema_sample = pd.read_csv(self.file_path, delimiter=';', nrows=5)
                    self.data_columns = schema_sample.columns.tolist()
                    
                    # Load first batch with proper size
                    self.current_batch = pd.read_csv(self.file_path, delimiter=';', nrows=self.batch_size)
                    # Estimate total rows (this is rough, but sufficient for cycling)
                    self.total_file_rows = self.batch_size * 100  # Conservative estimate
                    
                    del schema_sample
                    gc.collect()
                    
                except Exception as e:
                    print(f"Error loading CSV: {e}")
                    print("Cannot proceed without valid CSV data.")
                    self.initialized = False
                    return
            
            # Process timestamp if exists
            if self.current_batch is not None and 'timestamp' in self.current_batch.columns:
                self.current_batch['timestamp'] = pd.to_datetime(self.current_batch['timestamp'], errors='coerce')
            
            self.initialized = True
            batch_rows = len(self.current_batch) if self.current_batch is not None else 0
            print(f"Efficient batch streamer initialized: {batch_rows} rows in current batch")
            print(f"Batch size: {self.batch_size} rows")
            print(f"Environment: {'Heroku (batch processing)' if self.is_heroku else 'local development'}")
            
        except Exception as e:
            print(f"Error initializing data streamer: {e}")
            print("Failed to initialize with real data. Application cannot proceed.")
            self.initialized = False
    
    def _load_next_batch(self):
        """Load the next batch of data from file."""
        try:
            if self.is_parquet:
                # Calculate skip rows for this batch
                skip_rows = self.current_file_batch * self.batch_size
                
                if skip_rows >= self.total_file_rows:
                    # Reset to beginning of file and continue loading new batches
                    self.current_file_batch = 0
                    skip_rows = 0
                    print(f"Reached end of file, cycling back to beginning. Loading next batch from row {skip_rows}")
                
                # Load next batch
                try:
                    import pyarrow.parquet as pq
                    parquet_file = pq.ParquetFile(self.file_path)
                    
                    # Read specific row range
                    row_groups = []
                    rows_read = 0
                    target_rows = self.batch_size
                    
                    for i in range(parquet_file.num_row_groups):
                        rg = parquet_file.read_row_group(i)
                        if rows_read + len(rg) > skip_rows and rows_read < skip_rows + target_rows:
                            row_groups.append(rg)
                            rows_read += len(rg)
                            if rows_read >= skip_rows + target_rows:
                                break
                    
                    if row_groups:
                        batch_df = pd.concat([rg.to_pandas() for rg in row_groups], ignore_index=True)
                        
                        # Slice to exact range needed
                        start_idx = max(0, skip_rows - (rows_read - len(batch_df)))
                        end_idx = start_idx + self.batch_size
                        self.current_batch = batch_df.iloc[start_idx:end_idx].copy()
                        
                        del batch_df
                        gc.collect()
                        
                except ImportError:
                    # Fallback without pyarrow
                    # For very large files, this is not ideal, but works for smaller files
                    full_df = pd.read_parquet(self.file_path)
                    end_row = min(skip_rows + self.batch_size, len(full_df))
                    self.current_batch = full_df.iloc[skip_rows:end_row].copy()
                    del full_df
                    gc.collect()
                
                self.current_file_batch += 1
                self.current_row_index = 0
                
                print(f"Loaded parquet batch {self.current_file_batch}: {len(self.current_batch)} rows (rows {skip_rows}-{skip_rows + len(self.current_batch) - 1})")
                
            else:
                # CSV batch loading
                skip_rows = self.current_file_batch * self.batch_size
                self.current_batch = pd.read_csv(
                    self.file_path, 
                    delimiter=';', 
                    skiprows=range(1, skip_rows + 1), 
                    nrows=self.batch_size
                )
                self.current_file_batch += 1
                self.current_row_index = 0
                
                print(f"Loaded CSV batch {self.current_file_batch}: {len(self.current_batch)} rows (rows {skip_rows}-{skip_rows + len(self.current_batch) - 1})")
                
        except Exception as e:
            print(f"Error loading next batch: {e}")
            # If we can't load next batch, reset to beginning of file
            if self.current_batch is None or len(self.current_batch) == 0:
                print("Failed to load any data. Resetting to beginning of file.")
                self.current_file_batch = 0
                self.current_row_index = 0
    

    
    def get_next_row(self):
        """Get the next data row, loading new batches as needed."""
        if not self.initialized:
            return None
        
        # Check if we need to load next batch
        if (self.current_batch is None or 
            self.current_row_index >= len(self.current_batch)):
            
            # Load next batch for all environments
            self._load_next_batch()
            print(f"Loaded new batch {self.current_file_batch}: {len(self.current_batch) if self.current_batch is not None else 0} rows")
        
        if self.current_batch is None or len(self.current_batch) == 0:
            return None
        
        # Get current row
        if self.current_row_index >= len(self.current_batch):
            self.current_row_index = 0
        
        row = self.current_batch.iloc[self.current_row_index]
        self.current_row_index += 1
        
        return row
    
    def get_columns(self):
        """Get column names."""
        return self.data_columns

# Global data streamer instance
data_streamer = None

# --- Data management functions ---
def initialize_data_streamer():
    """Initialize the memory-efficient data streamer."""
    global data_streamer, data_loaded, data_columns
    
    try:
        data_streamer = MemoryEfficientDataStreamer(DATA_FILE_PATH)
        if data_streamer.initialized:
            data_columns = data_streamer.get_columns()
            data_loaded = True
            print("Data streamer initialized successfully")
            return True
        else:
            print("Failed to initialize data streamer")
            return False
    except Exception as e:
        print(f"Error initializing data streamer: {e}")
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
    print("Starting memory-efficient sensor data simulation...")
    
    # Initialize data streamer - only proceed with real data
    if not initialize_data_streamer():
        print("Failed to initialize data streamer with real data. Stopping simulation.")
        print("Make sure the parquet file exists and is accessible.")
        return
    
    print(f"Simulation started. Updating every {DATA_INTERVAL_SECONDS} seconds.")
    
    while not thread_stop_event.is_set():
        try:
            # Get next data point
            row = data_streamer.get_next_row()
            
            if row is not None:
                # Convert to dictionary with memory optimization
                data_point = row.to_dict()
                
                # Handle timestamp formatting
                if 'timestamp' in data_point and pd.notna(data_point['timestamp']):
                    if hasattr(data_point['timestamp'], 'isoformat'):
                        data_point['timestamp'] = data_point['timestamp'].isoformat()
                    else:
                        data_point['timestamp'] = str(data_point['timestamp'])
                
                # Convert any NaN values to None and optimize data types for memory
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
                        message = {"type": "sensor_data", "data": data_point}
                        loop.run_until_complete(broadcast_to_websockets(message))
                    except Exception as e:
                        print(f"Error broadcasting to WebSocket clients: {e}")
                
                print(f"Updated sensor data: {data_point.get('timestamp', 'N/A')} - {len(data_point)} fields")
            else:
                print("No data available from streamer")
            
            # Force aggressive garbage collection for memory efficiency
            if hasattr(simulate_sensor_data, 'gc_counter'):
                simulate_sensor_data.gc_counter += 1
            else:
                simulate_sensor_data.gc_counter = 1
            
            # More frequent garbage collection on Heroku
            gc_frequency = 3 if 'PORT' in os.environ else 10
            if simulate_sensor_data.gc_counter % gc_frequency == 0:
                gc.collect()
                print(f"Garbage collection performed (cycle {simulate_sensor_data.gc_counter})")
            
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
        "version": "2.1.0-real-data-only",
        "memory_optimized": True,
        "real_data_only": True,
        "data_source": "parquet_files",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def api_status():
    """Get API status and data information."""
    with current_reading_lock:
        has_current_data = bool(current_reading)
    
    with historical_readings_lock:
        historical_count = len(historical_readings)
    
    # Detailed memory usage info
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = round(memory_info.rss / 1024 / 1024, 2)
        memory_percent = process.memory_percent()
    except ImportError:
        memory_mb = 0
        memory_percent = 0
    
    # Get data streamer info
    streamer_info = {}
    if data_streamer:
        current_batch_size = len(data_streamer.current_batch) if data_streamer.current_batch is not None else 0
        streamer_info = {
            'current_batch_size': current_batch_size,
            'batch_size_limit': data_streamer.batch_size,
            'current_file_batch': data_streamer.current_file_batch,
            'total_estimated_rows': data_streamer.total_file_rows
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
        'memory_usage_mb': memory_mb,
        'memory_percent': memory_percent,
        'memory_optimized': True,
        'ultra_minimal_mode': True,
        'heroku_mode': 'PORT' in os.environ,
        'streamer_info': streamer_info,
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/current")
async def api_current():
    """Get the current sensor reading."""
    with current_reading_lock:
        if not current_reading:
            if not data_loaded:
                return {"error": "No current reading available", "message": "Real data file not loaded. Check if parquet file exists and is accessible."}
            else:
                return {"error": "No current reading available", "message": "Wait for the simulation to start processing real data"}
        
        return {"status": "success", "data": current_reading.copy(), "timestamp": datetime.now().isoformat()}

@app.get("/api/all")
async def api_all():
    """Get all historical sensor readings."""
    with historical_readings_lock:
        if not historical_readings:
            if not data_loaded:
                return {"error": "No historical readings available", "message": "Real data file not loaded. Check if parquet file exists and is accessible."}
            else:
                return {"error": "No historical readings available", "message": "Wait for the simulation to generate data from real parquet file"}
        
        return {"status": "success", "count": len(historical_readings), "data": list(historical_readings), "timestamp": datetime.now().isoformat()}

@app.get("/api/latest/{count}")
async def api_latest(count: int):
    """Get the latest N sensor readings."""
    if count <= 0:
        return {"error": "Count must be a positive integer"}
    
    # Limit count for memory efficiency
    count = min(count, 20)
    
    with historical_readings_lock:
        if not historical_readings:
            if not data_loaded:
                return {"error": "No historical readings available", "message": "Real data file not loaded. Check if parquet file exists and is accessible."}
            else:
                return {"error": "No historical readings available", "message": "Wait for the simulation to generate data from real parquet file"}
        
        latest_readings = list(historical_readings)[-count:]
        
        return {"status": "success", "requested_count": count, "returned_count": len(latest_readings), "data": latest_readings, "timestamp": datetime.now().isoformat()}

@app.get("/api/sensor/{sensor_name}")
async def api_sensor_value(sensor_name: str):
    """Get the current value of a specific sensor."""
    with current_reading_lock:
        if not current_reading:
            if not data_loaded:
                return {"error": "No current reading available", "message": "Real data file not loaded. Check if parquet file exists and is accessible."}
            else:
                return {"error": "No current reading available", "message": "Wait for the simulation to start processing real data"}
        
        if sensor_name not in current_reading:
            available_sensors = list(current_reading.keys())
            return {"error": f'Sensor "{sensor_name}" not found', "available_sensors": available_sensors}
        
        return {"status": "success", "sensor_name": sensor_name, "value": current_reading[sensor_name], "timestamp": datetime.now().isoformat()}

@app.get("/api/sensors")
async def api_available_sensors():
    """Get list of available sensors."""
    with current_reading_lock:
        if not current_reading:
            if data_loaded:
                return {"status": "success", "available_sensors": data_columns, "message": "Real data loaded but no current reading yet"}
            else:
                return {"error": "No real data loaded", "message": "Real data file not loaded. Check if parquet file exists and is accessible."}
        
        return {"status": "success", "available_sensors": list(current_reading.keys()), "timestamp": datetime.now().isoformat()}

# --- Legacy Socket.IO Compatibility ---
@app.get("/socket.io/")
async def socket_io_fallback():
    """Fallback for old Socket.IO requests."""
    return {
        "error": "Socket.IO is no longer supported",
        "message": "This API now uses native WebSockets. Please connect to /ws endpoint instead.",
        "websocket_endpoint": "/ws",
        "migration_info": "The API has been upgraded to FastAPI with native WebSocket support."
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
            # Keep connection alive
            data = await websocket.receive_text()
            # Send keep-alive response
            await websocket.send_json({"type": "keepalive", "message": "Connection active", "timestamp": datetime.now().isoformat()})
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
        <title>Cholesterol-Lowering Drug Manufacturing Live Sensor Data (Memory Optimized)</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; margin: 0; padding: 2rem; }
            .container { max-width: 1200px; margin: auto; background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
            h1, h2 { color: #0b57d0; border-bottom: 2px solid #e7e9ec; padding-bottom: 0.5rem; }
            .badge { color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-left: 0.5rem; }
            .streaming-badge { background-color: #1e8e3e; }
            .memory-badge { background-color: #ff6b35; }
            #status { font-weight: bold; margin-bottom: 1rem; padding: 0.75rem; border-radius: 8px; }
            .connected { color: #1e8e3e; background-color: #e6f4ea; }
            .disconnected { color: #d93025; background-color: #fce8e6; }
            #data-container { margin-top: 1.5rem; background: #f8f9fa; padding: 1.5rem; border-radius: 8px; border: 1px solid #e0e0e0; min-height: 200px; font-family: monospace; overflow-y: auto; max-height: 400px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem; }
            .endpoint { background: #fff; padding: 1rem; margin: 0.5rem 0; border-radius: 6px; border-left: 4px solid #0b57d0; }
            .endpoint code { background: #f1f3f4; padding: 0.2rem 0.4rem; border-radius: 4px; }
            .api-docs-link { background: #0b57d0; color: white; padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; display: inline-block; margin: 0.5rem 0.5rem 0 0; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Cholesterol Drug Manufacturing Live Sensor Data<span class="streaming-badge badge">REAL DATA</span><span class="memory-badge badge">MEMORY OPTIMIZED</span></h1>
            <p><strong>Ultra memory-efficient FastAPI streaming from real parquet data</strong> - Optimized for Heroku deployment</p>
            <p>
                <a href="/docs" class="api-docs-link" target="_blank">📚 API Docs</a>
                <a href="/redoc" class="api-docs-link" target="_blank">📖 ReDoc</a>
                <a href="/api/status" class="api-docs-link" target="_blank">📊 Status</a>
            </p>
            
            <div class="grid">
                <div>
                    <h2>Real-time Data Stream</h2>
                    <div id="status" class="disconnected">Status: Connecting...</div>
                    <div id="data-container">Connecting to real-time sensor data from parquet files...</div>
                </div>
                
                <div>
                    <h2>API Endpoints</h2>
                    <div class="endpoint"><strong>Health Check:</strong><br><code>GET /health</code></div>
                    <div class="endpoint"><strong>Current Reading:</strong><br><code>GET /api/current</code></div>
                    <div class="endpoint"><strong>Latest Readings:</strong><br><code>GET /api/latest/5</code></div>
                    <div class="endpoint"><strong>All Sensors:</strong><br><code>GET /api/sensors</code></div>
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
                
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                socket = new WebSocket(wsUrl);

                socket.onopen = function() {
                    console.log('Connected to WebSocket');
                    statusDiv.textContent = 'Status: Connected (Real-time Streaming)';
                    statusDiv.className = 'connected';
                    reconnectAttempts = 0;
                };

                socket.onclose = function() {
                    console.log('WebSocket disconnected');
                    statusDiv.textContent = 'Status: Disconnected';
                    statusDiv.className = 'disconnected';
                    
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
                        }
                    } catch (error) {
                        console.error('Error parsing message:', error);
                    }
                };

                socket.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
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
    global simulation_thread, MAX_HISTORICAL_READINGS, historical_readings
    print("FastAPI startup: Starting efficient batch-processing sensor simulation...")
    
    # Optimized memory usage with proper batch processing
    if 'PORT' in os.environ:
        print(f"Heroku mode: Processing in batches of 500 rows")
        print(f"Historical readings limited to {MAX_HISTORICAL_READINGS}")
        
        # Force immediate garbage collection
        gc.collect()
    
    # Start simulation thread
    if simulation_thread is None or not simulation_thread.is_alive():
        simulation_thread = Thread(target=simulate_sensor_data, daemon=True)
        simulation_thread.start()
        print("Background simulation thread started with efficient batch processing!")

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

    def run_demo(self):
        print("FastAPI Sensor Data API Demo")
        print("=" * 40)
        
        if not self.check_api_status():
            print("API not available!")
            return False
        
        self.get_current_reading()
        return True

# --- Server functions ---
def run_server(host=SERVER_HOST, port=SERVER_PORT):
    print("Starting memory-optimized FastAPI server...")
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
    
    parser = argparse.ArgumentParser(description='Memory-Optimized FastAPI Sensor Data Streaming')
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
    print(f"Memory-Optimized FastAPI | Interval: {DATA_INTERVAL_SECONDS}s")
    
    if args.mode == 'server':
        run_server(host=server_host, port=server_port)
    elif args.mode == 'client':
        run_client(api_base_url=api_base_url)
    else:
        run_both(host=server_host, port=server_port, api_base_url=api_base_url)

if __name__ == '__main__':
    main() 