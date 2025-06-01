import datetime
import uuid
import json

from app.neptune_client import run_query
from gremlin_python.process.traversal import T
from app.models.completion import create_completion


def generate_habit_id() -> str:
    """Generate a unique habit ID that fits in a 64-bit integer."""
    return str(uuid.uuid4().int % (2 ** 63))


def create_habit(character_id: str, habit_name: str, attribute: str, description: str = ""):
    """
    Create a Habit vertex and link it to the Character vertex.

    - Generates a unique numeric habit_id.
    - Stores the habit_name, attribute, description, and an empty completion_history.
    - Creates an edge 'hasHabit' from the Character vertex to the Habit vertex.

    Returns a dictionary with the habit_id and the query result.
    """

    # Input validation
    if not character_id or not character_id.strip():
        raise ValueError("Character ID cannot be empty")
    if not habit_name or not habit_name.strip():
        raise ValueError("Habit name cannot be empty")
    if not attribute or not attribute.strip():
        raise ValueError("Attribute cannot be empty")

    valid_attributes = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    if attribute.lower() not in valid_attributes:
        raise ValueError(f"Attribute must be one of: {', '.join(valid_attributes)}")

    try:
        habit_id = generate_habit_id()
        # Initialize completion_history as an empty JSON array.
        completions = "[]"

        # Build the Gremlin query.
        query = (
            f"g.addV('Habit')"
            f".property('habit_id', '{habit_id}')"
            f".property('character_id', '{character_id}')"
            f".property('habit_name', '{habit_name}')"
            f".property('attribute', '{attribute.lower()}')"
            f".property('description', '{description}')"
            f".property('completion_history', '{completions}')"
            f".as('h')"  # Label this vertex as 'h'
            f".V().hasLabel('Character').has('character_id', '{character_id}').addE('hasHabit').to('h')"
        )
        print(f"Created Habit {habit_id}, {attribute}, {description}")
        result = run_query(query)
        return {"habit_id": habit_id, "result": result}
    except Exception as e:
        print(f"Error creating Habit: {e}")
        raise e


def update_habit_completion(habit_id: str, completion_date: str = None, completed: bool = True):
    # Default to today's date if not provided.
    if completion_date is None:
        completion_date = datetime.date.today().isoformat()

    # Debug: log the values
    print(f"Updating habit completion for habit_id: {habit_id} on {completion_date}, completed: {completed}")

    # FIXED: Use custom property lookup with proper quoting
    query_find = (
        f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}')"
        f".outE('hasCompletion').inV()"
        f".has('completion_date', '{completion_date}')"
        f".id()"
    )
    find_result = run_query(query_find)
    print("Find result:", find_result)

    if find_result and len(find_result) > 0:
        # A completion vertex exists—update its 'completed' property.
        existing_completion_id = find_result[0]
        query_update = (
            f"g.V('{existing_completion_id}')"
            f".property('completed', {str(completed).lower()})"
        )
        result = run_query(query_update)
        return {"completion_id": existing_completion_id, "result": result}
    else:
        # No existing completion for this date—create a new completion vertex.
        return create_completion(habit_id, completion_date, completed)


def get_habit(habit_id: str):
    """
    Retrieve a habit vertex and return its properties, including the parsed completion history.
    """
    # Query by custom property
    query = f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}').elementMap()"
    result = run_query(query)
    if not result:
        return None

    habit_data = result[0]

    # Extract the JSON completion history and parse it.
    completion_history = habit_data.get("completion_history")
    if isinstance(completion_history, list):
        # Sometimes the value may come wrapped in a list.
        completion_history = completion_history[0]
    try:
        completion_history = json.loads(completion_history)
    except Exception:
        completion_history = []

    habit = {
        "id": habit_data.get("habit_id"),
        "habit_name": habit_data.get("habit_name"),
        "attribute": habit_data.get("attribute"),
        "description": habit_data.get("description"),
        "completion_history": completion_history
    }
    return habit


def get_completions_for_habit(habit_id: str):
    """
    Retrieve all completion vertices associated with a habit.
    """
    # FIXED: Use custom property lookup
    query = f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}').outE('hasCompletion').inV().elementMap()"
    result = run_query(query)
    return result


def get_habits_for_attribute(character_id: str, attribute: str):
    # FIXED: Add quotes around character_id
    query = f"g.V().hasLabel('Habit').has('character_id', '{character_id}').has('attribute', '{attribute}').elementMap()"
    result = run_query(query)
    print(f"Habits query result: ", result)
    return result


def get_all_habits(character_id: str):
    """
    Retrieve all habits associated with a given character.
    This function traverses from the character vertex via the 'hasHabit' edge,
    then returns all habit vertices and their properties using elementMap().
    """
    # Use custom properties for traversal
    query = (
        f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
        f".out('hasHabit').hasLabel('Habit').elementMap()"
    )
    print(f"{character_id}: {query}")
    result = run_query(query)
    print(f"Habits query result: ", result)
    return result


def delete_habit(habit_id: str):
    """
    Delete a habit vertex from the graph database using its ID.
    """
    # Query by custom property
    query = f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}').drop()"
    result = run_query(query)
    return result


def get_current_week_completions(character_id: str, start_date: datetime, end_date: datetime):
    """
    Get all habit completions for a character within the specified date range
    """
    # Convert datetime objects to YYYY-MM-DD strings
    start_date_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
    end_date_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)

    # FIXED: Use proper custom property lookup and date formatting
    query = (
        f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
        f".out('hasHabit').hasLabel('Habit').as('habit')"
        f".out('hasCompletion').hasLabel('HabitCompletion')"
        f".has('completion_date', gte('{start_date_str}'))"
        f".has('completion_date', lte('{end_date_str}'))"
        f".as('completion')"
        f".select('habit', 'completion')"
        f".by(valueMap(true))"
        f".by(valueMap(true))"
    )

    result = run_query(query)
    return result


def get_current_day_completions(character_id: str, today: datetime):
    """
    Get habit completions for a character for a specific day
    """
    # Convert datetime to string
    today_str = today.strftime('%Y-%m-%d') if hasattr(today, 'strftime') else str(today)

    # FIXED: Use proper custom property lookup
    query = (
        f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
        f".out('hasHabit').hasLabel('Habit').as('habit')"
        f".out('hasCompletion').hasLabel('HabitCompletion')"
        f".has('completion_date', '{today_str}')"
        f".as('completion')"
        f".select('habit', 'completion')"
        f".by(valueMap(true))"
        f".by(valueMap(true))"
    )

    result = run_query(query)
    return result