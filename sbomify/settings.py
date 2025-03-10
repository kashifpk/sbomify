"""
Django settings for sbomify project.

Generated by 'django-admin startproject' using Django 5.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
import sentry_sdk
from django.contrib import messages
from dotenv import find_dotenv, load_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


API_VERSION = "v1"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False") == "True"

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Append 'APP_HOSTNAME' value if defined
if os.environ.get("APP_BASE_URL", False):
    ALLOWED_HOSTS.append(urlparse(os.environ.get("APP_BASE_URL")).netloc)

AUTH_USER_MODEL = "core.User"

# Make Django work behind reverse proxy
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "django_vite",
    "ninja",
    "widget_tweaks",
    "core",
    "social_django",
    "anymail",
    "teams",
    "sboms",
    "access_tokens",
    "billing",
    "notifications",
    "health_check",
    "health_check.db",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

INTERNAL_IPS = [
    "127.0.0.1",
]

ROOT_URLCONF = "sbomify.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "sbomify.wsgi.application"


MESSAGE_TAGS = {
    messages.constants.DEBUG: "alert-info",
    messages.constants.INFO: "alert-info",
    messages.constants.SUCCESS: "alert-success",
    messages.constants.WARNING: "alert-warning",
    messages.constants.ERROR: "alert-danger",
}


# Django Vite
DJANGO_VITE = {
    "default": {
        "dev_mode": DEBUG,
        "dev_server_host": "127.0.0.1",
        "dev_server_port": 5170,
    }
}


# Database


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ENGINE": os.environ["SQL_ENGINE"],
#         "NAME": os.environ["SQL_DATABASE"],
#         "USER": os.environ["SQL_USER"],
#         "PASSWORD": os.environ["SQL_PASSWORD"],
#         "HOST": os.environ["SQL_HOST"],
#         "PORT": os.environ["SQL_PORT"],
#     }
# }

IN_DOCKER = bool(int(os.environ["AM_I_IN_DOCKER_CONTAINER"])) if "AM_I_IN_DOCKER_CONTAINER" in os.environ else False

# DB_URL = os.environ.get("DATABASE_URL", "")
if "DATABASE_URL" in os.environ:
    db_config_dict = dj_database_url.parse(os.environ["DATABASE_URL"])
else:
    db_config_dict = {}
    DATABASE_USER = os.environ.get("DATABASE_USER", "")
    DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "")
    DATABASE_PORT = os.environ.get("DATABASE_PORT", "")

    if IN_DOCKER:
        DATABASE_HOST = os.environ.get("DOCKER_DATABASE_HOST", "")
    else:
        DATABASE_HOST = os.environ.get("DATABASE_HOST", "")

    db_config_dict = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
    }


DATABASES = {"default": db_config_dict}


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

# Logging config
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s:%(name)s:%(levelname)s:%(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "sbomify": {
            "handlers": ["console"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "core": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        # "teams": {
        #     "handlers": ["console"],
        #     "level": os.getenv("LOG_LEVEL", "INFO"),
        #     "propagate": False,
        # },
    },
}


# Auth0 settings
SOCIAL_AUTH_TRAILING_SLASH = False  # Remove trailing slash from routes
SOCIAL_AUTH_AUTH0_DOMAIN = os.environ.get("SOCIAL_AUTH_AUTH0_DOMAIN", "")
SOCIAL_AUTH_AUTH0_KEY = os.environ.get("SOCIAL_AUTH_AUTH0_KEY", "")
SOCIAL_AUTH_AUTH0_SECRET = os.environ.get("SOCIAL_AUTH_AUTH0_SECRET", "")
SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_AUTH0_SCOPE = ["openid", "profile", "email"]

# Ensure we get the correct response type from Auth0
SOCIAL_AUTH_AUTH0_RESPONSE_TYPE = "code"

# JWT validation settings for Auth0
SOCIAL_AUTH_AUTH0_JWT_ENABLED = True
SOCIAL_AUTH_AUTH0_JWT_ALGORITHM = "RS256"
SOCIAL_AUTH_AUTH0_JWT_VERIFY = True
SOCIAL_AUTH_AUTH0_JWT_VERIFY_EXP = True
SOCIAL_AUTH_AUTH0_JWT_LEEWAY = 60  # 1 minute leeway for clock skew

# Custom Auth0 Pipeline
SOCIAL_AUTH_PIPELINE = (
    # "core.pipeline.auth0.debug_pipeline",  # Debug pipeline at the start
    "social_core.pipeline.social_auth.social_details",
    "core.pipeline.auth0.get_auth0_user_id",  # Extract user ID before social_uid
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "core.pipeline.auth0.require_email",  # Email verification
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

if DEBUG is False:  # If in production, then force HTTPS for auth0
    SOCIAL_AUTH_REDIRECT_IS_HTTPS = True


AUTHENTICATION_BACKENDS = {
    "core.auth.SafeAuth0OAuth2",
    "django.contrib.auth.backends.ModelBackend",
}

LOGIN_URL = "/login/auth0"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

APP_BASE_URL = os.environ.get("APP_BASE_URL", "")

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
# EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
# EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
# EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "25"))
# EMAIL_USE_TLS = str_to_bool(os.environ.get("EMAIL_USE_TLS", "False"))

ANYMAIL = {"SENDGRID_API_KEY": os.environ.get("SENDGRID_API_KEY", "")}

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@sbomify.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)


# Teams app related config
TEAMS_SUPPORTED_ROLES = [("owner", "Owner"), ("admin", "Admin"), ("guest", "Guest")]
TEAMS_INVITATION_EXPIRY_DURATION = 60 * 60 * 24 * 7  # 7 days


JWT_ISSUER = os.environ.get("JWT_ISSUER", "sbomify")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "sbomify")

# Localstack and AWS/S3 related settings
AWS_REGION = os.environ.get("AWS_REGION", "")
AWS_ENDPOINT_URL_S3 = os.environ.get("AWS_ENDPOINT_URL_S3", "")

AWS_MEDIA_ACCESS_KEY_ID = os.environ.get("AWS_MEDIA_ACCESS_KEY_ID", "")
AWS_MEDIA_SECRET_ACCESS_KEY = os.environ.get("AWS_MEDIA_SECRET_ACCESS_KEY", "")
AWS_MEDIA_STORAGE_BUCKET_NAME = os.environ.get("AWS_MEDIA_STORAGE_BUCKET_NAME", "")
AWS_MEDIA_STORAGE_BUCKET_URL = os.environ.get("AWS_MEDIA_STORAGE_BUCKET_URL", "")

AWS_SBOMS_ACCESS_KEY_ID = os.environ.get("AWS_SBOMS_ACCESS_KEY_ID", "")
AWS_SBOMS_SECRET_ACCESS_KEY = os.environ.get("AWS_SBOMS_SECRET_ACCESS_KEY", "")
AWS_SBOMS_STORAGE_BUCKET_NAME = os.environ.get("AWS_SBOMS_STORAGE_BUCKET_NAME", "")
AWS_SBOMS_STORAGE_BUCKET_URL = os.environ.get("AWS_SBOMS_STORAGE_BUCKET_URL", "")

if DEBUG:
    # CSRF settings for development
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

STRIPE_API_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_SECRET_KEY = STRIPE_API_KEY
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_BILLING_URL = os.environ.get("STRIPE_BILLING_URL", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Enable specific notification providers
NOTIFICATION_PROVIDERS = [
    "billing.notifications.get_notifications",
    # "core.notifications.get_notifications",  # For future system-wide notifications
]

# Optionally override refresh interval
NOTIFICATION_REFRESH_INTERVAL = 60 * 1000  # 1 minute
