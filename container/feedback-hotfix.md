# Feedback hotfix (1 November 2026)

Invalid anonymous POSTs to `/feedback` crashed because the custom CreateView.post
left self.object undefined. Pages commit 8eaec96578692996f24b62fa231ebc7d1eb3d35d
restores Django's default POST lifecycle and preserves authenticated ownership.
Source and nine regression cases: https://github.com/chris-mcdo/django-overcomingbias-pages/pull/2

Build from the repository root:

```sh
docker build -f container/feedback-hotfix.Dockerfile -t obcollection:feedback-fix-8eaec965 .
```

The recipe pins the existing 0.8.2 production image by registry digest and the
changed file by full upstream commit and SHA-256. It changes only obpages/views.py;
package version metadata remains pages 0.8.0 / collection 0.8.2. The additional
image label identifies the hotfix. No dependencies, settings or migrations change.
The normal release path should publish a pages release containing the fix and
update the regular collection build's OBPAGES_REQUIREMENT accordingly.

Validation: all 14 pages tests pass in an isolated Python 3.13 container using
SQLite and memory queues. The three anonymous invalid cases fail with the exact
reported AttributeError before the patch. Valid anonymous/authenticated saves
and reCAPTCHA task scheduling remain covered.

On the single-node production Swarm, preserve the current web and worker image
references, then update both services to the built image using
`docker service update --no-resolve-image --image obcollection:feedback-fix-8eaec965 SERVICE`.
Confirm convergence and GET /feedback plus a CSRF-protected empty anonymous POST:
the POST must return HTTP 200 with the required-field error, creating no feedback
and no spam-check task. Keep the prior image available for rollback using the
same service-update command and its original pinned digest. No database rollback
is needed. Multi-node deployment requires distributing the image to each node
or publishing it to a registry and using its digest before the service update.
