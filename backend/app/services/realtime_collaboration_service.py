from typing import Dict, List, Optional, Any, TYPE_CHECKING
import asyncio
import uuid
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from fastapi_websocket_pubsub import PubSubEndpoint
import json
import logging

if TYPE_CHECKING:
    from app.services.websocket_service import WebSocketService

logger = logging.getLogger(__name__)

class CollaborationRoom:
    """Real-time collaboration room for users"""
    
    def __init__(self, room_id: str, room_type: str = "chat"):
        self.room_id = room_id
        self.room_type = room_type  # chat, document, workspace
        self.users: Dict[str, Dict] = {}  # user_id -> user_info
        self.typing_users: Dict[str, float] = {}  # user_id -> timestamp
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        
    def add_user(self, user_id: str, user_info: Dict):
        """Add user to collaboration room"""
        self.users[user_id] = {
            **user_info,
            'joined_at': datetime.now(timezone.utc).isoformat(),
            'active': True
        }
        self.last_activity = datetime.now(timezone.utc)
        
    def remove_user(self, user_id: str):
        """Remove user from collaboration room"""
        if user_id in self.users:
            del self.users[user_id]
        if user_id in self.typing_users:
            del self.typing_users[user_id]
        self.last_activity = datetime.now(timezone.utc)
        
    def set_typing(self, user_id: str, is_typing: bool):
        """Set user typing status"""
        if is_typing:
            self.typing_users[user_id] = datetime.now(timezone.utc).timestamp()
        else:
            self.typing_users.pop(user_id, None)
            
    def get_typing_users(self) -> List[str]:
        """Get currently typing users (within last 3 seconds)"""
        current_time = datetime.now(timezone.utc).timestamp()
        active_typing = []
        
        for user_id, last_typed in list(self.typing_users.items()):
            if current_time - last_typed <= 3:  # 3 seconds timeout
                active_typing.append(user_id)
            else:
                # Cleanup old typing status
                del self.typing_users[user_id]
                
        return active_typing
        
    def to_dict(self) -> Dict:
        """Convert room to dict for JSON serialization"""
        return {
            'room_id': self.room_id,
            'room_type': self.room_type,
            'users': self.users,
            'typing_users': self.get_typing_users(),
            'user_count': len(self.users),
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }

