# ai-native-sdlc

A Claude Code plugin that turns Anthropic's [AI-Native SDLC Playbook](https://claude.com/blog/the-ai-native-sdlc-playbook) into slash commands.

The playbook's core rule is that **each stage ends by committing a versioned artifact that the next stage reads**. Humans approve at the gates, and git history is the audit trail. This plugin makes that rule deterministic. Every artifact has a fixed template and frontmatter, and a stdlib Python script decides whether an artifact is valid, whether a stage may start, and what comes next.

```
 /sdlc-intent ─► intent.md ─► /sdlc-spec ─► spec.md ─► /sdlc-plan ─► plan.md ─► /sdlc-build ─► code
      ▲              (accept)                 (accept)                 (accept)                  │
      │                                                                                          ▼
 /sdlc-maintain ◄── incident ◄── production ◄── /sdlc-review ─► review.md ◄── verify.md ◄── /sdlc-verify
 (new bug.md / intent.md)                        (fresh context, never approves)   (verdict: pass)
```

## Lanes

| Lane | Starts with | Chain | Use for |
|---|---|---|---|
| **full** | `/sdlc-intent` | intent → spec → plan → build → verify → review | new features, anything needing design |
| **standard** | `/sdlc-plan <ticket or brief>` | plan (with Source) → build → verify → review | well-understood changes |
| **bugfix** | `/sdlc-maintain` or a hand-written `bug.md` | bug (failing test) → build → verify → review | defects: the failing test is the contract |

## Commands

| Command | Stage | Writes | Pinned model · effort |
|---|---|---|---|
| `/sdlc-setup` | bootstrap | `CLAUDE.md` sdlc block, `REVIEW.md`, `docs/sdlc/README.md` | Sonnet 5.5 · medium |
| `/sdlc-intent [idea\|TICKET]` | 1 Plan | `intent.md` | Opus 5.5 · medium |
| `/sdlc-spec <ID>` | 2 Design | `spec.md` (R1…Rn, flagged concerns) | Opus 5.5 · high |
| `/sdlc-plan <ID\|TICKET\|brief>` | 3 Build (plan) | `plan.md` (files, checklist, risks, proof) | Opus 5.5 · high |
| `/sdlc-build <ID>` | 3 Build (code) | code; ticks `plan.md` checklist | Sonnet 5.5 · medium |
| `/sdlc-verify <ID>` | 4 Test | `verify.md` (pasted output, R# traceability, verdict) | Sonnet 5.5 · medium |
| `/sdlc-review <ID>` | 5 Deploy | `review.md` (findings, ≤5 nits, release checklist) | Opus 5.5 · high |
| `/sdlc-maintain <incident>` | 6 Maintain | `incident.md` + new `bug.md`/`intent.md` | Opus 5.5 · high |
| `/sdlc-accept <ID> [artifact]` | human gate | sets `accepted`, commits that file only | Haiku 5.5 · low |
| `/sdlc-status [ID]` | overview | — | Haiku 5.5 · low |

Each skill pins its model and effort in frontmatter for its own turn. Your session goes back to its own setting afterwards. `routing.json` is the single source of truth, and a unit test fails if any skill drifts from it. Every hand-off ends with a line like:

```
Next: /sdlc-accept SF-24-claims-status spec (Haiku 5.5 · effort low) → then /sdlc-plan SF-24-claims-status (Opus 5.5 · effort high)
```

All stage skills are slash-only (`disable-model-invocation: true`), so they never hijack ordinary "plan this" or "review this" requests. Only `/sdlc-status` can be triggered by natural language.

## Progress pane

The plugin ships a mod (`hooks/register.tsx`) that opens an **SDLC** pane beside the chat. Each work item gets a progress bar across its lane's stages:

```
CLM-7-claim-status  full · 1/6 · spec awaiting your approval
█████████ █████████ ░░░░░░░░░ ░░░░░░░░░ ░░░░░░░░░ ░░░░░░░░░
intent    spec      plan      build     verify    review
Next: /sdlc-accept CLM-7-claim-status spec
```

Done stages are green. The current stage is yellow while it waits for `/sdlc-accept`, red when verify failed or an artifact was rejected, and cyan while its `/sdlc-*` command runs (the status line names it too). The pane reads `sdlc_artifact.py status`, so it reflects the files, and refreshes at session start and after every turn. `/sdlc-pane` reopens it. Mods need a Claude Code build that supports hooks modules; older builds simply skip it.

## The artifact contract

Work items live in `docs/sdlc/<ID>/`, where `<ID>` is `<TRACKER-ID>-<slug>` or `<YYYYMMDD>-<slug>`. Every artifact starts with:

```yaml
---
id: SF-24-claims-status
artifact: spec            # intent | spec | plan | bug | verify | review | incident
lane: full                # full | standard | bugfix
status: draft             # draft | accepted | rejected — only /sdlc-accept sets accepted
upstream: docs/sdlc/SF-24-claims-status/intent.md
created: 2026-10-30
accepted_by:
accepted_at:
---
```

`scripts/sdlc_artifact.py` enforces the following:
- **Required sections** for each artifact type.
- **Numbered requirements** (`R1…`) in `spec.md`. Every one must appear in `plan.md` Proof and in `verify.md` Traceability.
- **Pasted evidence**: `bug.md` must include the failing output, and `verify.md` the command output.
- **The nit cap** from `REVIEW.md`.
- **Gates**: a stage starts only when its upstream artifact is valid and accepted. Review needs `verdict: pass` in `verify.md`.
- **Approval**: `accept` records `accepted_by` and `accepted_at` and commits only that file.

```bash
python3 scripts/sdlc_artifact.py --help        # new | scaffold | check | gate | accept | reject | next | status | base | route
```

## Install

From a local checkout:

```
/plugin marketplace add /path/to/ai-native-sdlc
/plugin install ai-native-sdlc@ai-native-sdlc
```

Once this is pushed to GitHub, `/plugin marketplace add <owner>/ai-native-sdlc` works the same way.

Requirements: Claude Code and `python3` (stdlib only). It works with any language or stack. The skills read `CLAUDE.md` and `AGENTS.md`, use a code-intelligence tool (such as Graft) when available, and read tracker tickets through any connected MCP. They never write back to the tracker.

## Quickstart

```
/sdlc-setup
/sdlc-intent Customers keep calling support to ask where their claim is
/sdlc-accept 20261030-claim-status intent
/sdlc-spec 20261030-claim-status
...
/sdlc-status
```

## Upgrade path: the enforcement layer (not in v1)

Skills are advisory. The playbook pairs must-hold policies with deterministic hooks. Later versions could add:
- `PreToolUse` hooks that block test-file edits during bugfix builds, block edits to protected paths, and gate production deploys on a release authorization.
- A verifier subagent in `.claude/agents/`.
- An `agent-evals.yml` CI workflow that re-runs evals whenever `CLAUDE.md`, skills or hooks change.
- `bands.yaml` drift detection that triggers `/sdlc-maintain` headlessly.
- Managed settings for regulated environments.

## Development

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
claude plugin validate . && claude plugin test .   # the progress pane mod
```

`evals/` holds the skill-creator evals for the core skills, with a small fixture app in `evals/fixtures/sample-app/`.

## License

MIT
