---
name: sdlc-verify
description: "AI-Native SDLC stage 4 (Test): run every Proof item from plan.md (or the failing test from bug.md) plus the full suite, paste real output, trace each requirement to evidence, and write verify.md with a pass/fail verdict."
argument-hint: "<ID>"
disable-model-invocation: true
model: claude-sonnet-5-5
effort: medium
---

# Stage 4 · Test → `verify.md`

"Done" means *verified*, with the output on the page. A human reviewer should never have to rerun anything to believe a claim. So every result in `verify.md` must come from a command you actually ran in this session, with its real output pasted. A summary of what the output "would" say doesn't count.

## Mechanics

- `sdlc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py"`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.
- Never commit.

## Steps

1. **Gate.** Run `sdlc gate <ID> verify`. On `BLOCKED`, stop and show the reasons. A verbal "it's approved" doesn't open the gate; point at the `/sdlc-accept` command instead.
2. **Collect the checks:**
   - every line of **Proof** in `plan.md`, or the failing test in `bug.md` for the bugfix lane
   - the full test suite, lint and build commands from `CLAUDE.md` ("Verifying your work"), or from the project's config if `CLAUDE.md` doesn't name them
   - for UI work, a screenshot or browser check if such a tool is available
3. **Run each check.** Record the exact command, its exit code and its output.
   - Keep long outputs to the relevant part (summary line, failures), but never edit what the tool printed.
   - **Never modify tests to make them pass.**
   - If a failure is a small, obvious defect in the new code (a typo, missing import, off-by-one), you may fix it, rerun everything, and say so in `verify.md`.
   - If it is anything bigger, leave it failing and let the verdict say so.
4. **Write `verify.md`.** Run `sdlc scaffold <ID> verify`, then fill it in:
   - **Proof results:** for each check, the command, `exit <code>`, the output in a ``` block, and PASS or FAIL.
   - **Traceability:** one line per requirement, `- R1 — PASS — <test name / evidence>`. The validator fails the file if any spec requirement is missing.
   - **Verdict:** `pass` only if every check passed. Otherwise `fail`, listing what failed.
   - Set `verdict: pass` or `verdict: fail` in the frontmatter to match.
5. **Validate** with `sdlc check docs/sdlc/<ID>/verify.md` until it prints `OK`.
6. **Hand off.** Give the verdict, any failures, and the `sdlc next <ID>` line: `/sdlc-review` on pass, or back to `/sdlc-build` on fail. Suggest the commit `git add docs/sdlc/<ID>/verify.md && git commit -m "sdlc(<ID>): verify <pass|fail>"`.
