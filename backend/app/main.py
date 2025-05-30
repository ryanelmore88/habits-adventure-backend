#backend/app/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import character, habit
app = FastAPI(title="DND Habit Tracker")

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(character.router, prefix="/api")
app.include_router(habit.router, prefix="/api")

# Get allowed origins from environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "message": exc.detail}
        )

    # Log unexpected errors
    print(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )