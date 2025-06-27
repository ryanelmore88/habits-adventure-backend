# backend/app/routers/adventure.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.models.character import get_character, update_character_hp
from app.neptune_client import run_query
from app.routers.auth import get_current_user
from app.models.user import get_user_characters

router = APIRouter(prefix="/adventure", tags=["adventure"])


# Pydantic models for request/response validation
class LootItem(BaseModel):
    type: str
    quantity: int
    id: str


class AdventureResults(BaseModel):
    characterId: str
    hpChange: int
    xpGained: int
    loot: List[LootItem]
    victory: bool


class AdventureResponse(BaseModel):
    status: str
    message: str
    rewards: Dict[str, int]

# Add this function after imports:
def verify_character_ownership(character_id: str, user_id: str) -> bool:
    """Verify that a user owns a specific character"""
    user_characters = get_user_characters(user_id)
    return any(char["character_id"] == character_id for char in user_characters)


# Helper functions
def update_character_xp(character_id: str, xp_gained: int) -> dict:
    """
    Update character's experience points
    """
    try:
        # Get current XP
        get_query = (
            f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
            f".project('current_xp', 'level')"
            f".by(coalesce(values('current_xp'), constant(0)))"
            f".by(coalesce(values('level'), constant(1)))"
        )
        result = run_query(get_query)

        if not result:
            raise ValueError("Character not found")

        current_xp = result[0].get('current_xp', 0)
        current_level = result[0].get('level', 1)
        new_xp = current_xp + xp_gained

        # Simple leveling system: 100 XP per level
        xp_for_next_level = current_level * 100
        new_level = current_level

        while new_xp >= xp_for_next_level:
            new_level += 1
            xp_for_next_level = new_level * 100

        # Update in database
        update_query = (
            f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
            f".property('current_xp', {new_xp})"
            f".property('level', {new_level})"
        )
        run_query(update_query)

        return {
            "character_id": character_id,
            "previous_xp": current_xp,
            "current_xp": new_xp,
            "previous_level": current_level,
            "current_level": new_level,
            "xp_gained": xp_gained,
            "leveled_up": new_level > current_level
        }

    except Exception as e:
        print(f"Error updating character XP: {e}")
        raise e


def add_loot_to_inventory(character_id: str, loot_items: List[dict]) -> dict:
    """
    Add loot items to character's inventory
    For now, just store as simple properties on the character
    """
    try:
        items_added = []

        for item in loot_items:
            item_type = item.get('type', 'unknown')
            quantity = item.get('quantity', 1)
            item_id = item.get('id', f"item_{len(items_added)}")

            # Get current quantity of this item type
            get_query = (
                f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
                f".coalesce(values('inventory_{item_type}'), constant(0))"
            )
            current_quantity = run_query(get_query)
            current_qty = current_quantity[0] if current_quantity else 0

            # Update quantity
            new_quantity = current_qty + quantity
            update_query = (
                f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
                f".property('inventory_{item_type}', {new_quantity})"
            )
            run_query(update_query)

            items_added.append({
                "type": item_type,
                "quantity_added": quantity,
                "total_quantity": new_quantity
            })

        return {
            "character_id": character_id,
            "items_added": items_added,
            "total_items": len(items_added)
        }

    except Exception as e:
        print(f"Error adding loot to inventory: {e}")
        raise e


def validate_adventure_results(results: dict) -> dict:
    """
    Basic validation to prevent extreme cheating
    """
    validated = results.copy()

    # Reasonable limits per adventure
    MAX_XP_PER_ADVENTURE = 500
    MAX_LOOT_ITEMS = 10
    MAX_HP_GAIN = 50  # Healing items
    MAX_HP_LOSS = 100  # Prevent instant death exploits

    # Validate XP
    if validated.get('xpGained', 0) > MAX_XP_PER_ADVENTURE:
        print(f"Warning: XP gain {validated['xpGained']} exceeds maximum, capping at {MAX_XP_PER_ADVENTURE}")
        validated['xpGained'] = MAX_XP_PER_ADVENTURE

    if validated.get('xpGained', 0) < 0:
        validated['xpGained'] = 0

    # Validate loot
    loot = validated.get('loot', [])
    if len(loot) > MAX_LOOT_ITEMS:
        print(f"Warning: Loot count {len(loot)} exceeds maximum, truncating to {MAX_LOOT_ITEMS}")
        validated['loot'] = loot[:MAX_LOOT_ITEMS]

    # Validate HP change
    hp_change = validated.get('hpChange', 0)
    if hp_change > MAX_HP_GAIN:
        print(f"Warning: HP gain {hp_change} exceeds maximum, capping at {MAX_HP_GAIN}")
        validated['hpChange'] = MAX_HP_GAIN
    elif hp_change < -MAX_HP_LOSS:
        print(f"Warning: HP loss {abs(hp_change)} exceeds maximum, capping at {MAX_HP_LOSS}")
        validated['hpChange'] = -MAX_HP_LOSS

    return validated


