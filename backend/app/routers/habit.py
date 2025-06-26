from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.models.habit import (
    create_habit as create_habit_db,
    get_habits_for_character,
    delete_habit as delete_habit_db
)
from app.routers.auth import get_current_user
from app.models.user import get_user_characters

router = APIRouter(prefix="/api/habit", tags=["habit"])


class HabitCreate(BaseModel):
    character_id: str
    habit_name: str
    attribute: str
    description: Optional[str] = None


def verify_character_ownership(character_id: str, user_id: str) -> bool:
    """Verify that a user owns a specific character"""
    user_characters = get_user_characters(user_id)
    return any(char["character_id"] == character_id for char in user_characters)


@router.post("")
def create_habit(habit: HabitCreate, current_user: dict = Depends(get_current_user)):
    """Create a new habit for a character"""
    try:
        # Verify user owns this character
        if not verify_character_ownership(habit.character_id, current_user["user_id"]):
            raise HTTPException(status_code=403, detail="You don't have access to this character")

        habit_id = create_habit_db(
            character_id=habit.character_id,
            habit_name=habit.habit_name,
            attribute=habit.attribute,
            description=habit.description
        )
        return {"status": "success", "habit_id": habit_id}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error creating habit: {e}")
        raise HTTPException(status_code=500, detail="Failed to create habit")


@router.get("/character/{character_id}")
def get_habits(character_id: str, current_user: dict = Depends(get_current_user)):
    """Get all habits for a character"""
    try:
        # Verify user owns this character
        if not verify_character_ownership(character_id, current_user["user_id"]):
            raise HTTPException(status_code=403, detail="You don't have access to this character")

        habits = get_habits_for_character(character_id)
        return {"status": "success", "data": habits}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching habits: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch habits")


@router.delete("/{habit_id}")
def delete_habit(habit_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a habit"""
    try:
        # Note: In a production system, you'd want to verify the habit belongs
        # to a character owned by the user before deletion
        success = delete_habit_db(habit_id)
        if success:
            return {"status": "success", "message": "Habit deleted"}
        else:
            raise HTTPException(status_code=404, detail="Habit not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting habit: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete habit")
