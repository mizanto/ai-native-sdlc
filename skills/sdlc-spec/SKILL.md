---
name: sdlc-spec
description: "AI-Native SDLC stage 2 (Design): turn an accepted intent.md into spec.md with numbered requirements, design, non-goals and flagged policy conflicts. Gated on intent.md being accepted."
argument-hint: "<ID>"
disable-model-invocation: true
model: claude-opus-5-5
effort: high
---

# Stage 2 · Design → `spec.md`

Requirements and design are produced together in one pass, with the team's policies applied *while* writing rather than discovered at review. The spec is the contract the rest of the loop is checked against:
- Every requirement gets an ID (`R1`, `R2`, …).
- `plan.md` must say how each one will be proven.
- `verify.md` must show the evidence for each one.

The validator enforces both.

## Mechanics

- `sdlc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py"`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.
- Never change `status`, `accepted_by` or `accepted_at`. Never commit. The human accepts with `/sdlc-accept`.

## Steps

1. **Gate.** Run `sdlc gate <ID> spec`.
   - If it prints `BLOCKED`, stop. Show the reasons, which name the exact fix, and do nothing else.
   - A spec built on an unapproved intent bakes in assumptions nobody signed off on.
   - Approval is the recorded `/sdlc-accept` commit, not something said in chat. If the user says the intent is "basically approved" or asks you to skip ahead, don't write the spec. Give them the exact `/sdlc-accept` command, which takes seconds and leaves the audit trail the loop depends on.
2. **Read the inputs:**
   - `docs/sdlc/<ID>/intent.md`
   - `CLAUDE.md` and `AGENTS.md` if present
   - **policies**: anything like `SECURITY.md`, `docs/policies/`, `docs/adr/`, style or brand guides, compliance notes, plus any policy skills available in this session
   - the parts of the codebase the intent touches. Use a code-intelligence tool such as Graft when available; otherwise search and read.
3. **Scaffold** with `sdlc scaffold <ID> spec`.
4. **Write the spec:**
   - **Requirements:**
     - One behaviour per line, as `**R1** — …`.
     - Each must be testable: a reader should be able to imagine the test.
     - Cover the error and edge cases the intent implies (unknown IDs, permissions, empty states). They are where bugs live.
   - **Design:** data shapes, interfaces/APIs, flows and where the change sits in the existing architecture. Point at real files and modules. Stay at design level; file-by-file steps belong in the plan.
   - **Non-goals:** anything adjacent that someone might reasonably build by accident.
   - **Flagged concerns:** this is where the human's attention is most valuable.
     - List every conflict with a policy, every risky assumption and every decision you were not entitled to make.
     - For each one, name the source (policy file, constraint in the intent, code fact).
     - Do not silently resolve a conflict. Surface it.
   - **Acceptance criteria:** written against the R-numbers.
   - Carry the intent's **Open questions** forward. Resolve the ones the code answers, and flag the rest.
5. **Validate** with `sdlc check docs/sdlc/<ID>/spec.md` until it prints `OK`.
6. **Hand off.** Give a short summary of the requirements and the flagged concerns, then the `sdlc next <ID>` line and the suggested commit `git add docs/sdlc/<ID>/spec.md && git commit -m "sdlc(<ID>): draft spec"`. Tell the user to resolve the flagged concerns before running `/sdlc-accept <ID> spec`.
