from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтра рецептов по тегам; вкладе 'избранное'; корзине покупок."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags', to_field_name='slug',
        lookup_expr='startswith',
        queryset=Tag.objects.all()
    )
    is_favourited = filters.BooleanFilter(method='filter_is_favourited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favourited', 'is_in_shopping_cart']

    def filter_is_favourited(self, queryset, name, values):
        user = self.request.user
        if values and not user.is_anonymous:
            return queryset.filter(favourite_by_users__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, values):
        user = self.request.user
        if values and not user.is_anonymous:
            return queryset.filter(shopping_cart__user=user)
        return queryset
