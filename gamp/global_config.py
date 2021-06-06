from pathlib import Path
import typing
import sys
import os
import shutil

import pint
import yaml

from . import core
from . import templates


def yaml_recipe_constructor(loader: yaml.Loader, node: yaml.MappingNode):
    kwargs = loader.construct_mapping(node, deep=True)
    kwargs['ingredients'] = {i: q for i, q in kwargs['ingredients'].items()}
    return core.Recipe(**kwargs)


yaml.add_constructor(u'!recipe', yaml_recipe_constructor)


def yaml_recipe_representer(dumper: yaml.Dumper, data: core.Recipe):
    mapping = dict(
        rating=data.rating,
        ingredients={i: str(q) for i, q in data.ingredient_qtys.items()},
        steps=data.steps,
    )
    return dumper.represent_mapping('!Recipe', mapping)


yaml.add_representer(core.Recipe, yaml_recipe_representer)


class RecipeHolder:
    def __init__(self, path: Path, recipe: core.Recipe):
        self.path = path
        self.recipe = recipe

    def __repr__(self):
        return f'{self.recipe.name}: {self.path}'


def load_recipe_from_yaml(recipe_path: Path) -> core.Recipe:
    recipe = yaml.full_load(recipe_path.open('r'))
    if not isinstance(recipe, core.Recipe):
        raise ValueError('{recipe_path} does not contain a Recipe!')
    recipe.name = recipe_path.stem
    return recipe


def load_recipes_from_dir(
        recipe_dir: Path) -> typing.Mapping[str, RecipeHolder]:
    recipe_dict = dict()
    for recipe_path in recipe_dir.glob('*.yaml'):
        try:
            recipe = load_recipe_from_yaml(recipe_path)
        except Exception as e:
            print(f'Skipping {recipe_path} because: {e}', file=sys.stderr)
            continue
        recipe_dict[recipe.name] = RecipeHolder(recipe_path, recipe)

    return recipe_dict


def load_ingredients_from_yaml(path: Path) -> typing.Set[str]:
    ingredients = yaml.safe_load(Path(path).open('r'))
    assert(all(isinstance(i, str) for i in ingredients))
    return set(ingredients)


def get_config_dir() -> Path:
    config_dir = Path(os.getenv('GAMP_CONFIG_DIR', '~/.config/gamp'))
    config_dir = config_dir.expanduser().resolve()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class GAMPConfig():
    def __init__(
            self,
            ingredients_path: Path = get_config_dir() / 'ingredients.yaml',
            recipe_dir: Path = get_config_dir() / 'recipes',
            meal_plan_dir: Path = get_config_dir() / 'meal_plans'):
        self.ureg = pint.UnitRegistry()
        self.ureg.define('@alias tbsp = tbs')
        self.ureg.define('@alias tsp = tsp')

        if not ingredients_path.exists():
            shutil.copy(templates.INGREDIENTS_TEMPLATE, ingredients_path)
        self.ingredients = load_ingredients_from_yaml(ingredients_path)
        self.recipe_dir = Path(recipe_dir)
        self.recipe_dict = load_recipes_from_dir(self.recipe_dir)

        self.meal_plan_dir = meal_plan_dir

    def recipes(self) -> typing.Iterable[core.Recipe]:
        return (rh.recipe for rh in self.recipe_dict.values())

    def recipe_names(self) -> typing.Sequence[str]:
        return list(r.name for r in self.recipes())

    def recipe_holders(self) -> typing.Iterable[RecipeHolder]:
        return self.recipe_dict.values()

    def get_recipe(self, recipe_name: str) -> core.Recipe:
        return self.recipe_dict[recipe_name].recipe


# TODO: load from cfg file
GAMP_CONFIG = GAMPConfig()
