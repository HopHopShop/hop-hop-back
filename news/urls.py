from django.urls import path, include
from rest_framework import routers
from news.views import NewsViewSet

router = routers.DefaultRouter()
router.register(r'news', NewsViewSet)

urlpatterns = router.urls
