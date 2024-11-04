from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/doc/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("__debug__/", include("debug_toolbar.urls")),
    path("admin/", admin.site.urls),
    path("api/email-subscription", include("email_subscription.urls")),
    path("api/shop/", include("shop.urls")),
    path("api/auth/", include("authentication.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/checkout/", include("checkout.urls")),
    path("api/wishlist/", include("wishlist.urls")),
    path("api/news/", include("news.urls")),
    path("api/contact-us/", include("contact_us.urls")),
]
