#!/usr/bin/env python3
"""
Main entry point for SOLEil Band Platform
Uses modular architecture with proper initialization
"""

import uvicorn
from modules.init_app import create_modular_app

# Create the FastAPI application using modular architecture
app = create_modular_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production to avoid double registration
        log_level="info"
    )
