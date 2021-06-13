from pathlib import Path
import typing
import tempfile
import subprocess
import shutil
import sys

import click
import yaml
import pandas as pd
import pint
from iterfzf import iterfzf

from . import click_utils
from . import global_config
from .global_config import GAMP_CONFIG
from . import core
from . import templates


# utils

def write_tag_file(
        tags: typing.Sequence[str],
        out_path: typing.Optional[Path] = None) -> Path:
    """ Write a tag file consiting of tags. Allows completion with YCM.

    out_path: optional

        If not provided use a named temporary file.

    Returns: Path to tag file.
    """
    tag_lines = '\n'.join(['\t'.join([tag, 'tag', 'language:yaml'])
                           for tag in tags])
    tag_lines += '\n'
    if out_path is None:
        out_file = tempfile.NamedTemporaryFile(mode='w')
        out_path = Path(out_file.name)
        out_file.write(tag_lines)
        out_file.flush()
    else:
        with out_path.open('w') as out_file:
            out_file.write(tag_lines)

    return out_path


def edit_with_tags(recipe_path: Path,
                   tags: typing.Optional[typing.Sequence[str]] = None):
    tag_file = tempfile.NamedTemporaryFile(mode='w')
    tag_path = Path(tag_file.name)
    write_tag_file(tags, tag_path)
    subprocess.run(['vim',
                    '-c', 'let g:ycm_collect_identifiers_from_tags_files = 1'
                    f' | set tags={tag_path}',
                    recipe_path], check=True)


def edit_recipe(recipe_path: Path):
    edit_with_tags(recipe_path, GAMP_CONFIG.ingredients)


def edit_meal_plan(meal_plan_path: Path):
    edit_with_tags(meal_plan_path, GAMP_CONFIG.recipe_names())


def validate_recipe(recipe: core.Recipe) -> bool:
    is_valid = True
    for ingredient, qty_str in recipe.ingredient_qtys.items():
        if ingredient not in GAMP_CONFIG.ingredients:
            is_valid = False
            print(f'\tinvalid ingredient: {ingredient}')
            # TODO offer to correct
        try:
            GAMP_CONFIG.ureg(str(qty_str))
        except pint.errors.UndefinedUnitError:
            is_valid = False
            print(f'\tinvalid qty: {qty_str}')
            # TODO offer to correct
    return is_valid


# CLI
@click.command(cls=click_utils.AliasedGroup)
def gamp():
    pass


class OrderedDumper(yaml.Dumper):
    def __init__(self, *args, sort_keys=False, **kwargs):
        super().__init__(*args, sort_keys=False, **kwargs)


@gamp.command()
@click.argument('recipe-name', type=click.STRING, required=False)
def recipe_edit(recipe_name):
    # TODO Version control recipe edits
    if recipe_name is None:
        recipe_name = iterfzf(GAMP_CONFIG.recipe_names())
        if recipe_name is None:
            print('no selection made, exiting')
            sys.exit(0)

    recipe_path = GAMP_CONFIG.recipe_dir / f'{recipe_name}.yaml'
    if not recipe_path.exists():
        shutil.copy(templates.RECIPE_TEMPLATE, recipe_path)

    edit_recipe(recipe_path)
    recipe = global_config.load_recipe_from_yaml(recipe_path)
    while not validate_recipe(recipe):
        response = input('Recipe failed validation.'
                         ' Would you like to fix it now? [y|n] ')
        if response.strip().lower() in ['n', 'no']:
            break

        edit_recipe(recipe_path)
        recipe = global_config.load_recipe_from_yaml(recipe_path)
    print(f'wrote recipe: {recipe_path}')


@gamp.command()
def validate_recipes():
    for recipe_holder in GAMP_CONFIG.recipe_holders():
        recipe = recipe_holder.recipe
        print(f'{recipe_holder}')
        if validate_recipe(recipe):
            print(f'Is Valid')


@gamp.command()
@click.argument('meal_plan_path', type=click.Path(dir_okay=False))
def meal_plan_edit(meal_plan_path):
    meal_plan_path = Path(meal_plan_path)
    if not meal_plan_path.exists():
        shutil.copy(templates.MEAL_PLAN_TEMPLATE, meal_plan_path)
    edit_meal_plan(meal_plan_path)
    # TODO meal plan validation
    # recipe = global_config.load_recipe_from_yaml(recipe_path)
    # while not validate_recipe(recipe):
    #     response = input('Recipe failed validation.'
    #                      'Would you like to fix it now? [y|n] ')
    #     if response.strip().lower() in ['n', 'no']:
    #         break
    #     edit_recipe(recipe_path)
    #     recipe = global_config.load_recipe_from_yaml(recipe_path)

    print(f'wrote meal_plan_path: {meal_plan_path}')


@gamp.command()
@click.argument('meal_plan_path', type=click.Path(exists=True, dir_okay=False))
@click.argument('worksheet_path', type=click.Path(dir_okay=False))
def inventory(meal_plan_path, worksheet_path):
    meal_plan_path = Path(meal_plan_path)
    worksheet_path = Path(worksheet_path)

    meal_plan = yaml.full_load(meal_plan_path.open('r'))
    ingredient_df = []
    for tag, recipe_name in meal_plan.items():
        if recipe_name not in GAMP_CONFIG.recipe_names():
            print(f'{recipe_name} is not a valid recipe, skipping...')
            continue

        recipe = GAMP_CONFIG.get_recipe(recipe_name)
        ingredient_df.append(recipe.ingredient_series(GAMP_CONFIG.ureg))

    ingredient_df = pd.concat(ingredient_df, axis=1).fillna(0)
    ingredient_qtys = ingredient_df.sum(axis=1).to_frame(name='need')
    ingredient_qtys = ingredient_qtys.reset_index()
    ingredient_qtys.insert(0, 'have', 0)
    ingredient_qtys.to_csv(worksheet_path, index=False)
    print(f'output inventory worksheet at: {worksheet_path}')


def parse_inventory_row(row):
    row.need = GAMP_CONFIG.ureg(str(row.need))

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


# @gamp.command()
# def cook():
#     # fzf search recipes
#     # show meal plan and select
#     # know from start date to now
#     pass


if __name__ == '__main__':
    gamp()
