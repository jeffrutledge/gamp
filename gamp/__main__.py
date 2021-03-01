from pathlib import Path
import typing
import itertools

import click
import yaml
import pint

# CLICK


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


class GAMPConfig():
    @staticmethod
    def load_ingredients(path: str) -> typing.List[str]:
        ingredients = yaml.safe_load(Path(path).open('r'))
        assert(all(isinstance(i, str) for i in ingredients))
        return ingredients

    def __init__(self, ingredients_path: str = './ingredients.yaml'):
        self.ingredients = self.load_ingredients(ingredients_path)

        self.ureg = pint.UnitRegistry()
        self.ureg.define('@alias tbsp = tbs')
        self.ureg.define('@alias tsp = tsp')


GAMP_CONFIG = GAMPConfig()


# YAML
class OrderedDumper(yaml.Dumper):
    def __init__(self, *args, sort_keys=False, **kwargs):
        super().__init__(*args, sort_keys=False, **kwargs)


def is_valid_ingredient(ingredient: str) -> bool:
    return ingredient in GAMP_CONFIG.ingredients


class Recipe():
    @classmethod
    def yaml_constructor(cls, loader: yaml.Loader, node: yaml.MappingNode):
        kwargs = loader.construct_mapping(node, deep=True)
        kwargs['ingredients'] = {i: GAMP_CONFIG.ureg(q)
                                 for i, q in kwargs['ingredients'].items()}
        return cls(**kwargs)

    @staticmethod
    def yaml_representer(dumper: yaml.Dumper, data: 'Recipe'):
        mapping = dict(
            name=data.name,
            rating=data.rating,
            ingredients={i: str(q) for i, q in data.ingredient_qtys.items()},
            steps=data.steps,
        )
        return dumper.represent_mapping('!Recipe', mapping)

    def __init__(self,
                 *,
                 name: str,
                 rating: [int] = 3,
                 ingredients: typing.Mapping[str, pint.Quantity],
                 steps: [str]):
        self.name = name
        self.rating = rating
        self.ingredient_qtys = ingredients
        self.steps = steps

    def __repr__(self):
        return f'{self.name} ({self.rating}/3): {self.ingredient_qtys}'

    def is_valid(self) -> bool:
        valid_ingredients = all(is_valid_ingredient(i)
                                for i in self.ingredients())
        valid_rating = 0 <= self.rating <= 3
        return valid_ingredients and valid_rating

    def ingredients(self):
        return list(self.ingredient_qtys.keys())


yaml.add_constructor(u'!recipe', Recipe.yaml_constructor)
yaml.add_representer(Recipe, Recipe.yaml_representer)


class MealPlan(yaml.YAMLObject):
    yaml_tag = u'!MealPlan'


# CLI
@click.command(cls=AliasedGroup)
def gamp():
    pass


@gamp.command()
@click.argument('recipe-dir', type=click.Path(file_okay=False, exists=True))
def validate_recipes(recipe_dir):
    recipe_dir = Path(recipe_dir)
    recipes = []
    for recipe_path in recipe_dir.glob('*.yaml'):
        recipes.extend(
            itertools.chain(*yaml.full_load_all(recipe_path.open('r'))))

    print(yaml.dump(recipes[0], Dumper=OrderedDumper))
    breakpoint()


@gamp.command()
def inventory_worksheet():
    pass


@gamp.command()
def grocery_list():
    pass


@gamp.command()
def cook():
    pass


if __name__ == '__main__':
    gamp()
