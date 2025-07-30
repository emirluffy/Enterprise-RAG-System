"""
Context7-Verified Real-Time Document Change Notification Service
Based on: https://github.com/miguelgrinberg/python-socketio
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import socketio
from sqlmodel import Session, select
from ..models import DocumentChangeNotification, Document, User
from ..core.db import get_session

logger = logging.getLogger(__name__)

class DocumentNotificationManager:
    """Context7-verified notification manager using Socket.IO patterns"""
    
    def __init__(self):
        # Context7 Pattern: AsyncServer for real-time notifications
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins=[
                'http://localhost:5174',
                'http://127.0.0.1:5174',
                '*'
            ],
            allow_credentials=True,
            logger=True,
            engineio_logger=True
        )
        
        # Context7 Pattern: Room-based organization for scalability
        self.rooms = {
            'admin': 'admin_notifications',
            'operations': 'operations_notifications', 
            'all_users': 'document_updates'
        }
        
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Context7-verified event handler setup"""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            """Client connection with authentication"""
            logger.info(f"Client connected: {sid}")
            
            # Context7 Pattern: Session-based authentication
            user_role = auth.get('role', 'user') if auth else 'user'
            await self.sio.save_session(sid, {'role': user_role})
            
            # Context7 Pattern: Auto-join relevant rooms
            await self.sio.enter_room(sid, self.rooms['all_users'])
            
            if user_role in ['admin', 'operations']:
                await self.sio.enter_room(sid, self.rooms[user_role])
            
            # Send pending notifications on connect
            await self.send_pending_notifications(sid, user_role)
        
        @self.sio.event
        async def disconnect(sid):
            """Client disconnection cleanup"""
            logger.info(f"Client disconnected: {sid}")
        
        @self.sio.event
        async def acknowledge_notification(sid, data):
            """Context7 Pattern: Bidirectional notification acknowledgment"""
            notification_id = data.get('notification_id')
            user_id = data.get('user_id')
            
            if notification_id and user_id:
                await self.mark_notification_acknowledged(notification_id, user_id)
                
                # Context7 Pattern: Broadcast acknowledgment to ops team
                await self.sio.emit('notification_acknowledged', {
                    'notification_id': notification_id,
                    'acknowledged_by': user_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=self.rooms['operations'])
    
    async def send_pending_notifications(self, sid: str, user_role: str):
        """Context7-verified pending notification delivery"""
        try:
            session = next(get_session())
            
            # Get unacknowledged notifications - fixed SQLModel syntax with proper Optional handling
            current_time = datetime.utcnow()
            statement = select(DocumentChangeNotification).where(
                DocumentChangeNotification.status == "PENDING"
            )
            notifications = session.exec(statement).all()
            
            # Filter in Python to handle Optional datetime properly
            valid_notifications = [
                n for n in notifications 
                if n.expires_at is not None and n.expires_at > current_time
            ]
            
            for notification in valid_notifications:
                affected_systems = []
                if notification.affected_systems:
                    try:
                        affected_systems = json.loads(notification.affected_systems)
                    except json.JSONDecodeError:
                        affected_systems = []
                
                await self.sio.emit('document_change_notification', {
                    'id': notification.id,
                    'type': notification.notification_type,
                    'description': notification.change_description,
                    'document_id': notification.document_id,
                    'affected_systems': affected_systems,
                    'created_at': notification.created_at.isoformat(),
                    'requires_acknowledgment': notification.notification_type == 'URGENT'
                }, room=sid)
                
        except Exception as e:
            logger.error(f"Error sending pending notifications: {e}")
        finally:
            session.close()
    
    async def broadcast_document_change(self, notification_data: Dict[str, Any]):
        """Context7 Pattern: Real-time document change broadcasting"""
        try:
            # Create notification record
            session = next(get_session())
            
            notification = DocumentChangeNotification(
                document_id=notification_data['document_id'],
                notification_type=notification_data.get('type', 'NORMAL'),
                change_description=notification_data['description'],
                affected_systems=json.dumps(notification_data.get('affected_systems', [])),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            session.add(notification)
            session.commit()
            
            # Context7 Pattern: Room-based targeted broadcasting
            broadcast_data = {
                'id': notification.id,
                'type': notification.notification_type,
                'description': notification.change_description,
                'document_id': notification.document_id,
                'affected_systems': notification_data.get('affected_systems', []),
                'timestamp': datetime.utcnow().isoformat(),
                'requires_acknowledgment': notification.notification_type == 'URGENT'
            }
            
            # Broadcast to all users
            await self.sio.emit('document_change_notification', 
                               broadcast_data, 
                               room=self.rooms['all_users'])
            
            # Enhanced notification for operations team
            if notification.notification_type in ['URGENT', 'NORMAL']:
                ops_data = {**broadcast_data, 'admin_actions_required': True}
                await self.sio.emit('admin_document_notification', 
                                   ops_data, 
                                   room=self.rooms['operations'])
            
            # Mark as sent
            notification.status = "SENT"
            notification.sent_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Broadcast sent for document {notification_data['document_id']}")
            
        except Exception as e:
            logger.error(f"Error broadcasting document change: {e}")
        finally:
            session.close()
    
    async def mark_notification_acknowledged(self, notification_id: str, user_id: str):
        """Context7-verified acknowledgment tracking"""
        try:
            session = next(get_session())
            
            statement = select(DocumentChangeNotification).where(
                DocumentChangeNotification.id == notification_id
            )
            notification = session.exec(statement).first()
            
            if notification:
                # Parse existing acknowledgments
                acknowledged_by = []
                if notification.acknowledged_by:
                    try:
                        acknowledged_by = json.loads(notification.acknowledged_by)
                    except json.JSONDecodeError:
                        acknowledged_by = []
                
                if user_id not in acknowledged_by:
                    acknowledged_by.append(user_id)
                    notification.acknowledged_by = json.dumps(acknowledged_by)
                    
                    # Mark as acknowledged if this is the first acknowledgment
                    if not notification.acknowledged_at:
                        notification.acknowledged_at = datetime.utcnow()
                        notification.status = "ACKNOWLEDGED"
                    
                    session.commit()
                    logger.info(f"Notification {notification_id} acknowledged by {user_id}")
                    
        except Exception as e:
            logger.error(f"Error marking notification acknowledged: {e}")
        finally:
            session.close()

# Context7 Pattern: Global instance for application use
notification_manager = DocumentNotificationManager()

async def send_document_update_notification(
    document_id: str,
    change_type: str,
    description: str,
    urgency: str = "NORMAL",
    affected_systems: Optional[List[str]] = None
):
    """Context7-verified helper function for sending notifications"""
    
    notification_data = {
        'document_id': document_id,
        'type': urgency,
        'description': description,
        'affected_systems': affected_systems or []
    }
    
    await notification_manager.broadcast_document_change(notification_data)

async def notify_bulk_document_changes(changes: List[Dict[str, Any]]):
    """Context7 Pattern: Efficient bulk notification handling"""
    
    for change in changes:
        await send_document_update_notification(
            document_id=change['document_id'],
            change_type=change['change_type'],
            description=change['description'],
            urgency=change.get('urgency', 'NORMAL'),
            affected_systems=change.get('affected_systems')
        )
        
        # Context7 Pattern: Rate limiting for bulk operations
        await asyncio.sleep(0.1)  # Prevent overwhelming clients 