import base64
import io
from PIL import Image
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from app.models.character import (create_character, get_character, delete_character, update_character_habit_score, list_characters, CharacterSummary, update_character_image)
from app.models.habit import get_all_habits

router = APIRouter(tags=["character"])

class CharacterCreateRequest(BaseModel):
    name: str
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    image_data: str = None

class HabitUpdateRequest(BaseModel):
    attribute: str # e.g., "strength"
    habit_points: int

class CharacterImageUpdateRequest(BaseModel):
    image_data: str  # Base64 image data

"""Character Management Endpoints"""
# POST endpoint for creating a character
@router.post("/character", summary="Create a new character")
def add_character(character: CharacterCreateRequest):
    try:
        # Call the model function to create a character node in Neptune
        result = create_character(
            character.name,
            character.strength,
            character.dexterity,
            character.constitution,
            character.intelligence,
            character.wisdom,
            character.charisma,
            character.image_data
        )
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error creating character: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# GET endpoint to retrieve a character by ID
@router.get("/character/{character_id}", summary="Get a character based on ID")
def read_character(character_id: str):
    try:
        result = get_character(character_id)
        if not result:
            raise HTTPException(status_code=404, detail="Character not found")
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error fetching character: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# DELETE endpoint to remove a character by ID
@router.delete("/character/{character_id}", summary="Delete a character by ID")
def remove_character(character_id: str):
    result = delete_character(character_id)
    if not result:
        raise HTTPException(status_code=404, detail="Character not found or deletion failed")
    return {"status": "success", "data": result}

@router.get("/characters", response_model=list[CharacterSummary], summary="List all characters")
def read_characters():
    """
    Return a list of all Characters, each with its id and name.
    """
    return list_characters()

"""Habit Management Endpoints"""

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
        return {"status": "success", "data": [], "message": "No Habits have been created for this Character"}  # Empty is valid
    return { "status": "success", "data": habits }




"""Image Management Endpoints"""

# Alternative file upload endpoint (if you prefer file uploads over base64)
@router.post("/character/{character_id}/upload-image", summary="Upload character image file")
async def upload_character_image(character_id: str, file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Validate file size (5MB limit)
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image file too large (max 5MB)")

        # Optional: Resize image if too large
        try:
            image = Image.open(io.BytesIO(content))

            # Resize if larger than 800x800
            max_size = (800, 800)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Convert back to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format)
                content = img_byte_arr.getvalue()

        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Convert to base64 data URL
        base64_data = base64.b64encode(content).decode('utf-8')
        image_data_url = f"data:{file.content_type};base64,{base64_data}"

        # Update character with image
        result = update_character_image(character_id, image_data_url)
        return {"status": "success", "message": "Image uploaded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error uploading image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# PUT endpoint for updating character image
@router.put("/character/{character_id}/image", summary="Update character image")
def update_character_image_endpoint(character_id: str, image_request: CharacterImageUpdateRequest):
    try:
        result = update_character_image(character_id, image_request.image_data)
        return {"status": "success", "message": "Image updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error updating image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
