from pathlib import Path
import typing

import click
import yaml
import pandas as pd
import numpy as np

from . import click_utils
from gamp.global_config import GAMP_CONFIG


# utils
# CLI
@click.command(cls=click_utils.AliasedGroup)
def gamp():
    pass


class OrderedDumper(yaml.Dumper):
    def __init__(self, *args, sort_keys=False, **kwargs):
        super().__init__(*args, sort_keys=False, **kwargs)


@gamp.command()
def validate_recipes():
    for recipe_holder in GAMP_CONFIG.recipe_holders():
        is_valid = True
        print(f'{recipe_holder}')
        # TODO check/fix rating
        # TODO check/fix unit
        for ingredient in recipe_holder.recipe.ingredients():
            if ingredient not in GAMP_CONFIG.ingredients:
                is_valid = False
                print(f'\tinvalid ingredient: {ingredient}')
                # TODO offer to correct

        if is_valid:
            print(f'Is Valid')


@gamp.command()
@click.argument('meal_plan_path', type=click.Path(exists=True, dir_okay=False))
@click.argument('worksheet_path', type=click.Path(dir_okay=False))
def inventory(meal_plan_path, worksheet_path):
    meal_plan_path = Path(meal_plan_path)
    worksheet_path = Path(worksheet_path)

    meal_plan = yaml.full_load(meal_plan_path.open('r'))
    ingredient_df = []
    for tag, recipe_name in meal_plan.items():
        if not GAMP_CONFIG.is_valid_recipe(recipe_name):
            print(f'{recipe_name} is not a valid recipe, skipping...')
            continue

        recipe = GAMP_CONFIG.get_recipe(recipe_name)
        ingredient_df.append(recipe.ingredient_series(GAMP_CONFIG.ureg))

    ingredient_df = pd.concat(ingredient_df, axis=1)
    ingredient_qtys = ingredient_df.sum(axis=1).to_frame(name='need')
    ingredient_qtys = ingredient_qtys.reset_index()
    ingredient_qtys.insert(0, 'have', 0)
    ingredient_qtys.to_csv(worksheet_path, index=False)
    print(f'output inventory worksheet at: {worksheet_path}')


def parse_inventory_row(row):
    row.need = GAMP_CONFIG.ureg(row.need)

    # TODO handle bad units
    row.have = GAMP_CONFIG.ureg(str(row.have))
    if not isinstance(row.have, GAMP_CONFIG.ureg.Quantity):
        row.have = row.have * row.need.units

    return row


@gamp.command()
@click.argument('worksheet_path', type=click.Path(exists=True, dir_okay=False))
@click.argument('list_path', type=click.Path(dir_okay=False))
def grocery_list(worksheet_path, list_path):
    list_path = Path(list_path)
    inventory = pd.read_csv(worksheet_path, index_col='ingredient')
    inventory = inventory.apply(parse_inventory_row, axis=1)

    to_buy = inventory.need - inventory.have
    to_buy = to_buy.loc[to_buy > 0]
    # TODO Convert to grocery units
    to_buy = to_buy.astype(str).to_dict()
    yaml.dump(to_buy, list_path.open('w'))


@gamp.command()
def cook():
    # fzf search recipes
    # show meal plan and select
    # know from start date to now
    pass


if __name__ == '__main__':
    gamp()
