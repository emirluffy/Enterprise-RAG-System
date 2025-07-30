"""
Enterprise RAG System - Conversation Management API
Multi-turn chat support with conversation history and context management
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, select, desc, func, and_
import uuid
import json

from app.core.db import get_session
from app.models import (
    Conversation, ConversationCreate, ConversationRead, ConversationUpdate,
    ConversationMessage, ConversationMessageCreate, ConversationMessageRead,
    QueryLog
)
from app.services.chat_title_service import chat_title_service

router = APIRouter()

# Request/Response Models
class ConversationResponse(BaseModel):
    """Enhanced conversation response with message preview"""
    id: str
    title: Optional[str] = None
    session_id: Optional[str] = None
    message_count: int
    last_activity: datetime
    created_at: datetime
    last_message_preview: Optional[str] = None  # First 100 chars of last message
    status: str = "active"

class ConversationListResponse(BaseModel):
    """Response for listing conversations"""
    conversations: List[ConversationResponse]
    total_count: int
    page: int
    per_page: int

class ConversationHistoryResponse(BaseModel):
    """Full conversation history with all messages"""
    conversation: ConversationResponse
    messages: List[ConversationMessageRead]
    context_summary: Optional[str] = None

class ConversationContextRequest(BaseModel):
    """Request for getting conversation context"""
    conversation_id: str
    max_messages: int = Field(default=10, ge=1, le=50)
    include_sources: bool = Field(default=True)

class ConversationContextResponse(BaseModel):
    """Response with conversation context for AI processing"""
    conversation_id: str
    context_messages: List[Dict[str, Any]]
    message_count: int
    context_summary: Optional[str] = None

# Conversation Management Endpoints

@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    session: Session = Depends(get_session)
):
    """Create a new conversation"""
    try:
        # Auto-generate title if not provided
        title = request.title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        conversation = Conversation(
            title=title,
            session_id=request.session_id,
            user_id=request.user_id,
            language=request.language,
            status="active"
        )
        
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            session_id=conversation.session_id,
            message_count=conversation.message_count,
            last_activity=conversation.last_activity,
            created_at=conversation.created_at,
            status=conversation.status
        )
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )

@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    session: Session = Depends(get_session)
):
    """List conversations with pagination"""
    try:
        # Build query with filters
        query = select(Conversation).where(Conversation.status == "active")
        
        if session_id:
            query = query.where(Conversation.session_id == session_id)
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        
        # Count total conversations
        count_query = select(func.count(Conversation.id)).where(Conversation.status == "active")
        if session_id:
            count_query = count_query.where(Conversation.session_id == session_id)
        if user_id:
            count_query = count_query.where(Conversation.user_id == user_id)
            
        total_count = session.exec(count_query).first() or 0
        
        # Apply pagination and ordering
        query = query.order_by(desc(Conversation.last_activity))
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        conversations = session.exec(query).all()
        
        # Build response with message preview
        conversation_responses = []
        for conv in conversations:
            # Get last message preview
            last_message_query = select(ConversationMessage).where(
                ConversationMessage.conversation_id == str(conv.id)
            ).order_by(desc(ConversationMessage.message_order)).limit(1)
            
            last_message = session.exec(last_message_query).first()
            preview = None
            if last_message:
                preview = last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content
            
            conversation_responses.append(ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                session_id=conv.session_id,
                message_count=conv.message_count,
                last_activity=conv.last_activity,
                created_at=conv.created_at,
                last_message_preview=preview,
                status=conv.status
            ))
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total_count=total_count,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )

@router.get("/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    session: Session = Depends(get_session)
):
    """Get full conversation history with all messages"""
    try:
        # Get conversation
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get all messages
        messages_query = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.message_order)
        
        messages = session.exec(messages_query).all()
        
        # Build response
        conversation_response = ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            session_id=conversation.session_id,
            message_count=conversation.message_count,
            last_activity=conversation.last_activity,
            created_at=conversation.created_at,
            status=conversation.status
        )
        
        message_responses = [
            ConversationMessageRead(
                id=str(msg.id),
                conversation_id=str(msg.conversation_id),
                message_type=msg.message_type,
                content=msg.content,
                message_order=msg.message_order,
                response_time_ms=msg.response_time_ms or 0,
                confidence_score=msg.confidence_score or 0.0,
                sources_used=msg.sources_used or [],
                attachments=msg.attachments or [],
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
        return ConversationHistoryResponse(
            conversation=conversation_response,
            messages=message_responses,
            context_summary=conversation.summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )

@router.post("/{conversation_id}/context", response_model=ConversationContextResponse)
async def get_conversation_context(
    conversation_id: str,
    request: ConversationContextRequest,
    session: Session = Depends(get_session)
):
    """Get conversation context for AI processing"""
    try:
        # Get conversation
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get recent messages (limited by context window)
        messages_query = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(desc(ConversationMessage.message_order)).limit(request.max_messages)
        
        messages = session.exec(messages_query).all()
        messages_list = list(messages)
        messages_list.reverse()  # Reverse to get chronological order
        
        # Build context messages for AI
        context_messages = []
        for msg in messages_list:
            context_msg = {
                "role": "user" if msg.message_type == "user" else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "message_order": msg.message_order
            }
            
            # Add sources for assistant messages
            if msg.message_type == "assistant" and request.include_sources and msg.sources_used:
                context_msg["sources"] = msg.sources_used
            
            # Add attachments for user messages
            if msg.message_type == "user" and msg.attachments:
                context_msg["attachments"] = msg.attachments
            
            context_messages.append(context_msg)
        
        return ConversationContextResponse(
            conversation_id=conversation_id,
            context_messages=context_messages,
            message_count=len(context_messages),
            context_summary=conversation.summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation context: {str(e)}"
        )

@router.post("/{conversation_id}/messages", response_model=ConversationMessageRead)
async def add_message_to_conversation(
    conversation_id: str,
    message: ConversationMessageCreate,
    session: Session = Depends(get_session)
):
    """Add a message to a conversation"""
    try:
        # Get conversation
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get next message order
        max_order_query = select(func.max(ConversationMessage.message_order)).where(
            ConversationMessage.conversation_id == conversation_id
        )
        max_order = session.exec(max_order_query).first() or 0
        
        # Create new message
        new_message = ConversationMessage(
            conversation_id=conversation_id,
            message_type=message.message_type,
            content=message.content,
            message_order=max_order + 1,
            attachments=message.attachments or [],
            model_used=None,  # Will be set later for assistant messages
            response_time_ms=0,
            confidence_score=0.0,
            sources_used=[]
        )
        
        session.add(new_message)
        
        # Update conversation
        conversation.message_count += 1
        conversation.last_activity = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        
        # Auto-generate title for first user message
        if (message.message_type == "user" and 
            max_order == 0 and 
            (not conversation.title or conversation.title == "Chat")):
            try:
                # Generate intelligent title using ChatTitleService
                generated_title = await chat_title_service.generate_title(
                    first_user_message=message.content
                )
                conversation.title = generated_title
                print(f"🎯 Auto-generated title: '{generated_title}' for conversation {conversation_id}")
            except Exception as title_error:
                print(f"⚠️ Title generation failed: {title_error}")
                # Continue without failing the message creation
        
        session.commit()
        session.refresh(new_message)
        
        return ConversationMessageRead(
            id=str(new_message.id),
            conversation_id=str(new_message.conversation_id),
            message_type=new_message.message_type,
            content=new_message.content,
            message_order=new_message.message_order,
            response_time_ms=new_message.response_time_ms or 0,
            confidence_score=new_message.confidence_score or 0.0,
            sources_used=new_message.sources_used or [],
            attachments=new_message.attachments or [],
            created_at=new_message.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )

@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    session: Session = Depends(get_session)
):
    """Update conversation metadata"""
    try:
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Update fields
        if update_data.title is not None:
            conversation.title = update_data.title
        if update_data.status is not None:
            conversation.status = update_data.status
        if update_data.user_rating is not None:
            conversation.user_rating = update_data.user_rating
        if update_data.user_feedback is not None:
            conversation.user_feedback = update_data.user_feedback
        
        conversation.updated_at = datetime.utcnow()
        
        session.commit()
        session.refresh(conversation)
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            session_id=conversation.session_id,
            message_count=conversation.message_count,
            last_activity=conversation.last_activity,
            created_at=conversation.created_at,
            status=conversation.status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation: {str(e)}"
        )

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    session: Session = Depends(get_session)
):
    """Delete a conversation (soft delete)"""
    try:
        conversation = session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Soft delete
        conversation.status = "deleted"
        conversation.updated_at = datetime.utcnow()
        
        session.commit()
        
        return {"success": True, "message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )

# Utility Functions for Chat Integration
def get_or_create_conversation(
    session_id: str,
    user_id: Optional[str] = None,
    session: Session = None
) -> Optional[Conversation]:
    """Get existing conversation or create new one for session"""
    if not session:
        return None
        
    try:
        # Try to find existing active conversation for this session
        query = select(Conversation).where(
            and_(
                Conversation.session_id == session_id,
                Conversation.status == "active"
            )
        ).order_by(desc(Conversation.last_activity))
        
        existing_conv = session.exec(query).first()
        
        if existing_conv:
            # Check if conversation is recent (within last 4 hours)
            if (datetime.utcnow() - existing_conv.last_activity).total_seconds() < 14400:
                return existing_conv
        
        # Create new conversation
        new_conv = Conversation(
            title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            session_id=session_id,
            user_id=user_id,
            status="active"
        )
        
        session.add(new_conv)
        session.commit()
        session.refresh(new_conv)
        
        return new_conv
        
    except Exception as e:
        print(f"Error in get_or_create_conversation: {e}")
        session.rollback()
        return None

@router.get("/health")
async def conversation_health_check():
    """Health check for conversation system"""
    return {
        "status": "healthy",
        "service": "conversation_management",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "multi_turn_chat",
            "conversation_history",
            "context_management",
            "message_attachments"
        ]
    } 