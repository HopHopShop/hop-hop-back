from django.urls import path
from rest_framework import routers

from authentication.views import (
    CreateCustomerView,
    CustomerProfileView,
    CustomTokenRefreshView,
    LoginView,
    LogoutView,
    CustomersListView, PasswordResetRequestView, ResetPasswordView, ProfileOrder,
)

router = routers.DefaultRouter()
router.register(r"customers", CustomersListView, basename="customers")
router.register(r"profile-orders", ProfileOrder, basename="profile-order")


app_name: str = "authentication"
urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("registration/", CreateCustomerView.as_view(), name="create"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", CustomerProfileView.as_view(), name="profile"),
    path("reset-password/request/", PasswordResetRequestView.as_view(), name="request_reset_password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
]

urlpatterns += router.urls
