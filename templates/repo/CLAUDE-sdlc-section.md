<!-- sdlc:begin -->
## AI-Native SDLC

Work items live in `docs/sdlc/<ID>/`. Each stage writes one artifact and the next
stage only starts once its upstream is accepted (`/sdlc-accept`).

- full lane: `/sdlc-intent` → `/sdlc-spec` → `/sdlc-plan` → `/sdlc-build` → `/sdlc-verify` → `/sdlc-review`
- standard lane: `/sdlc-plan` (from a ticket/brief) → build → verify → review
- bugfix lane: `bug.md` with a failing test → build → verify → review
- `/sdlc-status` shows where every item is; `/sdlc-maintain` turns incidents into new items.

### Commands
<!-- One line each: install, build, test (all / single file), lint, run locally. -->

### Verifying your work
<!-- The exact commands that prove a change works and what healthy output looks like.
     "Done" means these passed and the output is pasted into verify.md. -->

### Things Claude gets wrong
<!-- Add a line whenever the same mistake happens twice. -->
<!-- sdlc:end -->
