"""
Enterprise RAG System - Database Models
Based on PRD requirements and user personas
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, String, Text, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
import os
from sqlalchemy.types import TypeDecorator, CHAR
from operator import attrgetter

# Context7-verified GUID TypeDecorator for SQLite UUID compatibility
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses CHAR(36), storing as stringified uuid values with hyphens.
    Context7 verified pattern for SQLite compatibility.
    """
    impl = CHAR
    cache_ok = True
    
    _default_type = CHAR(36)
    _uuid_as_str = str  # Store with hyphens for readability
    
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(self._default_type)
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif not isinstance(value, uuid.UUID):
            return str(uuid.UUID(value))
        else:
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value

# Query-Document Link Table (Context7: Must be defined first)
class QueryDocumentLink(SQLModel, table=True):
    """Context7-verified link table for many-to-many QueryLog <-> Document relationship"""
    query_id: Optional[str] = Field(default=None, foreign_key="querylog.id", primary_key=True)
    document_id: Optional[str] = Field(default=None, foreign_key="document.id", primary_key=True)
    relevance_score: Optional[float] = Field(default=0.0)  # How relevant this doc was to the query

# Document Management Models

class DocumentBase(SQLModel):
    """Base document model with shared fields"""
    title: str = Field(max_length=255, index=True)
    filename: str = Field(max_length=255)
    file_type: str = Field(max_length=10)  # pdf, docx, txt, etc.
    file_size: int  # in bytes
    content_preview: Optional[str] = Field(max_length=500)  # First few lines
    upload_status: str = Field(default="processing")  # processing, completed, failed
    is_active: bool = Field(default=True)

class Document(DocumentBase, table=True):
    """Main document table"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(GUID(), primary_key=True)
    )
    
    # Content and processing
    full_text: Optional[str] = Field(sa_column=Column(Text))
    doc_metadata: Optional[dict] = Field(default={}, sa_column=Column(JSON))
    
    # File storage
    file_path: str  # Storage path for original file
    processed_at: Optional[datetime] = Field(sa_column=Column(DateTime))
    
    # User tracking
    uploaded_by: Optional[str] = Field(foreign_key="user.id")
    department: Optional[str] = Field(max_length=100, index=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    
    # Relationships
    chunks: List["DocumentChunk"] = Relationship(back_populates="document")
    queries: List["QueryLog"] = Relationship(back_populates="source_documents", link_model=QueryDocumentLink)
    versions: List["DocumentVersion"] = Relationship(back_populates="document")

class DocumentCreate(DocumentBase):
    """For creating new documents"""
    pass

class DocumentRead(DocumentBase):
    """For reading documents (public view)"""
    id: str
    created_at: datetime
    updated_at: datetime
    chunk_count: Optional[int] = 0

# Text Chunking Models

class DocumentChunkBase(SQLModel):
    """Base chunk model"""
    content: str = Field(sa_column=Column(Text))
    chunk_index: int  # Order within document
    start_char: Optional[int] = 0  # Character position in original document
    end_char: Optional[int] = 0
    token_count: Optional[int] = 0

class DocumentChunk(DocumentChunkBase, table=True):
    """Text chunks from documents for RAG processing"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(GUID(), primary_key=True)
    )
    
    # Document relationship
    document_id: str = Field(foreign_key="document.id", index=True)
    document: Optional[Document] = Relationship(back_populates="chunks")
    
    # Vector embedding (stored as JSON for now)
    embedding: Optional[dict] = Field(default={}, sa_column=Column(JSON))
    embedding_model: Optional[str] = Field(max_length=100)  # Model used for embedding
    
    # Metadata
    chunk_metadata: Optional[dict] = Field(default={}, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))

class DocumentChunkRead(DocumentChunkBase):
    """For reading chunks"""
    id: str
    document_id: str
    created_at: datetime

# Query and Response Models

# Conversation Models (Context7 verified Multi-Turn Chat Support)
class ConversationBase(SQLModel):
    """Base conversation model for multi-turn chat"""
    title: Optional[str] = Field(max_length=255, index=True)  # Auto-generated or user-set
    session_id: Optional[str] = Field(max_length=255, index=True)  # Browser session
    user_id: Optional[str] = Field(foreign_key="user.id")  # Optional user tracking
    language: str = Field(default="tr", max_length=5)  # "tr", "en" for Turkish/English
    status: str = Field(default="active", max_length=20)  # "active", "archived", "deleted"

