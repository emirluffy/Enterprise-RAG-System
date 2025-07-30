"""
Enterprise RAG System - Authentication Service (Context7 Verified)
JWT token creation, verification, password hashing with python-jose patterns

Context7 verified implementation using:
- python-jose for JWT operations
- passlib for password hashing
- FastAPI security patterns
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User, UserCreate, UserRegister
from app.core.db import get_session

# Context7 verified: Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Context7 verified: JWT Configuration
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthenticationService:
    """Context7 verified authentication service with JWT and password management"""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        
    # Context7 verified: Password hashing methods
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password for storage"""
        return self.pwd_context.hash(password)
    
    # Context7 verified: JWT token methods using python-jose
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token using Context7 verified python-jose patterns
        
        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            
        # Context7 verified: Standard JWT claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        # Context7 verified: JWT encoding with HS256
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode JWT token using Context7 verified patterns
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            # Context7 verified: JWT decoding with algorithm verification
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != "access":
                return None
                
            return payload
            
        except JWTError:
            return None
    
    def create_refresh_token(self, data: dict) -> str:
        """Create refresh token with longer expiration"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    # Context7 verified: User authentication methods
    def authenticate_user(self, email: str, password: str, session: Session) -> Optional[User]:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: Plain text password
            session: Database session
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Get user by email
        query = select(User).where(User.email == email)
        user = session.exec(query).first()
        
        if not user:
            return None
            
        if not user.is_active:
            return None
            
        # Verify password
        if not self.verify_password(password, user.hashed_password):
            return None
            
        # Update last login
        user.last_login = datetime.utcnow()
        session.add(user)
        session.commit()
        
        return user
    
    def create_user(self, user_data: UserCreate, session: Session) -> Optional[User]:
        """
        Create new user with hashed password
        
        Args:
            user_data: User creation data
            session: Database session
            
        Returns:
            Created User object or None if email exists
        """
        # Check if user already exists
        existing_query = select(User).where(User.email == user_data.email)
        existing_user = session.exec(existing_query).first()
        
        if existing_user:
            return None
            
        # Hash password and create user
        hashed_password = self.get_password_hash(user_data.password)
        
        db_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            department=user_data.department,
            role=user_data.role,
            is_active=user_data.is_active,
            hashed_password=hashed_password,
            avatar_url=None,
            last_login=None
        )
        
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        
        return db_user
    
    def register_user(self, user_data: UserRegister, session: Session) -> Optional[User]:
        """
        Register new user (simplified version of create_user)
        
        Args:
            user_data: User registration data
            session: Database session
            
        Returns:
            Created User object or None if email exists
        """
        # Check if user already exists
        existing_query = select(User).where(User.email == user_data.email)
        existing_user = session.exec(existing_query).first()
        
        if existing_user:
            return None
            
        # Hash password and create user
        hashed_password = self.get_password_hash(user_data.password)
        
        db_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role="user",  # Default role for registration
            is_active=True,
            department=None,
            avatar_url=None,
            last_login=None
        )
        
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        
        return db_user
    
    def get_user_by_id(self, user_id: str, session: Session) -> Optional[User]:
        """Get user by ID"""
        query = select(User).where(User.id == user_id)
        return session.exec(query).first()
    
    def get_user_by_email(self, email: str, session: Session) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        return session.exec(query).first()
    
    def update_user_password(self, user_id: str, new_password: str, session: Session) -> bool:
        """Update user password"""
        user = self.get_user_by_id(user_id, session)
        if not user:
            return False
            
        user.hashed_password = self.get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        session.add(user)
        session.commit()
        
        return True
    
    def deactivate_user(self, user_id: str, session: Session) -> bool:
        """Deactivate user account"""
        user = self.get_user_by_id(user_id, session)
        if not user:
            return False
            
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        session.add(user)
        session.commit()
        
        return True

# Global service instance
auth_service = AuthenticationService() 