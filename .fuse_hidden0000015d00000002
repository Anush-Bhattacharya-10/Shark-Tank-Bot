#!/bin/bash

# Navigate to the folder where this script lives
cd "$(dirname "$0")"

# Activate the virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Error: .venv folder not found. Please create it first."
    exit 1
fi

# Run the Shark Tank bot
echo "🦈 Launching Shark Tank Bot..."
python3 Shark-Tank.py
