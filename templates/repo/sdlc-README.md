# docs/sdlc

One folder per work item: `<TRACKER-ID>-<slug>` or `<YYYYMMDD>-<slug>`.
Every file has frontmatter (`id, artifact, lane, status, upstream, created, accepted_by, accepted_at`).

| Lane | Chain |
|---|---|
| full | intent.md → spec.md → plan.md → (build) → verify.md → review.md |
| standard | plan.md (with Source) → (build) → verify.md → review.md |
| bugfix | bug.md (failing test) → (build) → verify.md → review.md |

A stage starts only when its upstream artifact is valid and `status: accepted`.
Only a human accepts, via `/sdlc-accept <ID> <artifact>`, which commits that one file.
Git history of this folder is the audit trail: who asked for what, what was built, who approved it.
