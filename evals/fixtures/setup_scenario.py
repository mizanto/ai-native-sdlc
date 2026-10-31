#!/usr/bin/env python3
"""Materialise an eval scenario as a fresh git repo: sample-app + ordered layers, one commit per layer.

Usage: python3 setup_scenario.py <scenario> <dest-dir>
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ID = "CLM-7-claim-status"
BASE = ["intent_accepted", "spec_accepted", "plan_accepted"]
SCENARIOS = {
    "base": [],
    "intent_draft": ["intent_draft"],
    "intent_accepted": ["intent_accepted"],
    "spec_accepted": ["intent_accepted", "spec_accepted"],
    "built_ok": BASE + ["impl_ok"],
    "built_buggy": BASE + ["impl_buggy"],
    "verified_insecure": BASE + ["impl_insecure", "verify_pass_insecure"],
    "verify_failed": BASE + ["impl_buggy", "verify_fail"],
}
MESSAGES = {
    "intent_draft": f"sdlc({ID}): draft intent",
    "intent_accepted": f"sdlc({ID}): accept intent",
    "spec_accepted": f"sdlc({ID}): accept spec",
    "plan_accepted": f"sdlc({ID}): accept plan",
    "impl_ok": f"feat({ID}): claim status endpoint",
    "impl_buggy": f"feat({ID}): claim status endpoint",
    "impl_insecure": f"feat({ID}): claim status endpoint",
    "verify_pass_insecure": f"sdlc({ID}): verify pass",
    "verify_fail": f"sdlc({ID}): verify fail",
}


def git(dest, *args):
    subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True)


def main(scenario, dest):
    dest = Path(dest)
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f"{dest} is not empty")
    shutil.copytree(HERE / "sample-app", dest, dirs_exist_ok=True)
    git(dest, "init", "-q", "-b", "main")
    git(dest, "config", "user.name", "Sergey Bendak")
    git(dest, "config", "user.email", "eval@example.com")
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "initial claims service")
    for layer in SCENARIOS[scenario]:
        shutil.copytree(HERE / "layers" / layer, dest, dirs_exist_ok=True)
        git(dest, "add", "-A")
        git(dest, "commit", "-q", "-m", MESSAGES[layer])
    print(f"{scenario} ready at {dest}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in SCENARIOS:
        sys.exit(f"usage: setup_scenario.py <{'|'.join(SCENARIOS)}> <dest>")
    main(sys.argv[1], sys.argv[2])
