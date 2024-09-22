from core.filtres import IngredientNameFilter, RecipeFilter
from core.models import CustomUser as User
from core.pagination import PageSizePagination
from core.permissions import IsAuthorOrReadOnly
from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from recipes.models import (Favourites, Ingredient, Recipe, RecipeIngredients,
                            RecipeShortLink, ShoppingCart, Subscribe, Tag)
from rest_framework import filters, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .serializers import (CustomUserAvatarSerializer, CustomUserSerializer,
                          FavouritesSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscribeSerialiazer, TagSerializer)


class CustomUserViewSet(viewsets.GenericViewSet):
    """Вьюсет для управления пользователем."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='me'
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
        serializer_class=CustomUserAvatarSerializer
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
        serializer_class=SubscribeSerialiazer,
        pagination_class=PageSizePagination
    )
    def subscribe(self, request, pk=None):
        """Управление подпиской на автора рецептов."""
        user = request.user
        author = get_object_or_404(User, id=pk)
        sibscribe = Subscribe.objects.filter(
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
        if sibscribe.exists():
            sibscribe.delete()
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
        queryset = User.objects.filter(subscribers__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerialiazer(
            pages, many=True,
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
    pagination_class = PageSizePagination
    filterset_class = RecipeFilter
    permission_classes = [IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly]
    serializer_class = RecipeSerializer

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """Управление списком покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = get_object_or_404(User, id=request.user.id)
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
    def favourites(self, request, pk):
        """Управление списком избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = get_object_or_404(User, id=request.user.id)
        favourites = Favourites.objects.filter(
            user=user.id,
            recipe=recipe
        )
        if request.method == 'POST':
            serializer = FavouritesSerializer(
                data={'user': user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if favourites.exists():
            favourites.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['GET'],
        pagination_class=None,
    )
    def download_shopping_cart(self, request):
        """Скачивание корзины покупок."""
        user = request.user
        list_recipes = (
            RecipeIngredients.objects.filter(
                recipe__recipe_download__user=user)
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
        return redirect(f"{settings.BASE_URL}recipes/{recipe.recipe.id}/")


class GetShortLinkView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        recipe, _ = RecipeShortLink.objects.get_or_create(recipe=recipe)
        short_link = recipe.get_short_link()
        absolute_short_link = f"{settings.BASE_URL}api/s/{short_link}/"
        return Response({"get_link": absolute_short_link}, status=200)
