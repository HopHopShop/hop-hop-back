from rest_framework.renderers import JSONRenderer
from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse


class MyExceptionFormatter(ExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        required_field_errors = [
            error for error in error_response.errors
            if (error_response.type == "validation_error"
                and error.attr != "non_field_errors"
                and error.attr is not None
                and 'this' in error.detail.lower())
        ]

        if required_field_errors:
            required_fields = ', '.join([error.attr for error in required_field_errors])
            error_message = f"{required_fields}: {required_field_errors[0].detail}"
        else:
            error_message = error_response.errors[0].detail

        return {
            "success": False,
            "error": {
                "message": error_message
            }
        }
