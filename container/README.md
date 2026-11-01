# Maintained application image

The image uses Python 3.13 on a pinned Debian 13 base and retains Pandoc/XeLaTeX,
profiling packages, UID/GID 373, existing filesystem paths and the mounted
Gunicorn configuration. Use the same image for web and Huey workers.

The builder creates wheels using `requirements.lock` constraints, generates a
SHA-256 install manifest and installs into a venv offline with `--require-hashes`.
The runtime stage contains the venv and document-conversion packages; compilers,
Git, source checkout and downloaded wheels stay in the builder. The Docker context
is allowlisted and does not need `.git`, live settings or credentials.

Three explicit build arguments are required:

- `OBAPI_REQUIREMENT`: an exact reviewed API package version or immutable public
  source requirement, for example `django-overcomingbias-api==X.Y.Z`.
- `OBPAGES_REQUIREMENT`: the corresponding reviewed pages requirement.
- `COLLECTION_VERSION`: the collection version to embed when building without
  Git metadata. The override applies only to collection, not its dependencies.

Both PR CI and release builds read the reviewed API and pages versions from
`container/package-versions.env`. Update that file when upgrading either package.
Release CI builds collection at the version derived from its Git tag. Dependency
versions must be published before building or tagging the collection release.
The feedback fix is included in pages 0.8.1 and subsequent releases, using this
same build path for the web application and Huey worker.

Run the offline image check after building:

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,size=64m \
  --mount type=bind,src="$PWD/container/smoke.py",dst=/smoke.py,readonly \
  --entrypoint /opt/obcollection/venv/bin/python IMAGE /smoke.py
```

The check uses synthetic settings, SQLite/memory queues and no live mounts. It
checks Django/WSGI and worker task imports as UID 373, without executing queued
work or contacting external services. Full migration/search checks remain part
of supervised upgrade rehearsal. The installed wheel manifest is preserved at
`/opt/obcollection/requirements.lock`. Keep the tested immutable image ID/digest
for deployment; a fresh build can incorporate later Debian security packages.
