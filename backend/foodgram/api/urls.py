from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, download_shopping_cart,
                    GetShortLinkView, IngredientViewSet,
                    RecipeViewSet, RedirectShortLinkView,
                    TagViewSet)

app_name = 'api'

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path("recipes/download_shopping_cart/",
         download_shopping_cart,
         name='download_shopping_cart'),
    path('s/<str:short_hash>/',
         RedirectShortLinkView.as_view(),
         name='redirect_short_link',),
    path('recipes/<int:pk>/get-link/',
         GetShortLinkView.as_view(),
         name="get_link",),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
