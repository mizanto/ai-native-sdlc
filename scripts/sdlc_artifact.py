#!/usr/bin/env python3
"""Deterministic contract for AI-Native SDLC artifacts.

Every stage of the loop writes one markdown artifact into docs/sdlc/<ID>/ and the
next stage gates on it. This script is the single place that decides whether an
artifact is well-formed, whether a stage may start, and what comes next, so the
skills never have to make that call by judgment.

Subcommands:
  new <slug> --lane L [--tracker T] [--upstream U] [--incident]
                                      create a work item folder + its first artifact
  scaffold <ID> <artifact> [--upstream U] [--force]
                                      render an artifact template into the item folder
  check <path>                        validate frontmatter, sections and cross-links
  gate <ID> <stage>                   may <stage> start? (upstream valid + accepted)
  accept <ID> <artifact> [--no-commit]
                                      human approval: mark accepted and commit that file only
  reject <ID> <artifact> --reason R   mark an artifact rejected
  next <ID>                           print the next step with model/effort routing
  status                              table of all work items and their next step
  base <ID>                           commit the review diff starts from (plan/bug acceptance)
  route <skill>                       print the model/effort a skill is pinned to

Python 3 stdlib only. Exit codes: 0 ok, 1 check/gate failed, 2 usage error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PLUGIN_ROOT / "templates"
ROUTING = PLUGIN_ROOT / "routing.json"

# Stages per lane, in order. "build" produces code, not an artifact file.
LANES = {
    "full": ["intent", "spec", "plan", "build", "verify", "review"],
    "standard": ["plan", "build", "verify", "review"],
    "bugfix": ["bug", "build", "verify", "review"],
}

SECTIONS = {
    "intent": ["Problem", "Proposed outcome", "Affected users and systems",
               "Constraints", "Success criteria", "Open questions"],
    "spec": ["Requirements", "Design", "Non-goals", "Flagged concerns",
             "Acceptance criteria"],
    "plan": ["Files that change", "Order of work", "Risks", "Proof"],
    "bug": ["Repro", "Expected vs actual", "Failing test", "Suspected area"],
    "verify": ["Proof results", "Traceability", "Verdict"],
    "review": ["Passes", "Important findings", "Nits", "Release checklist"],
    "incident": ["Anomaly and evidence", "Impact", "Timeline",
                 "Root-cause hypothesis", "Regression test", "Follow-up item"],
}

# Artifacts a human approves. verify.md is judged by its verdict instead.
ACCEPTABLE = {"intent", "spec", "plan", "bug", "review", "incident"}
REQUIRED_KEYS = ["id", "artifact", "lane", "status", "upstream", "created"]
STATUSES = {"draft", "accepted", "rejected"}
DEFAULT_NIT_CAP = 5
REQ_ID = re.compile(r"\bR(\d+)\b")


# ---------------------------------------------------------------- helpers

def fail(msg: str, code: int = 2) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def repo_root() -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def sdlc_dir(args) -> Path:
    if getattr(args, "root", None):
        return Path(args.root).resolve()
    return repo_root() / "docs" / "sdlc"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root().resolve()))
    except ValueError:
        return str(path)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60].rstrip("-") or "item"


def load_routing() -> dict:
    return json.loads(ROUTING.read_text())


def route_label(skill: str) -> str:
    routing = load_routing()
    entry = routing["skills"].get(skill)
    if not entry:
        return ""
    model = routing["display"].get(entry["model"], entry["model"])
    return f"{model} · effort {entry['effort']}"


def parse(path: Path) -> tuple[dict, str]:
    """Return (frontmatter, body). Frontmatter is flat `key: value` lines."""
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            value = value.split(" #", 1)[0].strip()
            meta[key.strip()] = value
    body = text[end + 4:].lstrip("\n")
    return meta, body


def write_meta(path: Path, updates: dict) -> None:
    text = path.read_text()
    end = text.find("\n---", 4)
    head, tail = text[4:end], text[end:]
    lines = head.splitlines()
    for key, value in updates.items():
        for i, line in enumerate(lines):
            if line.split(":", 1)[0].strip() == key:
                lines[i] = f"{key}: {value}"
                break
        else:
            lines.append(f"{key}: {value}")
    path.write_text("---\n" + "\n".join(lines) + tail)


def sections(body: str) -> dict[str, str]:
    """Map lower-cased `## Heading` -> its content (comments stripped)."""
    found: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current is not None:
                found[current] = "\n".join(buf)
            current, buf = m.group(1).strip().lower(), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        found[current] = "\n".join(buf)
    return {k: re.sub(r"<!--.*?-->", "", v, flags=re.S).strip() for k, v in found.items()}


def find_section(secs: dict[str, str], name: str) -> str | None:
    """Headings match by prefix so 'Regression test / eval to add' satisfies 'Regression test'."""
    name = name.lower()
    for heading, content in secs.items():
        if heading == name or heading.startswith(name):
            return content
    return None


def req_ids(text: str) -> set[str]:
    return {f"R{n}" for n in REQ_ID.findall(text)}


def nit_cap() -> int:
    review = repo_root() / "REVIEW.md"
    if review.exists():
        m = re.search(r"nit cap\D{0,20}(\d+)", review.read_text(), re.I)
        if m:
            return int(m.group(1))
    return DEFAULT_NIT_CAP


def item_dir(args, item_id: str) -> Path:
    d = sdlc_dir(args) / item_id
    if not d.is_dir():
        fail(f"no work item folder {rel(d)}")
    return d


def item_lane(folder: Path) -> str | None:
    for md in sorted(folder.glob("*.md")):
        meta, _ = parse(md)
        if meta.get("lane") in LANES:
            return meta["lane"]
    return None


def chain_artifacts(lane: str) -> list[str]:
    return [s for s in LANES[lane] if s != "build"]


def upstream_of(lane: str, stage: str) -> str | None:
    """Artifact a stage reads. build/verify read the plan (or bug); review reads verify."""
    if stage in ("build", "verify"):
        return "bug" if lane == "bugfix" else "plan"
    if stage == "review":
        return "verify"
    arts = chain_artifacts(lane)
    if stage not in arts:
        fail(f"stage '{stage}' is not part of the {lane} lane ({' → '.join(LANES[lane])})")
    i = arts.index(stage)
    return arts[i - 1] if i > 0 else None


# ---------------------------------------------------------------- check

def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    path = path.resolve()
    if not path.exists():
        return [f"{rel(path)} does not exist"]
    meta, body = parse(path)
    if not meta:
        return ["missing YAML frontmatter (--- block at top of file)"]

    for key in REQUIRED_KEYS:
        if not meta.get(key):
            problems.append(f"frontmatter: '{key}' is missing or empty")
    art = meta.get("artifact", "")
    if art and art != path.stem:
        problems.append(f"frontmatter: artifact '{art}' does not match file name '{path.name}'")
    if art and art not in SECTIONS:
        problems.append(f"frontmatter: unknown artifact type '{art}'")
        return problems
    if meta.get("id") and meta["id"] != path.parent.name:
        problems.append(f"frontmatter: id '{meta['id']}' does not match folder '{path.parent.name}'")
    if meta.get("lane") and meta["lane"] not in LANES:
        problems.append(f"frontmatter: lane must be one of {sorted(LANES)}")
    if meta.get("status") and meta["status"] not in STATUSES:
        problems.append(f"frontmatter: status must be one of {sorted(STATUSES)}")
    if meta.get("status") == "accepted":
        for key in ("accepted_by", "accepted_at"):
            if not meta.get(key):
                problems.append(f"frontmatter: status is accepted but '{key}' is empty")

    if "{{" in body or re.search(r"\bTODO\b", body):
        problems.append("body still contains template placeholders ({{…}} or TODO)")

    secs = sections(body)
    required = list(SECTIONS.get(art, []))
    if art == "plan" and meta.get("lane") == "standard":
        required.insert(0, "Source")
    for name in required:
        content = find_section(secs, name)
        if content is None:
            problems.append(f"missing section '## {name}'")
        elif not content:
            problems.append(f"section '## {name}' is empty (write 'None' if there is nothing)")

    problems += type_checks(path, art, meta, secs)
    return problems


def type_checks(path: Path, art: str, meta: dict, secs: dict) -> list[str]:
    problems: list[str] = []
    spec_path = path.parent / "spec.md"
    spec_reqs: set[str] = set()
    if spec_path.exists() and art in {"plan", "verify"}:
        _, spec_body = parse(spec_path)
        spec_reqs = req_ids(find_section(sections(spec_body), "Requirements") or "")

    if art == "spec":
        if not req_ids(find_section(secs, "Requirements") or ""):
            problems.append("Requirements must be numbered R1, R2, … so plan and verify can trace them")

    if art == "plan":
        order = find_section(secs, "Order of work") or ""
        if not re.search(r"^\s*[-*] \[[ xX]\]", order, re.M):
            problems.append("Order of work must be a checklist (- [ ] step) that /sdlc-build ticks off")
        missing = spec_reqs - req_ids(find_section(secs, "Proof") or "")
        if missing:
            problems.append(f"Proof does not cover spec requirements: {', '.join(sorted(missing, key=lambda r: int(r[1:])))}")

    if art == "bug":
        if "```" not in (find_section(secs, "Failing test") or ""):
            problems.append("Failing test must include the pasted failing output in a ``` block")

    if art == "verify":
        verdict = meta.get("verdict", "")
        if verdict not in {"pass", "fail"}:
            problems.append("frontmatter: 'verdict' must be pass or fail")
        if "```" not in (find_section(secs, "Proof results") or ""):
            problems.append("Proof results must include pasted command output in ``` blocks")
        missing = spec_reqs - req_ids(find_section(secs, "Traceability") or "")
        if missing:
            problems.append(f"Traceability does not cover spec requirements: {', '.join(sorted(missing, key=lambda r: int(r[1:])))}")

    if art == "review":
        nits = find_section(secs, "Nits") or ""
        count = len(re.findall(r"^\s*(?:[-*]|\d+\.)\s+(?!none\b)", nits, re.M | re.I))
        cap = nit_cap()
        if count > cap:
            problems.append(f"Nits has {count} items; the cap is {cap} (REVIEW.md). Keep the most useful ones")
        if meta.get("status") == "accepted" and meta.get("approves"):
            problems.append("review.md must not carry an approval; branch protection / the human does that")
    return problems


def cmd_check(args) -> int:
    path = Path(args.path)
    problems = check_file(path)
    if problems:
        print(f"FAIL {rel(path)}")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK {rel(path)}")
    return 0


# ---------------------------------------------------------------- gate

def gate(folder: Path, stage: str) -> list[str]:
    lane = item_lane(folder)
    if not lane:
        return [f"cannot determine lane: no artifact with a valid 'lane' in {rel(folder)}"]
    if stage not in LANES[lane]:
        return [f"stage '{stage}' is not part of the {lane} lane ({' → '.join(LANES[lane])})"]
    up = upstream_of(lane, stage)
    if up is None:
        return []
    up_path = folder / f"{up}.md"
    if up == "verify":
        problems = check_file(up_path)
        if not problems and parse(up_path)[0].get("verdict") != "pass":
            problems.append("verify.md verdict is not pass — fix and re-run /sdlc-verify first")
        return problems
    problems = check_file(up_path)
    if not problems:
        status = parse(up_path)[0].get("status")
        if status != "accepted":
            problems.append(f"{up}.md is '{status}', not accepted — review it, then run /sdlc-accept {folder.name} {up}")
    return problems


def cmd_gate(args) -> int:
    folder = item_dir(args, args.id)
    problems = gate(folder, args.stage)
    if problems:
        print(f"BLOCKED {args.stage} for {args.id}")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OPEN {args.stage} for {args.id}")
    return 0


# ---------------------------------------------------------------- scaffold / new

def render(folder: Path, art: str, lane: str, upstream: str, force: bool = False) -> Path:
    target = folder / f"{art}.md"
    if target.exists() and not force:
        fail(f"{rel(target)} already exists (use --force to overwrite)")
    tpl = (TEMPLATES / f"{art}.md").read_text()
    values = {"id": folder.name, "artifact": art, "lane": lane, "upstream": upstream,
              "created": dt.date.today().isoformat()}
    for key, value in values.items():
        tpl = tpl.replace("{{" + key + "}}", value)
    target.write_text(tpl)
    return target


def cmd_scaffold(args) -> int:
    folder = item_dir(args, args.id)
    lane = args.lane or item_lane(folder)
    if not lane:
        fail("cannot determine lane; pass --lane")
    if args.artifact not in SECTIONS:
        fail(f"unknown artifact '{args.artifact}'")
    upstream = args.upstream
    if not upstream:
        up = upstream_of(lane, args.artifact) if args.artifact in LANES[lane] else None
        upstream = rel(folder / f"{up}.md") if up else "none"
    print(rel(render(folder, args.artifact, lane, upstream, args.force)))
    return 0


def cmd_new(args) -> int:
    lane = args.lane
    slug = slugify(args.slug)
    if args.incident:
        slug = f"incident-{slug}"
    prefix = args.tracker or dt.date.today().strftime("%Y%m%d")
    item_id = f"{prefix}-{slug}"
    folder = sdlc_dir(args) / item_id
    if folder.exists():
        fail(f"{rel(folder)} already exists")
    folder.mkdir(parents=True)
    first = LANES[lane][0]
    created = []
    if args.incident:
        created.append(render(folder, "incident", lane, args.upstream or "none"))
        created.append(render(folder, first, lane, rel(folder / "incident.md")))
    else:
        created.append(render(folder, first, lane, args.upstream or args.tracker or "none"))
    print(f"ID {item_id}")
    for path in created:
        print(rel(path))
    return 0


# ---------------------------------------------------------------- accept / reject

def git_user() -> str:
    try:
        out = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True)
        if out.stdout.strip():
            return out.stdout.strip()
    except FileNotFoundError:
        pass
    return os.environ.get("USER", "unknown")


def cmd_accept(args) -> int:
    folder = item_dir(args, args.id)
    if args.artifact not in ACCEPTABLE:
        fail(f"'{args.artifact}' is not accepted by a human (verify.md is judged by its verdict)")
    path = folder / f"{args.artifact}.md"
    problems = check_file(path)
    if problems:
        print(f"NOT ACCEPTED {rel(path)} — fix these first:")
        for p in problems:
            print(f"  - {p}")
        return 1
    write_meta(path, {"status": "accepted", "accepted_by": git_user(),
                      "accepted_at": dt.datetime.now().replace(microsecond=0).isoformat()})
    print(f"ACCEPTED {rel(path)}")
    if args.no_commit:
        return 0
    msg = f"sdlc({args.id}): accept {args.artifact}"
    try:
        subprocess.run(["git", "add", "--", str(path)], check=True, capture_output=True, text=True)
        res = subprocess.run(["git", "commit", "-m", msg, "--", str(path)],
                             capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"not committed: {e}")
        return 0
    if res.returncode == 0:
        print(f"committed: {msg}")
    else:
        print(f"not committed: {(res.stderr or res.stdout).strip()}")
    return 0


def cmd_reject(args) -> int:
    folder = item_dir(args, args.id)
    path = folder / f"{args.artifact}.md"
    if not path.exists():
        fail(f"{rel(path)} does not exist")
    write_meta(path, {"status": "rejected", "rejected_reason": args.reason.replace("\n", " ")})
    print(f"REJECTED {rel(path)}: {args.reason}")
    return 0


# ---------------------------------------------------------------- next / status

def next_step(folder: Path) -> tuple[str, str | None]:
    """Return (primary step, follow-up step or None) as '/command args' strings."""
    lane = item_lane(folder)
    if not lane:
        return (f"/sdlc-intent or /sdlc-plan — {folder.name} has no artifacts yet", None)
    item = folder.name
    for stage in LANES[lane]:
        if stage == "build":
            if (folder / "verify.md").exists():
                continue
            plan = folder / "plan.md"
            if plan.exists():
                order = find_section(sections(parse(plan)[1]), "Order of work") or ""
                if re.search(r"^\s*[-*] \[[xX]\]", order, re.M) and not re.search(r"^\s*[-*] \[ \]", order, re.M):
                    return (f"/sdlc-verify {item}", f"/sdlc-review {item}")
            return (f"/sdlc-build {item}", f"/sdlc-verify {item}")
        path = folder / f"{stage}.md"
        if not path.exists():
            nxt = LANES[lane][LANES[lane].index(stage) + 1] if stage != LANES[lane][-1] else None
            return (f"/sdlc-{stage} {item}", f"/sdlc-accept {item} {stage}" if stage in ACCEPTABLE else
                    (f"/sdlc-{nxt} {item}" if nxt else None))
        meta, _ = parse(path)
        if stage == "verify":
            if meta.get("verdict") != "pass":
                return (f"/sdlc-build {item}  (fix the failures in verify.md)", f"/sdlc-verify {item}")
            continue
        status = meta.get("status")
        if status == "rejected":
            return (f"/sdlc-{stage} {item}  (revise: {meta.get('rejected_reason', 'rejected')})",
                    f"/sdlc-accept {item} {stage}")
        if status != "accepted":
            later = LANES[lane][LANES[lane].index(stage) + 1:] if stage != "review" else []
            return (f"/sdlc-accept {item} {stage}", f"/sdlc-{later[0]} {item}" if later else None)
    return ("done — review accepted; merge and release per the checklist in review.md", None)


def label(step: str) -> str:
    m = re.match(r"/(sdlc-[a-z]+)", step)
    route = route_label(m.group(1)) if m else ""
    return f"{step} ({route})" if route else step


def cmd_next(args) -> int:
    folder = item_dir(args, args.id)
    primary, then = next_step(folder)
    line = f"Next: {label(primary)}"
    if then:
        line += f" → then {label(then)}"
    print(line)
    return 0


def cmd_status(args) -> int:
    root = sdlc_dir(args)
    folders = sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    if not folders:
        print(f"No work items in {rel(root)}. Start one with /sdlc-intent, /sdlc-plan or /sdlc-maintain.")
        return 0
    print("| ID | Lane | Artifacts | Next |")
    print("|---|---|---|---|")
    for folder in folders:
        lane = item_lane(folder) or "?"
        arts = []
        for art in (chain_artifacts(lane) if lane in LANES else []) + ["incident"]:
            path = folder / f"{art}.md"
            if path.exists():
                meta, _ = parse(path)
                state = meta.get("verdict") if art == "verify" else meta.get("status")
                arts.append(f"{art}:{state}")
        primary, _ = next_step(folder)
        print(f"| {folder.name} | {lane} | {' '.join(arts) or '—'} | {primary} |")
    return 0


def cmd_base(args) -> int:
    """Print the commit the change under review starts from: the plan/bug acceptance commit.

    Not "last commit touching plan.md": /sdlc-build ticks the plan checklist in the
    implementation commit, so that would hide the code from the review diff.
    """
    folder = item_dir(args, args.id)
    lane = item_lane(folder)
    if not lane:
        fail(f"{folder.name} has no artifacts")
    art = upstream_of(lane, "build")
    msg = f"sdlc({args.id}): accept {art}"
    res = subprocess.run(["git", "log", "-1", "--format=%H", "--fixed-strings", f"--grep={msg}"],
                         capture_output=True, text=True)
    sha = res.stdout.strip()
    if res.returncode != 0 or not sha:
        print(f"NO BASE: no commit '{msg}'. Fall back to `git merge-base HEAD <default-branch>`.")
        return 1
    print(sha)
    return 0


def cmd_route(args) -> int:
    routing = load_routing()
    entry = routing["skills"].get(args.skill)
    if not entry:
        fail(f"no routing for '{args.skill}'")
    print(f"{args.skill}: {route_label(args.skill)} ({entry['model']})")
    return 0


# ---------------------------------------------------------------- cli

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sdlc_artifact.py", description=__doc__.split("\n\n")[0])
    p.add_argument("--root", help="sdlc directory (default: <repo>/docs/sdlc)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new"); s.add_argument("slug")
    s.add_argument("--lane", required=True, choices=sorted(LANES))
    s.add_argument("--tracker"); s.add_argument("--upstream")
    s.add_argument("--incident", action="store_true"); s.set_defaults(func=cmd_new)

    s = sub.add_parser("scaffold"); s.add_argument("id"); s.add_argument("artifact")
    s.add_argument("--lane", choices=sorted(LANES)); s.add_argument("--upstream")
    s.add_argument("--force", action="store_true"); s.set_defaults(func=cmd_scaffold)

    s = sub.add_parser("check"); s.add_argument("path"); s.set_defaults(func=cmd_check)
    s = sub.add_parser("gate"); s.add_argument("id"); s.add_argument("stage"); s.set_defaults(func=cmd_gate)

    s = sub.add_parser("accept"); s.add_argument("id"); s.add_argument("artifact")
    s.add_argument("--no-commit", action="store_true"); s.set_defaults(func=cmd_accept)

    s = sub.add_parser("reject"); s.add_argument("id"); s.add_argument("artifact")
    s.add_argument("--reason", required=True); s.set_defaults(func=cmd_reject)

    s = sub.add_parser("next"); s.add_argument("id"); s.set_defaults(func=cmd_next)
    s = sub.add_parser("status"); s.set_defaults(func=cmd_status)
    s = sub.add_parser("base"); s.add_argument("id"); s.set_defaults(func=cmd_base)
    s = sub.add_parser("route"); s.add_argument("skill"); s.set_defaults(func=cmd_route)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
