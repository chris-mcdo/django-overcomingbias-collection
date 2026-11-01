# Angara security deployment

Prepared for the single-node angara Swarm; no production action happens merely
by importing this module or checking out this repository. F1 is delivered by
pages 0.8.2; F2/F3 by this configuration and the collection security module.
No database schema migration is needed. Production activation requires separate
approval after the final image digest, config hashes and checks are reviewed.

## Release order

1. Review/merge the pages authorization PR and publish pages **0.8.2** through its
   existing tag workflow. Title: **0.8.2 — Enforce sequence-member ownership**.
   Notes: Anonymous and non-owner users can no longer delete/reorder sequence
   members. Owners retain both actions on public/private sequences. No migrations.
2. After PyPI publication, change `container/package-versions.env` to
   `OBPAGES_VERSION=0.8.2` in this collection PR and rerun collection CI. The current
   preparation pin remains 0.8.1 so the infrastructure work can be validated
   against an available release; **do not release it as the complete F1 fix**.
3. Review/merge the final collection revision and publish **0.8.4** through its
   standard tag workflow. Title: **0.8.4 — Sequence authorization and Redis security**.
   Notes: Includes pages 0.8.2 ownership enforcement; supplies opt-in authenticated
   Redis clients, signed Huey messages and tested single-node Swarm firewall
   configuration. Site-specific config and queue transition are required.
4. Record the published GHCR digest, confirm installed versions, and run
   `container/smoke.py`, `deploy/security/check.sh IMAGE`, and the firewall test.
   Present digest, config hashes, evidence, impacts and rollback for approval.
   Deploy the same digest to web and worker only after approval.

## F2: Redis and task signing

The current production Redis starts with `redis-server` and its existing data
volume. Preserve image, data volume, durability settings, networks, resources,
restart/update policy and every unrelated service/config/secret reference.

Generate fresh production inputs into a **new private root-owned directory**,
using the reviewed script. This step does not apply them:

```sh
sudo -n python3 deploy/security/prepare_redis_secrets.py /root/obcollection-security-20261101
```

Never commit, print, pass passwords as CLI arguments, or upload these files.
Import versioned Docker secrets from the generated files:

- `redis-huey-password` (web + worker, UID/GID 373, mode 0400)
- `redis-cache-password` (web + worker, UID/GID 373, mode 0400)
- `redis-select2-password` (web + worker, UID/GID 373, mode 0400)
- `huey-signing-key` (web + worker, UID/GID 373, mode 0400)
- `redis-users.acl` (Redis only, UID 999/GID 1000, mode 0400, as verified in the pinned
  image; recheck on image changes)

Use versioned secret names with stable target paths under `/run/secrets/`.
The admin password stays only in root-owned recovery storage; never mount it
in web/worker. The generated ACL disables the default user and creates separate
queue, default-cache and Select2 users with command/key restrictions. The admin
credential is for supervised recovery only. The application users cannot use
`CONFIG`, `ACL`, or `FLUSHALL`; cache users cannot access queue keys. Cache
`clear()`/FLUSHDB is intentionally not permitted; use scoped invalidation.

The tracked `redis.conf` preserves the observed `/data`, `dump.rdb`,
`save 3600 1 300 100 60 10000`, and `appendonly no` settings and adds:

```conf
aclfile /run/secrets/redis-users.acl
```

Mount this config at `/etc/redis/redis.conf` and start the existing pinned image
with `redis-server /etc/redis/redis.conf`. Do not alter or replace its data mount.
Do not use runtime-only ACL edits: they disappear on replacement.

Create a versioned copy of the existing Django config, preserving all previous
settings, and append:

```python
from obcollection.security import configure_redis
configure_redis(globals(), '/run/secrets', redis_host='message-broker')
```

Mount this versioned config to the existing settings target in both web and
worker. It replaces every application Redis connection and uses a separate
signing secret. Existing cache keys are intentionally cold because the new ACL
uses separate key prefixes; do not grant wildcard access to old caches.

### Queue transition and coordinated activation

Do not mix unsigned and signed producers/consumers. During an approved short
maintenance window, prevent public writes and pause other producers (including
imports/admin jobs); let existing tasks finish, then stop the worker. Check that
both `huey.redis.obcollection` and `huey.schedule.obcollection` are empty. If
scheduled work remains, stop and explicitly resolve it; do not delete or blindly
sign it. Save a restricted Redis persistence snapshot and original complete
service specs/config references before changes. Keep all writers stopped until
Redis, web and worker have matching settings and successful authentication.

