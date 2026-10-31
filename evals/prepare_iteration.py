#!/usr/bin/env python3
"""Create workspace/iteration-N/eval-<id>-<name>/<config>/run-1/{repo,outputs} for every eval.

Usage: python3 evals/prepare_iteration.py <N> [--configs with_skill without_skill]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
EVALS = json.loads((PLUGIN / "evals" / "evals.json").read_text())["evals"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("iteration", type=int)
    p.add_argument("--configs", nargs="+", default=["with_skill", "without_skill"])
    args = p.parse_args()
    root = PLUGIN / "workspace" / f"iteration-{args.iteration}"
    for ev in EVALS:
        eval_dir = root / f"eval-{ev['id']}-{ev['name']}"
        eval_dir.mkdir(parents=True, exist_ok=True)
        (eval_dir / "eval_metadata.json").write_text(json.dumps({
            "eval_id": ev["id"], "eval_name": ev["name"], "prompt": ev["prompt"],
            "assertions": ev["assertions"]}, indent=2))
        for config in args.configs:
            run = eval_dir / config / "run-1"
            (run / "outputs").mkdir(parents=True, exist_ok=True)
            # the review viewer looks for metadata next to the run's parent
            (eval_dir / config / "eval_metadata.json").write_text((eval_dir / "eval_metadata.json").read_text())
            repo = run / "repo"
            if not repo.exists():
                subprocess.run([sys.executable, str(PLUGIN / "evals/fixtures/setup_scenario.py"),
                                ev["scenario"], str(repo)], check=True, capture_output=True)
            print(f"{ev['id']:>2} {config:<14} {repo}")


if __name__ == "__main__":
    main()