class Conversation(ConversationBase, table=True):
    """Conversation table for multi-turn chat history"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(GUID(), primary_key=True)
    )
    
    # Conversation metadata
    message_count: int = Field(default=0)
    last_activity: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    
    # Context management
    context_window: int = Field(default=10)  # Max messages to keep in context
    summary: Optional[str] = Field(sa_column=Column(Text))  # AI-generated conversation summary
    
    # User experience
    user_rating: Optional[int] = Field(default=None, ge=1, le=5)  # User satisfaction rating
    user_feedback: Optional[str] = Field(sa_column=Column(Text))  # User feedback
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    
    # Relationships
    messages: List["ConversationMessage"] = Relationship(back_populates="conversation")
    queries: List["QueryLog"] = Relationship(back_populates="conversation")

class ConversationMessage(SQLModel, table=True):
    """Individual messages within a conversation"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(GUID(), primary_key=True)
    )
    
    # Message content
    conversation_id: str = Field(foreign_key="conversation.id", index=True)
    message_type: str = Field(max_length=20)  # "user", "assistant", "system", "notification"
    content: str = Field(sa_column=Column(Text))
    
    # Message metadata
    message_order: int = Field(index=True)  # Order within conversation
    tokens_used: Optional[int] = Field(default=0)  # Token count for AI messages
    model_used: Optional[str] = Field(max_length=100)  # AI model for assistant messages
    
    # Response metadata (for assistant messages)
    response_time_ms: Optional[int] = Field(default=0)
    confidence_score: Optional[float] = Field(default=0.0)
    sources_used: Optional[List[str]] = Field(default=[], sa_column=Column(JSON))
    
    # File attachments (for user messages)
    attachments: Optional[List[dict]] = Field(default=[], sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    
    # Relationships
    conversation: Optional[Conversation] = Relationship(back_populates="messages")

# API Models for Conversations
class ConversationCreate(SQLModel):
    """API model for creating new conversations"""
    title: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    language: str = "tr"

class ConversationRead(ConversationBase):
    """API model for reading conversations"""
    id: str
    message_count: int
    last_activity: datetime
    created_at: datetime
    updated_at: datetime

class ConversationUpdate(SQLModel):
    """API model for updating conversations"""
    title: Optional[str] = None
    status: Optional[str] = None
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None

class ConversationMessageCreate(SQLModel):
    """API model for creating conversation messages"""
    conversation_id: str
    message_type: str
    content: str
    attachments: Optional[List[dict]] = []

class ConversationMessageRead(SQLModel):
    """API model for reading conversation messages"""
    id: str
    conversation_id: str
    message_type: str
    content: str
    message_order: int
    response_time_ms: Optional[int] = 0
    confidence_score: Optional[float] = 0.0
    sources_used: Optional[List[str]] = []
    attachments: Optional[List[dict]] = []
    created_at: datetime

class QueryLogBase(SQLModel):
    """Base query model"""
    query_text: str = Field(sa_column=Column(Text))
    user_session: Optional[str] = Field(max_length=255)  # Session tracking
    department: Optional[str] = Field(max_length=100, index=True)
    # Add conversation support
    conversation_id: Optional[str] = Field(foreign_key="conversation.id", index=True)

class QueryLog(QueryLogBase, table=True):
    """Log of all user queries for analytics"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(GUID(), primary_key=True)
    )
    
    # User tracking
    user_id: Optional[str] = Field(foreign_key="user.id")
    user_ip: Optional[str] = Field(max_length=45)  # IPv6 support
    
    # Response details
    response_text: Optional[str] = Field(sa_column=Column(Text))
    model_used: Optional[str] = Field(max_length=100)  # AI model identifier
    response_time_ms: Optional[int] = 0  # Response time in milliseconds
    
    # Retrieved context
    retrieved_chunks: Optional[List[str]] = Field(default=[], sa_column=Column(JSON))
    confidence_score: Optional[float] = 0.0
    
    # User feedback
    user_rating: Optional[int] = Field(default=None, ge=1, le=5)  # 1-5 star rating
    user_feedback: Optional[str] = Field(sa_column=Column(Text))
    
    # Analytics
    status: str = Field(default="completed")  # completed, failed, timeout
    error_message: Optional[str] = Field(sa_column=Column(Text))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    
    # Relationships  
    source_documents: List["Document"] = Relationship(back_populates="queries", link_model=QueryDocumentLink)
    conversation: Optional[Conversation] = Relationship(back_populates="queries")

class QueryRequest(SQLModel):
    """API request model for queries"""
    question: str = Field(min_length=1, max_length=500)
    max_tokens: Optional[int] = Field(default=1000, ge=50, le=2000)
    temperature: Optional[float] = Field(default=0.3, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    session_id: Optional[str] = None

class QueryResponse(SQLModel):
    """API response model for queries"""
    answer: str
    sources: List[DocumentRead] = []
    confidence: float = 0.0
    response_time_ms: int
    model_used: str
    query_id: str

# Dynamic Learning Models (Context7-verified)

class LearnedKnowledgeBase(SQLModel):
    """Context7-verified base model for dynamic learning"""
    content: str = Field(sa_column=Column(Text))
    knowledge_type: str = Field(max_length=50)  # "announcement", "policy_update", "procedure_change", "duyuru", "güncelleme"
    title: str = Field(max_length=255, index=True)
    summary: Optional[str] = Field(max_length=500)  # Brief summary for quick reference
    keywords: Optional[List[str]] = Field(default=[], sa_column=Column(JSON))  # For better searchability
    priority: str = Field(default="normal", max_length=20)  # "urgent", "normal", "low"
    language: str = Field(default="tr", max_length=5)  # "tr", "en" for Turkish/English content

class LearnedKnowledge(LearnedKnowledgeBase, table=True):
    """Context7-verified dynamic knowledge storage for real-time learning"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(GUID(), primary_key=True)
    )
    
    # Source tracking (Context7 pattern)
    source_type: str = Field(max_length=50)  # "chat_input", "announcement", "manual_entry", "api_update"
    source_reference: Optional[str] = Field(max_length=255)  # Original source identifier
    learned_from_query: Optional[str] = Field(foreign_key="querylog.id")  # If learned from a chat interaction
    
    # Vector embedding for hybrid search (Context7-verified pattern)
    embedding: Optional[dict] = Field(default={}, sa_column=Column(JSON))
    embedding_model: Optional[str] = Field(max_length=100, default="all-MiniLM-L6-v2")
    
    # Content validation and versioning
    is_verified: bool = Field(default=False)  # Admin verification status
    verified_by: Optional[str] = Field(foreign_key="user.id")
    verified_at: Optional[datetime] = Field(sa_column=Column(DateTime))
    confidence_score: Optional[float] = Field(default=0.8, ge=0.0, le=1.0)  # System confidence in this knowledge
    
    # Usage analytics (Context7 pattern)
    access_count: int = Field(default=0)  # Track how often this knowledge is accessed
    usefulness_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)  # User feedback based
    last_accessed: Optional[datetime] = Field(sa_column=Column(DateTime))
    
    # Lifecycle management (Context7-verified pattern)
    status: str = Field(default="active", max_length=20)  # "active", "superseded", "deprecated", "pending_review"
    superseded_by: Optional[str] = Field(foreign_key="learnedknowledge.id")  # Points to newer version
    expires_at: Optional[datetime] = Field(sa_column=Column(DateTime))  # For time-sensitive information
    
    # User and session tracking
    created_by: Optional[str] = Field(foreign_key="user.id")
    session_id: Optional[str] = Field(max_length=255)  # Chat session where this was learned
    department: Optional[str] = Field(max_length=100, index=True)  # Relevant department
    
    # Timestamps (Context7 standard)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))

