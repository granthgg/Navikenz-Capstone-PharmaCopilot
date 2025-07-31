#!/usr/bin/env python3
"""
Simplified PharmaCopilot Report Generation System
Optimized for efficiency and simplicity
"""

import os
import sys
import logging
import uvicorn
import argparse
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Disable chromadb telemetry to prevent posthog errors
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False'

# Set up logging to reduce noise
logging.basicConfig(
    level=logging.WARNING,  # Reduced from INFO to WARNING to reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress specific noisy loggers
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('chromadb').setLevel(logging.ERROR)
logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('torch').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

def check_core_dependencies():
    """Check only essential dependencies"""
    missing_deps = []
    
    try:
        import fastapi
        import chromadb
        import groq
    except ImportError as e:
        missing_deps.append(str(e))
        
    if missing_deps:
        logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
        logger.error("Install with: pip install fastapi chromadb groq uvicorn")
        return False
        
    return True

def print_simple_info(port):
    """Print simplified system information"""
    print("\n" + "="*50)
    print(" 🏭 PharmaCopilot Report Generation")
    print("="*50)
    print(f" Status: Ready at {datetime.now().strftime('%H:%M:%S')}")
    print(f" API Server: http://localhost:{port}")
    print(f" Documentation: http://localhost:{port}/docs")
    print(f" Health Check: http://localhost:{port}/api/reports/health")
    print("="*50)

def main():
    """Simplified main entry point"""
    parser = argparse.ArgumentParser(description="PharmaCopilot Report Generation System")
    parser.add_argument("--port", type=int, default=8001, help="Port for API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host for API server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check dependencies
    if not check_core_dependencies():
        sys.exit(1)
    
    print_simple_info(args.port)
    
    try:
        # Import and start the API
        from api.simple_api import app
        
        logger.info(f"Starting API server on {args.host}:{args.port}")
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="warning",  # Reduce log noise
            access_log=False      # Disable access logs for cleaner output
        )
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
