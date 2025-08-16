#!/usr/bin/env python3
"""
Simple script to start the Dashboard API server for testing.
"""

import uvicorn
from src.dashboard.api import app

if __name__ == "__main__":
    print("Starting Dashboard API server on http://localhost:8002")
    print("Press Ctrl+C to stop the server")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")