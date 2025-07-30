#!/bin/bash

# Soleil Band Platform - Mac Desktop Launcher
# Double-click this file to start the backend

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Run the start script
./start_backend.sh