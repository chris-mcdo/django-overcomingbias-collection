"""Generate fresh private Swarm-secret inputs; never prints their contents."""
import argparse
import hashlib
import os
from pathlib import Path
import secrets


COMMANDS = "+ping +select +hello +client|setinfo +client|setname"
HUEY_COMMANDS = (
    "+zadd +zpopmin +bzpopmin +zcard +zrange +zrangebyscore +zremrangebyscore "
    "+hset +hsetnx +hget +hgetall +hexists +hdel +hlen +del "
    "+eval +evalsha +script|load +multi +exec +discard"
)
CACHE_COMMANDS = (
    "+get +mget +set +mset +del +exists +expire +ttl +incr +incrby "
    "+multi +exec +discard"
)


def prepare(directory):
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    values = {name: secrets.token_urlsafe(48) for name in [
        "redis-huey-password", "redis-cache-password", "redis-select2-password",
        "huey-signing-key", "redis-admin-password",
    ]}
    for name, value in values.items():
        with open(directory / name, "x", opener=lambda p, f: os.open(p, f, 0o600)) as out:
            out.write(value + "\n")
    lines = ["user default reset off"]
    for username, secret_name, keys, commands in [
        ("huey", "redis-huey-password", "~huey.*.obcollection", HUEY_COMMANDS),
        ("cache", "redis-cache-password", "~obcollection-cache:*", CACHE_COMMANDS),
        ("select2", "redis-select2-password", "~obcollection-select2:*", CACHE_COMMANDS),
        ("security-admin", "redis-admin-password", "~* &*", "+@all"),
    ]:
        digest = hashlib.sha256(values[secret_name].encode()).hexdigest()
        lines.append(f"user {username} reset on #{digest} {keys} {COMMANDS} {commands}")
    with open(directory / "redis-users.acl",
        "x", opener=lambda p, f: os.open(p, f, 0o600)
    ) as out:
        out.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="New private directory outside the repository")
    prepare(parser.parse_args().directory)
