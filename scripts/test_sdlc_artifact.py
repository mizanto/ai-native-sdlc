"""Tests for sdlc_artifact.py and the routing ↔ skill frontmatter contract.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import json
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "scripts" / "sdlc_artifact.py"

FM = """---
id: {id}
artifact: {art}
lane: {lane}
status: {status}
upstream: {up}
created: 2026-10-30
accepted_by: {by}
accepted_at: {at}
{extra}---
"""

BODIES = {
    "intent": """
## Problem
Customers phone support to ask where their claim is.
## Proposed outcome
Customers see claim status themselves.
## Affected users and systems
Policy holders; claims API.
## Constraints
No PII in URLs.
## Success criteria
Status calls drop 30%.
## Open questions
None
""",
    "spec": """
## Requirements
- **R1** — GET /claims/{id}/status returns the status.
- **R2** — Unknown claim returns 404.
## Design
Add a route in app.py.
## Non-goals
Editing claims.
## Flagged concerns
None
## Acceptance criteria
R1, R2 covered by tests.
""",
    "plan": """
## Files that change
app.py — new route.
## Order of work
- [ ] 1. Add route
- [ ] 2. Add tests
## Risks
Low.
## Proof
- R1 — `pytest tests/test_status.py::test_ok`
- R2 — `pytest tests/test_status.py::test_404`
""",
    "bug": """
## Repro
GET /claims/0/status
## Expected vs actual
Expected 404, got 500.
## Failing test
`pytest tests/test_status.py::test_zero`
```
FAILED tests/test_status.py::test_zero - assert 500 == 404
```
## Suspected area
app.py lookup.
""",
    "verify": """
## Proof results
```
$ pytest -q
2 passed
```
## Traceability
- R1 — PASS — test_ok
- R2 — PASS — test_404
## Verdict
pass
""",
    "review": """
