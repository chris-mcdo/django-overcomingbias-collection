import os
from pathlib import Path

from dotenv import load_dotenv
from redis import ConnectionPool

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


# Huey settings
# https://huey.readthedocs.io/en/latest/django.html#setting-things-up

# Create redis connection pool
# use URL set by environment variable in production
# e.g. os.getenv('REDIS_URL', 'redis://localhost:6379/?db=1')
connection_pool = ConnectionPool(host="127.0.0.1", port=6379, db=0, max_connections=100)

# See docs for full list of settings
HUEY = {
    "huey_class": "huey.PriorityRedisHuey",
    "name": "obcollection",
    "immediate": False,
    "connection": {
        "connection_pool": connection_pool,
        # see redis-py for more options
        # https://redis-py.readthedocs.io/en/latest/connections.html
        # huey-specific connection parameters.
        "read_timeout": 0,
    },
    "consumer": {
        "workers": 4,  # Probably increase
        "worker_type": "thread",
    },
}


# Haystack settings
# https://django-haystack.readthedocs.io/en/master/tutorial.html

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine",
        "URL": "http://127.0.0.1:9200/",
        "INDEX_NAME": "haystack",
    },
}
