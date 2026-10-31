---
name: sdlc-maintain
description: "AI-Native SDLC stage 6 (Maintain): turn a pasted incident, alert, anomaly or error log into incident.md plus a new work item (bug.md with a failing regression test, or intent.md when it needs design), closing the loop. Diagnosis is read-only."
argument-hint: "<incident / alert / log text>"
disable-model-invocation: true
model: claude-opus-5-5
effort: high
---

# Stage 6 · Maintain → `incident.md` + a new work item

This is where the loop closes. Something went wrong in the running system, and the fix must re-enter the pipeline as a normal work item, so it gets the same gates as everything else. Your job is **diagnosis, not repair**:
- Read code, logs, git history and metrics freely.
- Don't change production code here. The fix happens later in `/sdlc-build`, after a human has accepted the work item.

## Mechanics

- `sdlc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py"`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.
- Never change `status`, `accepted_by` or `accepted_at`. Never commit.

## Steps

1. **Read the evidence** in `$ARGUMENTS`: alert text, stack trace, metrics, a user report. Find the code involved, and use `git log` and `git blame` around it to find recent changes. Check `docs/sdlc/` for the work item that last touched that area; its spec and plan often explain the intent the incident violated.
2. **Choose the follow-up lane:**
   - **bugfix**: the cause is localized and you can reproduce it with a test. This is the usual case, and it's better because the fix becomes provable.
   - **full**: the cause is a design gap, needs a product decision, or can't be reproduced locally.
3. **Create the item:**
   ```bash
   sdlc new "<slug>" --lane <bugfix|full> --incident [--upstream "<alert URL / ticket>"]
   ```
   This creates `docs/sdlc/<date>-incident-<slug>/` with `incident.md` and the follow-up `bug.md` or `intent.md`, already linked to it.
4. **Fill `incident.md`:**
   - **Anomaly and evidence:** pasted log lines, timestamps and sources.
   - **Impact**
   - **Timeline**
   - **Root-cause hypothesis:** include what would confirm or refute it.
   - **Regression test / eval to add:** the check that would have caught this.
   - **Follow-up item:** the file and the lane.
5. **Fill the follow-up:**
   - **bug.md:** write the regression test so it reproduces the failure. Adding a *new test file* is the one code change allowed here. Run it and paste its **failing** output into **Failing test**. If it unexpectedly passes, your hypothesis is wrong: revise it, or switch to the full lane.
   - **intent.md:** write the problem from the incident's point of view. Put the open product and design decisions in **Open questions**.
6. **Validate** with `sdlc check` on both files until each prints `OK`.
7. **Hand off.** Give a 3-line diagnosis, the chosen lane and why, the `sdlc next <ID>` line, and the suggested commit `git add docs/sdlc/<ID>/ <new test file> && git commit -m "sdlc(<ID>): incident report + follow-up"`. The on-call human triages: accept, schedule, or reject with a reason.
