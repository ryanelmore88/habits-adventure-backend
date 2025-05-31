# backend/app/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import character, habit

# Load environment-specific .env file
environment = os.getenv("ENVIRONMENT", "development")
env_file = f".env.{environment}"

# Try to load environment-specific file, fallback to .env
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

# CORS Configuration
IS_DEVELOPMENT = os.getenv("ENVIRONMENT", "development") == "development"

if IS_DEVELOPMENT:
    # In development, check if we want to allow all origins
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    if allowed_origins_env == "*":
        ALLOWED_ORIGINS = ["*"]
        print("CORS: Allowing all origins (development mode)")
    else:
        ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
        print(f"CORS: Allowing specific origins: {ALLOWED_ORIGINS}")
else:
    # Production - always use specific origins
    origins_string = os.getenv("ALLOWED_ORIGINS", "")
    ALLOWED_ORIGINS = [origin.strip() for origin in origins_string.split(",") if origin.strip()]
    print(f"CORS: Production mode, allowing: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: Add debug endpoints in development
if IS_DEVELOPMENT and os.getenv("ENABLE_DEBUG_ENDPOINTS", "false").lower() == "true":
    @app.get("/debug/env")
    def debug_env():
        return {
            "environment": os.getenv("ENVIRONMENT"),
            "neptune_endpoint": os.getenv("NEPTUNE_ENDPOINT"),
            "cors_origins": ALLOWED_ORIGINS,
            "debug_mode": os.getenv("DEBUG"),
            "log_level": os.getenv("LOG_LEVEL")
        }

app.include_router(character.router, prefix="/api")
app.include_router(habit.router, prefix="/api")