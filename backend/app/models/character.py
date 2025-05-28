# backend/app/models/character.py
import uuid
from gremlin_python.process.traversal import T
from app.neptune_client import run_query
from app.models.Attribute import Attribute
from pydantic import BaseModel

class CharacterSummary(BaseModel):
    id: str
    name: str

def list_characters() -> list[CharacterSummary]:
    # Project each Character vertex into just id & name
    query = (
        "g."
        "V().hasLabel('Character')"
        ".project('id','name')"
        ".by(T.id).by('name')"
    )
    results = run_query(query)
    summaries = []
    for row in results:
        # row will be a dict like {'id': 12345, 'name': 'Vigil'}
        summaries.append(
            CharacterSummary(
                id=str(row['id']),
                name=row['name']
            )
        )
    return summaries

def create_character(name: str, strength: int, dexterity: int, constitution: int,
                     intelligence: int, wisdom: int, charisma: int):

    # Generate a unique character ID that fits in a 64-bit integer
    character_id = str(uuid.uuid4().int % (2**63))

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
        f".property({T.id}, '{character_id}')"
        f".property('name', '{name}')"
        f".property('id', '{character_id}')"
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
    return result

def get_basic_character(character_id: str):
    # Build a Gremlin query that retrieves a vertex by its id and returns all properties
    query = f"g.V('{character_id}').valueMap(true)"
    result = run_query(query)
    return result

def delete_character(character_id: str):
    """
    Delete a character vertex from the graph database using its ID.

    This function builds a Gremlin query that finds the vertex by its ID and drops it.
    """
    query = f"g.V('{character_id}').drop()"
    run_query(query)
    # Since drop() returns an empty list on success, we consider that a success.
    return {"status": "success", "message": f"Character {character_id} deleted."}

def get_character(character_id: str):
    # Build a Gremlin query to fetch the character's properties.
    query = f"g.V('{character_id}').elementMap()"
    result = run_query(query)
    if not result:
        return None

    # Assume result[0] is a dictionary of properties.
    char_data = result[0]

    # Sometimes the properties returned by valueMap(true) are lists.
    def extract_value(value):
        return value[0] if isinstance(value, list) else value

    char_id = extract_value(char_data.get("id"))
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

    # Query to get the current habit points value.
    # Note: Using values() returns a list, so we extract the first element.
    get_query = f"g.V('{character_id}').values('{property_key}')"
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

    # Build the Gremlin query. For example, if the attribute is 'Strength',
    # the property key would be strength_habit_points
    query_update = (
        f"g.V('{character_id}')"
        f".property('{property_key}', '{updated_total}')"
    )

    result = run_query(query_update)
    
    # Does this need a return