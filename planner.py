"""
Core logic for the AI Diet Planner.

This module is pure stdlib and contains no I/O side effects beyond reading
the bundled food database, so it can be imported and unit tested directly.

IMPORTANT: This is a simplified educational nutrition demo. It is NOT
medical advice. Consult a registered dietitian or physician before making
real dietary changes.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "foods.json")

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_CALORIE_ADJUSTMENT = {
    "lose": -500,
    "maintain": 0,
    "gain": 300,
}

# Macro split as a fraction of total daily calories: (protein, carbs, fat)
GOAL_MACRO_SPLIT = {
    "lose": {"protein": 0.35, "carbs": 0.35, "fat": 0.30},
    "maintain": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
    "gain": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
}

CALORIES_PER_GRAM = {"protein": 4, "carbs": 4, "fat": 9}

MEAL_SLOTS = ["breakfast", "lunch", "dinner", "snack"]

# Rough share of total daily calories assigned to each meal slot.
MEAL_CALORIE_SHARE = {
    "breakfast": 0.25,
    "lunch": 0.30,
    "dinner": 0.30,
    "snack": 0.15,
}


@dataclass
class Targets:
    bmr: float
    tdee: float
    target_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


@dataclass
class MealPlan:
    meals: Dict[str, List[dict]] = field(default_factory=dict)
    total_calories: float = 0.0
    total_protein_g: float = 0.0
    total_carbs_g: float = 0.0
    total_fat_g: float = 0.0


def load_food_database(path: str = DATA_PATH) -> List[dict]:
    """Load the local food database from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_bmr(age: int, sex: str, weight_kg: float, height_cm: float) -> float:
    """Mifflin-St Jeor equation.

    Men:   BMR = 10*weight + 6.25*height - 5*age + 5
    Women: BMR = 10*weight + 6.25*height - 5*age - 161
    """
    sex_normalized = sex.strip().lower()
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex_normalized in ("male", "m"):
        return base + 5
    elif sex_normalized in ("female", "f"):
        return base - 161
    else:
        raise ValueError(f"Unknown sex: {sex!r}. Expected 'male' or 'female'.")


def compute_tdee(bmr: float, activity_level: str) -> float:
    """Total Daily Energy Expenditure = BMR * activity multiplier."""
    key = activity_level.strip().lower()
    if key not in ACTIVITY_MULTIPLIERS:
        raise ValueError(
            f"Unknown activity level: {activity_level!r}. "
            f"Expected one of {sorted(ACTIVITY_MULTIPLIERS)}."
        )
    return bmr * ACTIVITY_MULTIPLIERS[key]


def compute_target_calories(tdee: float, goal: str) -> float:
    """Adjust TDEE for the stated goal (lose/maintain/gain)."""
    key = goal.strip().lower()
    if key not in GOAL_CALORIE_ADJUSTMENT:
        raise ValueError(
            f"Unknown goal: {goal!r}. Expected one of {sorted(GOAL_CALORIE_ADJUSTMENT)}."
        )
    target = tdee + GOAL_CALORIE_ADJUSTMENT[key]
    # Keep a sane floor so calculations never fall into unsafe territory.
    return max(target, 1200.0)


def compute_macros(target_calories: float, goal: str) -> Dict[str, float]:
    """Return grams of protein/carbs/fat for a given goal and calorie target."""
    key = goal.strip().lower()
    if key not in GOAL_MACRO_SPLIT:
        raise ValueError(
            f"Unknown goal: {goal!r}. Expected one of {sorted(GOAL_MACRO_SPLIT)}."
        )
    split = GOAL_MACRO_SPLIT[key]
    grams = {}
    for macro, fraction in split.items():
        macro_calories = target_calories * fraction
        grams[macro] = round(macro_calories / CALORIES_PER_GRAM[macro], 1)
    return grams


def compute_targets(age: int, sex: str, weight_kg: float, height_cm: float,
                     activity_level: str, goal: str) -> Targets:
    """Run the full pipeline: BMR -> TDEE -> target calories -> macros."""
    bmr = compute_bmr(age, sex, weight_kg, height_cm)
    tdee = compute_tdee(bmr, activity_level)
    target_calories = compute_target_calories(tdee, goal)
    macros = compute_macros(target_calories, goal)
    return Targets(
        bmr=round(bmr, 1),
        tdee=round(tdee, 1),
        target_calories=round(target_calories, 1),
        protein_g=macros["protein"],
        carbs_g=macros["carbs"],
        fat_g=macros["fat"],
    )


def _foods_for_slot(foods: List[dict], slot: str) -> List[dict]:
    return [f for f in foods if slot in f.get("meal_types", [])]


def _build_slot_selection(candidates: List[dict], slot_calorie_target: float,
                           rng: random.Random, max_items: int = 4) -> List[dict]:
    """Greedily pick foods for a single meal slot until close to the target."""
    if not candidates:
        return []
    pool = candidates[:]
    rng.shuffle(pool)
    selected: List[dict] = []
    running_total = 0.0
    for food in pool:
        if len(selected) >= max_items:
            break
        projected = running_total + food["calories"]
        # Only add if it doesn't overshoot the slot target by more than 40%,
        # unless we have nothing selected yet (avoid an empty meal).
        if projected <= slot_calorie_target * 1.4 or not selected:
            selected.append(food)
            running_total = projected
        if running_total >= slot_calorie_target * 0.85:
            break
    return selected


def generate_meal_plan(targets: Targets, foods: List[dict] = None,
                        seed: int = None) -> MealPlan:
    """Generate a sample day's meal plan close to the target calories/macros."""
    if foods is None:
        foods = load_food_database()
    rng = random.Random(seed)

    plan = MealPlan()
    for slot in MEAL_SLOTS:
        slot_target_calories = targets.target_calories * MEAL_CALORIE_SHARE[slot]
        candidates = _foods_for_slot(foods, slot)
        selection = _build_slot_selection(candidates, slot_target_calories, rng)
        plan.meals[slot] = selection
        for item in selection:
            plan.total_calories += item["calories"]
            plan.total_protein_g += item["protein_g"]
            plan.total_carbs_g += item["carbs_g"]
            plan.total_fat_g += item["fat_g"]

    plan.total_calories = round(plan.total_calories, 1)
    plan.total_protein_g = round(plan.total_protein_g, 1)
    plan.total_carbs_g = round(plan.total_carbs_g, 1)
    plan.total_fat_g = round(plan.total_fat_g, 1)
    return plan


def generate_meal_plan_within_tolerance(targets: Targets, foods: List[dict] = None,
                                         tolerance: float = 0.10, attempts: int = 60,
                                         seed: int = None) -> MealPlan:
    """Try several random seeds and return the plan closest to the calorie target.

    Prefers a plan within `tolerance` (default +/-10%) of targets.target_calories,
    but always returns the best attempt found even if none land inside tolerance.
    `seed`, if given, offsets the sequence of seeds tried (for reproducibility).
    """
    if foods is None:
        foods = load_food_database()

    base_seed = 0 if seed is None else seed
    best_plan = None
    best_diff = None
    for offset in range(attempts):
        plan = generate_meal_plan(targets, foods=foods, seed=base_seed + offset)
        diff = abs(plan.total_calories - targets.target_calories)
        if best_diff is None or diff < best_diff:
            best_plan = plan
            best_diff = diff
        if diff <= targets.target_calories * tolerance:
            return plan
    return best_plan
