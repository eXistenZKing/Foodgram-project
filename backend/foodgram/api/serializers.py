from core.models import CustomUser as User
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from recipes.models import (Favorites, Ingredient, Recipe, RecipeIngredients,
                            ShoppingCart, Subscribe, Tag)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from .fields import Base64ImageField


class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор создания нового пользователя."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        if User.objects.filter(username=attrs.get('username')).exists():
            raise ValidationError("Имя пользователя занято.")
        return super().validate(attrs)

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'email': instance.email,
            'username': instance.username
        }


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор получения (просмотра) профиля пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'is_subscribed',
            'avatar'
        ]

    def get_is_subscribed(self, obj):
        """Проверка наличия подписки на просматриваемого пользователя"""
        user = self.context['request'].user
        return user.subscriber.filter(
            author=obj
        ).exists() if user.is_authenticated else False


class CustomUserAvatarSerializer(CustomUserSerializer):
    """Сериализатор для добавления аватара."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ['avatar']


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов."""
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для связной модели RecipeIngredients,
    списка ингредиентов для рецепта.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredients
        fields = ['id', 'name', 'amount', 'measurement_unit']


# class AmountIngredientsSerializer(serializers.ModelSerializer):
#     """Сериализатор количества ингредиента."""
#     id = serializers.PrimaryKeyRelatedField(
# queryset=Ingredient.objects.all())
#     amount = serializers.IntegerField()

#     class Meta:
#         model = RecipeIngredients
#         fields = ("id", "amount")

#     def validate(self, data):
#         if data['amount'] < 1:
#             raise serializers.ValidationError(
#                 'Мин. количество ингредиента 1 у.е.'
#             )
#         return data


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = RecipeIngredientsSerializer(many=True, read_only=True,
                                              source='recipeingredients')
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def get_is_favorited(self, obj):
        user = self.context['request'].user.id
        recipe = obj.id
        return Favorites.objects.filter(
            user_id=user,
            recipe_id=recipe).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user.id
        recipe = obj.id
        return ShoppingCart.objects.filter(
            user_id=user,
            recipe_id=recipe).exists()

    def create_ingredients_list(self, ingredients, recipe):
        """Создание списка ингредиентов для рецепта."""
        RecipeIngredients.objects.bulk_create(
            [
                RecipeIngredients(
                    recipe=recipe,
                    ingredient_id=ingredient['id'],
                    amount=ingredient['amount'],
                )
                for ingredient in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = self.context['request'].data.get('ingredients', [])
        tags = self.context['request'].data.get('tags', [])
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        self.create_ingredients_list(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = self.context['request'].data.get('ingredients', [])
        tags = self.context['request'].data.get('tags', [])

        image = validated_data.pop('image', None)
        if image:
            instance.image = image

        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.recipeingredients.all().delete()
        self.create_ingredients_list(ingredients, instance)
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        ingredients = instance.recipeingredients.all()
        ingredients_representation = RecipeIngredientsSerializer(
            ingredients, many=True
        ).data
        representation['ingredients'] = ingredients_representation

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            author = instance.author
            is_subscribed = Subscribe.objects.filter(
                user=request.user, author=author
            ).exists()
            representation['author']['is_subscribed'] = is_subscribed

        return representation

    def validate(self, data):
        if self.instance is None and not data.get('image'):
            raise ValidationError('Необходимо изображение рецепта.')

        tags = self.context['request'].data.get('tags', [])
        ingredients = self.context['request'].data.get('ingredients', [])

        if not tags:
            raise ValidationError('Необходимо выбрать хотя бы один тэг.')

        if not ingredients:
            raise ValidationError('Необходимо добавить хотя '
                                  'бы один ингредиент.')

        checked_ingredients = set()
        for ingredient in ingredients:
            if int(ingredient['amount']) < 1:
                raise ValidationError('Мин. количество ингредиента 1 у.е.')
            if ingredient['id'] in checked_ingredients:
                raise ValidationError('Нельзя использовать два '
                                      'одинаковых ингредиента.')
            checked_ingredients.add(ingredient['id'])

        return data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода сокращенной информации о рецепте."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор для списка 'Избранное'."""
    class Meta:
        model = Favorites
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        """Представление данных для формата JSON в списке 'Избранное'."""
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class SubscribeSerialiazer(serializers.ModelSerializer):
    """Сериализатор модели подписки на автора."""
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = CustomUserSerializer.Meta.fields + [
            'recipes', 'recipes_count'
        ]
        read_only_fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'avatar'
        ]

    def get_is_subscribed(self, obj):
        """Проверка наличия подписки на просматриваемого пользователя"""
        user = self.context['request'].user
        return user.subscriber.filter(
            author=obj
        ).exists() if user.is_authenticated else False

    def get_recipes_count(self, obj):
        """Подсчитывает кол-во рецептов для 'recipes_limit'."""
        return Recipe.objects.filter(author=obj).count()

    def get_recipes(self, obj):
        """Добавляет в выдачу подписок рецепты избранных авторов."""
        request = self.context.get('request')
        recipes = Recipe.objects.filter(author=obj).count()
        recipes_limit = request.GET.get('recipes_limit')

        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = ShortRecipeSerializer(recipes, many=True)
        return serializer.data

    def validate_subscribe(self, validated_data):
        author = validated_data['author']
        user = self.context.get('request').user
        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя!')
        elif not User.objects.filter(username=author).exists():
            raise serializers.ValidationError(
                f'Пользователь с username {author} не существует.')
        return validated_data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для сохранения рецепта в список покупок."""
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe')
            ),
        )

    def to_representation(self, instance):
        """Представление данных для формата JSON в списке покупок."""
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
