# backend/app/models/character.py

# TODO Update character.py to remove user-specific filtering from get_all_characters
# TODO This function should now only be used internally, not exposed via API
import base64
import uuid
from gremlin_python.process.traversal import T
from app.neptune_client import run_query
from app.models.Attribute import Attribute
from pydantic import BaseModel

class CharacterSummary(BaseModel):
    id: str
    name: str
    image_url: str = None # Allow users to add an avatar for their character.

def generate_character_id() -> str:
    """Generate a unique character ID that fits within a 64-bit integer."""
    return str(uuid.uuid4().int % (2**63))

def list_characters() -> list[CharacterSummary]:
    # Use custom character_id property instead of T.id
    query = (
        "g.V().hasLabel('Character')"
        ".project('character_id','name')"
        ".by('character_id').by('name')"
    )
    results = run_query(query)
    summaries = []
    for row in results:
        summaries.append(
            CharacterSummary(
                id=str(row['character_id']),  # FIXED: Use 'character_id' key
                name=row['name']
            )
        )
    return summaries


def create_character(name: str, strength: int, dexterity: int, constitution: int,
                     intelligence: int, wisdom: int, charisma: int, image_data: str = None):
    # Add input validation
    if not name or not name.strip():
        raise ValueError("Character name cannot be empty")

    for attr_name, value in [("strength", strength), ("dexterity", dexterity),
                             ("constitution", constitution), ("intelligence", intelligence),
                             ("wisdom", wisdom), ("charisma", charisma)]:
        if not isinstance(value, int) or value < 1 or value > 30:
            raise ValueError(f"{attr_name} must be between 1 and 30")

    # Validate image data if provided
    if image_data:
        try:
            # Validate base64 format
            if not image_data.startswith('data:image/'):
                raise ValueError("Image must be a valid data URL")
            # You can add size limits here if needed
            if len(image_data) > 5 * 1024 * 1024:  # 5MB limit
                raise ValueError("Image file too large (max 5MB)")
        except Exception as e:
            raise ValueError("Invalid image data provided")

    try:
        character_id = generate_character_id()

        # FIXED: Build the base attributes using correct Attribute constructor
        # Attribute(name: str, base_score: int, habit_points: int = 0)
        strength_attr = Attribute("strength", strength, 0)
        dexterity_attr = Attribute("dexterity", dexterity, 0)
        constitution_attr = Attribute("constitution", constitution, 0)
        intelligence_attr = Attribute("intelligence", intelligence, 0)
        wisdom_attr = Attribute("wisdom", wisdom, 0)
        charisma_attr = Attribute("charisma", charisma, 0)

        # Calculate HP based on constitution (D&D style: 10 + CON modifier)
        max_hp = 10 + constitution_attr.calculate_base_bonus()
        current_hp = max_hp

        # Build the Gremlin query to create the character vertex
        query = (
            f"g.addV('Character')"
            f".property('character_id', '{character_id}')"
            f".property('name', '{name}')"
            f".property('level', 1)"
            f".property('current_xp', 0)"
            f".property('current_hp', {current_hp})"
            f".property('max_hp', {max_hp})"
            f".property('strength', {strength_attr.base_score})"
            f".property('strength_habit_points', {strength_attr.habit_points})"
            f".property('dexterity', {dexterity_attr.base_score})"
            f".property('dexterity_habit_points', {dexterity_attr.habit_points})"
            f".property('constitution', {constitution_attr.base_score})"
            f".property('constitution_habit_points', {constitution_attr.habit_points})"
            f".property('intelligence', {intelligence_attr.base_score})"
            f".property('intelligence_habit_points', {intelligence_attr.habit_points})"
            f".property('wisdom', {wisdom_attr.base_score})"
            f".property('wisdom_habit_points', {wisdom_attr.habit_points})"
            f".property('charisma', {charisma_attr.base_score})"
            f".property('charisma_habit_points', {charisma_attr.habit_points})"
        )

        if image_data:
            # Escape single quotes in base64 data
            escaped_image_data = image_data.replace("'", "\\'")
            query += f".property('image_data', '{escaped_image_data}')"

        result = run_query(query)
        if not result:
            raise RuntimeError("Failed to create Character vertex")

        # Return just the character_id string
        return character_id

    except Exception as e:
        print(f"Error creating Character: {e}")
        raise e


def update_character(character_id: str, image_data: str = None) -> bool:
    """
    Update a character's image data
    """
    try:
        if image_data:
            # Validate image data format
            if not image_data.startswith('data:image/'):
                raise ValueError("Invalid image data format")

            # Update the character's image
            query = (
                f"g.V().hasLabel('Character')"
                f".has('character_id', '{character_id}')"
                f".property('image_data', '{image_data}')"
            )
            run_query(query)

        return True

    except Exception as e:
        print(f"Error updating character {character_id}: {e}")
        return False


def link_habits_with_character(character_id: str):
    """
    Link any orphaned habits to a character
    This is mainly for backwards compatibility
    """
    try:
        # This function can be empty for now since new habits
        # are created with character_id already
        pass
    except Exception as e:
        print(f"Error linking habits with character: {e}")


