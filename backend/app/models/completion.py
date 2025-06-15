import datetime
import json
import uuid
from gremlin_python.process.traversal import T
from app.neptune_client import run_query


def create_completion(habit_id: str, completion_date: str, completed: bool = True):
    """
    Create a new HabitCompletion vertex and link it to the Habit vertex.
    All IDs are treated as strings.
    """
    # Generate a unique completion_id as a string.
    completion_id = str(uuid.uuid4().int % (2 ** 63))

    # Build the Gremlin query.
    # Note: Wrap string values in quotes.
    query = (
        f"g.addV('HabitCompletion')"
        f".property(id, '{completion_id}')"
        f".property('completion_date', '{completion_date}')"
        f".property('completed', {str(completed).lower()})"
        f".as('completion')"
        f".V().hasLabel('Habit').has('habit_id', '{habit_id}')"
        f".addE('hasCompletion').to('completion')"
        f".iterate()"
    )

    result = run_query(query)
    return {"completion_id": completion_id, "result": result}

def get_completions_for_habit(habit_id: str):
    """
    Retrieve all completion vertices associated with a habit.
    """
    query = (
        f"g.V('{habit_id}').outE('hasCompletion').inV().elementMap(true)"
    )
    result = run_query(query)
    # Depending on how your Gremlin server returns results, you might need to process them.
    return result

def get_completion(completion_id: str):
    """
    Retrieve a completion vertex.
    :param completion_id:
    :return: completion data
    """
    query = (
        f"g.V('{completion_id}').elementMap()"
    )

    result = run_query(query)
    return result
