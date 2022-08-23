from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from recipes.models import Tag

from .serializers import TagSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
