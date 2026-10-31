---
name: sdlc-plan
description: "AI-Native SDLC stage 3a (Build: plan): write plan.md (files that change, ordered checklist, risks, proof per requirement) without editing code. For a full-lane item it gates on an accepted spec.md; given a ticket or brief it starts a standard-lane item."
argument-hint: "<ID> | <TRACKER-ID or brief text>"
disable-model-invocation: true
model: claude-opus-5-5
effort: high
---

# Stage 3a · Build (plan) → `plan.md`

Nothing gets implemented without an accepted plan. The plan is where a human can cheaply catch a wrong approach: the wrong files, missing migration, untestable change. It is also the checklist `/sdlc-build` executes and the **Proof** list `/sdlc-verify` runs. So write it for an implementer who has not read this conversation.

**Do not edit source files in this stage.** You read code and write `plan.md`, nothing else. This replaces built-in plan mode, so the discipline is yours to keep.

## Mechanics

- `sdlc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py"`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.
- Never change `status`, `accepted_by` or `accepted_at`. Never commit.

## Steps

1. **Decide the lane from `$ARGUMENTS`.**
   - **The argument is an existing work-item ID with a `docs/sdlc/<ID>/spec.md`: full lane.**
     - Run `sdlc gate <ID> plan`.
     - On `BLOCKED`, stop and show the reasons. A verbal "it's approved" doesn't open the gate; point at the `/sdlc-accept` command instead.
     - Otherwise run `sdlc scaffold <ID> plan`.
   - **Otherwise, standard lane: the argument is a ticket or a brief.**
     - If it is a tracker ID, read the ticket with whatever tracker tool is connected, read-only.
     - Run `sdlc new "<slug>" --lane standard [--tracker <ID>] --upstream <TRACKER-ID or brief>`.
     - Add a `## Source` section at the top of the body. Quote or summarize the ticket or brief there, and turn its asks into numbered requirements (`**R1** — …`) so Proof can trace them.
2. **Understand before planning.**
   - Read `CLAUDE.md` and `AGENTS.md`, the spec (full lane), and the code you will change and its tests.
   - Use a code-intelligence tool such as Graft when available: callers, related modules, existing helpers to reuse.
   - Find the project's real test, lint and build commands. Proof must use commands that actually run here.
3. **Write the plan:**
   - **Files that change:** every file, with its path and one line on what changes and why, tests included. Prefer reusing existing helpers, and name them.
   - **Order of work:** a `- [ ]` checklist of small, safe steps. Each step should leave the code building, and each names the test that covers it. `/sdlc-build` ticks these off.
   - **Risks:** what could break, how big the blast radius is, data and migration concerns, and how to roll back.
   - **Proof:** one line per requirement in the form `- R1 — <exact command or test id>`.
     - The validator fails the plan if any spec requirement is missing here.
     - Add the full-suite, lint and build commands as a final Proof line.
4. **Validate** with `sdlc check docs/sdlc/<ID>/plan.md` until it prints `OK`.
5. **Hand off.** Show the order of work and the main risks in a few lines. Then give the `sdlc next <ID>` line and the suggested commit `git add docs/sdlc/<ID>/plan.md && git commit -m "sdlc(<ID>): draft plan"`. The user reviews, then runs `/sdlc-accept <ID> plan`.