class LearnedKnowledgeCreate(LearnedKnowledgeBase):
    """API model for creating new learned knowledge"""
    source_type: str = "chat_input"
    created_by: Optional[str] = None
    session_id: Optional[str] = None

class LearnedKnowledgeRead(LearnedKnowledgeBase):
    """API model for reading learned knowledge"""
    id: str
    source_type: str
    is_verified: bool
    confidence_score: float
    access_count: int
    status: str
    created_at: datetime
    created_by: Optional[str] = None

class LearnRequest(SQLModel):
    """Context7-verified API request for learning new information"""
    content: str = Field(min_length=5, max_length=2000)
    title: Optional[str] = Field(max_length=255)
    knowledge_type: str = Field(default="announcement")
    priority: str = Field(default="normal")
    session_id: Optional[str] = None

class LearnResponse(SQLModel):
    """Context7-verified API response for learning operations"""
    success: bool
    message: str
    learned_knowledge_id: Optional[str] = None
    confidence_score: float
    knowledge_integrated: bool = False  # Whether immediately available for queries

# User Preferences Models (Context7 Verified)

class UserPreferences(SQLModel):
    """User preferences data model"""
    # UI Preferences
    theme: str = Field(default="twilight-dream", max_length=50)  # theme selection
    language: str = Field(default="tr", max_length=10)  # Turkish by default
    sidebar_collapsed: bool = Field(default=False)
    
    # AI Preferences  
    default_ai_model: str = Field(default="gemini-2.5-flash-lite", max_length=100)
    response_style: str = Field(default="detailed", max_length=50)  # detailed, concise, technical
    enable_ai_enhancement: bool = Field(default=True)
    
    # Workspace Preferences
    workspace_name: str = Field(default="Kişisel Çalışma Alanı", max_length=255)
    default_department_filter: Optional[str] = Field(default=None, max_length=100)
    auto_save_conversations: bool = Field(default=True)
    
    # Notification Preferences
    enable_notifications: bool = Field(default=True)
    email_notifications: bool = Field(default=False)
    document_upload_notifications: bool = Field(default=True)

