import os
from pathlib import Path

from django.urls import reverse_lazy
from dotenv import load_dotenv
from datetime import timedelta

from utils.settings_utils import add_prefix_to_allowed_hosts

load_dotenv()  # take environment variables from .env.

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = bool(int(os.getenv("DEBUG", "0")))

ALLOWED_HOSTS = []
ALLOWED_HOSTS.extend(filter(None, os.environ.get("ALLOWED_HOSTS", "").split(",")))


CORS_ALLOWED_ORIGINS = add_prefix_to_allowed_hosts(os.environ.get("ALLOWED_HOSTS", ""))

CSRF_TRUSTED_ORIGINS = add_prefix_to_allowed_hosts(os.environ.get("ALLOWED_HOSTS", ""))
CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "None"

SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework_simplejwt",
    "rest_framework",
    "drf_standardized_errors",
    "django_filters",
    "corsheaders",
    "django_celery_results",
    "drf_spectacular",
    "cloudinary_storage",
    "cloudinary",

    "authentication",
    "shop",
    "email_subscription",
    "cart",
    "wishlist",
    "checkout",
    "news",
    "contact_us"
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "authentication.middleware.BruteForceProtectionMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "cart.middleware.CartTransferMiddleware",
]

ROOT_URLCONF = "online_store.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "online_store.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

if not bool(int(os.getenv("DEBUG", "0"))):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_NAME"),
            "USER": os.getenv("POSTGRES_USER"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "HOST": os.getenv("POSTGRES_HOST"),
            "PORT": os.getenv("POSTGRES_PORT"),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.RawMediaCloudinaryStorage"

AUTH_USER_MODEL = "authentication.Customer"

AUTHENTICATION_BACKENDS = [
    'authentication.backends.CustomAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUD_NAME"),
    "API_KEY": os.getenv("API_KEY"),
    "API_SECRET": os.getenv("API_SECRET"),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Hop Hop Shop API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    'COMPONENT_SPLIT_REQUEST': True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "defaultModelRendering": "model",
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
    },
}


REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
    "DEFAULT_RENDERER_CLASSES": ("utils.renderers.SuccessJsonResponsee",),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

DRF_STANDARDIZED_ERRORS = {
    "EXCEPTION_FORMATTER_CLASS": "utils.standardized_errors.MyExceptionFormatter",
    "EXCEPTION_HANDLER_CLASS": "utils.custom_exceptions.CartExceptionHandler",
    "EXCEPTION_CLASSES": {
        "utils.custom_exceptions.StripeCardError": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.StripeRateLimitError": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.StripeInvalidRequestError": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.StripeAuthenticationError": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.StripeAPIConnectionError": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.StripeGeneralError": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.ProductAlreadyExistException": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.ProductNotExistException": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.CouponNotExistException": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.InvalidCredentialsError": "drf_standardized_errors.exceptions.BaseAPIException",
        "utils.custom_exceptions.AccountIsNotVerifyError": "drf_standardized_errors.exceptions.BaseAPIException",
    },
}

CSRF_COOKIE_HTTPONLY = True

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_COOKIE": "refresh_token",
    "AUTH_COOKIE_SECURE": True,
    "AUTH_COOKIE_HTTPONLY": True,
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_SAMESITE": "None",
}

LOGIN_URL = reverse_lazy("authentication:login")

BRUTE_FORCE_THRESHOLD = 3  # Allow only 3 failed login attempts
BRUTE_FORCE_TIMEOUT = 300  # Lock the user out for 5 minutes (300 seconds)

CART_SESSION_ID = "cart"
WISHLIST_SESSION_ID = "wishlist"

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")

CELERY_BROKER_URL = os.getenv("REDIS_URL")
CELERY_ACCEPT_CONTENT = {"application/json"}
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Kyiv"
CELERY_RESULT_BACKEND = "django-db"


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