At preparation time queue/schedule counts were 0/0, but there were **1,001 legacy
result hash entries**. Recheck while quiesced. Preserve these legacy results by
renaming `huey.results.obcollection` to a versioned recovery key such as
`legacy-huey-results-20261101` before starting signed clients. Never overwrite an
existing archive; never deserialize these legacy values in a migration. They
remain admin-only because the application ACL cannot access that key. Old task
handles will no longer retrieve these archived results; no public result API
was found. Keep the recovery key and protected snapshot until a separately
reviewed retention/cleanup decision, and record both in the deployment handover.
No queued or scheduled task may be silently discarded.

After approval, update Redis's config/ACL secret, then both application services'
image/config/secrets while they remain stopped; start authenticated Redis, then
worker and web. Do not reopen writes until checks below pass. Existing producers
with old credentials/config must remain stopped, including ad hoc jobs.

Verification:

- All expected replicas healthy; web/worker use the identical approved digest.
- Unauthenticated Redis PING fails; scoped clients connect.
- Queue/schedule/results work with signed messages; unsigned/tampered messages
  fail before pickle deserialization (use an isolated rehearsal, not production
  injection). Cache users cannot write queue keys or change ACL/config.
- Default and Select2 cache operations succeed. Missing secret fails startup.
- Anonymous/other-owner delete and move are denied; owner's operations work in a
  disposable fixture/rehearsal. Public reads, search and login continue working.
- Verify async work via an approved benign smoke task and observe completion.

## F3: host Swarm ingress restriction

`angara-swarm.nft` drops public-interface TCP 2377/7946 and UDP 4789/7946 before
VXLAN decapsulation. It affects both IP families and changes no SSH/web rules.
This is deliberately for **one node**, with public interface **eth0** (confirmed
from angara's default route). Confirm node count and all public interfaces again
before applying. A future multi-node/private-peer deployment needs explicit
trusted peer rules; this file must not be applied unchanged to that topology.

Run syntax and behavior validation first:

```sh
sudo -n nft -c -f deploy/security/angara-swarm.nft
sudo -n unshare -n python3 deploy/security/check_firewall.py --isolated
systemd-analyze verify deploy/security/obcollection-swarm-guard.service
```

After approval, install the reviewed rules at
`/etc/obcollection-security/angara-swarm.nft` and the unit at
`/etc/systemd/system/obcollection-swarm-guard.service`, reload systemd, and enable
and start that unit. It adds only its own nftables table; it does not flush
Docker or other rules. Do not also load this table from another firewall manager.
The service preserves rules through reboot and loads before Docker. Its stop
operation removes only its own table. Confirm service enabled/active and the
expected nft counters. Check SSH and public HTTP/HTTPS immediately.

Repeat off-host checks for TCP 2377/7946 and verify perimeter UDP 4789/7946 rules
through DigitalOcean. Cloud firewall access was unavailable during preparation;
a self-connection is not an external reachability test. Defense at the host does
not depend on discovering the existing cloud rules. Restrict these ports at the
cloud perimeter as well when account access is available.

## Rollback

F3: stop/disable only `obcollection-swarm-guard.service`; verify its table was
removed and all unrelated firewall rules remain. This restores the previous
Swarm exposure, so use only after explicit rollback approval.

F2/F1: prevent writes and stop both application services before restoring the
saved service specs/config references and previous immutable application digest.
Preserve the current Redis snapshot first. Signed tasks/results created after
activation cannot be consumed by an unsigned worker: finish them with the signed
worker or explicitly reconcile them before rollback. Never simply point an old
worker at the new queue. Restore the legacy result key only if the destination
is empty and that recovery decision is approved. Redis authentication and Django
client credentials must match at every start. Restoring the old open ACL or old
image reintroduces the findings; prefer rolling forward. No PostgreSQL schema
rollback is required. Backups/legacy results/secrets retained for recovery must
be listed in the handover and cleaned only after a reviewed retention decision.

## References

- https://docs.docker.com/engine/swarm/swarm-tutorial/ (trusted-only VXLAN ingress)
- https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/
- https://huey.readthedocs.io/en/latest/api.html (SignedSerializer)

Compatibility is tested against the collection's locked Huey 2.6.0 and Redis
7.4.x, not assumed from the latest documentation. Signing protects against clients
that lack the signing key; a compromised web/worker possessing that key remains
trusted. This change does not claim to fix the audit's medium-severity items.
