---
name: sdlc-accept
description: "AI-Native SDLC human gate: accept (or reject) an artifact such as intent, spec, plan, bug or review for a work item. Validates it, records accepted_by/accepted_at, and commits only that file."
argument-hint: "<ID> [artifact] [reject <reason>]"
disable-model-invocation: true
model: claude-haiku-5-5
effort: low
---

# Human gate · accept or reject an artifact

The human typing this command *is* the approval. It is the one place in the loop where an artifact moves from `draft` to `accepted`, and the next stage refuses to start without that. Do not add your own judgment of the artifact's quality here: the human has read it. Just run the deterministic step and report.

`sdlc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py"`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.

## Steps

1. **Parse `$ARGUMENTS`:** `<ID> [artifact] [reject <reason>]`.
   - If the artifact is omitted, run `sdlc next <ID>`. If it says `/sdlc-accept <ID> <artifact>`, use that artifact. Otherwise tell the user there is nothing waiting for acceptance and show the next line.
2. **Accept:** run `sdlc accept <ID> <artifact>`.
   - The script validates the file, sets `status: accepted`, `accepted_by` (from git `user.name`) and `accepted_at`, and commits **only that file** as `sdlc(<ID>): accept <artifact>`.
   - If it prints `NOT ACCEPTED`, show the problems and stop. The artifact needs fixing first; don't fix it yourself.
   - If it says `not committed`, relay why (for example, not a git repo or a pre-commit hook failed). The acceptance itself is still recorded in the file.
3. **Reject:** run `sdlc reject <ID> <artifact> --reason "<reason>"`.
4. **Report** the result line and the `sdlc next <ID>` line. Keep it to 2–3 lines.
