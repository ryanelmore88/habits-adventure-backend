# File: backend/app/models/enemy.py
# Enemy management and database operations

import json
import uuid
from app.neptune_client import run_query
from typing import List, Dict, Optional


def create_enemy_templates():
    """
    Initialize the default enemy templates in the database.
    This should be run once during application setup.
    """
    enemy_templates = [
        {
            "enemy_id": "template_goblin",
            "name": "Goblin",
            "level": 1,
            "max_hp": 7,
            "dice_pool": "2d4",
            "xp_reward": 25,
            "loot_table": ["potion", "coins"],
            "description": "A small, green-skinned humanoid with sharp teeth and cunning eyes.",
            "difficulty": "Easy",
            "environment": ["forest", "caves", "ruins"]
        },
        {
            "enemy_id": "template_orc",
            "name": "Orc",
            "level": 2,
            "max_hp": 15,
            "dice_pool": "3d4",
            "xp_reward": 50,
            "loot_table": ["weapon", "coins", "potion"],
            "description": "A brutish humanoid with gray skin and prominent tusks.",
            "difficulty": "Medium",
            "environment": ["mountains", "ruins", "strongholds"]
        },
        {
            "enemy_id": "template_skeleton",
            "name": "Skeleton",
            "level": 1,
            "max_hp": 13,
            "dice_pool": "2d4+1",
            "xp_reward": 30,
            "loot_table": ["bones", "coins"],
            "description": "The animated bones of a long-dead warrior.",
            "difficulty": "Easy",
            "environment": ["crypts", "ruins", "battlefields"]
        },
        {
            "enemy_id": "template_troll",
            "name": "Troll",
            "level": 5,
            "max_hp": 84,
            "dice_pool": "6d4+2",
            "xp_reward": 200,
            "loot_table": ["rare_weapon", "gold", "gem"],
            "description": "A massive, regenerating creature with claws and an insatiable hunger.",
            "difficulty": "Hard",
            "environment": ["swamps", "mountains", "deep_caves"]
        },
        {
            "enemy_id": "template_dark_knight",
            "name": "Dark Knight",
            "level": 4,
            "max_hp": 65,
            "dice_pool": "4d6",
            "xp_reward": 150,
            "loot_table": ["armor"],
            "description": "A fallen paladin clad in blackened plate armor.",
            "difficulty": "Hard",
            "environment": ["swamps", "mountains", "deep_caves"]
        },
        {
            "enemy_id": "template_young_dragon",
            "name": "Young Dragon",
            "level": 5,
            "max_hp": 84,
            "dice_pool": "2d12",
            "xp_reward": 400,
            "loot_table": ["dragon_scale", "gold", "gem"],
            "description": "A young but powerful dragon with scales that gleam like metal.",
            "difficulty": "Legendary",
            "environment": ["mountains", "deep_caves", "ancient_ruins"]
        },
        {
            "enemy_id": "template_ancient_dragon",
            "name": "Ancient Dragon",
            "level": 10,
            "max_hp": 200,
            "dice_pool": "20d12",
            "xp_reward": 4000,
            "loot_table": ["dragon_scale", "gold", "gem"],
            "description": "A massive, ancient dragon with scales like molten metal..",
            "difficulty": "Legendary",
            "environment": ["mountains", "deep_caves", "ancient_ruins"]
        }
    ]

    created_enemies = []
    for template in enemy_templates:
        result = create_enemy_template(template)
        if result:
            created_enemies.append(result)

    return created_enemies


def create_enemy_template(enemy_data: Dict) -> Optional[Dict]:
    """
    Create an enemy template in the database.
    """
    try:
        # Convert lists to JSON strings for storage
        loot_table_json = json.dumps(enemy_data.get("loot_table", []))
        environment_json = json.dumps(enemy_data.get("environment", []))

        query = (
            f"g.addV('EnemyTemplate')"
            f".property('enemy_id', '{enemy_data['enemy_id']}')"
            f".property('name', '{enemy_data['name']}')"
            f".property('level', {enemy_data['level']})"
            f".property('max_hp', {enemy_data['max_hp']})"
            f".property('dice_pool', '{enemy_data['dice_pool']}')"
            f".property('xp_reward', {enemy_data['xp_reward']})"
            f".property('loot_table', '{loot_table_json}')"
            f".property('description', '{enemy_data['description']}')"
            f".property('difficulty', '{enemy_data['difficulty']}')"
            f".property('environment', '{environment_json}')"
            f".elementMap()"
        )

        result = run_query(query)
        if result:
            return parse_enemy_template(result[0])
        return None

    except Exception as e:
        print(f"Error creating enemy template: {e}")
        return None


def get_all_enemy_templates() -> List[Dict]:
    """
    Retrieve all enemy templates from the database.
    """
    try:
        query = "g.V().hasLabel('EnemyTemplate').elementMap()"
        result = run_query(query)

        return [parse_enemy_template(template) for template in result]

    except Exception as e:
        print(f"Error fetching enemy templates: {e}")
        return []


