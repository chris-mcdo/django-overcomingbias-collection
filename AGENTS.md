# Project release policy

## Change and release workflow

These rules apply to bug fixes and other changes across this project, including
its application packages, container builds, configuration, infrastructure and
supporting repositories. Historical deployment notes are context, not permission
to repeat an earlier hotfix or bypass this workflow.

### Prepare and validate

- Work on branches and submit pull requests for repository changes. Never push
  directly to `main` or another protected/default branch. Preserve unrelated
  work; use an isolated worktree when appropriate.
- Include the problem, resulting behavior, relevant regression tests, validation
  results and any material limitations in each PR. Use tests appropriate to the
  change rather than adding tests that merely duplicate the implementation.
- Use the established CI pipeline. Application tests, package builds and relevant
  container startup checks must pass before merge. Explain blocked or failed
  checks and resolve them; do not bypass checks or weaken them to obtain a pass.
- Keep deployment inputs reproducible and tracked upstream: source revisions,
  package version pins, dependency locks, build recipes and necessary configuration
  changes. Keep credentials and production secrets out of repositories and builds.

### Approval boundaries

- The user retains final approval for every merge and release. Agents may prepare
  branches, PRs, release titles, notes and commands, but must leave merging and
  publishing to the user unless the user explicitly authorizes the agent to carry
  out the specified action on the reviewed revision.
- Do not create or push release tags, publish packages or images, create a
  published release, or trigger a workflow that publishes them before that
  approval. Consider workflow side effects before pushing changes or triggering CI.
- Treat deployment as a separate approval step. Before requesting approval,
  present the published image digest or other immutable artifact, verification
  results, expected impact, migration requirements and rollback procedure.
- Authorization is specific to the action and revision presented. Silence,
  elapsed time, or approval of an earlier stage does not authorize merging,
  publishing a release, or deploying. If scope or the reviewed revision changes,
  present the updated result before proceeding. A request to diagnose or fix a
  bug alone does not authorize those actions.
- Prepare all work and evidence that does not depend on approval before asking
  for it. Continue independent authorized preparation while an approval is pending,
  without performing the gated action.

### Standard release and deployment path

- Collection source versions and application image builds are separate. A
  backwards-compatible API/pages update does not require a new collection tag,
  GitHub release or collection source-version bump. Collection runtime source
  changes still receive an appropriate reviewed source version.
- Release API/pages through their normal approved package workflows first. The
  collection's preparation workflow may discover published stable versions within
  reviewed compatibility bounds and open a manifest PR automatically. The tracked
  manifest must select exact package versions, public wheel URLs and SHA-256
  hashes; retain third-party constraints. Builds must consume that manifest,
  rather than resolve floating dependencies or install updates at runtime.
- After manifest PR checks pass and merge is approved, prepare an application
  image from the exact reviewed main commit. Run application tests and offline
  web/worker startup checks before publication. Record collection source version,
  exact source revision, package versions/hashes, installation lock and unique
  application build identity. A minimum-version declaration alone is not proof
  of compatibility; assess migrations for each candidate.
- Publication still needs explicit approval of the tested candidate. Use the
  owner-configured application-image environment gate in the new workflow; publish
  the same tested image and record its immutable registry digest. Dependency-only
  builds use unique app-<source>-<run>-<attempt> identities without collection
  releases. No workflow may merge, approve its own PR or deploy automatically.
  The collection container README contains the maintained setup/runbook. Configure
  environment reviewers and the environment-level publication-enable variable
  before using the new path; this document does not enforce GitHub permissions.
- Legacy collection source-tag releases remain available for actual source
  releases with reviewed matching version metadata. Do not move existing tags.
- Deploy the verified published artifact by immutable digest after deployment
  approval. Use the same application image for web and worker services. Complete
  appropriate post-deployment checks and record the deployed versions/digest.
- Do not edit installed production code, patch running containers, create overlay
  hotfix images, or deploy unpublished development builds. Do not introduce
  temporary build paths, manual runtime adjustments or deferred cleanup as a
  substitute for the standard release. Urgent fixes follow the same pipeline
  with a smaller change and expedited review.
- An explicitly approved rollback may restore a previously verified release using
  its documented procedure. Assess migration compatibility and accepted writes;
  do not assume an image rollback can reverse database changes safely.
- Finish with a complete handover: PR links, checks, exact release order and
  versions, release titles and notes, verification and deployment instructions,
  rollback steps, and anything awaiting approval. Clearly distinguish prepared,
  merged, published and deployed work. Do not leave unreported cleanup or migration
  work for the user.

### Maintaining this policy

- When the user requests a lasting workflow change, update the relevant sections
  of this `AGENTS.md` as part of the authorized task so future chats inherit it.
  Update related maintained instructions where needed and remove contradictions;
  preserve historical records as history. If permanence or scope is unclear, ask
  whether the change is a one-time exception or a standing policy update.
- The user's explicit instructions take precedence. Record a one-time exception
  with the task evidence rather than silently changing the standing policy. Never
  infer an exception from urgency or from a request to fix an issue.
- Changes to this local policy do not themselves authorize changes to repository
  protections, permissions, CI workflows or GitHub environments. Propose such
  enforcement changes separately for review and obtain authorization before
  applying them. Do not claim this file technically enforces GitHub controls.
- This workspace policy covers supporting repositories used for the project.
  When work moves to a project copy outside this directory, ensure its applicable
  instructions carry the same policy; do not assume chat context or an SSH
  connection synchronizes instruction files.

