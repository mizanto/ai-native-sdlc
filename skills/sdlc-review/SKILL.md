---
name: sdlc-review
description: "AI-Native SDLC stage 5 (Deploy: review): review the change in a fresh context against REVIEW.md, spec.md and plan.md, and write review.md with important findings, capped nits and a release checklist. Never approves. Gated on verify.md verdict pass."
argument-hint: "<ID>"
disable-model-invocation: true
context: fork
model: claude-opus-5-5
effort: high
---

# Stage 5 · Deploy (review) → `review.md`

You are reviewing someone else's change. You run in a fresh context on purpose: the agent that wrote the code must not be the one that judges it. Judge only what is on disk: the diff, the artifacts and the policy. **You do not approve.** A human code owner does, so your job is to point their attention at what matters. Burying them in nits does the opposite.

**Do not edit any code or tests.** The only file you write is `review.md`.

## Mechanics

- `sdlc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py"`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.
- Never change `status`, `accepted_by` or `accepted_at`. Never commit.

## Steps

1. **Gate.** The item ID is `$ARGUMENTS`. Run `sdlc gate <ID> review`. On `BLOCKED` (for example, the verify verdict isn't pass), stop and report the reasons.
   - Don't review anyway because the user says a failure is flaky or they need to ship. Deciding whether a failure is real is `/sdlc-verify`'s job. A review of code that hasn't passed verification gives the code owner false confidence. Point at `/sdlc-build <ID>` then `/sdlc-verify <ID>`, or a re-run of `/sdlc-verify` if they believe it's flaky.
2. **Load the policy and contract:**
   - `REVIEW.md` at the repo root. If it is missing, use the passes in `${CLAUDE_PLUGIN_ROOT}/templates/repo/REVIEW.md`.
   - `CLAUDE.md`, and the item's `spec.md`, `plan.md` (including any `## Deviations`) or `bug.md`, and `verify.md`.
3. **Find the change under review.**
   - Run `sdlc base <ID>`. It prints the commit that accepted the plan (or bug), which is where the work started. Review `git diff <base>` plus new untracked files from `git status`.
   - If it prints `NO BASE`, use `git merge-base HEAD <default-branch>` on a feature branch. On the default branch, ask which commit the work started from, or pick the commit before the first one touching the plan's **Files that change**, and say which you chose.
   - Don't use "the last commit that touched plan.md": `/sdlc-build` ticks the checklist in the implementation commit, so that would hide the code.
   - Ignore `docs/sdlc/` itself.
   - Read surrounding code where a hunk's correctness depends on it.
4. **Run each pass from `REVIEW.md`.** At minimum:
   - **Bugs:** logic, edge cases, error handling, data loss.
   - **Security:** authn/authz, input validation, injection, secrets, PII.
   - **Compliance:** every `R#` implemented as specified, no unplanned scope, deviations justified.
   - **Tests:** Proof tests really exercise the behaviour. In the bugfix lane, check that the failing test was not weakened (`git diff` on that test file should be empty after the bug's commit).
5. **Write `review.md`.** Run `sdlc scaffold <ID> review`, then fill it in:
   - **Passes:** each pass run and what you examined.
   - **Important findings:** each as `file:line`, problem, why it matters, suggested fix. Only things that should block a merge. Write "None" if there are none; don't invent findings to look useful.
   - **Nits:** at most the cap in `REVIEW.md` (default 5). The validator enforces this. Pick the most useful ones.
   - **Release checklist:** migrations, feature flags, config and secrets, the rollback command, change-log notes, and who must sign off. Write "None needed" where true.
6. **Validate** with `sdlc check docs/sdlc/<ID>/review.md` until it prints `OK`.
7. **Report back.** You are a forked context, so your final message is what the user sees. Give:
   - the important findings, or "no blocking findings"
   - the nit count
   - the release checklist highlights
   - the `sdlc next <ID>` line

   Remind the user that `/sdlc-accept <ID> review` records *their* sign-off. This review is not an approval.
