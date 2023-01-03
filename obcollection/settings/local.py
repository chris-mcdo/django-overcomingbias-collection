import os
from pathlib import Path

from dotenv import load_dotenv

from obcollection.settings.base import *  # noqa

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# take environment variables from .env
load_dotenv(BASE_DIR / ".env")

# Secrets
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "fake-key")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Debug mode
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = ["127.0.0.1"]

# Static files
# https://whitenoise.evans.io/en/stable/django.html
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_MANIFEST_STRICT = False

# Prevent runserver from serving static files
INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa
    }
}

# Internal IP addresses

INTERNAL_IPS = [
    "127.0.0.1",
]


# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "general.log",
        },
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "obscraper": {
            "level": "DEBUG",
            "handlers": ["file"],
        },
        "obpages": {
            "level": "INFO",
            "handlers": ["console"],
        },
    },
}

# Email
# https://docs.djangoproject.com/en/4.0/topics/email/

EMAIL_BACKEND = "hueymail.backends.EmailBackend"
HUEY_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# Huey settings
# https://huey.readthedocs.io/en/latest/django.html#setting-things-up

# Create redis connection pool

# See docs for full list of settings
HUEY = {
    "huey_class": "huey.MemoryHuey",
    "name": "obcollection",
    "immediate": True,
}


# Haystack settings
# https://django-haystack.readthedocs.io/en/master/tutorial.html

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
    },
}

# Whether to use recaptcha
USE_RECAPTCHA = False
# RECAPTCHA_KEY = "your-key-here"

# django-overcomingbias-api settings

OBAPI_DOWNLOAD_BATCH_SIZE = 200
