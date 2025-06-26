from fastapi import APIRouter, HTTPException

from app.models.completion import get_completion

router = APIRouter(tags=["completion"])

@router.get("/api/completion/{completion_id}", summary="Retrieve a habit completion")
def read_completion(completion_id: str):
    completion = get_completion(completion_id)
    if not completion:
        raise HTTPException(status_code=404, detail="Completion not found")
    return {"status": "success", "data": completion}