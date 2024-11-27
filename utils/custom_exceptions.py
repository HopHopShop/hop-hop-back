import requests
from drf_standardized_errors.handler import ExceptionHandler
from rest_framework.exceptions import APIException


class ProductAlreadyExistException(APIException):
    status_code = 400
    default_detail = "Product is already exist."


class ProductNotExistException(APIException):
    status_code = 400
    default_detail = "Product does not exist."


class CouponNotExistException(APIException):
    status_code = 400
    default_detail = "Coupon does not exist."


class CartEmptyException(APIException):
    status_code = 400
    default_detail = "Cart is empty"


class StripeCardError(APIException):
    status_code = 400
    default_detail = "Card error."
    default_code = "card_error"


class StripeRateLimitError(APIException):
    status_code = 429
    default_detail = "Rate limit error."
    default_code = "rate_limit_error"


class StripeInvalidRequestError(APIException):
    status_code = 400
    default_detail = "Invalid parameters."
    default_code = "invalid_request"


class StripeAuthenticationError(APIException):
    status_code = 401
    default_detail = "Authentication error."
    default_code = "authentication_error"


class StripeAPIConnectionError(APIException):
    status_code = 502
    default_detail = "Network error."
    default_code = "api_connection_error"


class StripeGeneralError(APIException):
    status_code = 500
    default_detail = "Something went wrong. You were not charged. Please try again."
    default_code = "stripe_error"


class InvalidCredentialsError(APIException):
    status_code = 401
    default_detail = "Invalid credentials."
    default_code = "invalid_credentials"


class CartExceptionHandler(ExceptionHandler):
    def convert_known_exceptions(self, exc: Exception) -> Exception:
        if isinstance(exc, requests.Timeout):
            return CartEmptyException()
        else:
            return super().convert_known_exceptions(exc)
