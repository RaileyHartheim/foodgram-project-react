from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription


User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'username', 'first_name', 'last_name',)


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if obj == user or user.is_anonymous:
            return False
        return Subscription.objects.filter(author=obj, user=user).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeIngredientEditSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time',)

    def get_ingredients(self, obj):
        queryset = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(queryset, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'ingredients', 'name',
                  'image', 'text', 'cooking_time',)
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data['ingredients']
        ingredients_list = []
        for item in ingredients:
            if item['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество должно быть не меньше единицы!'
                )
            ingredient = get_object_or_404(
                Ingredient, id=item['id']
            )
            if ingredient in ingredients_list:
                raise serializers.ValidationError(
                    'Нельзя добавлять ингредиент дважды!'
                )
            ingredients_list.append(ingredient)

        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Нужен как минимум один тэг!'
            )
        for tag in tags:
            if not Tag.objects.filter(name=tag).exists():
                raise serializers.ValidationError(
                    f'Тэга {tag} не существует.'
                )

        cooking_time = data['cooking_time']
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время приготовления должно составлять больше минуты!'
            )

        return data

    def create_tags(self, tags, recipe):
        for tag in tags:
            recipe.tags.add(tag)

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        tags = validated_data.pop['tags']
        ingredients = validated_data.pop['ingredients']
        recipe = Recipe.objects.create(**validated_data)
        self.create_tags(tags, recipe)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            instance.tags.clear()
            self.create_tags(
                validated_data.pop('tags'), instance
            )
        if 'ingredients' in validated_data:
            instance.ingredients.clear()
            self.create_ingredients(
                validated_data.pop('ingredients'), instance
            )
        return super().update(instance, validated_data)


class FavAndShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
