#!/usr/bin/env python3
"""
Minimal test server to bypass Unicode encoding issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set encoding before any imports
os.environ['PYTHONIOENCODING'] = 'utf-8'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="RAG Test Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat")
async def chat_endpoint(request: dict):
    """Test chat endpoint"""
    message = request.get("message", "")
    
    return {
        "response": f"TEST RESPONSE: You asked about '{message}'. This is a test server response.",
        "sources": ["test_document.txt"]
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Test server running"}

if __name__ == "__main__":
    print("Starting test server on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")