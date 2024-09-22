from django.contrib import admin
from recipes.models import (Favorites, Ingredient, Recipe, RecipeIngredients,
                            RecipeShortLink, ShoppingCart, Subscribe, Tag)

from .constants import EMPTY_FIELD_MSG
from .models import CustomUser as User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ['username', 'email',]
    empty_value_display = EMPTY_FIELD_MSG


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'author', 'get_favorite_count',]
    search_fields = ['author__first_name', 'name',]
    list_filter = ['tags',]

    empty_value_display = EMPTY_FIELD_MSG

    def get_favorite_count(self, obj):
        return obj.favorite_by_users.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'measurement_unit',]
    search_fields = ['name',]


admin.site.register(Tag)
admin.site.register(RecipeIngredients)
admin.site.register(Subscribe)
admin.site.register(Favorites)
admin.site.register(ShoppingCart)
admin.site.register(RecipeShortLink)
