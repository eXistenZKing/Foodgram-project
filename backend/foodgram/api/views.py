from django.http import HttpResponse
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredients,
    Subscribe,
    Favourites,
    ShoppingCart
)
from .serializers import (
    CreateUserSerializer,
    CustomUserSerializer,
    CustomUserAvatarSerializer,
    IngredientSerializer,
    TagSerializer,
    RecipeIngredientsSerializer,
    RecipeListSerializer,
    AmountIngredientsSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    ShoppingCartSerializer,
    FavouritesSerializer,
    SubscribeListSerizliazer,
    SubscribeSerializer,
    ShoppingCartDownloadSerializer
)


class CustomUserViewset(viewsets.GenericViewSet):
    pass


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None