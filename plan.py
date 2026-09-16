#!/usr/bin/env python3
"""
AI Diet Planner - CLI entry point.

Example:
    python plan.py --age 25 --sex male --weight 75 --height 178 \\
        --activity moderate --goal lose

This is a simplified educational nutrition demo, NOT medical advice.
"""

import argparse
import sys

from planner import (
    ACTIVITY_MULTIPLIERS,
    GOAL_CALORIE_ADJUSTMENT,
    MEAL_SLOTS,
    compute_targets,
    generate_meal_plan_within_tolerance,
    load_food_database,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plan.py",
        description="Rule-based BMR/TDEE calculator and sample meal plan generator "
                     "(educational demo, not medical advice).",
    )
    parser.add_argument("--age", type=int, required=True, help="Age in years")
    parser.add_argument("--sex", type=str, required=True, choices=["male", "female"],
                         help="Biological sex used for the Mifflin-St Jeor equation")
    parser.add_argument("--weight", type=float, required=True, help="Weight in kilograms")
    parser.add_argument("--height", type=float, required=True, help="Height in centimeters")
    parser.add_argument("--activity", type=str, required=True,
                         choices=sorted(ACTIVITY_MULTIPLIERS.keys()),
                         help="Activity level")
    parser.add_argument("--goal", type=str, required=True,
                         choices=sorted(GOAL_CALORIE_ADJUSTMENT.keys()),
                         help="Dietary goal")
    parser.add_argument("--seed", type=int, default=None,
                         help="Optional random seed for reproducible meal plans")
    return parser


def format_report(targets, plan) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("AI DIET PLANNER - Educational demo, NOT medical advice")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Computed Targets")
    lines.append("-" * 60)
    lines.append(f"BMR (Mifflin-St Jeor): {targets.bmr:.0f} kcal/day")
    lines.append(f"TDEE (BMR x activity): {targets.tdee:.0f} kcal/day")
    lines.append(f"Target calories (goal-adjusted): {targets.target_calories:.0f} kcal/day")
    lines.append(f"Macro targets: protein {targets.protein_g:.0f}g | "
                  f"carbs {targets.carbs_g:.0f}g | fat {targets.fat_g:.0f}g")
    lines.append("")
    lines.append("Sample Meal Plan")
    lines.append("-" * 60)
    for slot in MEAL_SLOTS:
        items = plan.meals.get(slot, [])
        lines.append(f"{slot.capitalize()}:")
        if not items:
            lines.append("  (no suitable items found)")
            continue
        for item in items:
            lines.append(
                f"  - {item['name']} ({item['serving']}): "
                f"{item['calories']:.0f} kcal | P {item['protein_g']:.1f}g | "
                f"C {item['carbs_g']:.1f}g | F {item['fat_g']:.1f}g"
            )
    lines.append("")
    lines.append("Daily Totals (sample plan)")
    lines.append("-" * 60)
    diff = plan.total_calories - targets.target_calories
    pct = (diff / targets.target_calories) * 100 if targets.target_calories else 0.0
    lines.append(
        f"Total: {plan.total_calories:.0f} kcal "
        f"(target {targets.target_calories:.0f} kcal, {pct:+.1f}%)"
    )
    lines.append(
        f"Protein: {plan.total_protein_g:.1f}g | "
        f"Carbs: {plan.total_carbs_g:.1f}g | "
        f"Fat: {plan.total_fat_g:.1f}g"
    )
    lines.append("")
    lines.append("Note: This is a simplified educational nutrition demo, not medical advice.")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        targets = compute_targets(
            age=args.age,
            sex=args.sex,
            weight_kg=args.weight,
            height_cm=args.height,
            activity_level=args.activity,
            goal=args.goal,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    foods = load_food_database()
    plan = generate_meal_plan_within_tolerance(targets, foods=foods, seed=args.seed)

    print(format_report(targets, plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
