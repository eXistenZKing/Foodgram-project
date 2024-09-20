import hashlib

from core.constants import RecipesLimits
from core.models import CustomUser as User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Ingredient(models.Model):
    """Модель ингридиента."""
    name = models.CharField(
        max_length=RecipesLimits.MAX_LEN_INGREDIENT_NAME,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=RecipesLimits.MAX_LEN_MEASURE_UNIT,
        verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name = 'ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тэга."""
    name = models.CharField(
        max_length=RecipesLimits.MAX_LEN_TAG,
        verbose_name='Название',
        unique=True
    )
    slug = models.SlugField(
        max_length=RecipesLimits.MAX_LEN_TAG,
        verbose_name='Уникальный слаг',
        unique=True
    )

    class Meta:
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=RecipesLimits.MAX_LEN_RECIPE_NAME,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredients',
        verbose_name='Список ингредиентов',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                RecipesLimits.MIN_COOK_TIME,
                message='Мин. время приготовления 1 минута'),
        ]
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    """
    Модель для создания списка ингредиентов
    с необходимым количеством для рецепта.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipeingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipeingredients'
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(
                RecipesLimits.MIN_AMOUNT_INGREDIENT,
                message='Мин. количество ингредиента 1 у.е.'),
        ],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='recipe with a list of unique ingredients'
            )
        ]


class Subscribe(models.Model):
    """Модель для подписки на авторов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Избранный автор'
    )

    class Meta:
        verbose_name = 'подписка на авторов'
        verbose_name_plural = 'Подписки на авторов'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='preventing self-subscription'
            )
        ]

    def save(self, *args, **kwargs):
        if self.user == self.author:
            raise ValidationError('На себя подписаться невозможно.')
        super().save(*args, **kwargs)


class Favourites(models.Model):
    """Модель для избранных рецептов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favourite_by_users',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique recipes in favourites'
            )
        ]


class ShoppingCart(models.Model):
    """Модель для списка покупок (корзины)."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт в списке покупок',
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique recipe in shopping cart'
            )
        ]


class RecipeShortLink(models.Model):
    """Модель для хранения сокращённых ссылок на рецепты."""
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_link',
        verbose_name='Рецепт'
    )
    short_link = models.CharField(
        max_length=RecipesLimits.LEN_SHORT_LINK,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Сокращённая ссылка"
    )

    def get_short_link(self):
        """Возвращает сокращённую ссылку на рецепт."""
        return self.short_link

    def generate_short_link(self):
        """Генератор сокращённой ссылки из хэша названия рецепта."""
        hash_object = hashlib.md5(
            f"{self.recipe.id}{self.recipe.name}".encode()
        )
        short_hash = hash_object.hexdigest()[:RecipesLimits.LEN_SHORT_LINK]

        while RecipeShortLink.objects.filter(short_link=short_hash).exists():
            short_hash = hashlib.md5(
                short_hash.encode()).hexdigest()[:RecipesLimits.LEN_SHORT_LINK]
        return short_hash

    def save(self, *args, **kwargs):
        """Создание сокращённой ссылки для нового запрашиваемого рецепта."""
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)
