import os
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from datetime import timedelta

from authentication.managers import UserManager
from utils.data_validation import validate_phone_number


def customer_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"customer-{instance.id}{extension}"

    return os.path.join("uploads/customers/", filename)


class Customer(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    phone_number = models.CharField(
        _("phone number"),
        max_length=17,
        null=True,
        unique=True,
        validators=[validate_phone_number],
    )
    avatar = models.ImageField(
        null=True,
        blank=True,
        upload_to=customer_image_file_path,
        max_length=255,
    )

    shipping_country = models.CharField(max_length=100, null=True, blank=True)
    shipping_city = models.CharField(max_length=100, null=True, blank=True)
    shipping_address = models.CharField(max_length=255, null=True, blank=True)
    shipping_postcode = models.CharField(max_length=20, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["id"]


class PasswordReset(models.Model):
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    user = models.OneToOneField(Customer, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return self.token

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)
