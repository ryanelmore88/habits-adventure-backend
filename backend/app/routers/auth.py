# File: backend/app/routers/auth.py
# Create this new file for authentication routing

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import jwt
import os
from datetime import datetime, timedelta

# You'll need to install PyJWT: pip install PyJWT
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Security scheme
security = HTTPBearer()

# JWT Configuration - use environment variables in production
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    username: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str


def create_access_token(user_id: str, email: str) -> str:
    """Create a JWT access token"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to get the current authenticated user"""
    token = credentials.credentials
    return verify_token(token)


# Temporary in-memory user storage (replace with database in production)
# For now, we'll use a simple dict - you should replace this with proper user storage
TEMP_USERS = {}


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        if request.email in TEMP_USERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # In production, hash the password properly
        import hashlib
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()

        # Generate user ID
        import uuid
        user_id = str(uuid.uuid4())

        # Store user (in production, use proper database)
        TEMP_USERS[request.email] = {
            "user_id": user_id,
            "email": request.email,
            "password_hash": password_hash,
            "username": request.username
        }

        # Create access token
        access_token = create_access_token(user_id, request.email)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Login with email and password"""
    try:
        # Find user
        user = TEMP_USERS.get(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password (in production, use proper password verification)
        import hashlib
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()

        if password_hash != user["password_hash"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Create access token
        access_token = create_access_token(user["user_id"], user["email"])

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user["user_id"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error logging in user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login"
        )


@router.get("/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"]
    }


@router.post("/logout")
def logout():
    """Logout (client should remove token)"""
    return {"message": "Logged out successfully"}