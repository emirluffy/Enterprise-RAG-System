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
        sa_column=Column(UUID(as_uuid=False), primary_key=True)
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
    queries: List["QueryLog"] = Relationship(back_populates="source_documents")

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
        sa_column=Column(UUID(as_uuid=False), primary_key=True)
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

class QueryLogBase(SQLModel):
    """Base query model"""
    query_text: str = Field(sa_column=Column(Text))
    user_session: Optional[str] = Field(max_length=255)  # Session tracking
    department: Optional[str] = Field(max_length=100, index=True)

class QueryLog(QueryLogBase, table=True):
    """Log of all user queries for analytics"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(UUID(as_uuid=False), primary_key=True)
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
    source_documents: List[Document] = Relationship(back_populates="queries")

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

# User Management Models (Basic for MVP)

class UserBase(SQLModel):
    """Base user model"""
    email: str = Field(unique=True, index=True, max_length=255)
    full_name: str = Field(max_length=255)
    department: Optional[str] = Field(max_length=100, index=True)
    role: str = Field(default="user", max_length=50)  # user, admin, super_admin
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    """User table"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column(UUID(as_uuid=False), primary_key=True)
    )
    
    # Authentication
    hashed_password: str = Field(max_length=255)
    
    # Profile
    avatar_url: Optional[str] = Field(max_length=500)
    preferences: Optional[dict] = Field(default={}, sa_column=Column(JSON))
    
    # Usage analytics
    last_login: Optional[datetime] = Field(sa_column=Column(DateTime))
    total_queries: int = Field(default=0)
    
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
    created_at: datetime
    last_login: Optional[datetime]
    total_queries: int

class UsersPublic(SQLModel):
    """For listing users"""
    data: List[UserRead]
    count: int

class UserUpdate(UserBase):
    """For updating user data"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    password: Optional[str] = None

class UserUpdateMe(SQLModel):
    """For users updating their own profile"""
    full_name: Optional[str] = None
    email: Optional[str] = None

class UserPublic(UserBase):
    """Public user data (same as UserRead but different name for compatibility)"""
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    total_queries: int = 0

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
