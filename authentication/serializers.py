import re

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from authentication.models import PasswordReset
from authentication.utils import send_reset_password_email


def validate_password_confirm(password, password2):
    if password != password2:
        raise serializers.ValidationError("Passwords do not match")
    return True


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=256)

    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
        )

        write_only_fields = ("password",)

    @staticmethod
    def validate_password(value):
        """
        Ensure that the password contains at least:
        - 1 uppercase letter
        - 1 special character
        - 1 number
        """
        if not re.search(r'[A-Z]', value):
            raise ValidationError("Password must contain at least 1 uppercase letter.")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError("Password must contain at least 1 special character.")

        if not re.search(r'\d', value):
            raise ValidationError("Password must contain at least 1 number.")

        return value

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    user_role = serializers.SerializerMethodField()
    old_password = serializers.CharField(write_only=True, min_length=8, max_length=256)
    password = serializers.CharField(write_only=True, min_length=8, max_length=256)

    def get_user_role(self, obj) -> str:
        if obj.is_superuser:
            return "Admin"
        elif obj.is_staff:
            return "Staff"
        return "User"

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "phone_number",
            "shipping_country",
            "shipping_city",
            "shipping_address",
            "shipping_postcode",
            "old_password",
            "password",
            "user_role",
        )
        read_only_fields = ["id", "user_role"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 6}}

    def validate_password_change(self, attrs):
        old_password = attrs.pop("old_password", None)

        if not old_password:
            raise serializers.ValidationError("Missing old password")
        elif not self.instance.check_password(old_password):
            raise serializers.ValidationError("Incorrect old password")

        if not attrs.get("password", None):
            raise serializers.ValidationError("Missing password")

        return attrs

    def validate(self, attrs):
        attrs = super().validate(attrs)
        filtered_attrs = {
            k: v for k, v in attrs.items()
            if not isinstance(v, str) or (isinstance(v, str) and v != "")
        }

        if "old_password" in filtered_attrs or "password" in filtered_attrs:
            filtered_attrs = self.validate_password_change(filtered_attrs)

        return filtered_attrs

    def update(self, instance, validated_data):
        """Update a user, set the password correctly and return it"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()
        return user


class CustomerAdminSerializer(CustomerSerializer):
    is_active = serializers.BooleanField()
    is_staff = serializers.BooleanField()

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "shipping_country",
            "shipping_city",
            "shipping_address",
            "shipping_postcode",
            "is_staff",
            "user_role",
            "is_active",
        )
        read_only_fields = ["id", "password"]

    def update(self, instance, validated_data):
        """Update a user, set the role or deactivate their account"""
        is_staff = validated_data.pop("is_staff", None)
        is_active = validated_data.pop("is_active", None)
        validated_data.pop("password", None)

        user = super().update(instance, validated_data)

        if is_staff is not None:
            user.is_staff = is_staff
        if is_active is not None:
            user.is_active = is_active

        user.save()

        return user


class ResetPasswordRequestSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = PasswordReset
        fields = ('email',)

    def validate(self, attrs):
        user = get_user_model().objects.filter(email__iexact=attrs["email"]).first()
        if not user:
            raise serializers.ValidationError("There is no user with provided email")

        if not user.is_active:
            raise ValidationError("Your account is banned, please contact the administration.")

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        attrs['token'] = token

        return attrs

    def create(self, validated_data):
        token = validated_data.pop('token', None)
        email = validated_data.pop('email', None)

        reset_password = PasswordReset.objects.filter(user__email__iexact=email).first()

        if reset_password:
            reset_password.delete()

        user = get_user_model().objects.filter(email__iexact=email).first()

        instance = PasswordReset(user=user, token=token)
        instance.save()

        send_reset_password_email(token, email)

        return instance


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        """
        Validate the password reset token, expiration, and password match.
        :param attrs:
        :return:
        """
        user = get_user_model().objects.filter(email__iexact=attrs['email']).first()
        if not user:
            raise serializers.ValidationError("There is no user with the provided id.")

        reset_password = PasswordReset.objects.filter(user__email__iexact=user.email).first()
        if not reset_password:
            raise serializers.ValidationError("Wrong recovery address, provided user didn't request "
                                              "recovery password.")

        valid_token = reset_password.token == attrs["token"]
        is_expired = reset_password.expires_at < timezone.now()

        if is_expired:
            raise serializers.ValidationError("The provided token is expired.")

        if not valid_token:
            raise serializers.ValidationError("Invalid secret token value.")

        validate_password_confirm(attrs["password"], attrs["password2"])

        return attrs

    def save(self, **kwargs):
        user = get_user_model().objects.filter(email__iexact=self.validated_data["email"]).first()
        user.set_password(self.validated_data["password"])
        user.save()

        reset_password = PasswordReset.objects.filter(user__email__iexact=self.validated_data["email"]).first()
        reset_password.delete()
