@echo off
title Enterprise RAG System

echo 🚀 Starting Enterprise RAG System...
echo 🛑 Stopping any existing servers first...

REM Kill existing Python/Node processes
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul
taskkill /f /im cmd.exe /fi "WINDOWTITLE eq Backend Server" 2>nul
taskkill /f /im cmd.exe /fi "WINDOWTITLE eq Frontend Server" 2>nul

REM Kill processes on specific ports using netstat and taskkill
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8001" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8002" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5174" ^| find "LISTENING"') do taskkill /f /pid %%a 2>nul

timeout /t 2 /nobreak >nul

echo ✅ All existing servers stopped
echo ⚡ Starting fresh Backend ^& Frontend servers...

echo.
echo 🔧 Starting Backend (FastAPI)...
start "Backend Server" cmd /c "cd backend && python simple_server.py"

timeout /t 3 /nobreak >nul

echo 🎨 Starting Frontend (React + Vite)...
start "Frontend Server" cmd /c "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo 🎉 Enterprise RAG System is ready!
echo 📊 Backend API:  http://localhost:8002
echo 📊 API Docs:     http://localhost:8002/docs  
echo 🎨 Frontend UI:  http://localhost:5174
echo.
echo 💡 Close terminal windows to stop servers
echo 💡 Or press any key to exit this launcher...

pause >nul 