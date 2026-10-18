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

PR CI currently selects the exact API/pages review commits so no package needs to
be published before review. `0.8.0rc1` identifies the local collection test build;
it is not a published or approved release. Replace temporary CI source pins after
the compatibility releases. Release CI requires repository variables
`OBAPI_VERSION` and `OBPAGES_VERSION` containing explicit reviewed package versions;
it builds collection at the image's tag-derived version. Do not tag a release
until the dependency PRs are reviewed and their package versions are available.

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
