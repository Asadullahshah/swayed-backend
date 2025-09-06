#!/usr/bin/env python3
"""
Quick start script for AI Content Suggestor API
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("AI Content Suggestor - Quick Start")
    print("=" * 40)
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    main_file = current_dir / "main.py"
    
    if not main_file.exists():
        print("main.py not found in current directory")
        print("Please run this script from the /scrape directory")
        return
    
    print("Current directory:", current_dir)
    print("Found main.py - starting server...")
    print()
    
    try:
        # Start the FastAPI server
        print("Starting FastAPI server on http://localhost:8000")
        print("API Documentation: http://localhost:8000/docs")
        print("Health check: http://localhost:8000/health")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 40)
        
        # Run uvicorn without auto-reload to prevent task data loss
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000"
            # Removed --reload to prevent server restarts
        ])
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Make sure you have installed all requirements:")
        print("   pip install -r ../requirements.txt")

if __name__ == "__main__":
    main()