from fastapi import APIRouter
from .routes import (
    auth, documents, chat, conversations, websocket, realtime_collaboration
)

api_router = APIRouter()

# Include core route modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(realtime_collaboration.router, prefix="/collaboration", tags=["real-time-collaboration"])
# WebSocket router is included in the main app factory for root access

@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "RAG System API is running",
        "features": [
            "Document Processing & RAG",
            "Real-time Chat via WebSockets",
            "User Authentication",
            "Conversation Management",
            "Real-time Collaboration"
        ]
    }
