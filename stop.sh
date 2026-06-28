#!/bin/bash

echo "🛑 Stopping Python processes..."

# Force kill any active python scripts running the Shark-Tank bot
pkill -9 -f Shark-Tank.py

echo "✅ Bot stopped."
