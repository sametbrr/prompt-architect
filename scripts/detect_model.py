#!/usr/bin/env python3
"""Resolve the active Claude Code model and effort level from the session transcript.

Usage:
    python3 detect_model.py              # inspect the transcript for $PWD
    python3 detect_model.py /some/path   # inspect the transcript for another cwd
    python3 detect_model.py --self-test  # run built-in checks

Output: a single JSON object on stdout.

    {"id": "claude-opus-5", "effort": "xhigh", "profile": "opus-5",
     "source": "session", "transcript": "/Users/.../<session>.jsonl"}

When no transcript is readable, the default profile is returned instead:

    {"id": null, "effort": null, "profile": "opus-5", "source": "default"}

Exit code is always 0 — an undetectable model is a normal outcome, not an error.
The caller decides what to do with `source`.

How it works
------------
Claude Code writes one JSONL transcript per session under
``~/.claude/projects/<cwd-with-slashes-replaced-by-dashes>/<session-id>.jsonl``.
Assistant records carry ``message.model``; records also carry a top-level
``effort``. Reading the newest transcript for the current working directory and
taking the last value of each gives the live model and effort with no cache
file, no hook, and no network access.

Caveats
-------
* Newest-by-mtime is a heuristic. With several concurrent sessions in the same
  directory it can pick the wrong one.
* Only Claude Code writes these transcripts. Other Agent Skills clients will
  fall through to the default, which is correct behaviour, not a failure.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

DEFAULT_PROFILE = "opus-5"

# Longest prefix wins, so order matters only for readability here.
PROFILE_MAP = (
    ("claude-opus-5", "opus-5"),
    ("claude-opus-4-8", "opus-4-8"),
    ("claude-sonnet-5", "sonnet-5"),
    ("claude-fable-5", "fable-5"),
    ("claude-mythos-5", "fable-5"),
    ("claude-mythos-preview", "fable-5"),
)


def profile_for(model_id: str | None) -> str:
    """Map a model id to a profile filename stem, defaulting to opus-5.

    The ``[1m]`` suffix marks the 1M-context variant; it changes the context
    budget, not prompting behaviour, so it is stripped before matching.
    """
    if not model_id:
        return DEFAULT_PROFILE
    normalized = model_id.split("[")[0].strip().lower()
    for prefix, profile in PROFILE_MAP:
        if normalized.startswith(prefix):
            return profile
    return DEFAULT_PROFILE


def transcript_dir(cwd: str) -> str:
    return os.path.expanduser("~/.claude/projects/" + cwd.replace("/", "-"))


def newest_transcript(cwd: str) -> str | None:
    paths = glob.glob(os.path.join(transcript_dir(cwd), "*.jsonl"))
    if not paths:
        return None
    return max(paths, key=os.path.getmtime)


def scan(path: str) -> tuple[str | None, str | None]:
    """Return the last (model, effort) seen in the transcript."""
    model = effort = None
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # partial final line while the session is live
            if not isinstance(record, dict):
                continue
            message = record.get("message")
            if isinstance(message, dict) and message.get("model"):
                model = message["model"]
            if record.get("effort"):
                effort = record["effort"]
    return model, effort


def detect(cwd: str | None = None) -> dict:
    cwd = cwd or os.getcwd()
    path = newest_transcript(cwd)
    if path is None:
        return {"id": None, "effort": None, "profile": DEFAULT_PROFILE, "source": "default"}
    try:
        model, effort = scan(path)
    except OSError:
        return {"id": None, "effort": None, "profile": DEFAULT_PROFILE, "source": "default"}
    if not model:
        return {"id": None, "effort": None, "profile": DEFAULT_PROFILE, "source": "default"}
    return {
        "id": model,
        "effort": effort,
        "profile": profile_for(model),
        "source": "session",
        "transcript": path,
    }


def self_test() -> int:
    cases = [
        ("claude-opus-5", "opus-5"),
        ("claude-opus-5[1m]", "opus-5"),
        ("claude-opus-4-8", "opus-4-8"),
        ("claude-sonnet-5", "sonnet-5"),
        ("claude-fable-5", "fable-5"),
        ("claude-mythos-5", "fable-5"),
        ("claude-mythos-preview", "fable-5"),
        ("claude-opus-4-7", "opus-5"),   # older model -> default
        ("claude-opus-6", "opus-5"),     # unknown newer model -> default
        (None, "opus-5"),
    ]
    failures = 0
    for model_id, expected in cases:
        actual = profile_for(model_id)
        ok = actual == expected
        failures += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {str(model_id):28} -> {actual}")
    print(f"\nprofile_for: {len(cases) - failures}/{len(cases)} passed")

    live = detect()
    print(f"live detect (cwd={os.getcwd()}): {json.dumps(live, ensure_ascii=False)}")
    if live["source"] == "default":
        print("  note: no transcript for this cwd — default profile returned, as designed")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the active Claude Code model.")
    parser.add_argument("cwd", nargs="?", help="working directory to inspect (default: $PWD)")
    parser.add_argument("--self-test", action="store_true", help="run built-in checks")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    print(json.dumps(detect(args.cwd), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
