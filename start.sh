#!/bin/bash

# Enterprise RAG System - Development Starter (MCP-Safe Version)
# Only kills processes on specific development ports (8002, 5174)
# Preserves MCP servers and other system processes

echo "🚀 Starting Enterprise RAG System..."
echo "🛑 Stopping existing development servers on ports 8002 & 5174..."

# Function to kill process on specific port (Windows/PowerShell)
kill_port_process() {
    local port=$1
    echo "🔍 Checking port $port..."
    
    # Use PowerShell to find and kill process on specific port
    powershell -Command "
        try {
            \$processId = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess)
            if (\$processId) {
                Stop-Process -Id \$processId -Force -ErrorAction SilentlyContinue
                Write-Host '✅ Stopped process on port $port (PID: '\$processId')'
            } else {
                Write-Host '✅ Port $port is already free'
            }
        } catch {
            Write-Host '✅ Port $port is free (no process found)'
        }
    " 2>/dev/null || {
        # Fallback for systems without PowerShell Get-NetTCPConnection
        echo "🔄 Using fallback method for port $port..."
        
        # Use netstat to find process on port
        local pid=$(netstat -ano 2>/dev/null | grep ":$port " | grep "LISTENING" | awk '{print $5}' | head -n1)
        if [ ! -z "$pid" ] && [ "$pid" != "0" ]; then
            taskkill //F //PID $pid 2>/dev/null && echo "✅ Stopped process on port $port (PID: $pid)" || echo "✅ Port $port is already free"
        else
            echo "✅ Port $port is already free"
        fi
    }
}

# Only kill processes on our specific development ports
echo "🎯 Targeting only development ports (preserving MCP servers)..."
kill_port_process 8002  # Backend FastAPI
kill_port_process 5174  # Frontend Vite

# Wait a moment for processes to clean up
sleep 2

echo "✅ Development ports cleared (MCP servers preserved)"
echo "⚡ Starting fresh Backend & Frontend servers..."

# Function to handle cleanup on script exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $(jobs -p) 2>/dev/null
    echo "✅ Development servers stopped (MCP servers still running)"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo "🔧 Starting Backend (FastAPI on port 8002)..."
cd backend
python simple_server.py &
BACKEND_PID=$!
cd ..

# Give backend a moment to start
sleep 2

# Start frontend server
echo "🎨 Starting Frontend (React + Vite on port 5174)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for both to initialize
sleep 3

echo ""
echo "🎉 Enterprise RAG System is ready!"
echo "📊 Backend API:  http://localhost:8002"
echo "📊 API Docs:     http://localhost:8002/docs"
echo "🎨 Frontend UI:  http://localhost:5174"
echo ""
echo "🛡️ MCP servers preserved and running"
echo "💡 Press Ctrl+C to stop only development servers"
echo ""

# Keep script running and wait for background processes
wait 