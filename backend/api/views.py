from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrAuthorOrReadOnly
from .serializers import (FavAndShoppingCartSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeListSerializer,
                          TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['post', 'delete'], detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        in_favorite = Favorite.objects.filter(
            user=user, recipe=recipe
        )
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.method == 'POST':
            if not in_favorite:
                favorite = Favorite.objects.create(
                    user=user, recipe=recipe
                )
                serializer = FavAndShoppingCartSerializer(favorite.recipe)
                return Response(
                    status=status.HTTP_201_CREATED, data=serializer.data)
            data = {'errors': 'Этот рецепт уже в избранном.'}
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data=data
            )
        elif request.method == 'DELETE':
            if not in_favorite:
                data = {'errors': 'Этот рецепт не находится в избранном.'}
                return Response(
                    status=status.HTTP_400_BAD_REQUEST, data=data
                )
            in_favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'], detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        is_in_shopping_cart = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        )
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.method == 'POST':
            if not is_in_shopping_cart:
                to_cart = ShoppingCart.objects.create(
                    user=user, recipe=recipe
                )
                serializer = FavAndShoppingCartSerializer(to_cart.recipe)
                return Response(
                    status=status.HTTP_201_CREATED, data=serializer.data
                )
            data = {'errors': 'Этот рецепт уже в списке покупок.'}
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data=data
            )
        elif request.method == 'DELETE':
            if not is_in_shopping_cart:
                data = {'errors': 'Этот рецепт не находится в списке покупок.'}
                return Response(
                    status=status.HTTP_400_BAD_REQUEST, data=data
                )
            is_in_shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
