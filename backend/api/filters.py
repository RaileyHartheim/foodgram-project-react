import django_filters
from django.contrib.auth import get_user_model

from recipes.models import Ingredient, Recipe

User = get_user_model()


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(
        queryset=User.objects.all()
    )
    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = django_filters.BooleanFilter(
        widget=django_filters.widgets.BooleanWidget()
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        widget=django_filters.widgets.BooleanWidget()
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart',)