# User Management Models (Enhanced for Personalization)

class UserBase(SQLModel):
    """Base user model"""
    email: str = Field(unique=True, index=True, max_length=255)
    full_name: str = Field(max_length=255)
    department: Optional[str] = Field(max_length=100, index=True)
    role: str = Field(default="user", max_length=50)  # user, admin, super_admin
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    """Enhanced User table with personalization"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(GUID(), primary_key=True)
    )
    
    # Authentication
    hashed_password: str = Field(max_length=255)
    
    # Profile & Personalization
    avatar_url: Optional[str] = Field(max_length=500)
    bio: Optional[str] = Field(max_length=1000)
    preferences: Optional[dict] = Field(default_factory=lambda: UserPreferences().model_dump(), sa_column=Column(JSON))
    
    # Workspace & Activity
    workspace_id: Optional[str] = Field(default=None, max_length=255)  # For future workspace groups
    last_login: Optional[datetime] = Field(sa_column=Column(DateTime))
    total_queries: int = Field(default=0)
    total_documents_uploaded: int = Field(default=0)
    total_conversations: int = Field(default=0)
    
    # Usage Analytics
    favorite_topics: Optional[List[str]] = Field(default=[], sa_column=Column(JSON))
    recent_searches: Optional[List[str]] = Field(default=[], sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))

class UserCreate(UserBase):
    """For user creation"""
    password: str = Field(min_length=8)

class UserRegister(SQLModel):
    """For user registration"""
    email: str
    password: str = Field(min_length=8)
    full_name: str

class UserRead(UserBase):
    """For reading user data (no password)"""
    id: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None
    workspace_id: Optional[str] = None
    total_queries: int = 0
    total_documents_uploaded: int = 0
    total_conversations: int = 0
    favorite_topics: Optional[List[str]] = None
    recent_searches: Optional[List[str]] = None
    created_at: datetime
    last_login: Optional[datetime] = None

class UsersPublic(SQLModel):
    """For listing users"""
    data: List[UserRead]
    count: int

class UserUpdate(UserBase):
    """For updating user data (admin only)"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserUpdateMe(SQLModel):
    """For users updating their own profile"""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None

