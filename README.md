# AI Diet Planner

A small, rule-based command-line diet planner written in pure Python
(standard library only — no external dependencies). It computes your
estimated daily calorie needs using well-known formulas and then builds a
sample day's meal plan from a bundled local food database.

**This is a simplified educational nutrition demo. It is NOT medical advice.**
Consult a registered dietitian or physician before making real dietary
changes.

## What it does

1. Takes your **age, sex, weight, height, activity level, and goal**.
2. Computes your **BMR** (Basal Metabolic Rate) using the Mifflin-St Jeor
   equation.
3. Computes your **TDEE** (Total Daily Energy Expenditure) by multiplying
   BMR by an activity factor.
4. Adjusts TDEE for your **goal** (lose / maintain / gain) to get a target
   daily calorie count.
5. Splits that calorie target into a **macro target** (protein / carbs / fat
   in grams).
6. Selects foods from a bundled database (`data/foods.json`, 64 foods) to
   build a **sample meal plan** (breakfast, lunch, dinner, snack) that lands
   within roughly 10% of your target calories and approximates your macro
   split.

## How it works (formulas)

**BMR (Mifflin-St Jeor):**

- Men: `BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5`
- Women: `BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161`

**TDEE:** `BMR * activity_multiplier`

| Activity level | Multiplier |
|---|---|
| sedentary | 1.2 |
| light | 1.375 |
| moderate | 1.55 |
| active | 1.725 |
| very_active | 1.9 |

**Goal-adjusted target calories:** `TDEE + adjustment`

| Goal | Adjustment |
|---|---|
| lose | -500 kcal |
| maintain | 0 kcal |
| gain | +300 kcal |

**Macro split** (as a fraction of target calories, then converted to grams
at 4 kcal/g for protein & carbs and 9 kcal/g for fat) varies slightly by
goal (e.g. a higher protein share when cutting).

## Requirements

Python 3.11+ (standard library only, no `pip install` needed).

## Running it

```bash
python plan.py --age 25 --sex male --weight 75 --height 178 --activity moderate --goal lose
```

Arguments:

| Flag | Values |
|---|---|
| `--age` | integer years |
| `--sex` | `male` \| `female` |
| `--weight` | kilograms |
| `--height` | centimeters |
| `--activity` | `sedentary` \| `light` \| `moderate` \| `active` \| `very_active` |
| `--goal` | `lose` \| `maintain` \| `gain` |
| `--seed` | (optional) integer, for a reproducible sample meal plan |

## Example output

```
============================================================
AI DIET PLANNER - Educational demo, NOT medical advice
============================================================

Computed Targets
------------------------------------------------------------
BMR (Mifflin-St Jeor): 1742 kcal/day
TDEE (BMR x activity): 2701 kcal/day
Target calories (goal-adjusted): 2201 kcal/day
Macro targets: protein 193g | carbs 193g | fat 73g

Sample Meal Plan
------------------------------------------------------------
Breakfast:
  - Orange (1 medium (131g)): 62 kcal | P 1.2g | C 15.4g | F 0.2g
  - Whey Protein Shake (1 scoop + water (~40g)): 150 kcal | P 25.0g | C 4.0g | F 2.5g
  - Peanut Butter (2 tbsp (32g)): 188 kcal | P 8.0g | C 6.9g | F 16.0g
  - Banana (1 medium (118g)): 105 kcal | P 1.3g | C 27.0g | F 0.4g
Lunch:
  - Baked Salmon Fillet (150g): 312 kcal | P 34.0g | C 0.0g | F 18.5g
  - Spinach Salad (no dressing) (2 cups (60g)): 14 kcal | P 1.7g | C 2.2g | F 0.2g
  - Cucumber Tomato Salad (1 cup (120g)): 30 kcal | P 1.2g | C 6.5g | F 0.3g
  - Olive Oil (1 tbsp (14g)): 119 kcal | P 0.0g | C 0.0g | F 13.5g
Dinner:
  - Baked Potato (1 medium (173g)): 161 kcal | P 4.3g | C 37.0g | F 0.2g
  - Grilled Chicken Breast (150g): 248 kcal | P 46.5g | C 0.0g | F 5.4g
  - Cooked Quinoa (1 cup (185g)): 222 kcal | P 8.1g | C 39.4g | F 3.6g
Snack:
  - Orange (1 medium (131g)): 62 kcal | P 1.2g | C 15.4g | F 0.2g
  - Trail Mix (1/4 cup (38g)): 173 kcal | P 5.0g | C 15.0g | F 11.0g
  - Plain Greek Yogurt (1 cup (245g)): 146 kcal | P 25.0g | C 8.0g | F 0.4g

Daily Totals (sample plan)
------------------------------------------------------------
Total: 1992 kcal (target 2201 kcal, -9.5%)
Protein: 162.5g | Carbs: 176.8g | Fat: 72.4g

Note: This is a simplified educational nutrition demo, not medical advice.
```

## Project structure

```
ai-diet-planner/
├── plan.py                    # CLI entry point
├── planner.py                 # Core logic: BMR/TDEE/macros + meal plan generator
├── data/
│   └── foods.json             # Bundled food database (~64 foods)
├── tests/
│   └── test_planner.py        # Unit tests (unittest)
├── .github/workflows/tests.yml # CI: runs tests on push/PR
├── LICENSE
└── README.md
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

All logic (BMR, TDEE, macro splits, and meal plan generation) is covered by
unit tests, including checks against known reference values and calorie
tolerance checks on generated meal plans.

## Disclaimer

This project is a simplified educational demo for learning about nutrition
math and rule-based generation. It does not account for medical conditions,
allergies, medications, or individual variation, and should not be used as
a substitute for professional medical or nutritional advice.
