from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтр рецептов по тегам; вкладе 'избранное'; корзине покупок."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug', to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, values):
        user = self.request.user
        if values and not user.is_anonymous:
            return queryset.filter(favorite_by_users__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, values):
        user = self.request.user
        if values and not user.is_anonymous:
            return queryset.filter(shopping_cart__user=user)
        return queryset


class IngredientNameFilter(FilterSet):
    """Фильтр для поиска ингредиентов по названию."""
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
