from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CreateDeleteSubscriptionView, IngredientViewSet,
                    RecipeViewSet, SubscriptionsListView, TagViewSet)


router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register(
    'users/<int:id>/subscribe',
    CreateDeleteSubscriptionView,
    basename='subscribe')
router.register(
    'users/subscriptions', SubscriptionsListView,
    basename='subscriptions'
)


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
