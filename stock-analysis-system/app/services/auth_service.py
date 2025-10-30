"""
Authentication Service
Handles user authentication, JWT tokens, and password management
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.user import User as UserModel
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.config import settings
from app.database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT token security
security = HTTPBearer()

class AuthService:
    """
    Authentication service for user management and JWT tokens
    """
    
    def __init__(self, db: Session):
        """
        Initialize Auth Service
        
        Args:
            db: Database session
        """
        self.db = db
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a password
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        # Truncate password to 72 bytes for bcrypt compatibility
        password = password[:72]
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Token payload data
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token
        
        Args:
            data: Token payload data
            
        Returns:
            JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            token_type: Expected token type (access or refresh)
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Register a new user
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user information
            
        Raises:
            HTTPException: If user already exists
        """
        # Check if user already exists
        existing_user = self.db.query(UserModel).filter(
            (UserModel.email == user_data.email) | 
            (UserModel.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create new user
        hashed_password = self.get_password_hash(user_data.password)
        user = UserModel(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            role=user_data.role,
            alert_threshold=user_data.alert_threshold,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            alert_threshold=user.alert_threshold,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserModel]:
        """
        Authenticate user with username and password
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User model if authentication successful, None otherwise
        """
        user = self.db.query(UserModel).filter(
            (UserModel.username == username) | (UserModel.email == username)
        ).first()
        
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
    
    def login_user(self, username: str, password: str) -> Dict[str, str]:
        """
        Login user and return tokens
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        user = self.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Create tokens
        access_token = self.create_access_token(data={"sub": user.username})
        refresh_token = self.create_refresh_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def login_user_with_data(self, login_data: UserLogin) -> Token:
        """
        Login user and return JWT tokens
        
        Args:
            login_data: User login credentials
            
        Returns:
            JWT access and refresh tokens
            
        Raises:
            HTTPException: If credentials are invalid
        """
        user = self.authenticate_user(login_data.username, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Create tokens
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.create_refresh_token(
            data={"sub": str(user.id), "username": user.username}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )
    
    def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        payload = self.verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = self.db.query(UserModel).filter(UserModel.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep the same refresh token
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )
    
    def get_current_user(self, token: str) -> UserModel:
        """
        Get current user from JWT token
        
        Args:
            token: JWT access token
            
        Returns:
            Current user model
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        payload = self.verify_token(token, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = self.db.query(UserModel).filter(UserModel.id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[UserModel]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User model if found, None otherwise
        """
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()
    
    def update_user_profile(self, user_id: int, update_data: Dict[str, Any]) -> UserResponse:
        """
        Update user profile
        
        Args:
            user_id: User ID
            update_data: Fields to update
            
        Returns:
            Updated user information
            
        Raises:
            HTTPException: If user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update allowed fields
        if "email" in update_data:
            # Check if email is already taken by another user
            existing_user = self.db.query(UserModel).filter(
                UserModel.email == update_data["email"],
                UserModel.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            user.email = update_data["email"]
        
        if "alert_threshold" in update_data:
            user.alert_threshold = update_data["alert_threshold"]
        
        self.db.commit()
        self.db.refresh(user)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            alert_threshold=user.alert_threshold,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            HTTPException: If old password is incorrect or user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not self.verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        user.password_hash = self.get_password_hash(new_password)
        self.db.commit()
        
        return True


# Dependency functions
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Get authentication service dependency
    
    Args:
        db: Database session
        
    Returns:
        AuthService instance
    """
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserModel:
    """
    Get current authenticated user
    
    Args:
        credentials: HTTP authorization credentials
        auth_service: Authentication service
        
    Returns:
        Current user model
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return auth_service.get_current_user(token)


def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Get current active user
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user model
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: str):
    """
    Create a dependency that requires a specific role
    
    Args:
        required_role: Required user role
        
    Returns:
        Dependency function
    """
    def role_checker(current_user: UserModel = Depends(get_current_active_user)) -> UserModel:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker


# Role-based dependencies
require_admin = require_role("ADMIN")
require_advisor = require_role("ADVISOR")
require_investor = require_role("INVESTOR")

# Additional utility methods for AuthService
def create_user(db: Session, username: str, email: str, password: str, role: str = "INVESTOR") -> UserModel:
    """
    Create a new user
    """
    # Check if user already exists
    if db.query(UserModel).filter(UserModel.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if db.query(UserModel).filter(UserModel.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = pwd_context.hash(password)
    user = UserModel(
        username=username,
        email=email,
        password_hash=hashed_password,
        role=role,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    """
    Get user by username
    """
    return db.query(UserModel).filter(UserModel.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    """
    Get user by email
    """
    return db.query(UserModel).filter(UserModel.email == email).first()