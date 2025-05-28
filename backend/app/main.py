#backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import character, habit
app = FastAPI(title="DND Habit Tracker")

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(character.router, prefix="/api")
app.include_router(habit.router, prefix="/api")

app.add_middleware(
    CORSMiddleware, # type: ignore
    allow_origins=["*"],  # or restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)