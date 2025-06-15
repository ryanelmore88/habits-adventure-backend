# backend/app/models/character.py
import uuid
from gremlin_python.process.traversal import T
from app.neptune_client import run_query
from app.models.Attribute import Attribute
from pydantic import BaseModel

class CharacterSummary(BaseModel):
    id: str
    name: str

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
                     intelligence: int, wisdom: int, charisma: int):
    # Add input validation
    if not name or not name.strip():
        raise ValueError("Character name cannot be empty")

    for attr_name, value in [("strength", strength), ("dexterity", dexterity),
                             ("constitution", constitution), ("intelligence", intelligence),
                             ("wisdom", wisdom), ("charisma", charisma)]:
        if not isinstance(value, int) or value < 1 or value > 30:
            raise ValueError(f"{attr_name} must be between 1 and 30")

    try:
        # Generate a unique character ID that fits in a 64-bit integer
        character_id = generate_character_id()

        # Create an Attribute instance for each parameter
        strength_attr = Attribute('strength', strength)
        dexterity_attr = Attribute('dexterity', dexterity)
        constitution_attr = Attribute('constitution', constitution)
        intelligence_attr = Attribute('intelligence', intelligence)
        wisdom_attr = Attribute('wisdom', wisdom)
        charisma_attr = Attribute('charisma', charisma)

        # Build the Gremlin query string for creating a Character vertex
        query = (
            f"g.addV('Character')"
            f".property('name', '{name}')"
            f".property('character_id', '{character_id}')"
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
        result = run_query(query)
        if not result:
            raise RuntimeError("Failed to create Character vertex")
        return result
    except Exception as e:
        print(f"Error creating Character: {e}")
        raise e

def get_basic_character(character_id: str):
    # Query by custom property
    query = f"g.V().hasLabel('Character').has('character_id', '{character_id}').valueMap(true)"
    result = run_query(query)
    return result

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