#!/usr/bin/env bash
set -euo pipefail
image=${1:?Supply a local image tag}
python3 container/application.py validate
source_version=$(python3 -c 'import json; print(json.load(open("container/application.json"))["collection_version"])')
collection_version=${2:-$source_version}
docker build --tag "$image" --build-arg "COLLECTION_VERSION=$collection_version" \
  --label "org.opencontainers.image.revision=$(git rev-parse HEAD)" \
  --label "org.opencontainers.image.source=https://github.com/${GITHUB_REPOSITORY:-chris-mcdo/django-overcomingbias-collection}" \
  --label "org.opencontainers.image.version=${image##*:}" .
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,nosuid,size=128m \
  --mount type=bind,src="$PWD/container/smoke.py",dst=/smoke.py,readonly \
  --entrypoint /opt/obcollection/venv/bin/python "$image" /smoke.py
sh deploy/security/check.sh "$image"
mkdir -p build
# Retain the actual offline installation lock, including built third-party wheels.
docker run --rm --network none --read-only --entrypoint cat "$image" \
  /opt/obcollection/requirements.lock > build/install.lock
cp container/application.json build/application.json