## Passes
Bugs, security, compliance.
## Important findings
None
## Nits
- rename x
## Release checklist
No migrations. Rollback: revert commit.
""",
}


def run(cwd, *args):
    res = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd,
                         capture_output=True, text=True)
    return res.returncode, res.stdout + res.stderr


class Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "init"], cwd=self.root, check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, item, art, lane="full", status="draft", body=None, extra="", up="none"):
        folder = self.root / "docs" / "sdlc" / item
        folder.mkdir(parents=True, exist_ok=True)
        by, at = ("Me", "2026-10-30T10:00:00") if status == "accepted" else ("", "")
        text = FM.format(id=item, art=art, lane=lane, status=status, up=up, by=by, at=at, extra=extra)
        (folder / f"{art}.md").write_text(text + (BODIES[art] if body is None else body))
        return folder / f"{art}.md"

    def sh(self, *args):
        return run(self.root, *args)


class CheckTests(Repo):
    def test_scaffolded_template_fails_until_filled(self):
        code, out = self.sh("new", "Claims status!", "--lane", "full")
        self.assertEqual(code, 0, out)
        item = re.search(r"ID (\S+)", out).group(1)
        self.assertTrue(item.endswith("-claims-status"))
        code, out = self.sh("check", f"docs/sdlc/{item}/intent.md")
        self.assertEqual(code, 1)
        self.assertIn("section '## Problem' is empty", out)

    def test_every_template_scaffolds(self):
        self.sh("new", "x", "--lane", "full", "--tracker", "SF-1")
        for art in ["spec", "plan", "verify", "review", "incident", "bug"]:
            code, out = self.sh("scaffold", "SF-1-x", art)
            self.assertEqual(code, 0, out)
            text = (self.root / "docs/sdlc/SF-1-x" / f"{art}.md").read_text()
            self.assertNotIn("{{", text, art)

    def test_valid_artifacts_pass(self):
        for art in ["intent", "spec", "plan", "review"]:
            path = self.write("A", art)
            code, out = self.sh("check", str(path))
            self.assertEqual(code, 0, f"{art}: {out}")
        path = self.write("A", "verify", extra="verdict: pass\n")
        self.assertEqual(self.sh("check", str(path))[0], 0)
        path = self.write("B", "bug", lane="bugfix")
        self.assertEqual(self.sh("check", str(path))[0], 0)

    def test_check_works_from_inside_the_item_folder(self):
        path = self.write("A", "intent")
        res = subprocess.run([sys.executable, str(SCRIPT), "check", "intent.md"], cwd=path.parent,
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_spec_needs_numbered_requirements(self):
        path = self.write("A", "spec", body=BODIES["spec"].replace("**R1**", "one").replace("**R2**", "two"))
        code, out = self.sh("check", str(path))
        self.assertEqual(code, 1)
        self.assertIn("numbered R1", out)

    def test_plan_must_cover_every_requirement_and_be_a_checklist(self):
        self.write("A", "spec")
        body = BODIES["plan"].replace("- R2 — `pytest tests/test_status.py::test_404`\n", "")
        body = body.replace("- [ ] ", "- ")
        code, out = self.sh("check", str(self.write("A", "plan", body=body)))
        self.assertEqual(code, 1)
        self.assertIn("Proof does not cover spec requirements: R2", out)
        self.assertIn("checklist", out)

    def test_standard_plan_needs_source(self):
        code, out = self.sh("check", str(self.write("S", "plan", lane="standard")))
        self.assertEqual(code, 1)
        self.assertIn("'## Source'", out)
        body = "\n## Source\nTicket SF-9: show claim status.\n" + BODIES["plan"]
        self.assertEqual(self.sh("check", str(self.write("S", "plan", lane="standard", body=body)))[0], 0)

    def test_bug_needs_pasted_failing_output(self):
        body = BODIES["bug"].replace("```", "")
        code, out = self.sh("check", str(self.write("B", "bug", lane="bugfix", body=body)))
        self.assertEqual(code, 1)
        self.assertIn("pasted failing output", out)

    def test_verify_needs_verdict_and_traceability(self):
        self.write("A", "spec")
        body = BODIES["verify"].replace("- R2 — PASS — test_404\n", "")
        code, out = self.sh("check", str(self.write("A", "verify", body=body)))
        self.assertEqual(code, 1)
        self.assertIn("verdict", out)
        self.assertIn("Traceability does not cover spec requirements: R2", out)

    def test_review_nit_cap_from_review_md(self):
        (self.root / "REVIEW.md").write_text("Nit cap: 2\n")
        body = BODIES["review"].replace("- rename x", "- a\n- b\n- c")
        code, out = self.sh("check", str(self.write("A", "review", body=body)))
        self.assertEqual(code, 1)
        self.assertIn("cap is 2", out)

    def test_accepted_requires_approver(self):
        path = self.write("A", "intent")
        text = path.read_text().replace("status: draft", "status: accepted")
        path.write_text(text)
        code, out = self.sh("check", str(path))
        self.assertEqual(code, 1)
        self.assertIn("accepted_by", out)


class GateAcceptNextTests(Repo):
    def test_gate_blocks_draft_and_opens_after_accept(self):
        self.write("A", "intent")
        code, out = self.sh("gate", "A", "spec")
        self.assertEqual(code, 1)
        self.assertIn("/sdlc-accept A intent", out)
        code, out = self.sh("accept", "A", "intent")
        self.assertEqual(code, 0, out)
        self.assertIn("committed: sdlc(A): accept intent", out)
        self.assertEqual(self.sh("gate", "A", "spec")[0], 0)

    def test_first_stage_has_no_gate(self):
        self.write("A", "intent")
        self.assertEqual(self.sh("gate", "A", "intent")[0], 0)

    def test_stage_outside_lane_is_blocked(self):
        self.write("B", "bug", lane="bugfix")
        code, out = self.sh("gate", "B", "spec")
        self.assertEqual(code, 1)
        self.assertIn("not part of the bugfix lane", out)

    def test_accept_commits_only_that_file(self):
        self.write("A", "intent")
        (self.root / "other.txt").write_text("staged elsewhere")
        subprocess.run(["git", "add", "other.txt"], cwd=self.root, check=True)
        self.assertEqual(self.sh("accept", "A", "intent")[0], 0)
        files = subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], cwd=self.root,
                               capture_output=True, text=True).stdout.split()
        self.assertEqual(files, ["docs/sdlc/A/intent.md"])
        text = (self.root / "docs/sdlc/A/intent.md").read_text()
        self.assertIn("status: accepted", text)
        self.assertIn("accepted_by: Test User", text)

    def test_accept_refuses_invalid_and_verify(self):
        self.write("A", "intent", body="## Problem\n")
        code, out = self.sh("accept", "A", "intent")
        self.assertEqual(code, 1)
        self.assertIn("NOT ACCEPTED", out)
        self.write("A", "verify", extra="verdict: pass\n")
        self.assertEqual(self.sh("accept", "A", "verify")[0], 2)

    def test_review_gates_on_verify_verdict(self):
        self.write("A", "plan", lane="standard", body="\n## Source\nbrief\n" + BODIES["plan"])
        self.write("A", "verify", lane="standard", extra="verdict: fail\n")
        code, out = self.sh("gate", "A", "review")
        self.assertEqual(code, 1)
        self.assertIn("verdict is not pass", out)

    def test_next_walks_the_full_lane(self):
        def nxt():
            return self.sh("next", "A")[1]
        self.write("A", "intent")
        self.assertIn("Next: /sdlc-accept A intent (Haiku 5.5 · effort low) → then /sdlc-spec A (Opus 5.5 · effort high)", nxt())
        self.write("A", "intent", status="accepted")
        self.assertIn("Next: /sdlc-spec A", nxt())
        self.write("A", "spec", status="accepted")
        self.write("A", "plan", status="accepted")
        self.assertIn("Next: /sdlc-build A (Sonnet 5.5 · effort medium) → then /sdlc-verify A", nxt())
        self.write("A", "plan", status="accepted", body=BODIES["plan"].replace("[ ]", "[x]"))
        self.assertIn("Next: /sdlc-verify A (Sonnet 5.5 · effort medium)", nxt())
        self.write("A", "verify", extra="verdict: fail\n")
        self.assertIn("Next: /sdlc-build A  (fix the failures", nxt())
        self.write("A", "verify", extra="verdict: pass\n")
        self.assertIn("Next: /sdlc-review A", nxt())
        self.write("A", "review")
        self.assertIn("Next: /sdlc-accept A review", nxt())
        self.write("A", "review", status="accepted")
        self.assertIn("done", nxt())

    def test_next_bugfix_and_rejected(self):
        self.write("B", "bug", lane="bugfix", status="accepted")
        self.assertIn("Next: /sdlc-build B", self.sh("next", "B")[1])
        self.write("C", "intent")
        self.sh("reject", "C", "intent", "--reason", "too vague")
        self.assertIn("revise: too vague", self.sh("next", "C")[1])

    def test_incident_creates_follow_up_item(self):
        code, out = self.sh("new", "5xx spike", "--lane", "bugfix", "--incident")
        self.assertEqual(code, 0, out)
        item = re.search(r"ID (\S+)", out).group(1)
        self.assertIn("-incident-5xx-spike", item)
        bug = (self.root / "docs/sdlc" / item / "bug.md").read_text()
        self.assertIn(f"upstream: docs/sdlc/{item}/incident.md", bug)

    def test_base_is_plan_acceptance_not_the_build_commit(self):
        def commit(msg):
            subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", msg], cwd=self.root, check=True)
        self.write("A", "intent", status="accepted")
        self.write("A", "spec", status="accepted")
        self.write("A", "plan")
        commit("draft")
        self.assertEqual(self.sh("base", "A")[0], 1)
        self.assertEqual(self.sh("accept", "A", "plan")[0], 0)
        accepted = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root,
                                  capture_output=True, text=True).stdout.strip()
        plan = self.root / "docs/sdlc/A/plan.md"
        plan.write_text(plan.read_text().replace("[ ]", "[x]"))
        (self.root / "app.py").write_text("print('built')\n")
        commit("feat: build ticks the plan in the same commit")
        code, out = self.sh("base", "A")
        self.assertEqual((code, out.strip()), (0, accepted))

    def test_status_table(self):
        self.write("A", "intent", status="accepted")
        self.write("B", "bug", lane="bugfix")
        out = self.sh("status")[1]
        self.assertIn("| A | full | intent:accepted | /sdlc-spec A |", out)
        self.assertIn("| B | bugfix | bug:draft | /sdlc-accept B bug |", out)


class RoutingContract(unittest.TestCase):
    """Skill frontmatter pins model/effort; routing.json is the source of truth."""

    def frontmatter(self, path):
        text = path.read_text()
        head = text.split("---", 2)[1]
        return {k.strip(): v.strip() for k, _, v in
                (line.partition(":") for line in head.splitlines() if ":" in line)}

    def test_every_skill_matches_routing(self):
        routing = json.loads((PLUGIN / "routing.json").read_text())["skills"]
        skills = {p.parent.name: p for p in (PLUGIN / "skills").glob("*/SKILL.md")}
        self.assertEqual(sorted(skills), sorted(routing), "skills/ and routing.json disagree")
        for name, path in skills.items():
            fm = self.frontmatter(path)
            self.assertEqual(fm.get("name"), name, path)
            self.assertEqual(fm.get("model"), routing[name]["model"], f"{name}: model")
            self.assertEqual(fm.get("effort"), routing[name]["effort"], f"{name}: effort")

    def test_stage_skills_are_slash_only(self):
        for path in (PLUGIN / "skills").glob("*/SKILL.md"):
            fm = self.frontmatter(path)
            expected = "false" if path.parent.name == "sdlc-status" else "true"
            self.assertEqual(fm.get("disable-model-invocation", "false"), expected, path)


if __name__ == "__main__":
    unittest.main()
