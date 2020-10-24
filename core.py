import sys
from pathlib import Path
import itertools as it
import functools

import pandas as pd
import yaml

THIS_DIR = Path(__file__).parent

groceries_path = THIS_DIR / 'groceries.yaml'
with groceries_path.open() as groceries_file:
    groceries = sorted(yaml.full_load(groceries_file))

recipes_path = THIS_DIR / 'recipes.yaml'
with recipes_path.open() as recipes_file:
    recipes = yaml.full_load(recipes_file)
    if recipes is None:
        recipes = {}

def menu_prompt_strs(prompt, options):
    options = list(options)
    prefix_to_option = {}
    for option in options:
        for i in range(1, len(option)):
            prefix = option[:i]
            if prefix not in prefix_to_option:
                prefix_to_option[prefix] = option
                break

    def get_selection():
        print(prompt)
        for prefix, option in prefix_to_option.items():
            rest = option[len(prefix):]
            print(f'\t-[{prefix}]{rest}')

        selection = input()
        return selection

    while (selection:=get_selection()) not in prefix_to_option:
        print(f'{selection} is not one of the options')
        print()

    print()
    return prefix_to_option[selection]

def menu_prompt(prompt, options, to_str=None):
    if to_str is not None:
        str_to_option = {to_str(option): option for option in options}
        option_str = menu_prompt(prompt, str_to_option.keys())
        return str_to_option[option_str]
    else:
        return menu_prompt_strs(prompt, options)

def menu_prompt_fn(prompt, options):
    return menu_prompt(prompt, options, lambda f: f.__name__)

def continously_prompt_fn(prompt, options):
    def done():
        pass

    while (fn:=menu_prompt_fn(prompt, it.chain(options, (done,)))) != done:
        fn()

    return

def select_grocery(prompt='select a grocery:'):
    return menu_prompt(prompt, groceries)

def input_float(prompt):
    def try_float():
        print(prompt)
        f = input()
        try:
            f = float(f)
        except ValueError:
            print(f'{f} is not a valid float')
            return None
        return f

    while (f:=try_float()) is None:
        pass

    return f

def print_recipe(d, name):
    print(f'{name}:')
    print(pd.Series(d, dtype=float).to_string())
    print()

def add_recipe():
    def get_name():
        def try_name():
            print('enter a name')
            name = input()
            if name in recipes:
                print(f'{name} is already a recipe.')
                return None
            return name

        while (name:=try_name()) is None:
            pass

        return name

    name = get_name()
    recipes[name] = {}
    edit_recipe(name)

def requires_recipes(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if len(recipes) == 0:
            print('no recipes')
        else:
            f(*args, **kwargs)

    return wrapper

@requires_recipes
def edit_recipe(recipe_name=None):
    if recipe_name is None:
        recipe_name = menu_prompt('select a recipe to edit:', recipes.keys())

    recipe = recipes[recipe_name]
    print_recipe(recipe, recipe_name)

    def edit_qty():
        print_recipe(recipe, recipe_name)
        grocery = select_grocery()
        print_recipe(recipe, recipe_name)
        qty = input_float(f'set {grocery} qty to:')
        recipe[grocery] = qty

    def inspect():
        print_recipe(recipe, recipe_name)

    continously_prompt_fn(f'editing recipe={recipe_name}', [edit_qty, inspect])

@requires_recipes
def inspect_recipe():
    recipe = menu_prompt('select a recipe to inspect:', recipes.keys())
    print_recipe(recipes[recipe], recipe)

@requires_recipes
def list_recipes():
    for name in recipes:
        print(name)

root_choices = [list_recipes, inspect_recipe, add_recipe, edit_recipe]

continously_prompt_fn('what would you like to do:', root_choices)

for recipe in recipes:
    print_recipe(recipes[recipe], recipe)

with recipes_path.open('w') as recipes_file:
    yaml.dump(recipes, recipes_file)
