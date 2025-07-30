import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
import socketio
from app.services.notification_service import notification_manager

from app.api.main import api_router
from app.core.config import settings
from app.services.websocket_service import websocket_service
from app.services.realtime_collaboration_service import collaboration_service
from app.services.caching_service import caching_service
# Context7 verified: Import WebSocket routes for direct app inclusion
from app.api.routes.websocket import router as websocket_router


def custom_generate_unique_id(route: APIRoute) -> str:
    # Handle routes without tags
    tag = route.tags[0] if route.tags else "api"
    return f"{tag}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Context7 verified: Include WebSocket routes directly on main app (no prefix)
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])

app.include_router(api_router, prefix=settings.API_V1_STR)

# Context7-verified WebSocket service registration
websocket_service.register_routes(app)

# Phase 5.3: Setup real-time collaboration PubSub endpoint
@app.on_event("startup")
async def setup_collaboration():
    # Inject WebSocket service into collaboration service
    collaboration_service.set_websocket_service(websocket_service)
    await collaboration_service.setup_pubsub_endpoint(app)

# Phase 5.4: Initialize advanced caching system
@app.on_event("startup")
async def setup_caching():
    await caching_service.initialize()

# Context7 Pattern: Socket.IO integration - temporarily disabled for WebSocket testing
# socket_app = socketio.ASGIApp(notification_manager.sio, app)
# app = socket_app

# ✅ Keep original FastAPI app for native WebSocket support
