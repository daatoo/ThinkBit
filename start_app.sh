#!/bin/bash
set -e

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install it first."
    exit 1
fi

# Backend Setup
echo "Setting up backend..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

# Google Credentials
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    if [ -f "credentials.json" ]; then
        export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/credentials.json
        echo "Set GOOGLE_APPLICATION_CREDENTIALS to $(pwd)/credentials.json"
    else
        echo "Warning: GOOGLE_APPLICATION_CREDENTIALS not set and credentials.json not found."
        echo "Please set GOOGLE_APPLICATION_CREDENTIALS to a valid Google Cloud service account key file."
        # Not creating dummy here because we want user to be aware
    fi
fi

# Start Backend
echo "Starting backend..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python -m backend.main > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend running (PID: $BACKEND_PID)"

# Frontend Setup
echo "Setting up frontend..."
cd website
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start Frontend
echo "Starting frontend..."
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend running (PID: $FRONTEND_PID)"

echo "Application started!"
echo "Backend logs: backend.log"
echo "Frontend logs: frontend.log"
echo "Press Ctrl+C to stop."

# Wait for user to kill
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
