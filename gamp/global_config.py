from pathlib import Path
import typing
import collections

import pint
import yaml

from gamp import core


def yaml_recipe_constructor(loader: yaml.Loader, node: yaml.MappingNode):
    kwargs = loader.construct_mapping(node, deep=True)
    kwargs['ingredients'] = {i: q for i, q in kwargs['ingredients'].items()}
    return core.Recipe(**kwargs)


yaml.add_constructor(u'!recipe', yaml_recipe_constructor)


def yaml_recipe_representer(dumper: yaml.Dumper, data: core.Recipe):
    mapping = dict(
        name=data.name,
        rating=data.rating,
        ingredients={i: str(q) for i, q in data.ingredient_qtys.items()},
        steps=data.steps,
    )
    return dumper.represent_mapping('!Recipe', mapping)


yaml.add_representer(core.Recipe, yaml_recipe_representer)


class RecipeHolder:
    def __init__(self, path, recipe):
        self.path = path
        self.recipe = recipe

    def __repr__(self):
        return f'{self.recipe.name}: {self.path}'


def load_recipes_from_yaml(recipe_dir: Path):
    recipe_dict = dict()
    for recipe_path in recipe_dir.glob('*.yaml'):
        recipe = yaml.full_load(recipe_path.open('r'))
        recipe_dict[recipe.name] = RecipeHolder(recipe_path, recipe)

    return recipe_dict


def load_ingredients_from_yaml(path: Path) -> typing.Set[str]:
    ingredients = yaml.safe_load(Path(path).open('r'))
    assert(all(isinstance(i, str) for i in ingredients))
    return set(ingredients)


class GAMPConfig():
    def __init__(self,
                 ingredients_path: str = './ingredients.yaml',
                 recipe_dir: str = './recipes'):
        self.ureg = pint.UnitRegistry()
        self.ureg.define('@alias tbsp = tbs')
        self.ureg.define('@alias tsp = tsp')

        self.ingredients = load_ingredients_from_yaml(Path(ingredients_path))
        self.recipe_dir = recipe_dir
        self.recipe_dict = load_recipes_from_yaml(Path(recipe_dir))

    def recipes(self) -> typing.Iterable[core.Recipe]:
        return (rh.recipe for rh in self.recipe_dict.values())

    def recipe_holders(self) -> typing.Iterable[RecipeHolder]:
        return self.recipe_dict.values()



# TODO: load from cfg file
GAMP_CONFIG = GAMPConfig()
