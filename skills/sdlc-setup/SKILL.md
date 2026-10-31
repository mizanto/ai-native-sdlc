---
name: sdlc-setup
description: "Bootstrap a repository for the AI-Native SDLC loop: add an sdlc section to CLAUDE.md with the project's real commands and verification steps, create REVIEW.md and docs/sdlc/README.md. Never overwrites existing content."
argument-hint: ""
disable-model-invocation: true
model: claude-sonnet-5-5
effort: medium
---

# Set up a repo for the AI-Native SDLC loop

Every later stage leans on three things being true in the repo:
- `CLAUDE.md` names the real build, test and lint commands, and says how to verify a change. `/sdlc-plan` writes Proof from them and `/sdlc-verify` runs them.
- `REVIEW.md` defines what review checks and the nit cap.
- `docs/sdlc/` exists, with a README explaining the lanes.

Setup writes these **without destroying anything the team already has**.

Templates are in `${CLAUDE_PLUGIN_ROOT}/templates/repo/`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.

## Steps

1. **Discover the project's commands.**
   - Look at `package.json` scripts, `pyproject.toml`, `Makefile`, `justfile`, `Cargo.toml`, `go.mod`, CI workflow files and the README.
   - Prefer commands that CI actually runs.
   - If you can, run the test command once, to confirm it works and to capture what healthy output looks like.
2. **Prepare the changes:**
   - **CLAUDE.md:**
     - Take `templates/repo/CLAUDE-sdlc-section.md` and fill **Commands** and **Verifying your work** with what you found. Leave **Things Claude gets wrong** with its hint comment.
     - If `CLAUDE.md` exists and already has a `<!-- sdlc:begin -->…<!-- sdlc:end -->` block, replace only that block.
     - If it exists without one, append the block at the end.
     - If there's no `CLAUDE.md`, create it with a one-line project heading and the block.
     - Never touch content outside the markers.
   - **REVIEW.md:** create it from `templates/repo/REVIEW.md` **only if absent**. If one exists, leave it and check whether it states a `Nit cap:`. If it doesn't, mention that the default of 5 will apply.
   - **docs/sdlc/README.md:** create it from `templates/repo/sdlc-README.md` only if absent.
3. **Show before writing.** Present the exact additions as a diff or as file contents, and ask for a go-ahead. If the user's request already said to just do it, proceed.
4. **Write the files.** Then run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py" status`, which should report no work items yet.
5. **Hand off.**
   - List the files written.
   - Suggest `git add CLAUDE.md REVIEW.md docs/sdlc/README.md && git commit -m "chore: set up AI-native SDLC loop"`.
   - Explain how to start: `/sdlc-intent` for new features, `/sdlc-plan <ticket>` for well-understood changes, or a `bug.md` via `/sdlc-maintain` for incidents.
