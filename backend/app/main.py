# backend/app/main.py - SECURE CORS FIX

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import character, habit, adventure

# Load environment-specific .env file
environment = os.getenv("ENVIRONMENT", "development")
env_file = f".env.{environment}"

if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"Loaded environment config from {env_file}")
else:
    load_dotenv()
    print("Loaded environment config from .env")

app = FastAPI(
    title=os.getenv("APP_NAME", "DND Habit Tracker"),
    debug=os.getenv("DEBUG", "false").lower() == "true"
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "debug": os.getenv("DEBUG", "false"),
        "app_name": os.getenv("APP_NAME")
    }


# SECURE CORS Configuration
def get_cors_origins():
    """
    Get CORS origins with security validation
    Never allows wildcard (*) in any environment
    """
    environment = os.getenv("ENVIRONMENT", "development")
    origins_env = os.getenv("ALLOWED_ORIGINS", "")

    if not origins_env or origins_env.strip() == "":
        # Default safe origins for development
        default_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",  # Common React dev port
            "http://127.0.0.1:3000"
        ]
        print(f"CORS: No origins specified, using defaults: {default_origins}")
        return default_origins

    # Parse origins and validate
    origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]

    # Security check - never allow wildcard
    if "*" in origins:
        raise ValueError(
            "Wildcard CORS (*) is not allowed for security reasons. "
            "Please specify explicit origins in ALLOWED_ORIGINS."
        )

    # Validate each origin format
    valid_origins = []
    for origin in origins:
        # Basic URL validation
        if not (origin.startswith("http://") or origin.startswith("https://")):
            print(f"CORS WARNING: Origin '{origin}' should include protocol (http:// or https://)")
            continue

        # Remove trailing slashes for consistency
        clean_origin = origin.rstrip("/")
        valid_origins.append(clean_origin)

    if not valid_origins:
        raise ValueError(
            "No valid CORS origins found. Please check ALLOWED_ORIGINS format. "
            "Expected format: 'http://localhost:5173,https://mydomain.com'"
        )

    print(f"CORS: Environment={environment}, Valid origins: {valid_origins}")
    return valid_origins


# Get CORS origins with validation
try:
    ALLOWED_ORIGINS = get_cors_origins()
except ValueError as e:
    print(f"CORS Configuration Error: {e}")
    # Exit early to prevent insecure startup
    exit(1)

# Apply CORS middleware with secure defaults
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Explicit origins only
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Explicit methods
    allow_headers=[  # Explicit headers
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization"
    ],
    expose_headers=[],  # Don't expose extra headers
    max_age=600,  # Cache preflight for 10 minutes
)

# Debug endpoints (only in development with explicit flag)
IS_DEVELOPMENT = os.getenv("ENVIRONMENT", "development") == "development"
ENABLE_DEBUG = os.getenv("ENABLE_DEBUG_ENDPOINTS", "false").lower() == "true"

if IS_DEVELOPMENT and ENABLE_DEBUG:
    @app.get("/debug/env")
    def debug_env():
        return {
            "environment": os.getenv("ENVIRONMENT"),
            "neptune_endpoint": os.getenv("NEPTUNE_ENDPOINT"),
            "cors_origins": ALLOWED_ORIGINS,
            "debug_mode": os.getenv("DEBUG"),
            "log_level": os.getenv("LOG_LEVEL")
        }


    @app.get("/debug/cors")
    def debug_cors():
        """Debug endpoint to test CORS configuration"""
        return {
            "message": "CORS is working!",
            "allowed_origins": ALLOWED_ORIGINS,
            "timestamp": "2025-01-01T00:00:00Z"
        }

app.include_router(character.router, prefix="/api")
app.include_router(habit.router, prefix="/api")

app.include_router(adventure.router, prefix="/api")