# // File: backend / app / main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from app.routers import character, habit, completion, adventure, enemy, auth
from app.neptune_client import run_query, init_neptune_client, close_neptune_client
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    init_neptune_client()
    yield
    print("Shutting down...")
    close_neptune_client()

app = FastAPI(
    title="Habits Adventure API",
    description="A gamified habit tracking system with RPG mechanics",
    version="1.0.0"
)


# Get allowed origins from environment
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(character.router, prefix="/api")
app.include_router(habit.router, prefix="/api")
app.include_router(completion.router, prefix="/api")
app.include_router(adventure.router, prefix="/api")
app.include_router(enemy.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Habits Adventure API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connectivity
        result = run_query("g.V().limit(1)")
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# Development endpoints (remove in production)
if os.getenv("ENVIRONMENT") == "development":
    @app.get("/debug/info")
    def debug_info():
        return {
            "allowed_origins": allowed_origins,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "neptune_endpoint": os.getenv("NEPTUNE_ENDPOINT", "localhost"),
            "neptune_port": os.getenv("NEPTUNE_PORT", "8182")
        }


# Initialize enemy templates on startup (optional)
@app.on_event("startup")
async def startup_event():
    """Initialize default data on application startup"""
    try:
        # You can optionally initialize enemy templates here
        # from app.models.enemy import create_enemy_templates
        # create_enemy_templates()
        print("Application started successfully")
    except Exception as e:
        print(f"Startup error: {e}")