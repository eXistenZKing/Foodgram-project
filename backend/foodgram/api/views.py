from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from recipes.models import (Favorites, Ingredient, Recipe, RecipeIngredients,
                            RecipeShortLink, ShoppingCart, Subscribe, Tag)
from rest_framework import status, views, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .serializers import (CustomUserAvatarSerializer, CustomUserSerializer,
                          FavoritesSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscribeSerialiazer, SubscriptionsSerialiazer,
                          TagSerializer)
from core.filtres import IngredientNameFilter, RecipeFilter
from core.models import CustomUser as User
from core.pagination import PageSizePagination
from core.permissions import IsAuthorOrReadOnly


class CustomUserViewSet(viewsets.GenericViewSet):
    """Вьюсет для управления пользователями."""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CustomUserSerializer
    pagination_class = PageSizePagination

    @action(
        detail=True,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='me',
    )
    def me(self, request):
        """Просмотр собственного профиля."""
        serializer = CustomUserSerializer(request.user,
                                          context={"request": request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['PUT', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        serializer_class=CustomUserAvatarSerializer,
    )
    def avatar(self, request):
        """Изменение аватара пользователя."""
        if request.method == 'PUT':
            if request.data:
                serializer = self.get_serializer(
                    request.user,
                    data=request.data,
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            self.request.user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        pagination_class=PageSizePagination,
        serializer_class=SubscribeSerialiazer
    )
    def subscribe(self, request, pk=None):
        """Управление подпиской на автора рецептов."""
        user = request.user
        author = get_object_or_404(User, id=pk)
        subscribe = Subscribe.objects.filter(
            user=user.id,
            author=author.id
        )
        if request.method == 'POST':
            serializer = SubscribeSerialiazer(
                data={
                    'user': user.id,
                    'author': author.id
                }, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if subscribe.exists():
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        pagination_class=PageSizePagination
    )
    def subscriptions(self, request):
        """Получение списка подписок."""
        queryset = User.objects.filter(subscriptions__user=request.user)
        pagination = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerialiazer(
            pagination, many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientNameFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageSizePagination
    filterset_class = RecipeFilter
    permission_classes = [IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly]

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Управление списком покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(
            user=user.id,
            recipe=recipe
        )
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'user': user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if shopping_cart.exists():
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Управление списком избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        favorites = Favorites.objects.filter(
            user=user.id,
            recipe=recipe
        )
        if request.method == 'POST':
            serializer = FavoritesSerializer(
                data={'user': user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if favorites.exists():
            favorites.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


@permission_classes(IsAuthenticated)
@api_view(['GET'])
def download_shopping_cart(request):
    """Скачивание корзины покупок."""
    user = request.user
    list_recipes = (
        RecipeIngredients.objects.filter(
            recipe__shopping_cart__user=user.id)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(amount=Sum('amount'))
    )
    filename = 'ingredients shopping list.txt'
    content = "\n".join(
        [
            f'{ingredient["ingredient__name"]} -'
            f' {ingredient["amount"]}'
            f' {ingredient["ingredient__measurement_unit"]}'
            for ingredient in list_recipes
        ]
    )
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


class RedirectShortLinkView(View):
    def get(self, request, short_hash):
        recipe = get_object_or_404(RecipeShortLink, short_link=short_hash)
        return redirect(f"{settings.BASE_URL}/recipes/{recipe.recipe.id}/")


class GetShortLinkView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        recipe, _ = RecipeShortLink.objects.get_or_create(recipe=recipe)
        short_link = recipe.get_short_link()
        absolute_short_link = f"{settings.BASE_URL}api/s/{short_link}/"
        return Response({"get_link": absolute_short_link}, status=200)
