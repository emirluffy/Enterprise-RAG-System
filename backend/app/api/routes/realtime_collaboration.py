from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any
from app.services.realtime_collaboration_service import collaboration_service

# Mock in-memory storage for collaboration rooms (now managed by the service)
# collaboration_rooms: Dict[str, Dict[str, Any]] = {}

router = APIRouter()

# Pydantic Models based on frontend expectations
class UserInfo(BaseModel):
    name: str
    avatar: str | None = None

class JoinRoomRequest(BaseModel):
    room_id: str
    user_id: str
    user_info: UserInfo
    room_type: str = "chat"

class LeaveRoomRequest(BaseModel):
    room_id: str
    user_id: str

class MessageRequest(BaseModel):
    room_id: str
    user_id: str
    content: str
    message_type: str = "text"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TypingRequest(BaseModel):
    room_id: str
    user_id: str
    is_typing: bool

@router.post("/rooms/join")
async def join_room(request: JoinRoomRequest):
    """Handles a user joining a collaboration room."""
    try:
        room_state = await collaboration_service.join_room(
            room_id=request.room_id,
            user_id=request.user_id,
            user_info=request.user_info.dict(),
            room_type=request.room_type
        )
        return room_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rooms/leave")
async def leave_room(request: LeaveRoomRequest):
    """Handles a user leaving a collaboration room."""
    try:
        await collaboration_service.leave_room(
            room_id=request.room_id,
            user_id=request.user_id
        )
        return {"status": "success", "message": f"User {request.user_id} left room {request.room_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rooms/message")
async def send_message(request: MessageRequest):
    """Handles sending a message to a collaboration room."""
    try:
        message_data = await collaboration_service.send_message(
            room_id=request.room_id,
            user_id=request.user_id,
            message=request.dict(exclude={"room_id", "user_id"})
        )
        return message_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rooms/typing")
async def set_typing_status(request: TypingRequest):
    """Handles typing status updates in a collaboration room."""
    try:
        await collaboration_service.set_typing_status(
            room_id=request.room_id,
            user_id=request.user_id,
            is_typing=request.is_typing
        )
        return {"status": "success", "message": f"Typing status updated for user {request.user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 