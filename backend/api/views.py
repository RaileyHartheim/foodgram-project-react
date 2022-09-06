from io import BytesIO

from django.conf import settings
from django.db.models import Sum
from django.db.models.expressions import Exists, OuterRef
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from reportlab import rl_config
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import generics, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .paginations import CustomPageNumberPagination
from .permissions import IsAdminOrAuthorOrReadOnly
from .serializers import (FavAndShoppingCartSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeListSerializer,
                          SubscribeSerializer, SubscriptionListSerializer,
                          TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет для просмотра тэгов. """

    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра ингредиентов. """

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ Вьюсет для работы с рецептами. """

    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAdminOrAuthorOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Recipe.objects.annotate(
                is_favorited=Exists(Favorite.objects.filter(
                    user=user, recipe=OuterRef('id'))
                ),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    user=user, recipe=OuterRef('id'))
                )
            ).select_related('author',)
        return Recipe.objects.all()

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def make_favorite_shopping_cart_action(self, request, check, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if check == 'favorite':
            checked_queryset = Favorite.objects.filter(
                user=user, recipe=recipe)
        elif check == 'shopping_cart':
            checked_queryset = ShoppingCart.objects.filter(
                user=user, recipe=recipe)
        if request.method == 'POST':
            if not checked_queryset:
                if check == 'favorite':
                    created = Favorite.objects.create(
                        user=user, recipe=recipe)
                    serializer = FavAndShoppingCartSerializer(created.recipe)
                elif check == 'shopping_cart':
                    created = ShoppingCart.objects.create(
                        user=user, recipe=recipe)
                    serializer = FavAndShoppingCartSerializer(created.recipe)
                return Response(
                    status=status.HTTP_201_CREATED, data=serializer.data)
            else:
                if check == 'favorite':
                    data = {'errors': 'Этот рецепт уже в избранном.'}
                elif check == 'shopping_cart':
                    data = {'errors': 'Этот рецепт уже в списке покупок.'}
                return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
        elif request.method == 'DELETE':
            if not checked_queryset:
                if check == 'favorite':
                    data = {
                        'errors': 'Этот рецепт не находится в избранном.'}
                elif check == 'shopping_cart':
                    data = {
                        'errors': 'Этот рецепт не находится в списке покупок.'}
                return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
            else:
                checked_queryset.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'], detail=True,
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """ Добавление/удаление рецептов в избранном. """

        return self.make_favorite_shopping_cart_action(
            request, check='favorite', pk=pk)

    @action(
        methods=['post', 'delete'], detail=True,
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """ Добавление/удаление рецептов в списке покупок. """

        return self.make_favorite_shopping_cart_action(
            request, check='shopping_cart', pk=pk)

    @action(
        methods=['get'], detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """ Скачивание списка покупок. """

        buffer = BytesIO()
        rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + '/data')
        pdfmetrics.registerFont(TTFont('FreeSans', 'FreeSans.ttf'))
        pdf_obj = canvas.Canvas(buffer, pagesize=A4)
        pdf_obj.setFont('FreeSans', 20)
        queryset = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user).values(
                'ingredient__name',
                'ingredient__measurement_unit'
                ).annotate(total_amount=Sum('amount'))
        pdf_title = 'Список покупок'
        title_x_coord = 260
        title_y_coord = 800
        x_coord = 50
        y_coord = 780
        if queryset:
            pdf_obj.drawCentredString(title_x_coord, title_y_coord, pdf_title)
            for item in queryset:
                pdf_obj.setFontSize(14)
                pdf_obj.drawString(
                    x_coord, y_coord,
                    f"{item['ingredient__name']} - "
                    f"{item['total_amount']} "
                    f"{item['ingredient__measurement_unit']}"
                )
                y_coord -= 15
                if y_coord < 30:
                    pdf_obj.showPage()
                    y_coord = 800
        else:
            pdf_obj.drawCentredString(
                title_x_coord,
                title_y_coord,
                'Список покупок пуст.')
        pdf_obj.showPage()
        pdf_obj.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename='shopping_cart.pdf')


class SubscriptionListView(generics.ListAPIView):
    """ Отображение подписок. """
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionListSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class SubscriptionManagementView(views.APIView):
    """ Подписка/отписка от другого пользователя. """

    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        data = {'author': id, 'user': request.user.id}
        serializer = SubscribeSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        follow = get_object_or_404(Subscription, user=user, author=author,)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
