# Mock Stripe settings for testing - set these before any other imports
import os

os.environ["STRIPE_API_KEY"] = "sk_test_dummy_key_for_ci"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy_key_for_ci"
os.environ["STRIPE_PUBLISHABLE_KEY"] = "pk_test_dummy_key_for_ci"
os.environ["STRIPE_BILLING_URL"] = "https://billing.stripe.com/test"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_webhook_secret_key"

import json

# Import settings in a way that ensures they are loaded immediately
from django.conf import settings as django_settings

from .settings import *  # NOQA
from .settings import BASE_DIR  # Import BASE_DIR explicitly

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("TEST_DB_NAME", "postgres"),  # Use the default postgres database
        "USER": os.environ.get("TEST_DB_USER", "postgres"),
        "PASSWORD": os.environ.get("TEST_DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("TEST_DB_HOST", "localhost"),
        "PORT": os.environ.get("TEST_DB_PORT", "5432"),
        "ATOMIC_REQUESTS": True,
        # Test database settings
        "TEST": {
            "NAME": os.environ.get("TEST_DB_NAME", "sbomify_test"),
            "SERIALIZE": False,  # Speeds up tests by not serializing db
        },
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

SECRET_KEY = "django-insecure-test-key-do-not-use-in-production"  # nosec B105 - This is a test-only key

# Mock AWS settings for testing
AWS_REGION = "test-region"
AWS_ENDPOINT_URL_S3 = "http://test-s3.localhost"
AWS_MEDIA_ACCESS_KEY_ID = "test-key"  # nosec B105
AWS_MEDIA_SECRET_ACCESS_KEY = "test-secret"  # nosec B105
AWS_MEDIA_STORAGE_BUCKET_NAME = "test-media-bucket"
AWS_MEDIA_STORAGE_BUCKET_URL = "http://test-s3.localhost/test-media-bucket"
AWS_SBOMS_ACCESS_KEY_ID = "test-key"  # nosec B105
AWS_SBOMS_SECRET_ACCESS_KEY = "test-secret"  # nosec B105
AWS_SBOMS_STORAGE_BUCKET_NAME = "test-sboms-bucket"
AWS_SBOMS_STORAGE_BUCKET_URL = "http://test-s3.localhost/test-sboms-bucket"

APP_BASE_URL = "http://localhost:8001"

# Static files configuration
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Django Vite test settings
DJANGO_VITE = {
    "default": {
        "dev_mode": False,  # Always False for tests
        "dev_server_host": "127.0.0.1",
        "dev_server_port": 5170,
        "manifest_path": str(BASE_DIR / "staticfiles" / "manifest.json"),
    }
}

# Ensure staticfiles directory exists
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# Create manifest in the static directory
manifest = {
    "core/js/main.ts": {
        "file": "assets/main.js",
        "src": "core/js/main.ts",
        "isEntry": True,
        "css": ["assets/main.css"]
    },
    "teams/js/main.ts": {
        "file": "assets/teams.js",
        "src": "teams/js/main.ts",
        "isEntry": True,
        "css": ["assets/teams.css"]
    },
    "core/js/django-messages.ts": {
        "file": "assets/django-messages.js",
        "src": "core/js/django-messages.ts",
        "isEntry": True
    },
    "core/js/alerts-global.ts": {
        "file": "assets/alerts-global.js",
        "src": "core/js/alerts-global.ts",
        "isEntry": True
    }
}

# Create manifest file in the static directory
with open(BASE_DIR / "static" / "manifest.json", "w") as f:
    json.dump(manifest, f)

# Ensure WhiteNoise is configured
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
] + MIDDLEWARE[2:]  # Keep the rest of the middleware unchanged
