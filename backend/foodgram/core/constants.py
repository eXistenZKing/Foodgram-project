"""Константы, используемые в проекте."""


class RecipesLimits():
    """
    Класс, содержащий константы
    для описания моделей связанных с рецептами сущностей.
    """
    MIN_COOK_TIME = 1
    MIN_AMOUNT_INGREDIENT = 1
    MAX_LEN_RECIPE_NAME = 256
    MAX_LEN_TAG = 32
    MAX_LEN_INGREDIENT_NAME = 128
    MAX_LEN_MEASURE_UNIT = 64
    LEN_SHORT_LINK = 6


class CustomUserLimits():
    """
    Класс, содержащий константы
    для описания характеристик модели пользователя.
    """
    MAX_LEN_NAME = 150
    MAX_LEN_EMAIL = 254
    MAX_LEN_PASS = 255


EMPTY_FIELD_MSG = '-пусто-'
