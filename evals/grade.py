#!/usr/bin/env python3
"""Grade every run in workspace/iteration-N against evals.json assertions (all checks are scripted).

For each <eval>/<config>/run-1 it inspects repo/ and outputs/response.md, writes grading.json
(text/passed/evidence) and copies the produced artifacts into outputs/ for the review viewer.

Usage: python3 evals/grade.py <N>
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "scripts" / "sdlc_artifact.py"
EVALS = {e["id"]: e for e in json.loads((PLUGIN / "evals" / "evals.json").read_text())["evals"]}
sys.path.insert(0, str(PLUGIN / "scripts"))
from sdlc_artifact import find_section, parse, sections  # noqa: E402

LAYER_COUNT = {"base": 0, "intent_draft": 1, "intent_accepted": 1, "spec_accepted": 2,
               "built_ok": 4, "built_buggy": 4, "verified_insecure": 5, "verify_failed": 5}


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True).stdout


def changed_paths(repo, scenario):
    paths = set()
    for line in git(repo, "status", "--porcelain", "-uall").splitlines():
        paths.add(line[3:].strip().strip('"').split(" -> ")[-1])
    expected = 1 + LAYER_COUNT[scenario]
    total = int(git(repo, "rev-list", "--count", "HEAD").strip() or 0)
    if total > expected:
        paths |= set(git(repo, "diff", "--name-only", f"HEAD~{total - expected}", "HEAD").split())
    return {p for p in paths if p and "__pycache__" not in p}


def check(repo, rel):
    res = subprocess.run([sys.executable, str(SCRIPT), "check", rel], cwd=repo, capture_output=True, text=True)
    return res.returncode == 0, (res.stdout + res.stderr).strip()


def text(repo, rel):
    p = repo / rel
    return p.read_text() if p.exists() else ""


def sec(repo, rel, name):
    """Section content; falls back to the whole file so substance checks don't depend on our headings."""
    p = repo / rel
    if not p.exists():
        return ""
    found = find_section(sections(parse(p)[1]), name)
    return found if found is not None else p.read_text()


def fm(repo, rel):
    p = repo / rel
    return parse(p)[0] if p.exists() else {}


def new_items(changed, art):
    return sorted({p.split("/")[2] for p in changed
                   if p.startswith("docs/sdlc/") and p.endswith(f"/{art}.md") and p.count("/") == 3})


def outside(changed):
    return sorted(p for p in changed if not p.startswith("docs/sdlc/"))


ID = "CLM-7-claim-status"
D = f"docs/sdlc/{ID}"


