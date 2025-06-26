import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.models.habit import create_habit, update_habit_completion, get_habit, get_completions_for_habit, \
    get_habits_for_attribute, get_all_habits, delete_habit, get_current_week_completions, get_current_day_completions
from app.models.completion import get_completion

router = APIRouter(tags=["habit"])

class HabitCreateRequest(BaseModel):
    character_id: str
    habit_name: str
    attribute: str
    description: str = ""

@router.post("/habit", summary="Create a new habit")
def add_habit(habit: HabitCreateRequest):
    result = create_habit(
        character_id=habit.character_id,
        habit_name=habit.habit_name,
        attribute=habit.attribute,
        description=habit.description
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create habit")
    return {"status": "success", "data": result}

class HabitCompletionRequest(BaseModel):
    habit_id: str
    completion_date: str  # Format "YYYY-MM-DD"
    completed: bool = True

@router.post("/habit/completion", summary="Mark a habit as completed, Format YYYY-MM-DD")
def add_habit_completion(completion: HabitCompletionRequest):
    result = update_habit_completion(
        habit_id=completion.habit_id,
        completion_date=completion.completion_date,
        completed=completion.completed
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to add completion record")
    return {"status": "success", "data": result}

@router.get("/habit/{habit_id}", summary="Retrieve a habit by ID")
def read_habit(habit_id: str):
    habit = get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"status": "success", "data": habit}

@router.get("/habit/{habit_id}/completions", summary="Get completions for a habit")
def read_habit_completions(habit_id: str):
    completions = get_completions_for_habit(habit_id)
    if completions is None:
        raise HTTPException(status_code=404, detail="Habit completions not found")
    return {"status": "success", "data": completions}

@router.get("/habit", summary="Retrieve habits for a character and attribute")
def read_habits(character_id: str = Query(...), attribute: str = Query(...)):
    habits = get_habits_for_attribute(character_id, attribute.lower())
    if habits is None:
        raise HTTPException(status_code=404, detail="Habits not found")
    return {"status": "success", "data": habits}


    return {"status": "success", "data": habits}

@router.delete("/habit/{habit_id}", summary="Delete a habit by ID")
def delete_habit_endpoint(habit_id: str):
    result = delete_habit(habit_id)
    # If drop() returns an empty list on success, consider that a success.
    return {"status": "success", "message": f"Habit {habit_id} deleted", "result": result}

@router.get("/habit/completions/week", summary="Get current week completions for a given character")
def week_completions(
    character_id: str = Query(...)
):
    today = datetime.date.today()
    # Using isoweekday: Monday=1, ... Sunday=7.
    # Compute days to subtract: if today is Sunday (7), then 7% 7 = 0 (i.e start_date is today.)
    start_date = today - datetime.timedelta(days=today.isoweekday() % 7)
    end_date = start_date + datetime.timedelta(days=6)
    data = get_current_week_completions(character_id, start_date, end_date)
    print(f"{character_id}, today: {today} Start Date {start_date}, End Date {end_date}")
    if not data or len(data) == 0:
        raise HTTPException(status_code=404, detail="No habit completions found for the specified week")
    return {"status": "success", "data": data}

@router.get("/habit/completions/day", summary="Get current day completions for a given character")
def day_completions(
    character_id: str = Query(...)
):
    data = get_current_day_completions(character_id, datetime.date.today())
    if not data or len(data) == 0:
        raise HTTPException(status_code=404, detail="No habit completions found for the specified day")
    return {"status": "success", "data": data}