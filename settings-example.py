from pathlib import Path

from redis import ConnectionPool

from obcollection.settings.base import *  # noqa

# Paths
SECRETS_DIR = Path("/path/to/secrets")


# Secrets
def load_secret(secret_name):
    """Load a secret from file.

    Returns an empty string if the file is not found.
    """
    try:
        with open(SECRETS_DIR / secret_name, mode="r", encoding="utf-8") as f:
            secret = f.readline()
    except FileNotFoundError:
        secret = ""
    return secret


SECRET_KEY = load_secret("django-secret-key")
YOUTUBE_API_KEY = load_secret("youtube-api-key")
SPOTIFY_CLIENT_ID = load_secret("spotify-client-id")
SPOTIFY_CLIENT_SECRET = load_secret("spotify-client-secret")
SITE_HOST_NAME = load_secret("site-host-name")
# RECAPTCHA_KEY = load_secret("recaptcha-key")
# GOOGLE_PROJECT_ID = load_secret("google-project-id")

# Debug mode
DEBUG = False

ALLOWED_HOSTS = [SITE_HOST_NAME]

# *Important* security settings
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Static file serve location
# https://docs.djangoproject.com/en/4.0/ref/settings/#static-root
STATIC_ROOT = "/var/www/example.com/static/"
STATIC_URL = "static/"

# Media file server location
# https://docs.djangoproject.com/en/4.0/ref/settings/#media-root
MEDIA_ROOT = "/var/opt/obcollection/media/"
MEDIA_URL = "/media/"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": load_secret("postgres-db"),
        "USER": load_secret("postgres-user"),
        "PASSWORD": load_secret("postgres-password"),
        "HOST": "127.0.0.1",
        "PORT": 5432,
    }
}

# Huey settings
# https://huey.readthedocs.io/en/latest/django.html#setting-things-up

# Create redis connection pool
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


# Lifetime of database connection (set to 0 if using a connection pooler)
CONN_MAX_AGE = 60

# Search settings
MEILISEARCH_INDEX = "content"
MEILISEARCH_CLIENT = {"url": "http://127.0.0.1:7700"}

# Email
# https://docs.djangoproject.com/en/4.0/topics/email/
EMAIL_BACKEND = "hueymail.backends.EmailBackend"
HUEY_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

SERVER_EMAIL = f"noreply@{SITE_HOST_NAME}"
DEFAULT_FROM_EMAIL = SERVER_EMAIL
ADMINS = [
    (f"{SITE_HOST_NAME} admin", load_secret("admin-email-address")),
]
MANAGERS = ADMINS

EMAIL_HOST = load_secret("email-host")
EMAIL_HOST_USER = load_secret("email-host-user")
EMAIL_HOST_PASSWORD = load_secret("email-host-password")
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            "format": "%(asctime)f %(name)s %(levelname)s %(module)s %(processName)s"
            " %(threadName)s %(message)s",
        },
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        # log everything to stderr
        "": {
            "level": "INFO",
            "handlers": ["stderr"],
        },
        # prevent Huey's default logger from setting itself up
        "huey": {
            "level": "INFO",
            "handlers": ["stderr"],
            "propagate": False,
        },
    },
}

# Caching
# Database 0 is used by Huey
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    },
    "select2": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
    },
}

# Cache to use with select2
SELECT2_CACHE_BACKEND = "select2"

# reCAPTCHA
USE_RECAPTCHA = True

# django-overcomingbias-api
OBAPI_DOWNLOAD_BATCH_SIZE = 500

# Silk
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = "/var/opt/obcollection/silk/"
