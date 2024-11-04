import phonenumbers
from django.core.exceptions import ValidationError


def validate_phone_number(value):
    try:
        parsed_number = phonenumbers.parse(value, None)
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationError(f"{value} is not a valid phone number.")
    except phonenumbers.NumberParseException:
        raise ValidationError(f"{value} is not a valid phone number format.")
