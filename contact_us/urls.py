from rest_framework import routers

from contact_us.views import ContactUsViewSet

router = routers.DefaultRouter()
router.register('', ContactUsViewSet, basename='contact-us')

urlpatterns = router.urls

