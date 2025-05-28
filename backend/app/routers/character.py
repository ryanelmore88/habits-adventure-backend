import datetime
from unittest import result

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.character import create_character, get_character, get_basic_character, delete_character, update_character_habit_score, list_characters, CharacterSummary
from app.models.habit import get_all_habits

router = APIRouter()

class CharacterCreateRequest(BaseModel):
    name: str
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

class HabitUpdateRequest(BaseModel):
    attribute: str # e.g., "strength"
    habit_points: int

# POST endpoint for creating a character
@router.post("/character", summary="Create a new character")
def add_character(character: CharacterCreateRequest):
    # Call the model function to create a character node in Neptune
    result = create_character(
        character.name,
        character.strength,
        character.dexterity,
        character.constitution,
        character.intelligence,
        character.wisdom,
        character.charisma,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create new character")
    return {"status": "success", "data": result}

# GET endpoint to retrieve a character by ID
@router.get("/character/{character_id}", summary="Get a character based on ID")
def read_character(character_id: str):
    result = get_character(character_id)
    if not result:
        raise HTTPException(status_code=404, detail="Character not found")
    return { "status": "success", "data": result }

# DELETE endpoint to remove a character by ID
@router.delete("/character/{character_id}", summary="Delete a character by ID")
def remove_character(character_id: str):
    result = delete_character(character_id)
    if not result:
        raise HTTPException(status_code=404, detail="Character not found or deletion failed")
    return {"status": "success", "data": result}

@router.get("/character/basic/{character_id}", summary="Get a character based on ID")
def read_basic_character(character_id: str):
    result = get_basic_character(character_id)
    if not result:
        raise HTTPException(status_code=404, detail="Character not found")
    return { "status": "success", "data": result }

@router.put("/character/{character_id}/habit", summary="Update habit points for an attribute based on ID")
def update_attribute_habit(character_id: str, habit_update: HabitUpdateRequest):
    result = update_character_habit_score(character_id, habit_update.attribute, habit_update.habit_points)
    # If your run_query returns an empty list on success, we can assume the update succeeded.
    if result is None or (isinstance(result, list) and not result):
        # You might choose to verify the update with an additional query if needed.
        return {"status": "success", "message": f"Updated {habit_update.attribute} habit points to {habit_update.habit_points} points"}
    else:
        # Otherwise, if the result indicates an error, return an error response.
        raise HTTPException(status_code=500, detail="Failed to update habit points")

@router.get("/character/{character_id}/habits", summary="Get all habits for a character")
def read_habits_for_character(character_id: str):
    habits = get_all_habits(character_id)
    if not habits:
        raise HTTPException(status_code=404, detail="No habits found for this character")

    return { "status": "success", "data": habits }

@router.get(
    "/characters",
    response_model=list[CharacterSummary],
    summary="List all characters",
)
def read_characters():
    """
    Return a list of all Characters, each with its id and name.
    """
    return list_characters()