def update_character_image(character_id: str, image_data: str):
    """Update character image"""
    if not character_id or not character_id.strip():
        raise ValueError("Invalid character ID")

    if not image_data:
        raise ValueError("Image data is required")

    # Validate image data
    if not image_data.startswith('data:image/'):
        raise ValueError("Image must be a valid data URL")

    if len(image_data) > 5 * 1024 * 1024:  # 5MB limit
        raise ValueError("Image file too large (max 5MB)")

    try:
        # Escape single quotes in base64 data
        escaped_image_data = image_data.replace("'", "\\'")

        query = (
            f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
            f".property('image_data', '{escaped_image_data}')"
        )

        result = run_query(query)
        return {"status": "success", "message": "Image updated successfully"}
    except Exception as e:
        print(f"Error updating character image: {e}")
        raise RuntimeError(f"Failed to update character image: {str(e)}")

def delete_character(character_id: str):
    """
    Delete a character vertex from the graph database using its ID.
    """
    # Query by custom property
    query = f"g.V().hasLabel('Character').has('character_id', '{character_id}').drop()"
    run_query(query)
    return {"status": "success", "message": f"Character {character_id} deleted."}

def get_character(character_id: str):
    if not character_id or not character_id.strip():
        raise ValueError("Invalid character ID")

    try:
        # Build a Gremlin query to fetch the character's properties.
        query = f"g.V().hasLabel('Character').has('character_id', '{character_id}').elementMap()"
        result = run_query(query)
        if not result:
            return None

        # Assume result[0] is a dictionary of properties.
        char_data = result[0]
    except Exception as e:
        print(f"Error fetching character {character_id}: {e}")
        raise

    # Sometimes the properties returned by valueMap(true) are lists.
    def extract_value(value):
        return value[0] if isinstance(value, list) else value

    # FIXED: Look for character_id in the data (not 'id')
    char_id = extract_value(char_data.get("character_id"))
    name = extract_value(char_data.get("name"))
    image_data = extract_value(char_data.get("image_data"))

    # List the attributes we care about.
    attribute_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    attributes = {}
    for attr in attribute_names:
        base_val = extract_value(char_data.get(attr))
        habit_val = extract_value(char_data.get(f"{attr}_habit_points")) or 0
        if base_val is None:
            continue

        # Create an Attribute instance and compute the bonus.
        attribute_obj = Attribute(attr, base_score=base_val, habit_points=habit_val)
        attributes[attr] = {
            "base": base_val,
            "habit_points": habit_val,
            "bonus": attribute_obj.total_bonus()
        }

    # Build and return the complete character data.
    return {
        "id": char_id,
        "name": name,
        "image_data": image_data,
        "attributes": attributes,
        # Include additional character properties as needed.
    }

def update_character_habit_score(character_id: str, attribute: str, habit_points_increase_value: int):
    """
    Update the habit points for the given attribute of a character.
    The habit_points_increase_value should be an integer meeting the reward value
    This function builds a Gremlin query that updates the habit points property
    for the specified attribute and returns the result.
    """

    # Normalize the attribute name to lowercase
    attr_lower_case = attribute.lower()
    property_key = f"{attr_lower_case}_habit_points"

    # FIXED: Use custom property lookup instead of T.id
    get_query = f"g.V().hasLabel('Character').has('character_id', '{character_id}').values('{property_key}')"
    current_values = run_query(get_query)

    if current_values and len(current_values) > 0:
        try:
            current_value = int(current_values[0])
        except Exception as e:
            print(f"Error converting current habit points to int: {e}")
            current_value = 0
    else:
        current_value = 0 # If not found, assume 0 habit points.

    #Calculate the new total habit points.
    updated_total = current_value + habit_points_increase_value

    # FIXED: Use custom property lookup for update
    query_update = (
        f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
        f".property('{property_key}', '{updated_total}')"
    )

    result = run_query(query_update)
    return result


def update_character_hp(character_id: str, hp_change: int) -> dict:
    """
    Update character's HP by a given amount
    """
    try:
        # Import here to avoid circular imports
        from app.neptune_client import run_query

        # Get current HP and max HP
        get_query = (
            f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
            f".project('current_hp', 'max_hp')"
            f".by(coalesce(values('current_hp'), constant(0)))"
            f".by(coalesce(values('max_hp'), constant(20)))"
        )
        result = run_query(get_query)

        if not result:
            raise ValueError("Character not found")

        current_hp = result[0].get('current_hp', 0)
        max_hp = result[0].get('max_hp', 20)

        # Calculate new HP (can't go below 0 or above max)
        new_hp = max(0, min(max_hp, current_hp + hp_change))

        # Update in database
        update_query = (
            f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
            f".property('current_hp', {new_hp})"
        )
        run_query(update_query)

        return {
            "character_id": character_id,
            "previous_hp": current_hp,
            "current_hp": new_hp,
            "max_hp": max_hp,
            "hp_change": hp_change,
            "actual_change": new_hp - current_hp
        }

    except Exception as e:
        print(f"Error updating character HP: {e}")
        raise e