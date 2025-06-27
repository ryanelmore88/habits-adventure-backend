# backend/app/models/habit.py - Enhanced version with better completion tracking

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
    """Enhanced habit completion with better tracking"""
    # Default to today's date if not provided.
    if completion_date is None:
        completion_date = datetime.date.today().isoformat()

    # Debug: log the values
    print(f"Updating habit completion for habit_id: {habit_id} on {completion_date}, completed: {completed}")

    # Check if completion already exists for this date
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

        # If marking as incomplete, we might want to remove the completion entirely
        if not completed:
            query_delete = f"g.V('{existing_completion_id}').drop()"
            run_query(query_delete)
            return {"completion_id": existing_completion_id, "action": "deleted", "result": result}

        return {"completion_id": existing_completion_id, "action": "updated", "result": result}
    else:
        # No existing completion for this date
        if completed:
            # Create a new completion vertex only if marking as complete
            return create_completion(habit_id, completion_date, completed)
        else:
            # If trying to mark as incomplete but no completion exists, do nothing
            return {"message": "No completion to remove for this date"}


def get_habit_with_completions(habit_id: str):
    """
    Retrieve a habit vertex with its completion data for the frontend
    """
    # Get basic habit data
    query = f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}').elementMap()"
    result = run_query(query)
    if not result:
        return None

    habit_data = result[0]

    # Get all completions for this habit
    completions_query = (
        f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}')"
        f".outE('hasCompletion').inV().hasLabel('HabitCompletion')"
        f".has('completed', true)"  # Only get completed ones
        f".values('completion_date')"
    )
    completions_result = run_query(completions_query)

    # Extract completion dates
    completion_dates = completions_result if completions_result else []

    # Parse the JSON completion history for backwards compatibility
    completion_history = habit_data.get("completion_history")
    if isinstance(completion_history, list):
        completion_history = completion_history[0]
    try:
        legacy_completions = json.loads(completion_history) if completion_history else []
    except Exception:
        legacy_completions = []

    # Combine legacy and new completion data
    all_completions = list(set(completion_dates + legacy_completions))

    habit = {
        "habit_id": habit_data.get("habit_id"),
        "character_id": habit_data.get("character_id"),
        "habit_name": habit_data.get("habit_name"),
        "attribute": habit_data.get("attribute"),
        "description": habit_data.get("description"),
        "completion_history": legacy_completions,  # Keep for backwards compatibility
        "completions": all_completions,  # New format for frontend
        "completed": False  # Will be set by frontend based on selected date
    }
    return habit


def get_all_habits_with_completions(character_id: str):
    """
    Retrieve all habits for a character with their completion data
    """
    # Get all habits for the character
    query = (
        f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
        f".out('hasHabit').hasLabel('Habit').elementMap()"
    )
    result = run_query(query)

    if not result:
        return []

    habits_with_completions = []

    for habit_data in result:
        habit_id = habit_data.get("habit_id")

        # Get completions for this habit
        completions_query = (
            f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}')"
            f".outE('hasCompletion').inV().hasLabel('HabitCompletion')"
            f".has('completed', true)"
            f".values('completion_date')"
        )
        completions_result = run_query(completions_query)
        completion_dates = completions_result if completions_result else []

        # Parse legacy completion history
        completion_history = habit_data.get("completion_history")
        if isinstance(completion_history, list):
            completion_history = completion_history[0]
        try:
            legacy_completions = json.loads(completion_history) if completion_history else []
        except Exception:
            legacy_completions = []

        # Combine all completion data
        all_completions = list(set(completion_dates + legacy_completions))

        habit = {
            "habit_id": habit_data.get("habit_id"),
            "character_id": habit_data.get("character_id"),
            "habit_name": habit_data.get("habit_name"),
            "attribute": habit_data.get("attribute"),
            "description": habit_data.get("description"),
            "completion_history": legacy_completions,
            "completions": all_completions,
            "completed": False  # Frontend will determine based on selected date
        }
        habits_with_completions.append(habit)

    return habits_with_completions


# Update the existing functions to use the new enhanced versions
def get_habit(habit_id: str):
    """Wrapper for backwards compatibility"""
    return get_habit_with_completions(habit_id)


def get_all_habits(character_id: str):
    """Enhanced version that returns habits with completion data"""
    return get_all_habits_with_completions(character_id)


# Keep all other existing functions unchanged...
def get_completions_for_habit(habit_id: str):
    """
    Retrieve all completion vertices associated with a habit.
    """
    query = f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}').outE('hasCompletion').inV().elementMap()"
    result = run_query(query)
    return result


def get_habits_for_attribute(character_id: str, attribute: str):
    """Enhanced to include completion data"""
    query = f"g.V().hasLabel('Habit').has('character_id', '{character_id}').has('attribute', '{attribute}').elementMap()"
    result = run_query(query)

    # Enhance each habit with completion data
    enhanced_habits = []
    for habit_data in result:
        habit_id = habit_data.get("habit_id")
        if habit_id:
            enhanced_habit = get_habit_with_completions(habit_id)
            if enhanced_habit:
                enhanced_habits.append(enhanced_habit)

    return enhanced_habits


def delete_habit(habit_id: str):
    """
    Delete a habit vertex from the graph database using its ID.
    """
    query = f"g.V().hasLabel('Habit').has('habit_id', '{habit_id}').drop()"
    result = run_query(query)
    return result


def get_current_week_completions(character_id: str, start_date: datetime, end_date: datetime):
    """Enhanced with path validation"""
    start_date_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
    end_date_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)

    # First, verify the character exists
    char_check = f"g.V().hasLabel('Character').has('character_id', '{character_id}').count()"
    if not run_query(char_check) or run_query(char_check)[0] == 0:
        print(f"Character {character_id} not found")
        return []

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
    print(f"Week completions query returned: {len(result) if result else 0} results")
    return result or []


def get_habits_for_character(character_id: str):
    """
    Get all habits for a character - compatibility function for the auth router
    This function provides the interface expected by the new authenticated router
    """
    if not character_id or not character_id.strip():
        raise ValueError("Character ID cannot be empty")

    try:
        # Use the existing function that gets all habits with completions
        return get_all_habits_with_completions(character_id)
    except Exception as e:
        print(f"Error getting habits for character {character_id}: {e}")
        raise e

def get_habit_by_id(habit_id: str):
    """
    Retrieve a habit by its ID
    This is an alias for get_habit for clarity
    """
    return get_habit(habit_id)


def get_current_day_completions(character_id: str, today: datetime):
    """
    Get habit completions for a character for a specific day
    """
    today_str = today.strftime('%Y-%m-%d') if hasattr(today, 'strftime') else str(today)

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