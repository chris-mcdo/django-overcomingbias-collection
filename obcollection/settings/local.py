import os

from dotenv import find_dotenv, load_dotenv

from obcollection.settings.base import *  # noqa

# take environment variables from .env
load_dotenv(find_dotenv())


# Secrets
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "fake-key")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Debug mode
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = []

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

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# Haystack settings
# https://django-haystack.readthedocs.io/en/master/tutorial.html

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine",
        "URL": "http://127.0.0.1:9200/",
        "INDEX_NAME": "haystack",
    },
}
