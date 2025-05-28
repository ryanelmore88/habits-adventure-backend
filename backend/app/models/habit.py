import datetime
import uuid
import json

from app.neptune_client import run_query
from gremlin_python.process.traversal import T
from app.models.completion import create_completion


def create_habit(character_id: str, habit_name: str, attribute: str, description: str = ""):
    """
    Create a Habit vertex and link it to the Character vertex.

    - Generates a unique numeric habit_id.
    - Stores the habit_name, attribute, description, and an empty completion_history.
    - Creates an edge 'hasHabit' from the Habit vertex to the Character vertex.

    Returns a dictionary with the habit_id and the query result.
    """
    # Generate a unique numeric habit ID that fits within 64 bits.
    habit_id = str(uuid.uuid4().int % (2 ** 63))
    # Initialize completion_history as an empty JSON array.
    completions = "[]"

    # Build the Gremlin query.
    # Note: Use proper quotes for string values. If habit_name or description contain special characters,
    # consider escaping them or using a more robust query builder.
    query = (
        f"g.addV('Habit')"
        f".property({T.id}, '{habit_id}')"
        f".property('habit_id', '{habit_id}')"
        f".property('character_id', {character_id})"
        f".property('habit_name', '{habit_name}')"
        f".property('attribute', '{attribute.lower()}')"
        f".property('description', '{description}')"
        f".property('completion_history', '{completions}')"
        f".as('h')"                                    # Label this vertex as 'h'
        f".V({character_id}).addE('hasHabit').to('h')" # Find the character vertex and add an edge labeled 'hasHabit' from the habit ('h') to it.
    )
    print(f"Created Habit {habit_id}, {attribute}, {description}")
    result = run_query(query)
    return {"habit_id": habit_id, "result": result}


def update_habit_completion(habit_id: str, completion_date: str = None, completed: bool = True):
    # Default to today's date if not provided.
    if completion_date is None:
        completion_date = datetime.date.today().isoformat()

    # Debug: log the values
    print(f"Updating habit completion for habit_id: {habit_id} on {completion_date}, completed: {completed}")

    # Instead of assuming habit_id is the vertex id, query by the 'habit_id' property.
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
    query = f"g.V('{habit_id}').elementMap()"
    result = run_query(query)
    if not result:
        return None

    habit_data = result[0]

    # Extract the JSON completion history and parse it.
    import json
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
    query = f"g.V('{habit_id}').outE('hasCompletion').inV().elementMap()"
    result = run_query(query)
    # Process result as needed, e.g., parse JSON completion history if stored
    return result

def get_habits_for_attribute(character_id: str, attribute: str):
    query = f"g.V().hasLabel('Habit').has('character_id', {character_id}).has('attribute', '{attribute}').elementMap()"
    result = run_query(query)
    print(f"Habits query result: ", result)
    return result

def get_all_habits(character_id: str):
    """
    Retrieve all habits associated with a given character.
    This function traverses from the character vertex via the 'hasHabit' edge,
    then returns all habit vertices and their properties using elementMap().
    """
    # This query starts at the character vertex, follows outgoing 'hasHabit' edges,
    # and retrieves the habit vertices.
    query = f"g.V().hasLabel('Habit').has('character_id').elementMap()"
    print(f"{character_id}: {query}")
    result = run_query(query)
    print(f"Habits query result: ", result)
    return result

def delete_habit(habit_id: str):
    """
    Delete a habit vertex from the graph database using its ID.
    """
    query = f"g.V({habit_id}).drop()"
    result = run_query(query)
    return result

def get_current_week_completions(character_id: str, start_date: datetime, end_date: datetime):
    query = (
        # For a single habit vertex, get all HabitCompletion vertices for the week:
        f"g.V(character_id).out('hasHabit').as_('habit')"
        f".out('hasCompletion').hasLabel('HabitCompletion')"
        f".has('completion_date', between(start_date, end_date)).as_('completion')"
        f".select('habit', 'completion')"
        f".by(valueMap(true))"
        f".by(valueMap())"
    )

    query = f"""
    g.V('{character_id}')
     .out('hasHabit').as('habit')
     .out('hasCompletion').hasLabel('HabitCompletion')
     .has('completion_date', between('{start_date}', '{end_date}'))
     .as('completion')
     .select('habit', 'completion')
     .by(valueMap(true))
     .by(valueMap())
    """

    result = run_query(query)

    return result

def get_current_day_completions(character_id: str, today: datetime):

    query = f"""
    g.V('{character_id}')
     .out('hasHabit').as('habit')
     .out('hasCompletion').hasLabel('HabitCompletion')
     .has('completion_date', '{today}')
     .as('completion')
     .select('habit', 'completion')
     .by(valueMap(true))
     .by(valueMap())
    """

    single_query = f"g.V().hasLabel('Habit').has('character_id').elementMap()"

    second_query = {
        f"g.V(habit_id).out('hasCompletion')"
        f".hasLabel('HabitCompletion')"
        f".has('completion_date', between(start_date, end_date))"
        f".values('completion_date')"
    }
    result = run_query(query)

    return result
