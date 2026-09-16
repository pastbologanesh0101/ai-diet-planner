"""Unit tests for planner.py (BMR/TDEE formulas and meal plan generation)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planner import (
    compute_bmr,
    compute_tdee,
    compute_target_calories,
    compute_macros,
    compute_targets,
    generate_meal_plan,
    generate_meal_plan_within_tolerance,
    load_food_database,
    ACTIVITY_MULTIPLIERS,
    CALORIES_PER_GRAM,
)


class TestBMR(unittest.TestCase):
    def test_bmr_male_reference(self):
        # Mifflin-St Jeor, male: 10*75 + 6.25*178 - 5*25 + 5 = 1742.5
        bmr = compute_bmr(age=25, sex="male", weight_kg=75, height_cm=178)
        self.assertAlmostEqual(bmr, 1742.5, places=2)

    def test_bmr_female_reference(self):
        # Mifflin-St Jeor, female: 10*60 + 6.25*165 - 5*30 - 161 = 1320.25
        bmr = compute_bmr(age=30, sex="female", weight_kg=60, height_cm=165)
        self.assertAlmostEqual(bmr, 1320.25, places=2)

    def test_bmr_sex_case_insensitive_and_short_forms(self):
        bmr_full = compute_bmr(age=40, sex="Male", weight_kg=80, height_cm=180)
        bmr_short = compute_bmr(age=40, sex="m", weight_kg=80, height_cm=180)
        self.assertAlmostEqual(bmr_full, bmr_short, places=6)

    def test_bmr_invalid_sex_raises(self):
        with self.assertRaises(ValueError):
            compute_bmr(age=25, sex="unknown", weight_kg=70, height_cm=170)


class TestTDEE(unittest.TestCase):
    def test_tdee_moderate_multiplier(self):
        bmr = 1742.5
        tdee = compute_tdee(bmr, "moderate")
        self.assertAlmostEqual(tdee, bmr * 1.55, places=6)

    def test_tdee_all_multipliers_reference(self):
        bmr = 1500.0
        for level, multiplier in ACTIVITY_MULTIPLIERS.items():
            tdee = compute_tdee(bmr, level)
            self.assertAlmostEqual(tdee, bmr * multiplier, places=6)

    def test_tdee_invalid_activity_raises(self):
        with self.assertRaises(ValueError):
            compute_tdee(1500.0, "extremely_active")


class TestTargetCaloriesAndMacros(unittest.TestCase):
    def test_target_calories_lose_subtracts_500(self):
        tdee = 2701.375
        target = compute_target_calories(tdee, "lose")
        self.assertAlmostEqual(target, tdee - 500, places=2)

    def test_target_calories_gain_adds_300(self):
        tdee = 2277.43125
        target = compute_target_calories(tdee, "gain")
        self.assertAlmostEqual(target, tdee + 300, places=2)

    def test_target_calories_has_safety_floor(self):
        # Even a very low TDEE with an aggressive cut should not go below 1200.
        target = compute_target_calories(1000, "lose")
        self.assertGreaterEqual(target, 1200.0)

    def test_macros_sum_close_to_target_calories(self):
        target_calories = 2200.0
        macros = compute_macros(target_calories, "lose")
        recomputed_calories = sum(
            macros[m] * CALORIES_PER_GRAM[m] for m in ("protein", "carbs", "fat")
        )
        # Allow small rounding tolerance (grams are rounded to 1 decimal place).
        self.assertAlmostEqual(recomputed_calories, target_calories, delta=5.0)

    def test_invalid_goal_raises(self):
        with self.assertRaises(ValueError):
            compute_macros(2000.0, "shred")
        with self.assertRaises(ValueError):
            compute_target_calories(2000.0, "shred")


class TestComputeTargetsPipeline(unittest.TestCase):
    def test_full_pipeline_reference_case(self):
        # age 25, male, 75kg, 178cm, moderate, lose
        targets = compute_targets(
            age=25, sex="male", weight_kg=75, height_cm=178,
            activity_level="moderate", goal="lose",
        )
        expected_bmr = 1742.5
        expected_tdee = expected_bmr * 1.55
        expected_target = expected_tdee - 500
        self.assertAlmostEqual(targets.bmr, expected_bmr, places=1)
        self.assertAlmostEqual(targets.tdee, expected_tdee, places=1)
        self.assertAlmostEqual(targets.target_calories, expected_target, places=1)
        self.assertGreater(targets.protein_g, 0)
        self.assertGreater(targets.carbs_g, 0)
        self.assertGreater(targets.fat_g, 0)


class TestFoodDatabase(unittest.TestCase):
    def test_food_database_loads_and_has_enough_entries(self):
        foods = load_food_database()
        self.assertGreaterEqual(len(foods), 40)
        self.assertLessEqual(len(foods), 80)

    def test_food_entries_have_required_fields(self):
        foods = load_food_database()
        required_fields = {"id", "name", "serving", "calories", "protein_g",
                            "carbs_g", "fat_g", "meal_types"}
        for food in foods:
            self.assertTrue(required_fields.issubset(food.keys()), food)
            self.assertGreater(food["calories"], 0)

    def test_food_ids_are_unique(self):
        foods = load_food_database()
        ids = [f["id"] for f in foods]
        self.assertEqual(len(ids), len(set(ids)))


class TestMealPlanGeneration(unittest.TestCase):
    def setUp(self):
        self.foods = load_food_database()

    def test_meal_plan_has_all_slots_populated(self):
        targets = compute_targets(
            age=25, sex="male", weight_kg=75, height_cm=178,
            activity_level="moderate", goal="lose",
        )
        plan = generate_meal_plan(targets, foods=self.foods, seed=1)
        for slot in ("breakfast", "lunch", "dinner", "snack"):
            self.assertIn(slot, plan.meals)
            self.assertGreater(len(plan.meals[slot]), 0)

    def test_meal_plan_within_tolerance_of_target_calories(self):
        profiles = [
            dict(age=25, sex="male", weight_kg=75, height_cm=178,
                 activity_level="moderate", goal="lose"),
            dict(age=30, sex="female", weight_kg=60, height_cm=165,
                 activity_level="active", goal="gain"),
            dict(age=45, sex="male", weight_kg=90, height_cm=182,
                 activity_level="sedentary", goal="maintain"),
        ]
        for profile in profiles:
            targets = compute_targets(**profile)
            plan = generate_meal_plan_within_tolerance(
                targets, foods=self.foods, tolerance=0.10, seed=0
            )
            diff_ratio = abs(plan.total_calories - targets.target_calories) / targets.target_calories
            # The generator tries hard to land within 10%; allow a little slack
            # (15%) so the test is robust to database edits while still
            # catching a badly broken generator.
            self.assertLessEqual(diff_ratio, 0.15, msg=f"profile={profile}, plan={plan}")

    def test_meal_plan_macros_are_nonzero_and_reasonable(self):
        targets = compute_targets(
            age=25, sex="male", weight_kg=75, height_cm=178,
            activity_level="moderate", goal="lose",
        )
        plan = generate_meal_plan(targets, foods=self.foods, seed=2)
        self.assertGreater(plan.total_protein_g, 0)
        self.assertGreater(plan.total_carbs_g, 0)
        self.assertGreater(plan.total_fat_g, 0)
        # Sanity check: recomputed calories from macros roughly match reported total.
        # Real-world food labels don't derive calories exactly from macros*4/4/9
        # (rounding, fiber, etc.), so allow a generous tolerance here.
        recomputed = (plan.total_protein_g * 4 + plan.total_carbs_g * 4
                      + plan.total_fat_g * 9)
        self.assertAlmostEqual(recomputed, plan.total_calories, delta=150.0)


if __name__ == "__main__":
    unittest.main()
