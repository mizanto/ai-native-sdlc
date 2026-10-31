#!/usr/bin/env python3
"""Append timing for finished runs: record_timing.py <N> <eval_id>:<config>:<tokens>:<ms> ..."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent / "workspace" / f"iteration-{sys.argv[1]}"
for spec in sys.argv[2:]:
    eval_id, config, tokens, ms = spec.split(":")
    run = next(root.glob(f"eval-{eval_id}-*")) / config / "run-1"
    (run / "timing.json").write_text(json.dumps({"total_tokens": int(tokens), "duration_ms": int(ms),
                                                 "total_duration_seconds": round(int(ms) / 1000, 1)}, indent=2))
    print("saved", run / "timing.json")
