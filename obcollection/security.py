"""Explicit production Redis hardening; call after site-specific settings."""
from copy import deepcopy
from pathlib import Path

from huey.serializer import SignedSerializer
from redis import ConnectionPool


def _secret(directory, name):
    value = (Path(directory) / name).read_text(encoding="utf-8").strip()
    if len(value) < 32:
        raise ValueError(f"Missing or too-short security secret: {name}")
    return value


def configure_redis(namespace, directory="/run/secrets", redis_host="message-broker"):
    """Require independent ACL passwords and authenticated task serialization.

    Existing unsigned tasks/results must be drained or preserved before activation.
    Both producer and consumer must switch together while writes are stopped.
    """
    huey_password = _secret(directory, "redis-huey-password")
    cache_password = _secret(directory, "redis-cache-password")
    select2_password = _secret(directory, "redis-select2-password")
    signing_key = _secret(directory, "huey-signing-key")
    if len({huey_password, cache_password, select2_password, signing_key}) != 4:
        raise ValueError("Redis passwords and task signing key must be distinct")
    huey = {key: deepcopy(value) for key, value in namespace["HUEY"].items()
            if key not in {"connection", "serializer"}}
    if huey.get("name") != "obcollection":
        raise ValueError("Redis ACL requires the obcollection Huey queue name")
    huey["serializer"] = SignedSerializer(secret=signing_key)
    huey["connection"] = {
        "connection_pool": ConnectionPool(
            host=redis_host, port=6379, db=0, max_connections=100,
            username="huey", password=huey_password,
        ),
        "read_timeout": 1,
    }
    caches = {}
    for alias, username, password, db, prefix in [
        ("default", "cache", cache_password, 1, "obcollection-cache"),
        ("select2", "select2", select2_password, 2, "obcollection-select2"),
    ]:
        caches[alias] = {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": f"redis://{redis_host}:6379/{db}",
            "KEY_PREFIX": prefix,
            "OPTIONS": {"username": username, "password": password},
        }
    namespace["HUEY"] = huey
    namespace["CACHES"] = caches
    namespace["SELECT2_CACHE_BACKEND"] = "select2"
