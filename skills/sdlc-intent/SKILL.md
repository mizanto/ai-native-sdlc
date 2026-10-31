---
name: sdlc-intent
description: "AI-Native SDLC stage 1 (Plan): capture an idea, request or problem as docs/sdlc/<ID>/intent.md in the originator's own words, starting a full-lane work item. Use for new features or changes that need design before planning."
argument-hint: "[idea text | TRACKER-ID]"
disable-model-invocation: true
model: claude-opus-5-5
effort: medium
---

# Stage 1 · Plan → `intent.md`

An idea is worth most when it is captured once, in the originator's words, as a versioned file that the next stage can read. `intent.md` is a *proto-spec*: it says what hurts and what "better" looks like. It deliberately says nothing about how to build it. That belongs to `/sdlc-spec` and `/sdlc-plan`. Writing a solution here anchors everyone on it before the problem is understood.

## Mechanics (same in every sdlc skill)

- The contract script is `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdlc_artifact.py"`. Below, it is called `sdlc`. If `CLAUDE_PLUGIN_ROOT` is unset, the plugin root is two directories above this skill's folder.
- Artifacts live in `docs/sdlc/<ID>/`. Every file keeps its frontmatter block. You may fill in placeholders in the body, but never change `status`, `accepted_by` or `accepted_at`. Only the human approves, with `/sdlc-accept`.
- A skill never commits. At the end, suggest the commit and let the human decide.

## Steps

1. **Read the input.** `$ARGUMENTS` is either free text describing the idea or a tracker ID (e.g. `SF-24`).
   - **Tracker ID:** read the ticket through whatever tracker tool is connected (YouTrack, Jira, Linear, GitHub…). It is read-only input, so never write back to it.
   - **Free text:** that text is the originator's voice.
2. **Fill gaps with judgment, not interrogation.**
   - If the problem, the people affected or the desired outcome is missing, ask **one** short round of questions (at most 3).
   - If you can draft something sensible from what you already have, draft first. The product owner corrects a draft faster than they answer a questionnaire, and unresolved points belong in **Open questions** anyway.
   - Skim the repo (README, `CLAUDE.md`, `AGENTS.md`, relevant code) only enough to name **Affected users and systems** accurately.
3. **Create the work item:**
   ```bash
   sdlc new "<short slug>" --lane full [--tracker <ID>]
   ```
   The ID is `<TRACKER-ID>-<slug>` when there is a ticket, otherwise `<YYYYMMDD>-<slug>`. The command prints the ID and the path of the scaffolded `intent.md`.
4. **Fill every section of `intent.md`.** Replace the `<!-- -->` hints and the title placeholder with content.
   - **Problem:** quote or closely paraphrase the originator. Say who feels it and what evidence exists.
   - **Proposed outcome:** describe the end state, not the implementation. "Customers can see claim status without calling" is an outcome. "Add a /status endpoint" is a solution.
   - **Success criteria:** make them observable and checkable later, with numbers where the originator gave them.
   - **Open questions:** list everything the product owner still has to decide. Write "None" only if that's genuinely true.
5. **Validate** with `sdlc check docs/sdlc/<ID>/intent.md` and fix until it prints `OK`.
6. **Hand off.** Show the user:
   - a 3–5 line summary of the intent and the open questions,
   - the line printed by `sdlc next <ID>`,
   - a suggested commit: `git add docs/sdlc/<ID>/intent.md && git commit -m "sdlc(<ID>): draft intent"`.

The artifact stays `status: draft`. Tell the user to read it, edit anything that isn't in their words, and then run `/sdlc-accept <ID> intent`.
