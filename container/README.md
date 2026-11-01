# Application images and source releases

Collection source versions and assembled application images have separate identities.
Updating API/pages packages does **not** require a collection tag or GitHub release.
Every application image is built from a reviewed commit and dependency manifest,
checked offline, published after approval, and deployed by immutable digest after
separate approval. Use the same image for web and Huey workers.

## Inputs and compatibility

- `application-policy.json`: collection source version and permitted API/pages
  intervals. Initially API `>=0.7.1,<0.8.0`, pages `>=0.8.1,<0.9.0`. Only stable
  three-component versions and universal `py3-none-any` wheels are selected.
- `application.json`: exact published API/pages versions, canonical wheel URLs
  and SHA-256 hashes. This tracked manifest is authoritative for both CI and
  publishing; package selection never floats during an image build.
- `requirements.lock`: existing exact third-party constraints.
- `pyproject.toml`: pages compatibility bounds for package consumers. Update
  these alongside policy bounds (CI checks agreement).

The package version embedded for collection describes its source version.
Dependency-only application builds retain it. When collection runtime source
changes, update the source version in policy and manifest through its PR.
Source tags/GitHub releases remain optional for dependency-only builds; an actual
collection source release uses the existing tag workflow and must agree with
that reviewed source version. Never move an existing tag or overwrite a full
application build tag.

Compatibility ranges express an intended contract; image CI checks integration.
A backwards-compatible Python API can still require a database migration. Inspect
package changes and migrations for every candidate and include them in the
release/deployment handover. Changing a range or third-party constraint requires
its own reviewed PR. Failed candidates stay unpublished until resolved.

## One-time owner setup, before enabling publication

In the collection repository:

1. Settings → Actions → General → Workflow permissions: enable **Allow GitHub
   Actions to create and approve pull requests**. Workflows request their own
   minimal permissions; the bot creates PRs and never approves or merges them.
2. Settings → Environments → create **application-image**. Set **Required
   reviewers** to the release owner. If you are the sole reviewer, leave
   **Prevent self-review** unchecked so you can approve your own manually started
   runs. Restrict deployment branches to **main**. Keep administrator bypass
   disabled where available. These are owner setup steps, not settings changed
   by this PR.
3. In that environment, add the non-secret variable
   **APPLICATION_IMAGE_PUBLISH_ENABLED=true**, after configuring its reviewers.
   Publication refuses to run if this variable is absent. Do not set it as a
   repository variable: it documents that this environment was configured.
4. Review and merge the implementation PR after its checks pass. No source tag,
   image publication, or production deployment is needed to activate the new
   workflows. No additional token, secret, webhook, or server credential is needed.

GitHub environment configuration:
https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments

## Normal API/pages update

1. Review and release API/pages using their existing package workflows. A GitHub
   release page is optional: the existing package workflows publish on approved
   version-tag pushes. Package publication must finish before image selection.
2. **prepare application update** checks PyPI hourly (GitHub schedules can be
   delayed) and opens a PR containing the exact manifest changes. For immediate
   selection use Actions → prepare application update → Run workflow on **main**.
   No package or image is published by this workflow. Public repositories may
   have schedules disabled after inactivity; the manual workflow remains usable.
3. Review package release notes, migrations and the PR's checks; merge only after
   successful application/container checks. The bot explicitly dispatches
   `container.yml` and `release-metadata.yml` on its branch using GITHUB_TOKEN.
   GitHub may also show an approval banner for bot-created PR event runs; approve
   those if necessary. This requires no long-lived personal access token.
4. Copy the full 40-character merged **main** commit SHA. Actions → **application
   image** → Run workflow on **main**, supplying that SHA as `revision`. The workflow
   requires that exact commit to be on main; it never silently follows a later
   main revision. It first builds and tests without publishing. No collection
   release or version bump is required for a dependency-only change.
5. Inspect the candidate summary, source SHA, selected package versions, checks
   and `application-candidate` artifact. Approve the **application-image**
   environment job to publish. It uploads the *same tested image*, rather than
   rebuilding after approval. Candidate artifacts expire after seven days; if
   approval is delayed past expiry, rerun and review the new candidate.
6. The publication summary supplies a digest such as
   `ghcr.io/chris-mcdo/django-overcomingbias-collection@sha256:...`. Tags look like
   `app-<source-sha-prefix>-<run-id>-<attempt>`; each rerun has a distinct identity.
   Download `application-publication` for provenance, exact installation lock and
   digest. Archive this evidence with the deployment record (Actions artifacts
   are retained for 90 days). The reviewed manifest and registry image persist
   independently of Actions artifacts.
7. Present digest, checks, impact, migrations and rollback to the owner. After
   explicit deployment approval, update both web and worker to that same digest,
   verify Swarm convergence, package versions, worker startup and public HTTPS
   feedback/search, and record the deployment. No production credentials are
   available to these workflows; they cannot deploy automatically.

A preparation failure changes neither main nor production. Resolution errors,
missing compatible wheels, unsupported package versions, and hash mismatches
must be fixed through review. Older bot PRs can remain open if newer candidates
appear; close superseded ones during review. A closed candidate PR is not
reopened automatically for the same manifest; prepare a reviewed manual PR if
reconsidering it. Both packages are resolved together, and pip must accept the
combined package metadata and existing third-party constraints.

## Local checks and provenance

```sh
python3 -m unittest discover -s container/tests -v
python3 container/application.py validate
# Network access; writes only container/application.json:
python3 container/application.py resolve
bash container/build-application.sh collection:review
```

The builder verifies public wheel hashes before dependency resolution, generates
an exact hash install lock and installs into the image offline with
`--require-hashes`. Python/Debian base image, third-party constraints, Pandoc/
XeLaTeX, UID/GID 373 and mounted settings paths are retained. Image CI uses no
network or production mounts for startup tests and checks Django/WSGI, worker
imports, manifest/package/hash agreement and invalid feedback rendering.

The image embeds `/opt/obcollection/application.json` and `requirements.lock`;
OCI labels identify the source revision and unique build identifier. Published
provenance ties those to the final digest. Rebuilding source can incorporate
new Debian packages and build-tool outputs, so source reconstruction is not a
claim of byte-identical image reproduction. Retain and deploy the tested digest.

Rollback is separately approved: restore the previous verified digest on both
services only after checking migrations and writes accepted since deployment.
An image rollback does not reverse database changes. Never patch running
containers or install floating dependencies at startup.
