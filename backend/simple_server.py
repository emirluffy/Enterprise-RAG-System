#!/usr/bin/env python3
"""
Enhanced FastAPI server for Enterprise RAG System
Includes full RAG pipeline with real chat endpoints and document processing
"""

import sys
import io
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Fix Windows encoding for emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import the real routers with RAG pipeline
from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router

app = FastAPI(title="Enterprise RAG System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the real RAG routers
app.include_router(chat_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Enterprise RAG System is operational"}

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "message": "Enterprise RAG System is operational"}

# Keep simple mock endpoint for backward compatibility during testing
@app.post("/api/v1/chat/simple")
async def simple_chat_query(request: dict):
    """Simple chat endpoint for testing (backup)"""
    query = request.get("query", "")
    return {
        "answer": f"Bu bir test cevabıdır: {query}",
        "confidence": 0.85,
        "sources": ["test_document.pdf"]
    }

@app.get("/api/v1/users/me")
async def get_current_user():
    """Mock user endpoint for development"""
    return {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_superuser": False
    }

@app.get("/api/v1/items/")
async def get_items(skip: int = 0, limit: int = 5):
    """Mock items endpoint to prevent 404 errors"""
    return {
        "data": [],
        "count": 0
    }

# Mock upload endpoint removed - using real documents router

if __name__ == "__main__":
    print("🔥 Starting Enterprise RAG System...")
    print("🔗 Health Check: http://localhost:8002/health")
    print("🤖 Chat API: http://localhost:8002/api/v1/chat/query")
    print("💚 Chat Health: http://localhost:8002/api/v1/chat/health")
    print("📁 Document Upload: http://localhost:8002/api/v1/documents/upload")
    print("📚 API Docs: http://localhost:8002/docs")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8002,
        reload=False,
        log_level="info"
    ) 