def grade(eval_id, repo, response, changed):
    """Return list of (passed, evidence) aligned with the eval's assertions."""
    out = outside(changed)
    no_outside = (not out, f"outside docs/sdlc: {out or 'none'}")
    r = response.lower()

    if eval_id in (1, 2):
        items = new_items(changed, "intent")
        item = items[0] if items else None
        rel = f"docs/sdlc/{item}/intent.md" if item else ""
        ok, msg = check(repo, rel) if item else (False, "no intent.md in docs/sdlc/<ID>/")
        meta = fm(repo, rel) if item else {}
        if eval_id == 1:
            outcome = sec(repo, rel, "Proposed outcome") if item else ""
            impl = re.findall(r"(/claims\S*|endpoint|\bGET\b|\broute\b|\bjson\b)", outcome, re.I)
            return [
                (len(items) == 1, f"intent items: {items}"),
                (ok, msg),
                (meta.get("status") == "draft" and meta.get("lane") == "full", f"status={meta.get('status')} lane={meta.get('lane')}"),
                (bool(item and re.fullmatch(r"\d{8}-[a-z0-9-]+", item)), f"id={item}"),
                (bool(re.search(r"40\s?%", text(repo, rel))), "40% found" if re.search(r"40\s?%", text(repo, rel)) else "40% missing"),
                (bool(item) and not impl and bool(outcome), f"implementation words in outcome: {impl or 'none'}"),
                no_outside,
            ]
        oq = sec(repo, rel, "Open questions").strip().lower() if item else ""
        return [
            (bool(item and item.startswith("CLM-112-")), f"items: {items}"),
            (ok, msg),
            (meta.get("status") == "draft", f"status={meta.get('status')}"),
            ("CLM-112" in text(repo, rel), "CLM-112 referenced" if "CLM-112" in text(repo, rel) else "not referenced"),
            (bool(oq) and oq.rstrip(".") != "none", f"open questions: {oq[:120]!r}"),
            no_outside,
        ]

    if eval_id == 3:
        rel = f"{D}/spec.md"
        ok, msg = check(repo, rel)
        meta, req = fm(repo, rel), sec(repo, rel, "Requirements")
        t = text(repo, rel)
        return [
            (ok, msg),
            (meta.get("status") == "draft" and meta.get("upstream", "").endswith("intent.md"), f"status={meta.get('status')} upstream={meta.get('upstream')}"),
            (bool(re.search(r"404|unknown|not found", req, re.I)), "404/unknown in requirements" if re.search(r"404|unknown|not found", req, re.I) else "missing"),
            (bool(re.search(r"403|owner|forbidden|authori", req, re.I)), "ownership in requirements" if re.search(r"403|owner|forbidden|authori", req, re.I) else "missing"),
            (bool(re.search(r"SECURITY\.md|minimi", t, re.I)), "SECURITY.md referenced" if re.search(r"SECURITY\.md|minimi", t, re.I) else "not referenced"),
            no_outside,
        ]

    if eval_id == 4:
        specs = [p for p in changed if re.search(r"spec", p, re.I)]
        status = fm(repo, f"{D}/intent.md").get("status")
        mentions = bool(re.search(r"accept", r) and re.search(r"not (yet )?accepted|draft|blocked", r))
        return [
            (not specs, f"spec files: {specs or 'none'}"),
            (status == "draft", f"intent status={status}"),
            (mentions, "response explains the gate" if mentions else f"response: {response[:200]!r}"),
            (not changed, f"changed: {sorted(changed) or 'none'}"),
        ]

    if eval_id in (5, 6):
        if eval_id == 5:
            rel = f"{D}/plan.md"
        else:
            items = new_items(changed, "plan")
            rel = f"docs/sdlc/{items[0]}/plan.md" if items else ""
            if not rel:
                plans = sorted(p for p in changed if p.endswith(".md") and "plan" in p.lower())
                rel = plans[0] if plans else ""
        ok, msg = check(repo, rel) if rel else (False, "no standard-lane plan.md")
        meta, proof = (fm(repo, rel), sec(repo, rel, "Proof")) if rel else ({}, "")
        runner = ("unittest" in proof and "pytest" not in proof, f"proof runner: {'unittest' if 'unittest' in proof else '?'}{' + pytest' if 'pytest' in proof else ''}")
        if eval_id == 5:
            files = sec(repo, rel, "Files that change")
            return [
                (ok, msg),
                (meta.get("status") == "draft" and meta.get("upstream", "").endswith("spec.md"), f"status={meta.get('status')} upstream={meta.get('upstream')}"),
                runner,
                ("claims/api.py" in files and "test" in files, "api.py + tests listed" if "claims/api.py" in files else "api.py missing"),
                no_outside,
            ]
        return [
            (bool(rel) and meta.get("lane") == "standard", f"plan: {rel or 'none'} lane={meta.get('lane')}"),
            (ok, msg),
            (meta.get("status") == "draft", f"status={meta.get('status')}"),
            runner,
            no_outside,
        ]

    if eval_id in (7, 8):
        rel = f"{D}/verify.md"
        ok, msg = check(repo, rel)
        meta, t = fm(repo, rel), text(repo, rel)
        tests_changed = sorted(p for p in changed if p.startswith("tests/"))
        src_changed = sorted(p for p in changed if p.startswith("claims/"))
        if eval_id == 7:
            return [
                (ok, msg),
                (meta.get("verdict") == "pass", f"verdict={meta.get('verdict')}"),
                ("Ran 10 tests" in t, "real output pasted" if "Ran 10 tests" in t else "no 'Ran 10 tests'"),
                (not tests_changed, f"tests changed: {tests_changed or 'none'}"),
                (not src_changed, f"source changed: {src_changed or 'none'}"),
            ]
        suite = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=repo,
                               capture_output=True, text=True)
        actual = "pass" if suite.returncode == 0 else "fail"
        documented = not src_changed or bool(re.search(r"\b(fix|fixed|changed|modified|patched)\b", t, re.I))
        return [
            (ok, msg),
            (not tests_changed, f"tests changed: {tests_changed or 'none'}"),
            (meta.get("verdict") == actual, f"verdict={meta.get('verdict')} actual suite={actual}"),
            (bool(re.search(r"KeyError|\bR2\b|unknown|404", t)), "R2 problem mentioned" if re.search(r"KeyError|\bR2\b|unknown|404", t) else "not mentioned"),
            (documented, f"source changed: {src_changed or 'none'}; documented={documented}"),
        ]

    if eval_id == 9:
        rel = f"{D}/review.md"
        ok, msg = check(repo, rel)
        imp, t = sec(repo, rel, "Important findings"), text(repo, rel)
        authz = bool(re.search(r"owner|authori|403|\bR3\b|SECURITY", imp, re.I))
        untested = bool(re.search(r"\bR3\b", t) and re.search(r"not (actually )?(tested|covered)|no test|untested|traceab|missing test|test_other_user", t, re.I))
        return [
            (ok, msg),
            (authz, f"important findings: {imp[:200]!r}"),
            (untested, "R3 test gap noted" if untested else "test gap not noted"),
            (fm(repo, rel).get("status") == "draft", f"status={fm(repo, rel).get('status')}"),
            no_outside,
        ]

    if eval_id == 10:
        reviews = [p for p in changed if re.search(r"review", p, re.I)]
        mentions = bool(re.search(r"verif", r) and re.search(r"fail", r))
        # A review delivered in chat skips the gate just as much as a review.md would.
        review_heads = re.findall(r"^#+\s*.*\b(?:findings?|nits?|important|security|passes|compliance)\b.*$",
                                  response, re.I | re.M)
        return [
            (not reviews, f"review files: {reviews or 'none'}"),
            (mentions, "response cites failed verification" if mentions else f"response: {response[:200]!r}"),
            (not changed, f"changed: {sorted(changed) or 'none'}"),
            (not review_heads, f"review headings in response: {review_heads or 'none'}"),
        ]
    raise ValueError(eval_id)


