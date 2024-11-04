from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from django.db import models
from rest_framework.response import Response

from news.filters import NewsFilter
from utils.pagination import Pagination

from news.models import News, NewsType
from news.serializers import NewsListSerializer, NewsDetailSerializer


@extend_schema(tags=["news"])
class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    filterset_class = NewsFilter
    pagination_class = Pagination
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return News.objects.order_by(
            models.Case(
                models.When(type=NewsType.DEFAULT, then=1),
                default=0
            ), '-created_at'
        )

    def get_serializer_class(self):
        if self.action == "list":
            return NewsListSerializer
        else:
            return NewsDetailSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "News deleted successfully."}, status=status.HTTP_200_OK
        )
