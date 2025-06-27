# backend/app/neptune_client.py
import logging
import os

from typing import List, Any
from gremlin_python.driver import client, serializer
from pydantic.v1.networks import host_regex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the Neptune endpoint from an environment variable or hardcode for development.
NEPTUNE_ENDPOINT = os.getenv("NEPTUNE_ENDPOINT", "ws://localhost:8182/gremlin")
NEPTUNE_PORT = os.getenv("NEPTUNE_PORT", 8182)

# Create a Gremlin client using GraphSON v2 serializer
gremlin_client = client.Client(NEPTUNE_ENDPOINT, 'g',
    message_serializer=serializer.GraphSONSerializersV3d0()
)


def run_query(query: str) -> List[Any]:
    """Submit a Gremlin query and return all results with better error handling."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    try:
        callback = gremlin_client.submit_async(query)
        if callback.result() is not None:
            result = callback.result().all().result()
            logger.info(f"Query executed successfully: {query[:100]}...")
            return result
        return []
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise RuntimeError("Database connection failed")
    except Exception as e:
        logger.error(f"Error running query: {query}\nException: {e}")
        raise RuntimeError(f"Database query failed: {str(e)}")

def debug_character_habits(character_id: str):
    """Debug function to check Character -> Habit relationships"""
    query = (
        f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
        f".out('hasHabit').hasLabel('Habit')"
        f".valueMap('habit_id', 'habit_name')"
    )
    result = run_query(query)
    print(f"Habits for character {character_id}: {result}")
    return result

def debug_habit_completions(habit_id: str):
    """Debug function to check Habit -> Completion relationships"""
    query = (
        f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}')"
        f".out('hasCompletion').hasLabel('HabitCompletion')"
        f".valueMap('completion_date', 'completed')"
    )
    result = run_query(query)
    print(f"Completions for habit {habit_id}: {result}")
    return result

def debug_full_path(character_id: str):
    """Debug the full Character -> Habit -> Completion path"""
    query = (
        f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
        f".out('hasHabit').hasLabel('Habit').as('habit')"
        f".out('hasCompletion').hasLabel('HabitCompletion').as('completion')"
        f".select('habit', 'completion')"
        f".by(valueMap('habit_id', 'habit_name'))"
        f".by(valueMap('completion_date', 'completed'))"
    )
    result = run_query(query)
    print(f"Full path for character {character_id}: {result}")
    return result


def init_neptune_client():
    """Initialize the Gremlin client."""
    global neptune_client
    host = NEPTUNE_ENDPOINT
    port = NEPTUNE_PORT
    url = f"ws://{host}:{port}/gremlin"

    neptune_client = client.Client(
        url,
        'g',
        username="",
        password="",
        message_serializer=serializer.GraphSONSerializersV3d0()()
    )
    print(f"Gremlin client initialized: {url}")


def close_neptune_client():
    global neptune_client
    if neptune_client:
        neptune_client.close()
        print(f"Neptune client closed")
    neptune_client = None

