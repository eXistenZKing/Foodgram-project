from core.models import CustomUser as User
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from recipes.models import (Favourites, Ingredient, Recipe, RecipeIngredients,
                            ShoppingCart, Subscribe, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .fields import Base64ImageField


class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор создания нового пользователя."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password',)
        extra_kwargs = {'password': {'write_only': True}}


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор получения (просмотра) профиля пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'is_subscribed',
            'avatar',
        )

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
        fields = ('avatar',)


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
        fields = ('id', 'name', 'amount', 'measurement_unit',)


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для получения спискка рецептов (GET method)."""
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = RecipeIngredientsSerializer(many=True,
                                              read_only=True,
                                              source='ingredients')
    tags = TagSerializer(many=True, read_only=True)
    is_favourite = serializers.SerializerMethodField()
    is_in_shoppingcart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favourite(self, obj):
        user = self.context['request'].user.id
        recipe = obj.id
        return Favourites.objects.filter(
            user_id=user,
            recipe_id=recipe).exists()

    def get_is_in_shoppingcart(self, obj):
        user = self.context['request'].user.id
        recipe = obj.id
        return ShoppingCart.objects.filter(
            user_id=user,
            recipe_id=recipe).exists()


class AmountIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор количества ингредиента."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredients
        fields = ("id", "amount")

    def validate(self, data):
        if data['amount'] < 1:
            raise serializers.ValidationError(
                'Мин. количество ингредиента 1 у.е.'
            )
        return data


class RecipeSerializer(serializers.ModelField):
    """Сериализатор рецептов."""
    image = Base64ImageField()
    ingredients = AmountIngredientsSerializer(many=True)
    tags = serializers.SlugRelatedField(
        slug_field='id', queryset=Tag.objects.all(), many=True, required=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'image',
            'name',
            'text',
            'cooking_time',
            'ingredients',
            'tags',
        )
        extra_kwargs = {'image': {'required': True}}

    def to_representation(self, instance):
        """Представление данных для формата JSON."""
        return RecipeListSerializer(instance, context=self.context).data

    def create_ingredients_list(self, ingredients, recipe):
        """Создание списка ингредиентов для рецепта."""
        RecipeIngredients.objects.bulk_create(
            [
                RecipeIngredients(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'],
                )
                for ingredient in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        self.create_ingredients_list(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().update(instance, validated_data)
        if ingredients:
            recipe.ingredients.clear()
            self.create_ingredients_list(ingredients, recipe)
        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)
        return recipe


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода сокращенной информации о рецепте."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


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


class FavouritesSerializer(serializers.ModelSerializer):
    """Сериализатор для списка 'Избранное'."""
    class Meta:
        model = Favourites
        fields = ('user', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=Favourites.objects.all(),
                fields=('user', 'recipe')
            ),
        )

    def to_representation(self, instance):
        """Представление данных для формата JSON в списке 'Избранное'."""
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class SubscribeListSerialiazer(serializers.ModelSerializer):
    """Сериализатор для получения списка подписок (GET method)."""
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )
        read_only_fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'avatar',
        )

    def get_recipes_count(self, data):
        """Подсчитывает кол-во рецептов для 'recipes_limit'."""
        return data.user.count()

    def get_recipes(self, data):
        """Добавляет в выдачу подписок рецепты избранных авторов."""
        request = self.context.get('request')
        recipes = data.user.all()
        recipes_limit = request.GET.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = ShortRecipeSerializer(recipes, many=True)
        return serializer.data


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор подписки на автора."""

    class Meta:
        modlel = Subscribe
        fields = ('user', 'author')
        validators = (
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'author')
            ),
        )

    def validate_subscribe(self, validated_data):
        author = validated_data['author']
        user = self.context.get('request').user
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!')
        elif not User.objects.filter(username=author).exists():
            raise serializers.ValidationError(
                f'Пользователь с username {author} не существует.')
        return validated_data

    def to_representation(self, instance):
        return SubscribeListSerialiazer(
            instance.subscription_on,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartDownloadSerializer(serializers.ModelSerializer):
    """Сериализатор для скачивания списка покупок."""

    shopping_cart = serializers.FileField()

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe', 'shopping_cart')
