#!/usr/bin/env bash
# Start the Bid Exchange server, killing any existing process on the port first.

PORT=${1:-8000}

# Kill existing processes on the port
pids=$(lsof -ti :"$PORT" 2>/dev/null)
if [ -n "$pids" ]; then
    echo "Killing existing processes on port $PORT: $pids"
    echo "$pids" | xargs kill -9
    sleep 0.5
fi

echo "Starting server on port $PORT..."
uv run uvicorn backend.main:app --reload --port "$PORT"
