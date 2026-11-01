#!/bin/sh
# Disposable network/Redis only. No production sockets, volumes or credentials.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
image=${1:?Usage: check.sh APPLICATION_TEST_IMAGE}
run_id="obcollection-security-$$"
tmp_dir=$(mktemp -d)
cleanup() {
    docker rm -f "$run_id" >/dev/null 2>&1 || true
    docker network rm "$run_id" >/dev/null 2>&1 || true
    rm -rf "$tmp_dir"
}
trap cleanup EXIT HUP INT TERM
python3 "$root/deploy/security/prepare_redis_secrets.py" "$tmp_dir/secrets"
docker network create --internal "$run_id" >/dev/null
docker run -d --name "$run_id" --network "$run_id" --network-alias redis-test \
    --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$tmp_dir/secrets/redis-users.acl,dst=/run/secrets/redis-users.acl,readonly" \
    --mount "type=bind,src=$root/deploy/security/redis.conf,dst=/etc/redis/redis.conf,readonly" \
    --entrypoint redis-server \
    redis@sha256:858f009f9709ce576febc734aa78b8f6d624b82571f9ddb6bda4377c833b3499 \
    /etc/redis/redis.conf --save '' --appendonly no >/dev/null
# Startup readiness only: unauthenticated PING must report NOAUTH.
attempt=0
until docker exec "$run_id" redis-cli ping 2>&1 | grep -q NOAUTH; do
    attempt=$((attempt + 1))
    test "$attempt" -lt 20 || exit 1
    sleep 1
done
docker run --rm --network "$run_id" --user "$(id -u):$(id -g)" \
    --env PYTHONPATH=/src --env REDIS_TEST_HOST=redis-test \
    --env REDIS_TEST_SECRETS=/test-secrets \
    --mount "type=bind,src=$root,dst=/src,readonly" \
    --mount "type=bind,src=$tmp_dir/secrets,dst=/test-secrets,readonly" \
    --workdir /src --entrypoint /opt/obcollection/venv/bin/python \
    "$image" -m unittest discover -s tests -v
