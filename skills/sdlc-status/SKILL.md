---
name: sdlc-status
description: "Show where AI-Native SDLC work items stand: lists docs/sdlc/ items with their lane, artifact statuses and the next command (with suggested model and effort). Use whenever the user asks what's next, where a work item or ticket is, what is waiting for approval, or for an overview of in-flight sdlc work."
argument-hint: "[ID]"
model: claude-haiku-5-5
effort: low
---

# Status of the SDLC loop

`sdlc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py"`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.

The status comes from the files, never from memory of this conversation. Artifacts may have been edited or accepted since then.

- **No ID given:** run `sdlc status` and show the table as printed. Then point out what needs the human:
  - items whose next step is `/sdlc-accept` (waiting for their review)
  - items whose verify verdict is fail
- **ID given** (or a tracker ID that matches a folder prefix):
  - Run `sdlc next <ID>`.
  - List the item's artifacts with their status. Read each artifact's title and summarize it in one line.
  - Show the `Next:` line exactly as printed. It includes the suggested model and effort for that step.
- **No `docs/sdlc/`:** say so, and suggest `/sdlc-setup` for a new repo, or `/sdlc-intent`, `/sdlc-plan` or `/sdlc-maintain` to start an item.
