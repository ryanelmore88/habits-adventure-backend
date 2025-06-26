# File: backend/app/routers/completion.py
# Update completion router to require authentication

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from app.models.completion import (
    mark_habit_completion,
    get_completions_for_date_range,
    get_all_completions_for_character
)
from app.models.habit import get_habit_by_id
from app.routers.auth import get_current_user
from app.models.user import get_user_characters

router = APIRouter(prefix="/api/habit", tags=["completion"])


class CompletionMark(BaseModel):
    habit_id: str
    completion_date: str
    completed: bool = True


def verify_habit_ownership(habit_id: str, user_id: str) -> bool:
    """Verify that a user owns the character that owns this habit"""
    habit = get_habit_by_id(habit_id)
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

        success = mark_habit_completion(
            habit_id=completion.habit_id,
            completion_date=completion.completion_date,
            completed=completion.completed
        )

        if success:
            return {"status": "success", "message": "Completion marked"}
        else:
            raise HTTPException(status_code=400, detail="Failed to mark completion")

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error marking completion: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark completion")
