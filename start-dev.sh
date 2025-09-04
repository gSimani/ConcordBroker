#!/bin/bash
# Bash script to start development servers (for Mac/Linux)

echo "========================================"
echo "  CONCORDBROKER DEVELOPMENT SERVER"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your Supabase credentials!"
    echo "Press Enter to continue after updating .env..."
    read
fi

echo "Starting development servers..."
echo ""

# Start FastAPI backend
echo "📦 Starting API Server (FastAPI)..."
cd apps/api
python -m uvicorn main:app --reload --port 8000 &
API_PID=$!
cd ../..

# Wait for API to start
sleep 3

# Start React frontend
echo "🌐 Starting Web Server (React)..."
cd apps/web
npm run dev &
WEB_PID=$!
cd ../..

echo ""
echo "========================================"
echo "  SERVERS RUNNING"
echo "========================================"
echo ""
echo "📍 API Server: http://localhost:8000"
echo "📍 API Docs:   http://localhost:8000/docs"
echo "📍 Web App:    http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for user to press Ctrl+C
trap "kill $API_PID $WEB_PID; exit" INT
wait