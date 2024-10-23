from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()


class CustomAuthenticationBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                raise ValidationError("Your account is banned, please contact the administration.")
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass
        return None