class UserPreferencesUpdate(SQLModel):
    """For updating user preferences"""
    theme: Optional[str] = None
    language: Optional[str] = None
    sidebar_collapsed: Optional[bool] = None
    default_ai_model: Optional[str] = None
    response_style: Optional[str] = None
    enable_ai_enhancement: Optional[bool] = None
    workspace_name: Optional[str] = None
    default_department_filter: Optional[str] = None
    auto_save_conversations: Optional[bool] = None
    enable_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    document_upload_notifications: Optional[bool] = None

class UserPublic(UserBase):
    """Public user data (enhanced for personalization)"""
    id: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None
    workspace_id: Optional[str] = None
    total_queries: int = 0
    total_documents_uploaded: int = 0
    total_conversations: int = 0
    created_at: datetime
    last_login: Optional[datetime] = None

class NewPassword(SQLModel):
    """For password reset functionality"""
    token: str
    new_password: str = Field(min_length=8)

class UpdatePassword(SQLModel):
    """For updating user password"""
    current_password: str
    new_password: str = Field(min_length=8)

class TokenPayload(SQLModel):
    """JWT token payload"""
    sub: Optional[str] = None

class Token(SQLModel):
    """Authentication token"""
    access_token: str
    token_type: str = "bearer"

class Message(SQLModel):
    """Generic message response"""
    message: str

# System Configuration Models

class SystemConfig(SQLModel, table=True):
    """System configuration and settings"""
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, max_length=100)
    value: str = Field(sa_column=Column(Text))
    description: Optional[str] = Field(max_length=500)
    is_public: bool = Field(default=False)  # Can be read by frontend
    
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))

# Analytics Models (for PRD metrics)

class DailyMetrics(SQLModel, table=True):
    """Daily aggregated metrics for dashboard"""
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(sa_column=Column(DateTime, index=True))
    
    # User metrics
    active_users: int = Field(default=0)
    new_users: int = Field(default=0)
    total_queries: int = Field(default=0)
    avg_session_duration: Optional[float] = 0.0
    
    # System metrics
    avg_response_time: Optional[float] = 0.0
    error_rate: Optional[float] = 0.0
    successful_queries: int = Field(default=0)
    failed_queries: int = Field(default=0)
    
    # Document metrics
    documents_uploaded: int = Field(default=0)
    total_documents: int = Field(default=0)
    
    # AI metrics
    gemini_requests: int = Field(default=0)
    gemini_tokens: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))

class DocumentVersion(SQLModel, table=True):
    """Context7-verified document versioning model"""
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    document_id: str = Field(foreign_key="document.id", index=True)
    version_number: int = Field(default=1)
    change_type: str  # CREATE, UPDATE, DEPRECATE, SUPERSEDE
    change_summary: Optional[str] = None
    is_current: bool = Field(default=True)
    superseded_by: Optional[str] = None
    
    # Context7 pattern: Change tracking with business context
    change_reason: Optional[str] = None  # "Policy Update", "Process Change", etc.
    effective_date: Optional[datetime] = None  # When change becomes effective
    notification_sent: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    # Relationships
    document: Optional[Document] = Relationship(back_populates="versions")

class DocumentChangeNotification(SQLModel, table=True):
    """Context7-verified change notification tracking"""
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    document_id: str = Field(foreign_key="document.id", index=True)
    notification_type: str  # URGENT, NORMAL, INFO
    change_description: str
    affected_systems: Optional[str] = None  # JSON string of systems
    
    # Context7 pattern: Real-time notification state
    status: str = Field(default="PENDING")  # PENDING, SENT, ACKNOWLEDGED
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None  # JSON string of user IDs
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class DocumentUpdateJob(SQLModel, table=True):
    """Context7-verified background job tracking for updates"""
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    document_id: str = Field(foreign_key="document.id", index=True)
    job_type: str  # AUTO_UPDATE, MANUAL_REVIEW, BULK_IMPORT
    
    # Context7 pattern: Dask-compatible job state
    status: str = Field(default="QUEUED")  # QUEUED, PROCESSING, COMPLETED, FAILED
    progress_percentage: int = Field(default=0)
    error_message: Optional[str] = None
    
    # Context7 pattern: Update metadata
    source_type: str  # EMAIL, API, MANUAL, SCHEDULED
    source_data: Optional[str] = None  # JSON string
    update_summary: Optional[str] = None
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
