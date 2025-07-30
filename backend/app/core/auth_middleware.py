"""
Enterprise RAG System - Authentication Middleware (Context7 Verified)
JWT authentication middleware for protecting API routes

Features:
- JWT token validation
- User context injection
- Optional authentication
- Route protection patterns
"""
from typing import Optional, Callable
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from app.services.auth_service import auth_service
from app.models import User
from app.core.db import get_session

# Context7 verified: Security scheme
security = HTTPBearer(auto_error=False)

class AuthenticationMiddleware:
    """Context7 verified authentication middleware for FastAPI"""
    
    def __init__(self):
        self.auth_service = auth_service
    
    async def get_current_user_from_token(self, token: str, session: Session) -> Optional[User]:
        """
        Extract user from JWT token
        
        Args:
            token: JWT token string
            session: Database session
            
        Returns:
            User object or None if token invalid
        """
        # Verify token
        payload = self.auth_service.verify_token(token)
        if payload is None:
            return None
        
        # Extract user ID
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        user = self.auth_service.get_user_by_id(user_id, session)
        if user is None or not user.is_active:
            return None
        
        return user
    
    async def require_auth(self, request: Request) -> User:
        """
        Require authentication - raises HTTPException if not authenticated
        
        Args:
            request: FastAPI request object
            
        Returns:
            Authenticated user
            
        Raises:
            HTTPException: If authentication fails
        """
        # Get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract token
        token = authorization.split(" ")[1]
        
        # Get user
        with next(get_session()) as session:
            user = await self.get_current_user_from_token(token, session)
            
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    async def optional_auth(self, request: Request) -> Optional[User]:
        """
        Optional authentication - returns None if not authenticated
        
        Args:
            request: FastAPI request object
            
        Returns:
            User object or None
        """
        try:
            return await self.require_auth(request)
        except HTTPException:
            return None
    
    def require_role(self, required_roles: list[str]) -> Callable:
        """
        Create a dependency that requires specific roles
        
        Args:
            required_roles: List of required roles (e.g., ["admin", "super_admin"])
            
        Returns:
            FastAPI dependency function
        """
        async def role_dependency(request: Request) -> User:
            user = await self.require_auth(request)
            
            if user.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(required_roles)}"
                )
            
            return user
        
        return role_dependency
    
    def require_admin(self) -> Callable:
        """Require admin role"""
        return self.require_role(["admin", "super_admin"])
    
    def require_super_admin(self) -> Callable:
        """Require super admin role"""
        return self.require_role(["super_admin"])

# Global middleware instance
auth_middleware = AuthenticationMiddleware()

# Context7 verified: Common dependency functions
async def get_current_user_dependency(request: Request) -> User:
    """Dependency for getting current authenticated user"""
    return await auth_middleware.require_auth(request)

async def get_current_user_optional_dependency(request: Request) -> Optional[User]:
    """Dependency for optional authentication"""
    return await auth_middleware.optional_auth(request)

async def require_admin_dependency(request: Request) -> User:
    """Dependency for admin access"""
    return await auth_middleware.require_admin()(request)

async def require_super_admin_dependency(request: Request) -> User:
    """Dependency for super admin access"""
    return await auth_middleware.require_super_admin()(request) 