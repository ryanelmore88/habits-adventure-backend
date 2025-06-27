#File: backend / app / routers / completion.py
# This is the complete file - replace everything in your completion.py with this

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta
from app.models.habit import (
    update_habit_completion,  # Import from habit model, not completion model
    get_habit,
    get_current_week_completions,
    get_current_day_completions
)
from app.routers.auth import get_current_user
from app.models.user import get_user_characters

router = APIRouter(prefix="/api/habit", tags=["completion"])


class CompletionMark(BaseModel):
    habit_id: str
    completion_date: str
    completed: bool = True


def verify_habit_ownership(habit_id: str, user_id: str) -> bool:
    """Verify that a user owns the character that owns this habit"""
    habit = get_habit(habit_id)
    if not habit:
        return False

    user_characters = get_user_characters(user_id)
    return any(char["character_id"] == habit["character_id"] for char in user_characters)


@router.post("/completion")
def mark_completion(completion: CompletionMark, current_user: dict = Depends(get_current_user)):
    """Mark a habit as complete or incomplete for a specific date"""
    try:
        # Verify user owns this habit's character
        if not verify_habit_ownership(completion.habit_id, current_user["user_id"]):
            raise HTTPException(status_code=403, detail="You don't have access to this habit")

        # Use update_habit_completion from habit model
        result = update_habit_completion(
            habit_id=completion.habit_id,
            completion_date=completion.completion_date,
            completed=completion.completed
        )

        if result:
            return {"status": "success", "message": "Completion marked", "data": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to mark completion")

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error marking completion: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark completion")


@router.get("/completions/week/{character_id}")
def get_week_completions(
        character_id: str,
        current_user: dict = Depends(get_current_user)
):
    """Get habit completions for the current week"""
    try:
        # Verify user owns this character
        user_characters = get_user_characters(current_user["user_id"])
        if not any(char["character_id"] == character_id for char in user_characters):
            raise HTTPException(status_code=403, detail="You don't have access to this character")

        # Calculate current week's start and end dates
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        completions = get_current_week_completions(
            character_id=character_id,
            start_date=start_of_week,
            end_date=end_of_week
        )

        return {"status": "success", "data": completions}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching week completions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch completions")


@router.get("/completions/today/{character_id}")
def get_today_completions(
        character_id: str,
        current_user: dict = Depends(get_current_user)
):
    """Get habit completions for today"""
    try:
        # Verify user owns this character
        user_characters = get_user_characters(current_user["user_id"])
        if not any(char["character_id"] == character_id for char in user_characters):
            raise HTTPException(status_code=403, detail="You don't have access to this character")

        today = datetime.now().date()
        completions = get_current_day_completions(
            character_id=character_id,
            today=today
        )

        return {"status": "success", "data": completions}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching today's completions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch completions")