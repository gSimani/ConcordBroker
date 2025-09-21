#!/usr/bin/env python3
"""
Railway entry point for ConcordBroker API with Redis caching
"""

import os
import sys
import subprocess

def main():
    """Start the ConcordBroker API server"""

    # Change to the API directory
    api_dir = os.path.join(os.path.dirname(__file__), 'apps', 'api')
    os.chdir(api_dir)

    # Get configuration from environment
    port = os.environ.get('PORT', '8000')
    workers = os.environ.get('GUNICORN_WORKERS', '2')

    # Start gunicorn with uvicorn workers
    cmd = [
        'gunicorn',
        'property_live_api:app',
        '--host', '0.0.0.0',
        '--port', port,
        '--workers', workers,
        '--worker-class', 'uvicorn.workers.UvicornWorker',
        '--timeout', '120',
        '--preload'
    ]

    print(f"Starting ConcordBroker API on port {port} with {workers} workers...")
    print(f"Command: {' '.join(cmd)}")

    # Execute the server
    subprocess.run(cmd)

if __name__ == '__main__':
    main()