# API Endpoints
@router.post("/{character_id}/complete", response_model=AdventureResponse)
def complete_adventure(
    character_id: str,
    results: AdventureResults,
    current_user: dict = Depends(get_current_user)
) -> AdventureResponse:
    """
    Called once when adventure is complete
    Updates character HP, XP, and inventory
    """
    try:

        # Verify user owns this character
        if not verify_character_ownership(character_id, current_user["user_id"]):
            raise HTTPException(status_code=403, detail="You don't have access to this character")
        # Validate character exists
        character = get_character(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        # Convert Pydantic model to dict and validate
        results_dict = results.dict()
        validated_results = validate_adventure_results(results_dict)

        rewards = {
            "hp_change": 0,
            "xp_gained": 0,
            "loot_count": 0,
            "levels_gained": 0
        }

        # Update HP if changed
        hp_change = validated_results.get('hpChange', 0)
        if hp_change != 0:
            hp_update = update_character_hp(character_id, hp_change)
            rewards["hp_change"] = hp_change
            print(f"Updated HP for character {character_id}: {hp_update}")

        # Update XP if gained
        xp_gained = validated_results.get('xpGained', 0)
        if xp_gained > 0:
            xp_update = update_character_xp(character_id, xp_gained)
            rewards["xp_gained"] = xp_gained
            rewards["levels_gained"] = xp_update["current_level"] - xp_update["previous_level"]
            print(f"Updated XP for character {character_id}: {xp_update}")

        # Add loot to inventory
        loot = validated_results.get('loot', [])
        if loot:
            loot_update = add_loot_to_inventory(character_id, loot)
            rewards["loot_count"] = len(loot)
            print(f"Added loot for character {character_id}: {loot_update}")

        # Determine success message
        victory = validated_results.get('victory', False)
        if victory:
            message = f"Adventure completed successfully! Gained {xp_gained} XP and {len(loot)} items."
        else:
            message = "Adventure ended. You fought bravely but were defeated."

        if rewards["levels_gained"] > 0:
            message += f" You gained {rewards['levels_gained']} level(s)!"

        return AdventureResponse(
            status="success",
            message=message,
            rewards=rewards
        )

    except ValueError as ve:
        print(f"Validation error in complete_adventure: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error in complete_adventure: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete adventure")


@router.get("/enemy-templates")
def get_enemy_templates():
    """
    Get available enemy templates for frontend combat
    """
    enemy_templates = {
        "goblin": {
            "name": "Goblin",
            "level": 1,
            "maxHp": 7,
            "attackBonus": 4,
            "damageDice": "1d6+2",
            "xpReward": 25,
            "description": "A small, green-skinned creature with sharp teeth and a nasty disposition."
        },
        "orc": {
            "name": "Orc",
            "level": 2,
            "maxHp": 15,
            "attackBonus": 5,
            "damageDice": "1d8+3",
            "xpReward": 50,
            "description": "A brutish humanoid with gray skin and prominent tusks."
        },
        "skeleton": {
            "name": "Skeleton",
            "level": 1,
            "maxHp": 5,
            "attackBonus": 3,
            "damageDice": "1d6+1",
            "xpReward": 20,
            "description": "The animated bones of a long-dead warrior."
        },
        "troll": {
            "name": "Troll",
            "level": 5,
            "maxHp": 84,
            "attackBonus": 7,
            "damageDice": "2d6+4",
            "xpReward": 200,
            "description": "A massive, regenerating creature with claws and an insatiable hunger."
        }
    }

    return {
        "status": "success",
        "enemies": enemy_templates
    }


@router.get("/{character_id}/status")
def get_adventure_status(character_id: str):
    """
    Get character's current adventure-related status
    """
    try:
        character = get_character(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        # Get inventory items (items that start with "inventory_")
        inventory_query = (
            f"g.V().hasLabel('Character').has('character_id', '{character_id}')"
            f".properties().has(key, within(['inventory_potion', 'inventory_coins', 'inventory_weapon', 'inventory_gold', 'inventory_gem', 'inventory_rare_weapon']))"
            f".project('item', 'quantity').by(key()).by(value())"
        )
        inventory_result = run_query(inventory_query)

        inventory = {}
        for item in inventory_result:
            item_name = item['item'].replace('inventory_', '')
            inventory[item_name] = item['quantity']

        return {
            "status": "success",
            "character": {
                "id": character_id,
                "name": character.get("name", "Unknown"),
                "level": character.get("level", 1),
                "current_hp": character.get("current_hp", 0),
                "max_hp": character.get("max_hp", 1),
                "current_xp": character.get("current_xp", 0),
                "inventory": inventory
            },
            "can_adventure": character.get("current_hp", 0) > 0
        }

    except Exception as e:
        print(f"Error getting adventure status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get adventure status")