from django.urls import path
from rest_framework import routers
from checkout.views import CheckoutView, OrderListView, OrderStatisticsView, CoinBaseWebhookView

router = routers.DefaultRouter()

router.register(r"orders", OrderListView, basename="order-list")
urlpatterns = [
    path("", CheckoutView.as_view(), name="checkout"),
    path("coinbase-webhook/", CoinBaseWebhookView.as_view(), name="coinbase-webhook"),
    path("order-statistics/", OrderStatisticsView.as_view(), name="order-statistics"),
]

urlpatterns += router.urls
