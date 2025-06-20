# File: backend/app/routers/enemy.py
# API endpoints for enemy management

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.models.enemy import (
    create_enemy_templates,
    get_all_enemy_templates,
    get_enemy_template,
    get_enemies_by_difficulty,
    get_enemies_by_environment,
    create_enemy_instance,
    create_enemy_template,
    update_enemy_template,
    delete_enemy_template
)

router = APIRouter(tags=["enemy"])


class EnemyTemplateCreateRequest(BaseModel):
    enemy_id: str
    name: str
    level: int
    max_hp: int
    dice_pool: str
    xp_reward: int
    loot_table: List[str]
    description: str
    difficulty: str
    environment: List[str]


class EnemyTemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    max_hp: Optional[int] = None
    dice_pool: Optional[str] = None
    xp_reward: Optional[int] = None
    loot_table: Optional[List[str]] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    environment: Optional[List[str]] = None


@router.post("/enemy/initialize", summary="Initialize default enemy templates")
def initialize_enemy_templates():
    """
    Create the default enemy templates in the database.
    This should be called once during application setup.
    """
    try:
        result = create_enemy_templates()
        return {
            "status": "success",
            "message": f"Initialized {len(result)} enemy templates",
            "data": result
        }
    except Exception as e:
        print(f"Error initializing enemy templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize enemy templates")


@router.get("/enemy/templates", summary="Get all enemy templates")
def get_enemy_templates():
    """
    Retrieve all available enemy templates.
    """
    try:
        templates = get_all_enemy_templates()
        return {"status": "success", "data": templates}
    except Exception as e:
        print(f"Error fetching enemy templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch enemy templates")


@router.get("/enemy/template/{enemy_id}", summary="Get specific enemy template")
def get_specific_enemy_template(enemy_id: str):
    """
    Retrieve a specific enemy template by ID.
    """
    try:
        template = get_enemy_template(enemy_id)
        if not template:
            raise HTTPException(status_code=404, detail="Enemy template not found")
        return {"status": "success", "data": template}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching enemy template {enemy_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch enemy template")


@router.get("/enemy/difficulty/{difficulty}", summary="Get enemies by difficulty")
def get_enemies_by_difficulty_level(difficulty: str):
    """
    Get enemy templates filtered by difficulty level.
    Valid difficulties: Easy, Medium, Hard, Legendary
    """
    try:
        valid_difficulties = ["Easy", "Medium", "Hard", "Legendary"]
        if difficulty not in valid_difficulties:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid difficulty. Must be one of: {valid_difficulties}"
            )

        enemies = get_enemies_by_difficulty(difficulty)
        return {"status": "success", "data": enemies}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching enemies by difficulty {difficulty}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch enemies by difficulty")


@router.get("/enemy/environment/{environment}", summary="Get enemies by environment")
def get_enemies_by_environment_type(environment: str):
    """
    Get enemy templates that can appear in a specific environment.
    Common environments: forest, caves, ruins, mountains, swamps, crypts
    """
    try:
        enemies = get_enemies_by_environment(environment)
        return {"status": "success", "data": enemies}
    except Exception as e:
        print(f"Error fetching enemies by environment {environment}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch enemies by environment")


@router.post("/enemy/instance/{template_id}", summary="Create enemy instance for combat")
def create_combat_enemy_instance(
        template_id: str,
        character_level: int = Query(1, description="Character level for scaling enemy difficulty")
):
    """
    Create an enemy instance from a template for combat.
    The enemy will be optionally scaled based on character level.
    """
    try:
        instance = create_enemy_instance(template_id, character_level)
        if not instance:
            raise HTTPException(status_code=404, detail="Enemy template not found")
        return {"status": "success", "data": instance}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating enemy instance: {e}")
        raise HTTPException(status_code=500, detail="Failed to create enemy instance")


@router.post("/enemy/template", summary="Create new enemy template")
def create_new_enemy_template(enemy: EnemyTemplateCreateRequest):
    """
    Create a new custom enemy template.
    """
    try:
        enemy_data = enemy.dict()
        result = create_enemy_template(enemy_data)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create enemy template")
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating enemy template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create enemy template")


@router.put("/enemy/template/{enemy_id}", summary="Update enemy template")
def update_existing_enemy_template(enemy_id: str, updates: EnemyTemplateUpdateRequest):
    """
    Update an existing enemy template.
    Only provided fields will be updated.
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No valid updates provided")

        result = update_enemy_template(enemy_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Enemy template not found")

        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating enemy template {enemy_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update enemy template")


@router.delete("/enemy/template/{enemy_id}", summary="Delete enemy template")
def delete_existing_enemy_template(enemy_id: str):
    """
    Delete an enemy template from the database.
    """
    try:
        success = delete_enemy_template(enemy_id)
        if not success:
            raise HTTPException(status_code=404, detail="Enemy template not found")

        return {"status": "success", "message": f"Enemy template {enemy_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting enemy template {enemy_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete enemy template")


# Legacy compatibility endpoint for the existing adventure system
@router.get("/enemy/available", summary="Get available enemies for combat selection")
def get_available_enemies_for_combat():
    """
    Legacy endpoint that returns available enemies in the format expected by the existing combat system.
    This maintains compatibility while transitioning to the new database-driven system.
    """
    try:
        templates = get_all_enemy_templates()

        # Convert to the format expected by the existing frontend
        available_enemies = []
        for template in templates:
            available_enemies.append(template['enemy_id'].replace('template_', ''))

        return {
            "status": "success",
            "available_enemies": available_enemies,
            "enemy_templates": {
                template['enemy_id'].replace('template_', ''): {
                    "name": template['name'],
                    "level": template['level'],
                    "maxHp": template['max_hp'],
                    "dicePool": template['dice_pool'],
                    "xpReward": template['xp_reward'],
                    "lootTable": template['loot_table'],
                    "description": template['description']
                } for template in templates
            }
        }
    except Exception as e:
        print(f"Error fetching available enemies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch available enemies")