#!/usr/bin/env python3
"""
Backend application entry point for Docker container
"""

import os
from backend.app import create_app

if __name__ == '__main__':
    print("🚀 Starting Planetarion Backend Server...")

    # Create Flask app
    app = create_app()

    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')

    print(f"🌐 Starting server on {host}:{port}")
    print("📡 Backend server is ready!")

    # Start the server
    app.run(host=host, port=port, debug=False)
