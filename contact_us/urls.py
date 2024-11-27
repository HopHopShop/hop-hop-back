from django.urls import path
from rest_framework import routers

from contact_us.views import ContactUsViewSet, SendQuickAnswer

router = routers.DefaultRouter()
router.register('', ContactUsViewSet, basename='contact-us')

urlpatterns = [
    path('quick-answer/', SendQuickAnswer.as_view(), name="quick-answer"),
]

urlpatterns += router.urls

