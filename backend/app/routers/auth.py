# File: backend/app/routers/auth.py
# Updated to create users in both TEMP_USERS and Neptune

from fastapi import APIRouter, HTTPException, Depends, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import jwt
import os
from datetime import datetime, timedelta
from app.models.user import create_user_in_neptune

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security schemes
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


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
    payload = verify_token(token)

    # Check if user still exists (important for in-memory storage)
    user_email = payload.get("email")
    if user_email not in TEMP_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists. Please login again."
        )

    return payload


# Temporary in-memory user storage (replace with database in production)
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

        # Store user in TEMP_USERS (for authentication)
        TEMP_USERS[request.email] = {
            "user_id": user_id,
            "email": request.email,
            "password_hash": password_hash,
            "username": request.username
        }

        # ALSO create user in Neptune (for character relationships)
        neptune_success = create_user_in_neptune(user_id, request.email)
        if not neptune_success:
            print(f"Warning: Failed to create user {user_id} in Neptune, but continuing...")

        print(f"Registered user: {request.email} with ID: {user_id}")  # Debug log

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
def login(username: str = Form(...), password: str = Form(...)):
    """Login with email and password - OAuth2 compatible"""
    try:
        print(f"Login attempt for: {username}")  # Debug log
        print(f"Current users in TEMP_USERS: {list(TEMP_USERS.keys())}")  # Debug log

        # Find user by email (username field contains email)
        user = TEMP_USERS.get(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password (in production, use proper password verification)
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if password_hash != user["password_hash"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Ensure user exists in Neptune (in case they were created before this fix)
        neptune_success = create_user_in_neptune(user["user_id"], user["email"])
        if not neptune_success:
            print(f"Warning: Failed to create/verify user {user['user_id']} in Neptune")

        print(f"Successful login for: {username}")  # Debug log

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


# Debug endpoint to check current users (remove in production)
@router.get("/debug/users")
def debug_users():
    """Debug endpoint to see current users"""
    return {
        "total_users": len(TEMP_USERS),
        "user_emails": list(TEMP_USERS.keys())
    }


# Debug endpoint to check Neptune users (remove in production)
@router.get("/debug/neptune-users")
def debug_neptune_users():
    """Debug endpoint to see Neptune users"""
    try:
        from app.neptune_client import run_query
        query = "g.V().hasLabel('User').elementMap()"
        result = run_query(query)
        return {
            "total_neptune_users": len(result),
            "neptune_users": [{"user_id": user.get('user_id'), "email": user.get('email')} for user in result]
        }
    except Exception as e:
        return {"error": str(e)}