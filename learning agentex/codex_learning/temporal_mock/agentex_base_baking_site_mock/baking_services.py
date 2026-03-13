from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
import uuid


@dataclass(frozen=True)
class Recipe:
    name: str
    difficulty: str
    dietary: str
    serves: int
    bake_minutes: int
    ingredients: tuple[str, ...]
    tags: tuple[str, ...]


RECIPE_CATALOG: tuple[Recipe, ...] = (
    Recipe(
        name="Classic Vanilla Cake",
        difficulty="beginner",
        dietary="any",
        serves=8,
        bake_minutes=40,
        ingredients=("flour", "sugar", "eggs", "butter", "milk", "vanilla", "baking powder"),
        tags=("birthday", "cake", "sweet"),
    ),
    Recipe(
        name="Chocolate Chip Cookies",
        difficulty="beginner",
        dietary="any",
        serves=24,
        bake_minutes=14,
        ingredients=(
            "flour",
            "sugar",
            "brown sugar",
            "eggs",
            "butter",
            "chocolate chips",
            "baking soda",
        ),
        tags=("cookies", "snack", "sweet"),
    ),
    Recipe(
        name="Banana Bread",
        difficulty="intermediate",
        dietary="any",
        serves=10,
        bake_minutes=55,
        ingredients=("flour", "sugar", "eggs", "butter", "banana", "baking soda", "salt"),
        tags=("bread", "snack", "sweet"),
    ),
    Recipe(
        name="Vegan Berry Muffins",
        difficulty="beginner",
        dietary="vegan",
        serves=12,
        bake_minutes=25,
        ingredients=(
            "flour",
            "sugar",
            "berries",
            "almond milk",
            "vegetable oil",
            "baking powder",
        ),
        tags=("muffin", "vegan", "sweet"),
    ),
)


ORDER_STORE: dict[str, dict[str, Any]] = {}


def reset_order_store() -> None:
    ORDER_STORE.clear()


def _difficulty_rank(value: str) -> int:
    ordering = {"beginner": 0, "intermediate": 1, "advanced": 2}
    return ordering.get(value.lower(), 0)


def _goal_matches(tags: tuple[str, ...], goal: str) -> bool:
    if not goal:
        return True
    lowered_goal = goal.lower()
    return any(tag in lowered_goal for tag in tags)


async def search_recipes(profile: dict[str, Any]) -> list[Recipe]:
    """
    Simulates external recipe retrieval.

    Teaching intent: even simple reads can be async if they eventually become DB/API calls.
    """
    await asyncio.sleep(0.03)

    dietary = str(profile.get("diet", "any")).lower()
    skill = str(profile.get("skill", "beginner")).lower()
    goal = str(profile.get("goal", "")).lower()

    skill_rank = _difficulty_rank(skill)
    matches: list[Recipe] = []
    for recipe in RECIPE_CATALOG:
        if dietary != "any" and recipe.dietary not in {"any", dietary}:
            continue
        if _difficulty_rank(recipe.difficulty) > skill_rank:
            continue
        if goal and not _goal_matches(recipe.tags, goal):
            continue
        matches.append(recipe)

    if matches:
        return matches

    # Fallback keeps UX resilient when filters are too strict.
    return [recipe for recipe in RECIPE_CATALOG if recipe.difficulty == "beginner"][:3]


async def check_missing_ingredients(recipe: Recipe, pantry: set[str]) -> list[str]:
    await asyncio.sleep(0.02)
    lowered_pantry = {item.lower().strip() for item in pantry if item.strip()}
    return [item for item in recipe.ingredients if item.lower() not in lowered_pantry]


async def build_timeline(recipe: Recipe | dict[str, Any], skill: str) -> dict[str, int]:
    await asyncio.sleep(0.02)
    if isinstance(recipe, dict):
        recipe_name = str(recipe.get("name", "recipe"))
        recipe_bake_minutes = int(recipe.get("bake_minutes", 30))
    else:
        recipe_name = recipe.name
        recipe_bake_minutes = recipe.bake_minutes

    prep_minutes = {"beginner": 25, "intermediate": 15, "advanced": 10}.get(skill, 20)
    cooling_minutes = 20 if "cake" in recipe_name.lower() else 10
    return {
        "prep_minutes": prep_minutes,
        "bake_minutes": recipe_bake_minutes,
        "cooling_minutes": cooling_minutes,
        "total_minutes": prep_minutes + recipe_bake_minutes + cooling_minutes,
    }


async def submit_ingredient_order(task_id: str, ingredients: list[str]) -> dict[str, Any]:
    await asyncio.sleep(0.04)
    payload = f"{task_id}:{','.join(sorted(ingredients))}"
    order_id = f"order-{uuid.uuid5(uuid.NAMESPACE_URL, payload).hex[:10]}"
    order = {
        "order_id": order_id,
        "status": "placed",
        "items": sorted(ingredients),
        "estimated_delivery_minutes": 45,
    }
    ORDER_STORE[order_id] = order
    return order