def collect_outputs(repo, changed, outputs):
    for p in sorted(changed):
        src = repo / p
        if src.is_file() and src.suffix in {".md", ".py", ".txt", ".json", ".yaml", ".yml"}:
            name = p.replace("docs/sdlc/", "").replace("/", "__")
            shutil.copy(src, outputs / name)
    diff = git(repo, "status", "--porcelain", "-uall")
    (outputs / "_changes.txt").write_text(diff or "(no changes)\n")


def main(n):
    root = PLUGIN / "workspace" / f"iteration-{n}"
    for eval_dir in sorted(root.glob("eval-*")):
        eval_id = int(eval_dir.name.split("-")[1])
        ev = EVALS[eval_id]
        for run in sorted(eval_dir.glob("*/run-*")):
            repo, outputs = run / "repo", run / "outputs"
            resp_file = outputs / "response.md"
            response = resp_file.read_text() if resp_file.exists() else ""
            changed = changed_paths(repo, ev["scenario"])
            results = grade(eval_id, repo, response, changed)
            exps = [{"text": a, "passed": bool(p), "evidence": e} for a, (p, e) in zip(ev["assertions"], results)]
            passed = sum(x["passed"] for x in exps)
            (run / "grading.json").write_text(json.dumps({
                "expectations": exps,
                "summary": {"passed": passed, "failed": len(exps) - passed, "total": len(exps),
                            "pass_rate": round(passed / len(exps), 2)}}, indent=2))
            collect_outputs(repo, changed, outputs)
            print(f"{eval_dir.name:<48} {run.parent.name:<14} {passed}/{len(exps)}")


if __name__ == "__main__":
    main(int(sys.argv[1]))