def get_enemy_template(enemy_id: str) -> Optional[Dict]:
    """
    Retrieve a specific enemy template by ID.
    """
    try:
        query = f"g.V().hasLabel('EnemyTemplate').has('enemy_id', '{enemy_id}').elementMap()"
        result = run_query(query)

        if result:
            return parse_enemy_template(result[0])
        return None

    except Exception as e:
        print(f"Error fetching enemy template {enemy_id}: {e}")
        return None


def get_enemies_by_difficulty(difficulty: str) -> List[Dict]:
    """
    Get enemy templates filtered by difficulty level.
    """
    try:
        query = f"g.V().hasLabel('EnemyTemplate').has('difficulty', '{difficulty}').elementMap()"
        result = run_query(query)

        return [parse_enemy_template(template) for template in result]

    except Exception as e:
        print(f"Error fetching enemies by difficulty {difficulty}: {e}")
        return []


def get_enemies_by_environment(environment: str) -> List[Dict]:
    """
    Get enemy templates that can appear in a specific environment.
    """
    try:
        # This requires a more complex query since environment is stored as JSON
        query = f"g.V().hasLabel('EnemyTemplate').where(__.values('environment').is(containing('{environment}'))).elementMap()"
        result = run_query(query)

        # Filter on the application side for more reliable results
        enemies = [parse_enemy_template(template) for template in result]
        return [enemy for enemy in enemies if environment in enemy.get('environment', [])]

    except Exception as e:
        print(f"Error fetching enemies by environment {environment}: {e}")
        return []


def create_enemy_instance(template_id: str, character_level: int = 1) -> Optional[Dict]:
    """
    Create an enemy instance from a template for combat.
    Optionally scale the enemy based on character level.
    """
    template = get_enemy_template(template_id)
    if not template:
        return None

    # Generate unique instance ID
    instance_id = f"enemy_{uuid.uuid4().hex[:8]}"

    # Scale enemy stats based on character level (optional enhancement)
    level_modifier = max(1, character_level // 2)
    scaled_hp = template['max_hp'] + (level_modifier - 1) * 5
    scaled_xp = template['xp_reward'] + (level_modifier - 1) * 10

    enemy_instance = {
        "instance_id": instance_id,
        "template_id": template_id,
        "name": template['name'],
        "level": template['level'] + max(0, level_modifier - 1),
        "max_hp": scaled_hp,
        "current_hp": scaled_hp,
        "dice_pool": template['dice_pool'],
        "xp_reward": scaled_xp,
        "loot_table": template['loot_table'],
        "description": template['description'],
        "difficulty": template['difficulty'],
        "environment": template['environment']
    }

    return enemy_instance


def parse_enemy_template(template_data: Dict) -> Dict:
    """
    Parse enemy template data from database format to application format.
    """
    try:
        # Parse JSON fields
        loot_table = template_data.get("loot_table")
        if isinstance(loot_table, list):
            loot_table = loot_table[0] if loot_table else "[]"
        loot_table = json.loads(loot_table) if loot_table else []

        environment = template_data.get("environment")
        if isinstance(environment, list):
            environment = environment[0] if environment else "[]"
        environment = json.loads(environment) if environment else []

        return {
            "enemy_id": template_data.get("enemy_id"),
            "name": template_data.get("name"),
            "level": template_data.get("level"),
            "max_hp": template_data.get("max_hp"),
            "dice_pool": template_data.get("dice_pool"),
            "xp_reward": template_data.get("xp_reward"),
            "loot_table": loot_table,
            "description": template_data.get("description"),
            "difficulty": template_data.get("difficulty"),
            "environment": environment
        }
    except Exception as e:
        print(f"Error parsing enemy template: {e}")
        return {}


def update_enemy_template(enemy_id: str, updates: Dict) -> Optional[Dict]:
    """
    Update an existing enemy template.
    """
    try:
        # Build update query dynamically based on provided fields
        update_parts = []
        for key, value in updates.items():
            if key in ['loot_table', 'environment'] and isinstance(value, list):
                value = json.dumps(value)
            if isinstance(value, str):
                update_parts.append(f".property('{key}', '{value}')")
            else:
                update_parts.append(f".property('{key}', {value})")

        if not update_parts:
            return None

        query = (
            f"g.V().hasLabel('EnemyTemplate').has('enemy_id', '{enemy_id}')"
            f"{''.join(update_parts)}"
            f".elementMap()"
        )

        result = run_query(query)
        if result:
            return parse_enemy_template(result[0])
        return None

    except Exception as e:
        print(f"Error updating enemy template {enemy_id}: {e}")
        return None


def delete_enemy_template(enemy_id: str) -> bool:
    """
    Delete an enemy template from the database.
    """
    try:
        query = f"g.V().hasLabel('EnemyTemplate').has('enemy_id', '{enemy_id}').drop()"
        result = run_query(query)
        return True

    except Exception as e:
        print(f"Error deleting enemy template {enemy_id}: {e}")
        return False