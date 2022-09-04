from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

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
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeIngredientEditSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField(max_length=None, use_url=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time',)
        read_only_fields = ('is_favorited', 'is_in_shopping_cart',)

    def get_ingredients(self, obj):
        queryset = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(queryset, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj.id).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientEditSerializer(many=True)
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'ingredients', 'name',
                  'image', 'text', 'cooking_time',)
        read_only_fields = ('author',)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients_data:
            amount = ingredient['amount']
            id = ingredient['id']
            RecipeIngredient.objects.create(
                ingredient=get_object_or_404(Ingredient, id=id),
                recipe=recipe, amount=amount
            )
        for tag in tags_data:
            recipe.tags.add(tag)
        return recipe

    def validate(self, data):
        ingredients_data = data['ingredients']
        ingredients_set = set()
        for ingredient in ingredients_data:
            if ingredient['amount'] <= 0:
                raise serializers.ValidationError(
                    'Вес ингредиента должен быть больше 0'
                )
            if ingredient['id'] in ingredients_set:
                raise serializers.ValidationError(
                    'Ингредиент в рецепте не должен повторяться.'
                )
            ingredients_set.add(ingredient['id'])
        return data

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )

        RecipeIngredient.objects.filter(recipe=instance).delete()
        for ingredient in ingredients_data:
            amount = ingredient['amount']
            id = ingredient['id']
            RecipeIngredient.objects.create(
                ingredient=get_object_or_404(Ingredient, id=id),
                recipe=instance, amount=amount
            )
        instance.save()
        instance.tags.set(tags_data)
        return instance

    def to_representation(self, instance):
        return RecipeListSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class FavAndShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


# class SubscriptionsSerializer(serializers.ModelSerializer):
#     # id = serializers.IntegerField(source='author.pk')
#     # email = serializers.EmailField(source='author.email')
#     # username = serializers.CharField(source='author.username')
#     # first_name = serializers.CharField(source='author.first_name')
#     # last_name = serializers.CharField(source='author.last_name')
#     is_subscribed = serializers.SerializerMethodField()
#     recipes = FavAndShoppingCartSerializer(many=True)
#     recipes_count = serializers.SerializerMethodField(read_only=True)

#     class Meta:
#         model = User
#         fields = ('id', 'email', 'username', 'first_name', 'last_name',
#                   'is_subscribed', 'recipes', 'recipes_count')

#     def get_is_subscribed(self, obj):
#         user = self.context.get('request').user
#         return (user.is_authenticated and Subscription.objects.filter(
#             author=obj, user=user).exists())

#     # def get_recipes(self, obj):
#     #     request = self.context.get('request')
#     #     recipes_limit = request.GET.get('recipes_limit')
#     #     if recipes_limit:
#     #         queryset = obj.author.recipes.all()[:int(recipes_limit)]
#     #     else:
#     #         queryset = obj.author.recipes.all()
#     #     return FavAndShoppingCartSerializer(queryset, many=True).data

#     def get_recipes_count(self, obj):
#         return obj.recipes.count()


# class ManageSubscribtionSerializer(serializers.ModelSerializer):
#     user = UserSerializer(read_only=True)
#     author = serializers.HiddenField(default=UserSerializer(read_only=True))

#     class Meta:
#         model = Subscription
#         fields = ('user', 'author',)

#     def validate(self, data):
#         user = self.context['request'].user
#         author_id = self.context['view'].kwargs['id']
#         author = get_object_or_404(
#             User, pk=author_id
#         )
#         if user == author:
#             raise serializers.ValidationError(
#                 {"errors": "Вы не можете подписаться на самого себя."}
#             )
#         if Subscription.objects.filter(user=user, author=author).exists():
#             raise serializers.ValidationError(
#                 {"errors": "Вы уже подписаны на этого пользователя."}
#             )
#         return data

#     def create(self, validated_data):
#         user = self.context['request'].user
#         author_id = author_id = self.context['view'].kwargs['id']
#         author = get_object_or_404(
#             User, pk=author_id
#         )
#         return Subscription.objects.create(user=user, author=author)


# class SubscriptionSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(source='author.id')
#     email = serializers.EmailField(source='author.email')
#     first_name = serializers.CharField(source='author.first_name')
#     last_name = serializers.CharField(source='author.last_name')
#     recipes = serializers.SerializerMethodField()
#     recipes_count = serializers.SerializerMethodField()

#     class Meta:
#         model = Subscription
#         fields = (
#             'id', 'email', 'first_name',
#             'last_name', 'recipes', 'recipes_count'
#         )

#     def get_recipes(self, obj):
#         request = self.context.get('request')
#         if request.GET.get('recipes_limit'):
#             recipes_limit = int(request.GET.get('recipes_limit'))
#             queryset = Recipe.objects.filter(
#                 author=obj.author
#             ).order_by('-id')[:recipes_limit]
#         else:
#             queryset = Recipe.objects.filter(
#                 author=obj.author
#             ).order_by('-id')
#         return FavAndShoppingCartSerializer(queryset, many=True).data

#     def get_recipes_count(self, obj):
#         return Recipe.objects.filter(author=obj.author).count()

class SubscriptionListSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        context = {'request': request}
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        return FavAndShoppingCartSerializer(
            recipes, many=True, context=context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора!'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return SubscriptionListSerializer(
            instance.author, context=context).data
