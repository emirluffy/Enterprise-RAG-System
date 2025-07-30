"""
Enterprise RAG System - Authentication API Routes (Context7 Verified)
JWT-based authentication endpoints with comprehensive error handling

Features:
- User login with JWT token generation
- User registration with validation
- Token refresh functionality
- Password management
- Profile management
"""
from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, Field, SQLModel
from datetime import datetime

from app.core.db import get_session
from app.services.auth_service import auth_service
from app.models import (
    User, UserCreate, UserRegister, UserRead, UserPublic, UserUpdate, UserUpdateMe,
    UserPreferences, UserPreferencesUpdate,
    Token, TokenPayload, NewPassword, UpdatePassword, Message
)

# Remove duplicate prefix - it's already added in main.py
router = APIRouter(tags=["Authentication"])

# Context7 verified: FastAPI security scheme
security = HTTPBearer()

# Request/Response Models (Context7 verified)
class LoginRequest(SQLModel):
    """Login request model"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

class RefreshTokenRequest(SQLModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Valid refresh token")

class AuthResponse(SQLModel):
    """Authentication response with tokens and user data"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublic

# Context7 verified: Dependency for getting current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: Bearer token from Authorization header
        session: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Extract token from credentials
    token = credentials.credentials
    
    # Verify token
    payload = auth_service.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = auth_service.get_user_by_id(user_id, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated"
        )
    
    return user

# Optional dependency for current user (doesn't fail if no auth)
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """Get current user but don't fail if not authenticated"""
    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None

# Authentication Endpoints

@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    session: Session = Depends(get_session)
) -> AuthResponse:
    """
    User login endpoint
    
    Args:
        login_data: Email and password
        session: Database session
        
    Returns:
        Access token, refresh token, and user data
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Authenticate user
    user = auth_service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
        session=session
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_service.create_refresh_token(
        data={"sub": str(user.id), "type": "refresh"}
    )
    
    # Return response
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserPublic(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            total_queries=user.total_queries
        )
    )

@router.post("/register", response_model=AuthResponse)
async def register(
    user_data: UserRegister,
    session: Session = Depends(get_session)
) -> AuthResponse:
    """
    User registration endpoint
    
    Args:
        user_data: Registration data (email, password, full_name)
        session: Database session
        
    Returns:
        Access token, refresh token, and user data
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    # Validate password length
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Create user
    user = auth_service.register_user(user_data, session)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_service.create_refresh_token(
        data={"sub": str(user.id), "type": "refresh"}
    )
    
    # Return response
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserPublic(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            total_queries=user.total_queries
        )
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: Session = Depends(get_session)
) -> Token:
    """
    Refresh access token using refresh token
    
    Args:
        refresh_data: Refresh token
        session: Database session
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    payload = auth_service.verify_token(refresh_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    user = auth_service.get_user_by_id(user_id, session)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserPublic)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserPublic:
    """
    Get current user profile
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Current user profile data
    """
    return UserPublic(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        department=current_user.department,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        total_queries=current_user.total_queries
    )

@router.patch("/me", response_model=UserPublic)
async def update_current_user_profile(
    user_update: UserUpdateMe,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> UserPublic:
    """
    Update current user profile
    
    Args:
        user_update: Updated profile data
        current_user: Authenticated user
        session: Database session
        
    Returns:
        Updated user profile
    """
    # Update fields that are provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_user = auth_service.get_user_by_email(user_update.email, session)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    # Update timestamp
    current_user.updated_at = datetime.utcnow()
    
    # Save changes
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return UserPublic(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        department=current_user.department,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        total_queries=current_user.total_queries
    )

@router.post("/change-password", response_model=Message)
async def change_password(
    password_data: UpdatePassword,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Message:
    """
    Change user password
    
    Args:
        password_data: Current and new password
        current_user: Authenticated user
        session: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Update password
    success = auth_service.update_user_password(
        user_id=str(current_user.id),
        new_password=password_data.new_password,
        session=session
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return Message(message="Password updated successfully")

# User Profile & Preferences Management Endpoints (Context7 Verified)

@router.get("/me", response_model=UserPublic)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserPublic:
    """
    Get current user's profile information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile data
    """
    return UserPublic(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        department=current_user.department,
        role=current_user.role,
        is_active=current_user.is_active,
        bio=current_user.bio,
        avatar_url=current_user.avatar_url,
        preferences=current_user.preferences,
        workspace_id=current_user.workspace_id,
        total_queries=current_user.total_queries,
        total_documents_uploaded=current_user.total_documents_uploaded,
        total_conversations=current_user.total_conversations,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.put("/me", response_model=UserPublic)
async def update_current_user_profile(
    user_update: UserUpdateMe,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> UserPublic:
    """
    Update current user's profile information
    
    Args:
        user_update: User profile update data
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Updated user profile data
    """
    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    # Update timestamp
    current_user.updated_at = datetime.utcnow()
    
    # Save changes
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return UserPublic(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        department=current_user.department,
        role=current_user.role,
        is_active=current_user.is_active,
        bio=current_user.bio,
        avatar_url=current_user.avatar_url,
        preferences=current_user.preferences,
        workspace_id=current_user.workspace_id,
        total_queries=current_user.total_queries,
        total_documents_uploaded=current_user.total_documents_uploaded,
        total_conversations=current_user.total_conversations,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.get("/me/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_user)
) -> UserPreferences:
    """
    Get current user's preferences
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User preferences
    """
    if current_user.preferences:
        return UserPreferences(**current_user.preferences)
    else:
        # Return default preferences if none set
        return UserPreferences()

@router.put("/me/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> UserPreferences:
    """
    Update current user's preferences
    
    Args:
        preferences_update: User preferences update data
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Updated user preferences
    """
    # Get current preferences or create default
    current_prefs = UserPreferences(**current_user.preferences) if current_user.preferences else UserPreferences()
    
    # Update preferences
    update_data = preferences_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_prefs, field, value)
    
    # Save updated preferences
    current_user.preferences = current_prefs.model_dump()
    current_user.updated_at = datetime.utcnow()
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_prefs

@router.post("/me/preferences/reset", response_model=UserPreferences)
async def reset_user_preferences(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> UserPreferences:
    """
    Reset user preferences to defaults
    
    Args:
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Default user preferences
    """
    # Reset to default preferences
    default_prefs = UserPreferences()
    current_user.preferences = default_prefs.model_dump()
    current_user.updated_at = datetime.utcnow()
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return default_prefs

@router.get("/me/workspace")
async def get_user_workspace_info(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get user workspace information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Workspace information
    """
    preferences = UserPreferences(**current_user.preferences) if current_user.preferences else UserPreferences()
    
    return {
        "workspace_id": current_user.workspace_id,
        "workspace_name": preferences.workspace_name,
        "user_id": str(current_user.id),
        "total_documents": current_user.total_documents_uploaded,
        "total_conversations": current_user.total_conversations,
        "total_queries": current_user.total_queries,
        "member_since": current_user.created_at,
        "last_activity": current_user.last_login
    }

@router.get("/health")
async def auth_health_check():
    """Authentication service health check"""
    return {
        "service": "authentication",
        "status": "healthy",
        "features": [
            "JWT token authentication",
            "User registration and login",
            "Password management",
            "Profile management",
            "User preferences",
            "Personal workspaces",
            "Token refresh"
        ]
    } 