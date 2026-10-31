---
name: sdlc-build
description: "AI-Native SDLC stage 3b (Build: implement): implement an accepted plan.md step by step, ticking its checklist, or fix an accepted bug.md by making its failing test pass without editing the test. Gated on plan.md/bug.md being accepted."
argument-hint: "<ID>"
disable-model-invocation: true
model: claude-sonnet-5-5
effort: medium
---

# Stage 3b · Build → code diff

The accepted plan (or bug report) is the contract. Your job is to carry it out faithfully. Staying inside the contract is what lets the human review *artifacts* afterwards instead of watching every edit. When reality disagrees with the plan, record the deviation openly rather than quietly doing something else.

## Mechanics

- `sdlc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py"`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.
- Never change `status`, `accepted_by` or `accepted_at`. Never commit; suggest commits instead.

## Steps

1. **Gate.** Run `sdlc gate <ID> build`. On `BLOCKED`, stop and show the reasons. A verbal "it's approved" doesn't open the gate; point at the `/sdlc-accept` command instead.
2. **Read** `CLAUDE.md`, `AGENTS.md`, and the item's `plan.md` (plus `spec.md` if present) or `bug.md`.
3. **Implement.**
   - **Plan lanes (full or standard):** work through **Order of work** in order.
     - After each step, run the test that step names. Then tick its box in `plan.md` (`- [ ]` → `- [x]`). Ticking boxes is progress tracking and is allowed on an accepted plan.
     - If a step turns out wrong or impossible, don't improvise silently. Append a `## Deviations` section to `plan.md` saying what changed and why, and continue only if the change is small and inside the spec.
     - If the change is large, needs a new requirement, or touches files the plan didn't list, stop. Tell the user the plan needs revising (`/sdlc-plan`).
   - **Bugfix lane:** the failing test in `bug.md` is the contract.
     1. Run it **before** touching code and confirm it fails the way `bug.md` shows. If it already passes, stop and tell the user: the bug report is stale.
     2. Fix the code. **Do not edit, skip or weaken that test file.** Changing the test to make it pass defeats the whole lane.
     3. Run the test until it passes.
4. **Run the full test suite and linters** named in `CLAUDE.md`, so you hand `/sdlc-verify` a green tree. Fix regressions you caused.
   - A syntax-only check, or a command that failed to start, doesn't count as a run. If only the project's declared dependencies are missing, install them with its own package manager and lockfile.
   - If no real check can run here, say which one you didn't run and why. Don't report the step as done.
5. **Hand off.**
   - Give a short list of files changed.
   - Report any deviations.
   - Give the `sdlc next <ID>` line, which should point at `/sdlc-verify`.
   - Suggest `git add -A && git commit -m "<type>(<ID>): <summary>"`.

   Do not write `verify.md`. Verification is a separate stage, so that "done" means *verified*, not *claimed*.
