# File: backend/app/routers/character.py
# Fixed version with correct imports

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.models.character import (
    create_character,
    get_character,
    update_character as update_character_db,
    delete_character,
    link_habits_with_character
)
from app.routers.auth import get_current_user  # Import auth dependency
from app.models.user import link_character_to_user, get_user_characters

router = APIRouter(prefix="/api/character", tags=["character"])


class CharacterCreate(BaseModel):
    name: str
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    image_data: Optional[str] = None


class CharacterUpdate(BaseModel):
    image_data: Optional[str] = None


@router.post("")
def create_new_character(
        character: CharacterCreate,
        current_user: dict = Depends(get_current_user)
):
    """Create a new character for the authenticated user"""
    try:
        # Check character limit for free users
        if not current_user.get("is_premium", False):
            existing_characters = get_user_characters(current_user["user_id"])
            if len(existing_characters) >= 3:
                raise HTTPException(
                    status_code=403,
                    detail="Free users can only create up to 3 characters. Upgrade to premium for unlimited characters."
                )

        # Create the character
        character_id = create_character(
            name=character.name,
            strength=character.strength,
            dexterity=character.dexterity,
            constitution=character.constitution,
            intelligence=character.intelligence,
            wisdom=character.wisdom,
            charisma=character.charisma,
            image_data=character.image_data
        )

        # Link character to user
        link_success = link_character_to_user(current_user["user_id"], character_id)
        if not link_success:
            # If linking fails, delete the character
            delete_character(character_id)
            raise HTTPException(status_code=500, detail="Failed to link character to user")

        # Link any existing habits to the new character
        link_habits_with_character(character_id)

        return {"status": "success", "character_id": character_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error creating character: {e}")
        raise HTTPException(status_code=500, detail="Failed to create character")


@router.get("/user/characters")
def get_current_user_characters(current_user: dict = Depends(get_current_user)):
    """Get all characters for the authenticated user"""
    try:
        characters = get_user_characters(current_user["user_id"])
        return {"status": "success", "data": characters}
    except Exception as e:
        print(f"Error fetching user characters: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch characters")


@router.get("/{character_id}")
def read_character(character_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific character (only if owned by user)"""
    try:
        # Verify user owns this character
        user_characters = get_user_characters(current_user["user_id"])
        if not any(char["character_id"] == character_id for char in user_characters):
            raise HTTPException(status_code=403, detail="You don't have access to this character")

        character = get_character(character_id)
        if character:
            return {"status": "success", "data": character}
        else:
            raise HTTPException(status_code=404, detail="Character not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching character: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch character")


@router.put("/{character_id}")
def update_character(
        character_id: str,
        update_data: CharacterUpdate,
        current_user: dict = Depends(get_current_user)
):
    """Update a character (only if owned by user)"""
    try:
        # Verify user owns this character
        user_characters = get_user_characters(current_user["user_id"])
        if not any(char["character_id"] == character_id for char in user_characters):
            raise HTTPException(status_code=403, detail="You don't have access to this character")

        updated = update_character_db(character_id, update_data.image_data)
        if updated:
            return {"status": "success", "message": "Character updated"}
        else:
            raise HTTPException(status_code=404, detail="Character not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating character: {e}")
        raise HTTPException(status_code=500, detail="Failed to update character")


@router.delete("/{character_id}")
def delete_character_endpoint(
        character_id: str,
        current_user: dict = Depends(get_current_user)
):
    """Delete a character (only if owned by user)"""
    try:
        # Verify user owns this character
        user_characters = get_user_characters(current_user["user_id"])
        if not any(char["character_id"] == character_id for char in user_characters):
            raise HTTPException(status_code=403, detail="You don't have access to this character")

        success = delete_character(character_id)
        if success:
            return {"status": "success", "message": "Character deleted"}
        else:
            raise HTTPException(status_code=404, detail="Character not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting character: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete character")