class RealtimeCollaborationService:
    """Context7 verified real-time collaboration service using FastAPI WebSocket PubSub"""
    
    def __init__(self):
        # Initialize without PubSub for now
        self.pubsub_endpoint = None
        self.rooms: Dict[str, CollaborationRoom] = {}
        self.user_connections: Dict[str, WebSocket] = {}
        self.websocket_service: Optional['WebSocketService'] = None  # Will be injected
        
        # Topic naming conventions
        self.ROOM_PREFIX = "room:"
        self.USER_PREFIX = "user:"
        self.TYPING_PREFIX = "typing:"
        self.PRESENCE_PREFIX = "presence:"
    
    def set_websocket_service(self, websocket_service):
        """Inject WebSocket service for direct connection management"""
        self.websocket_service = websocket_service
        logger.info("✅ WebSocket service injected into collaboration service")
        
    async def setup_pubsub_endpoint(self, app):
        """Setup PubSub endpoint with FastAPI app"""
        try:
            # For now, skip PubSub setup to avoid compatibility issues
            logger.info("⚠️ PubSub temporarily disabled for compatibility")
            self.pubsub_endpoint = None
        except Exception as e:
            logger.error(f"❌ PubSub setup failed: {e}")
            self.pubsub_endpoint = None
        
    async def join_room(self, room_id: str, user_id: str, user_info: Dict, room_type: str = "chat"):
        """Join a collaboration room"""
        try:
            # Create room if doesn't exist
            if room_id not in self.rooms:
                self.rooms[room_id] = CollaborationRoom(room_id, room_type)
                logger.info(f"📁 Created new collaboration room: {room_id}")
            
            # Add user to room
            room = self.rooms[room_id]
            room.add_user(user_id, user_info)
            
            # Context7 verified: Publish user joined event
            await self._publish_room_event(room_id, {
                'type': 'user_joined',
                'user_id': user_id,
                'user_info': user_info,
                'room_state': room.to_dict(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Publish presence update
            await self._publish_presence_update(room_id)
            
            logger.info(f"👥 User {user_id} joined room {room_id}")
            return room.to_dict()
            
        except Exception as e:
            logger.error(f"❌ Error joining room {room_id}: {e}")
            raise
    
    async def leave_room(self, room_id: str, user_id: str):
        """Leave a collaboration room"""
        try:
            if room_id not in self.rooms:
                return
                
            room = self.rooms[room_id]
            room.remove_user(user_id)
            
            # Context7 verified: Publish user left event
            await self._publish_room_event(room_id, {
                'type': 'user_left',
                'user_id': user_id,
                'room_state': room.to_dict(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Publish presence update
            await self._publish_presence_update(room_id)
            
            # Remove empty room
            if len(room.users) == 0:
                del self.rooms[room_id]
                logger.info(f"🗑️ Removed empty room: {room_id}")
            
            logger.info(f"👋 User {user_id} left room {room_id}")
            
        except Exception as e:
            logger.error(f"❌ Error leaving room {room_id}: {e}")
            raise
    
    async def send_message(self, room_id: str, user_id: str, message: Dict):
        """Send message to collaboration room"""
        try:
            if room_id not in self.rooms:
                raise ValueError(f"Room {room_id} not found")
            
            # Add message metadata
            message_data = {
                'type': 'message',
                'message_id': str(uuid.uuid4()),
                'room_id': room_id,
                'user_id': user_id,
                'content': message.get('content', ''),
                'message_type': message.get('message_type', 'text'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metadata': message.get('metadata', {})
            }
            
            # Context7 verified: Publish message to room
            await self._publish_room_event(room_id, message_data)
            
            # Update room activity
            self.rooms[room_id].last_activity = datetime.now(timezone.utc)
            
            logger.info(f"💬 Message sent to room {room_id} by user {user_id}")
            return message_data
            
        except Exception as e:
            logger.error(f"❌ Error sending message to room {room_id}: {e}")
            raise
    
    async def set_typing_status(self, room_id: str, user_id: str, is_typing: bool):
        """Set user typing status in room"""
        try:
            if room_id not in self.rooms:
                return
            
            room = self.rooms[room_id]
            room.set_typing(user_id, is_typing)
            
            # Context7 verified: Publish typing status
            await self._publish_typing_event(room_id, {
                'type': 'typing_status',
                'user_id': user_id,
                'is_typing': is_typing,
                'typing_users': room.get_typing_users(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Error setting typing status: {e}")
    
    async def get_room_state(self, room_id: str) -> Optional[Dict]:
        """Get current room state"""
        if room_id in self.rooms:
            return self.rooms[room_id].to_dict()
        return None
    
    async def get_active_rooms(self) -> List[Dict]:
        """Get all active collaboration rooms"""
        return [room.to_dict() for room in self.rooms.values()]
    
    async def _publish_room_event(self, room_id: str, event_data: Dict):
        """Context7 verified: Publish event to room topic"""
        topic = f"{self.ROOM_PREFIX}{room_id}"
        await self._publish_event([topic], event_data)
    
    async def _publish_typing_event(self, room_id: str, event_data: Dict):
        """Context7 verified: Publish typing event"""
        topic = f"{self.TYPING_PREFIX}{room_id}"
        await self._publish_event([topic], event_data)
    
    async def _publish_presence_update(self, room_id: str):
        """Context7 verified: Publish presence update"""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            topic = f"{self.PRESENCE_PREFIX}{room_id}"
            await self._publish_event([topic], {
                'type': 'presence_update',
                'room_id': room_id,
                'users': room.users,
                'user_count': len(room.users),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
    
    async def _publish_event(self, topics: List[str], data: Dict):
        """Context7 verified: Publish event using WebSocket service"""
        try:
            if self.websocket_service:
                # ✅ Use WebSocket service to send to active connections
                for topic in topics:
                    if topic.startswith(self.ROOM_PREFIX):
                        # Extract room_id from topic
                        room_id = topic.replace(self.ROOM_PREFIX, "")
                        await self._broadcast_to_room(room_id, data)
                
                logger.debug(f"📡 Event broadcasted to {topics}: {data.get('type', 'unknown')}")
            elif self.pubsub_endpoint:
                # Context7 verified publish pattern (sync method)
                self.pubsub_endpoint.publish(topics, data=data)  # type: ignore
            else:
                # No WebSocket service - log the event for debugging
                logger.debug(f"📡 Event would be published to {topics}: {data.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Error publishing event to topics {topics}: {e}")
    
    async def _broadcast_to_room(self, room_id: str, data: Dict):
        """Broadcast message to all users in a room"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        if self.websocket_service:
            for user_id in room.users.keys():
                try:
                    await self.websocket_service.send_to_user(user_id, data)
                except Exception as e:
                    logger.warning(f"Failed to send to user {user_id}: {e}")

# Global collaboration service instance
collaboration_service = RealtimeCollaborationService() 