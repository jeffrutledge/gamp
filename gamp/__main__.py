from pathlib import Path
import typing

import click
import yaml

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
def inventory(meal_plan_path, inventory_worksheet_path):
    pass


@gamp.command()
def grocery_list(invent):
    pass


@gamp.command()
def cook():
    # fzf search recipes
    # show meal plan and select
    # know from start date to now
    pass


if __name__ == '__main__':
    gamp()
