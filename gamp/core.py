import typing

import pint
import pandas as pd


def parse_qty_with_default_unit(qty_str: str,
                                ureg: pint.UnitRegistry,
                                default_unit: str = 'ton') -> pint.Quantity:
    qty = ureg(qty_str)
    if not isinstance(qty, ureg.Quantity):
        qty = ureg(qty_str + ' ' + default_unit)

    return qty


class Recipe():
    def __init__(self,
                 *,
                 name: typing.Optional[str] = None,
                 rating: [int] = 3,
                 ingredients: typing.Mapping[str, str],
                 steps: [str]):
        self.name = name
        self.rating = rating
        self.ingredient_qtys = ingredients
        self.steps = steps

    def __repr__(self):
        return f'{self.name} ({self.rating}/3): {self.ingredient_qtys}'

    def is_valid(self,
                 ingredients: typing.Set[str],
                 ureg: pint.UnitRegistry) -> bool:
        valid_ingredients = all(i in ingredients for i in self.ingredients())
        valid_rating = 0 <= self.rating <= 3

        return valid_ingredients and valid_rating

    def ingredients(self):
        return list(self.ingredient_qtys.keys())

    def ingredient_series(self, ureg: pint.UnitRegistry):
        s = pd.Series({ingredient: parse_qty_with_default_unit(str(qty), ureg)
                       for ingredient, qty in self.ingredient_qtys.items()})
        s.index.name = 'ingredient'
        return s
