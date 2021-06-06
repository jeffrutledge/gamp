# GAMP
_Groceries and Meal Planning_

## Installation

Add `alias gamp=/path/to/gamp/bin/gamp`

## Usage Tips

- Use `--help` after any command for options; e.g. `gamp --help` or `gamp recipe-edit --help`.
- `$GAMP_CONFIG_DIR` defaults to `~/.config/gamp`
- All subcommands can be called using unique prefixes; e.g. `gamp reci` is the same as `gamp recipe-edit`


## Suggested Usage

### Recipe Storage

1. Define ingredients in `$GAMP_CONFIG_DIR/ingredients.yaml`.
1. Collect recipes with `gamp recipe-edit [recipe_name]`
  - This opens `vim` with a tag file set to ingredients for easy completion.

### Meal Planning
1. Define a meal plan with `gamp meal-plan-edit [meal_plan_path]`
  - The keys in this file are not used by `gamp`, but may be later.
  - Create as many or as few rows as you like.
  - This opens `vim` with a tag file set to recipe names for easy completion.
1. Create inventory worksheet with `gamp inventory [meal_plan_path] [worksheet_path]`.
1. Fill in the inventory worksheet
  1. Fill in the `have` column with the amount in your inventory
  1. You can also delete rows if you don't need that item.
1. Create a grocery list with `gamp grocery-list [worksheet_path] [list_path]`
1. Buy groceries

### Cooking
1. Open the recipe you want to cook with `gamp recipe-edit [recipe_name]`
1. Use recipe for reference while cooking, and make any edits you wish to
   remember for next time you cook this.

## Future Features
[] create as pip installable package
[] validate meal plans like recipes
[] remove need to define file paths while Meal Planning
  [] add interactive inventory worksheet instead of csv
[] suggest corrections upon invalidate recipe or meal plan
[] view meal plan
  [] what you are supposed to cook today, make mealplan key relative date?
[] Don't require ingredients to be defined in ingredients.yaml
[] Preferred units for each ingredient in grocery list
[] log cooked recipes
  [] recipe suggestions based on ranking and last cooked time
[] inventory tacking
  - probably only useful as an approximation for some items
