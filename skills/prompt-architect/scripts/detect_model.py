#!/usr/bin/env python3
"""Resolve the host, model, effort and prompt profile for prompt-architect.

Usage:
    python3 scripts/detect_model.py                  # detect from the live session
    python3 scripts/detect_model.py --model "Opus 5.5"   # resolve an explicit target
    python3 scripts/detect_model.py --self-test      # built-in checks (temp dirs only)

Output: one JSON object on stdout, for example

    {"host": "claude-code", "model": "claude-opus-5-5", "effort": "high",
     "family": "claude", "profile": "opus-5-5", "source": "session",
     "profile_files": ["references/models/_matrix.md",
                       "references/models/_shared-canon.md",
                       "references/models/opus-5-5.md"],
     "session_file": "...", "note": null}

``profile_files`` are relative to the skill directory. Read exactly those files.
Exit code is 0 for every detection outcome; an undetectable model is normal.

Detection order (compat contract section 7)
-------------------------------------------
1. Override: ``PROMPT_ARCHITECT_MODEL`` / ``PROMPT_ARCHITECT_EFFORT``.
2. Codex, when ``CODEX_THREAD_ID`` is set. Checked first because Codex started
   from inside Claude Code inherits every ``CLAUDE_*`` variable. The model and
   effort come from the last ``turn_context`` record of
   ``$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*-<thread_id>.jsonl``; fallback is
   ``model`` / ``model_reasoning_effort`` in ``$CODEX_HOME/config.toml``.
3. Claude Code, when ``CLAUDECODE=1`` or ``CLAUDE_CODE_SESSION_ID`` is set. The
   model is the last assistant ``message.model`` in
   ``$CLAUDE_CONFIG_DIR/projects/*/<id>.jsonl`` (then ``~/.claude/projects``);
   effort is ``CLAUDE_EFFORT`` (transcript ``effort`` as fallback).
   When both hosts' variables are present (one launched from inside the other),
   the host whose session file was modified most recently wins.
4. Anything else: unknown host, generic profile.

Session files are read from the end, in growing chunks, and malformed or
partial lines are skipped. Local reads only: no network, no cache, no writes.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import tempfile

MODELS_DIR = "references/models"
MATRIX = f"{MODELS_DIR}/_matrix.md"
CLAUDE_CANON = f"{MODELS_DIR}/_shared-canon.md"
OPENAI_CANON = f"{MODELS_DIR}/openai/_openai-canon.md"
GENERIC = f"{MODELS_DIR}/_generic.md"

CLAUDE_DEFAULT = "opus-5-5"
OPENAI_DEFAULT = "gpt-sol"
GENERIC_PROFILE = "generic"
CLAUDE_CANON_ONLY = "claude-canon"

# Canonical model-id prefix -> profile. Matching is longest-prefix-wins on a
# token boundary (see match_profile), so "claude-opus-5-5" never falls into
# "claude-opus-5". Keys are written in canonical form: lowercase, dots -> dashes.
CLAUDE_MAP = {
    "claude-opus-5-5": "opus-5-5",
    "claude-sonnet-5-5": "sonnet-5-5",
    "claude-haiku-5-5": "haiku-5-5",
    "claude-fable-5-1": "fable-5-1",
    "claude-mythos-5-1": "fable-5-1",  # named in the Fable 5.1 guide; ID string unverified
    # legacy profiles
    "claude-opus-5": "opus-5",
    "claude-sonnet-5": "sonnet-5",
    "claude-opus-4-8": "opus-4-8",
    "claude-fable-5": "fable-5",
    "claude-mythos-5": "fable-5",
    "claude-mythos-preview": "fable-5",
}
OPENAI_MAP = {
    "gpt-6-astra": "gpt-astra",
    "gpt-6-1-sol": "gpt-sol",
    "gpt-6-sol": "gpt-sol",
    "gpt-5-6-sol": "gpt-sol",
    "gpt-5-6": "gpt-sol",  # bare "gpt-5.6": not a catalog slug; mapped to Sol as the closest tier (assumption)
    "gpt-6-1-terra": "gpt-terra",
    "gpt-5-6-terra": "gpt-terra",
    "gpt-6-luna": "gpt-luna",
    "gpt-5-6-luna": "gpt-luna",
    "gpt-reserve": "gpt-luna",  # hidden catalog entry: "fast and affordable"; unverified
}
# Bare family or host names ("Codex", "Claude", "Sonnet", "Astra") -> that family's
# current profile. Compared against canonical() output, so "Sonnet" is "claude-sonnet".
FAMILY_ALIASES = {
    "claude": "opus-5-5", "anthropic": "opus-5-5", "claude-code": "opus-5-5",
    "claude-opus": "opus-5-5", "claude-sonnet": "sonnet-5-5", "claude-haiku": "haiku-5-5",
    "claude-fable": "fable-5-1", "claude-mythos": "fable-5-1",
    "codex": "gpt-sol", "codex-cli": "gpt-sol", "openai": "gpt-sol", "chatgpt": "gpt-sol",
    "gpt": "gpt-sol", "sol": "gpt-sol", "astra": "gpt-astra", "terra": "gpt-terra",
    "luna": "gpt-luna",
}
LEGACY = {"opus-5", "sonnet-5", "opus-4-8", "fable-5"}
CLAUDE_PROFILES = ("opus-5-5", "sonnet-5-5", "haiku-5-5", "fable-5-1",
                   "opus-5", "sonnet-5", "opus-4-8", "fable-5", CLAUDE_CANON_ONLY)
OPENAI_PROFILES = ("gpt-sol", "gpt-astra", "gpt-terra", "gpt-luna")
ALL_PROFILES = CLAUDE_PROFILES + OPENAI_PROFILES + (GENERIC_PROFILE,)

_BOUNDARY = re.compile(r"$|\[|@|-\d{8}\b|-latest\b|-preview\b|-codex\b|-mini\b")
_CLAUDE_FAMILIES = ("opus", "sonnet", "haiku", "fable", "mythos")


# ---------------------------------------------------------------- resolution

def canonical(model_id: str) -> str:
    """Normalise an id or alias.

    Lowercase; strip the [1m] variant tag, Bedrock region/vendor prefixes
    (us.anthropic., anthropic.), Bedrock -v1:0 and Vertex @version suffixes, and
    provider/ prefixes; spaces/underscores/dots -> dashes; add claude- to bare
    family names.
    """
    s = model_id.strip().lower()
    s = s.split("[")[0] if not s.startswith("[") else s  # strip [1m] variant tag
    s = re.sub(r"^(anthropic|openai)/", "", s)
    s = re.sub(r"^([a-z]{2,6}\.)?anthropic\.", "", s)  # us.anthropic.claude-..., anthropic.claude-...
    s = s.split("@")[0]                                  # vertex: claude-...@20261001
    s = re.sub(r"-v\d+(:\d+)?$", "", s)                  # bedrock: ...-v1:0
    s = re.sub(r"[\s_.]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if s.startswith(_CLAUDE_FAMILIES):
        s = "claude-" + s
    return s


def _longest_prefix(s: str, table: dict) -> str | None:
    best = None
    for key in table:
        if s.startswith(key) and _BOUNDARY.match(s, len(key)):
            if best is None or len(key) > len(best):
                best = key
    return table[best] if best else None


def _claude_version(s: str) -> tuple[int, int] | None:
    nums = re.findall(r"(?<![a-z])(\d{1,2})(?![0-9])", s.replace("claude-", "", 1))
    if not nums:
        return None
    major = int(nums[0])
    minor = int(nums[1]) if len(nums) > 1 else 0
    return major, minor


def resolve(model_id: str | None, host: str = "unknown") -> dict:
    """Map a model id (or alias) to family, profile, files and a note."""
    note = None
    if model_id and canonical(model_id) in ALL_PROFILES:  # a profile stem given directly
        profile = canonical(model_id)
        family = ("claude" if profile in CLAUDE_PROFILES
                  else "openai" if profile in OPENAI_PROFILES else "generic")
        return _pack(family, profile, None)

    if not model_id:
        if host == "claude-code":
            return _pack("claude", CLAUDE_DEFAULT,
                         "model not readable from the session; Claude default profile used")
        if host == "codex":
            return _pack("openai", OPENAI_DEFAULT,
                         "model not readable from the session; OpenAI default profile used")
        return _pack("generic", GENERIC_PROFILE,
                     "unknown host and no explicit target; generic profile used")

    s = canonical(model_id)
    if s in FAMILY_ALIASES:
        profile = FAMILY_ALIASES[s]
        family = "openai" if profile in OPENAI_PROFILES else "claude"
        return _pack(family, profile, f"'{model_id}' names a family, not a model; its current profile was used")
    profile = _longest_prefix(s, CLAUDE_MAP)
    if profile:
        if profile in LEGACY:
            note = "legacy profile; a newer generation exists"
        return _pack("claude", profile, note)
    profile = _longest_prefix(s, OPENAI_MAP)
    if profile:
        if s.startswith("gpt-reserve"):
            note = "gpt-reserve mapped to the Luna tier from its catalog description; unverified"
        return _pack("openai", profile, note)

    if s.startswith("claude-"):
        ver = _claude_version(s)
        if ver and (ver[0] < 4 or ver == (4, 0) or (ver[0] == 4 and ver[1] < 8)):
            return _pack("claude", CLAUDE_CANON_ONLY,
                         "older Claude model; shared canon only, no per-model deltas")
        return _pack("claude", CLAUDE_DEFAULT,
                     f"no profile for {model_id}; using the current Claude flagship profile")
    if re.match(r"(gpt-|o\d|codex-|chatgpt-)", s):
        return _pack("openai", OPENAI_DEFAULT,
                     f"no profile for {model_id}; using the OpenAI workhorse profile")
    return _pack("generic", GENERIC_PROFILE,
                 f"{model_id} is not a Claude or OpenAI model; generic profile used")


def profile_files(profile: str) -> list[str]:
    if profile in OPENAI_PROFILES:
        return [MATRIX, OPENAI_CANON, f"{MODELS_DIR}/openai/{profile}.md"]
    if profile == GENERIC_PROFILE:
        return [MATRIX, GENERIC]
    if profile == CLAUDE_CANON_ONLY:
        return [MATRIX, CLAUDE_CANON]
    sub = "legacy/" if profile in LEGACY else ""
    return [MATRIX, CLAUDE_CANON, f"{MODELS_DIR}/{sub}{profile}.md"]


def _pack(family: str, profile: str, note: str | None) -> dict:
    return {"family": family, "profile": profile,
            "profile_files": profile_files(profile), "note": note}


# ---------------------------------------------------------------- file readers

def iter_records_reverse(path: str, chunk: int = 256 * 1024):
    """Yield JSON objects from a JSONL file, newest first.

    Reads the tail first and doubles the window until a caller stops consuming
    or the whole file has been read. Malformed and partial lines are skipped.
    """
    size = os.path.getsize(path)
    seen_from = size
    window = chunk
    with open(path, "rb") as handle:
        while seen_from > 0:
            start = max(0, size - window)
            handle.seek(start)
            data = handle.read(seen_from - start)
            lines = data.split(b"\n")
            if start > 0:
                # first line may be cut mid-record; leave it for the next window
                carry = len(lines[0])
                lines = lines[1:]
            else:
                carry = 0
            for raw in reversed(lines):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw.decode("utf-8", errors="replace"))
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(rec, dict):
                    yield rec
            seen_from = start + carry
            if start == 0:
                break
            window *= 2


def claude_transcript_model(path: str) -> tuple[str | None, str | None]:
    model = effort = None
    for rec in iter_records_reverse(path):
        if effort is None and isinstance(rec.get("effort"), str):
            effort = rec["effort"]
        msg = rec.get("message")
        if isinstance(msg, dict):
            m = msg.get("model")
            if isinstance(m, str) and m and not m.startswith("<"):  # skip <synthetic>
                model = m
                if effort is None and isinstance(rec.get("effort"), str):
                    effort = rec["effort"]
                break
    return model, effort


def codex_rollout_model(path: str) -> tuple[str | None, str | None]:
    for rec in iter_records_reverse(path):
        if rec.get("type") == "turn_context":
            payload = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
            model = payload.get("model")
            effort = payload.get("effort") or payload.get("reasoning_effort")
            if isinstance(model, str) and model:
                return model, effort if isinstance(effort, str) else None
    return None, None


def codex_config_model(config_path: str) -> tuple[str | None, str | None]:
    try:
        with open(config_path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None, None
    try:
        import tomllib  # Python 3.11+
        data = tomllib.loads(raw.decode("utf-8", errors="replace"))
        model, effort = data.get("model"), data.get("model_reasoning_effort")
    except Exception:  # 3.10 or a broken file: top-level key regex
        text = raw.decode("utf-8", errors="replace").split("\n[", 1)[0]
        m = re.search(r'^\s*model\s*=\s*"([^"]+)"', text, re.M)
        e = re.search(r'^\s*model_reasoning_effort\s*=\s*"([^"]+)"', text, re.M)
        model, effort = (m.group(1) if m else None), (e.group(1) if e else None)
    return (model if isinstance(model, str) else None,
            effort if isinstance(effort, str) else None)


# ---------------------------------------------------------------- detection

def claude_projects_roots(env: dict, home: str) -> list[str]:
    roots = []
    if env.get("CLAUDE_CONFIG_DIR"):
        roots.append(os.path.join(os.path.expanduser(env["CLAUDE_CONFIG_DIR"]), "projects"))
    roots.append(os.path.join(home, ".claude", "projects"))
    return list(dict.fromkeys(roots))


def find_claude_transcript(env: dict, home: str) -> str | None:
    sid = env.get("CLAUDE_CODE_SESSION_ID")
    if not sid:
        return None
    hits = []
    for root in claude_projects_roots(env, home):
        hits += glob.glob(os.path.join(glob.escape(root), "*", f"{glob.escape(sid)}.jsonl"))
    return max(hits, key=os.path.getmtime) if hits else None


def codex_home_dir(env: dict, home: str) -> str:
    return env.get("CODEX_HOME") or os.path.join(home, ".codex")


def find_codex_rollout(env: dict, home: str) -> str | None:
    tid = env.get("CODEX_THREAD_ID")
    if not tid:
        return None
    hits = glob.glob(os.path.join(glob.escape(codex_home_dir(env, home)), "sessions", "**",
                                  f"rollout-*-{glob.escape(tid)}.jsonl"), recursive=True)
    return max(hits, key=os.path.getmtime) if hits else None


def pick_host(env: dict, codex_file: str | None, claude_file: str | None) -> str:
    """Codex vs Claude Code.

    Each host inherits the other's variables when launched from inside it, so
    when both are present the host whose session file changed most recently is
    the one running this script. With only one file, that host wins; with
    neither, Codex wins (Codex-inside-Claude is the documented common case).
    """
    is_codex = bool(env.get("CODEX_THREAD_ID"))
    is_claude = env.get("CLAUDECODE") == "1" or bool(env.get("CLAUDE_CODE_SESSION_ID"))
    if is_codex and is_claude:
        if codex_file and claude_file:
            return "codex" if os.path.getmtime(codex_file) >= os.path.getmtime(claude_file) else "claude-code"
        if claude_file and not codex_file:
            return "claude-code"
        return "codex"
    if is_codex:
        return "codex"
    if is_claude:
        return "claude-code"
    return "unknown"


def detect(env: dict | None = None, home: str | None = None) -> dict:
    env = dict(os.environ if env is None else env)
    home = home or os.path.expanduser("~")
    model = effort = session_file = None
    source = "none"

    codex_file = find_codex_rollout(env, home)
    claude_file = find_claude_transcript(env, home)
    host = pick_host(env, codex_file, claude_file)

    if host == "codex":
        session_file = codex_file
        if codex_file:
            try:
                model, effort = codex_rollout_model(codex_file)
            except OSError:
                model = effort = None
            if model:
                source = "session"
        if not model:
            model, cfg_effort = codex_config_model(os.path.join(codex_home_dir(env, home), "config.toml"))
            effort = effort or cfg_effort
            source = "config" if model else "default"
    elif host == "claude-code":
        session_file = claude_file
        t_effort = None
        if claude_file:
            try:
                model, t_effort = claude_transcript_model(claude_file)
            except OSError:
                model, t_effort = None, None
        effort = env.get("CLAUDE_EFFORT") or t_effort
        source = "session" if model else "default"

    if env.get("PROMPT_ARCHITECT_MODEL"):
        model, source = env["PROMPT_ARCHITECT_MODEL"], "override"
    if env.get("PROMPT_ARCHITECT_EFFORT"):
        effort = env["PROMPT_ARCHITECT_EFFORT"]

    out = {"host": host, "model": model, "effort": effort, "source": source}
    out.update(resolve(model, host))
    out["session_file"] = session_file
    return out


# ---------------------------------------------------------------- self-test

def self_test() -> int:
    failures = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        failures += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -> ' + detail) if detail else ''}")

    print("resolve():")
    cases = [
        ("claude-opus-5-5", "opus-5-5"), ("claude-opus-5-5[1m]", "opus-5-5"),
        ("Opus 5.5", "opus-5-5"), ("claude-sonnet-5-5", "sonnet-5-5"),
        ("claude-haiku-5-5", "haiku-5-5"), ("claude-haiku-5-5-20261001", "haiku-5-5"),
        ("claude-fable-5-1", "fable-5-1"), ("claude-mythos-5-1", "fable-5-1"),
        ("claude-opus-5", "opus-5"), ("claude-sonnet-5", "sonnet-5"),
        ("claude-opus-4-8", "opus-4-8"), ("claude-fable-5", "fable-5"),
        ("claude-mythos-preview", "fable-5"), ("claude-haiku-4-5", CLAUDE_CANON_ONLY),
        ("claude-opus-4-7", CLAUDE_CANON_ONLY), ("claude-opus-6", CLAUDE_DEFAULT),
        ("claude-opus-5-6", CLAUDE_DEFAULT),
        ("gpt-6.1-sol", "gpt-sol"), ("gpt-6-sol", "gpt-sol"), ("gpt-5.6-sol", "gpt-sol"),
        ("gpt-6-astra", "gpt-astra"), ("GPT-6 Astra", "gpt-astra"),
        ("gpt-6.1-terra", "gpt-terra"), ("gpt-5.6-terra", "gpt-terra"),
        ("gpt-6-luna", "gpt-luna"), ("gpt-5.6-luna", "gpt-luna"),
        ("gpt-7-nova", OPENAI_DEFAULT), ("gemini-3-pro", GENERIC_PROFILE),
        ("llama-5", GENERIC_PROFILE), ("opus-5-5", "opus-5-5"), ("gpt-luna", "gpt-luna"),
        # bare family / host names
        ("Codex", "gpt-sol"), ("Claude", "opus-5-5"), ("Astra", "gpt-astra"), ("Sol", "gpt-sol"),
        ("Terra", "gpt-terra"), ("Luna", "gpt-luna"), ("Sonnet", "sonnet-5-5"),
        ("Haiku", "haiku-5-5"), ("Fable", "fable-5-1"), ("Opus", "opus-5-5"),
        ("Claude Sonnet", "sonnet-5-5"), ("OpenAI", "gpt-sol"),
        # cloud-provider ids
        ("us.anthropic.claude-sonnet-5-5-20261001-v1:0", "sonnet-5-5"),
        ("anthropic.claude-haiku-5-5-v1:0", "haiku-5-5"),
        ("claude-opus-5-5@20261101", "opus-5-5"), ("eu.anthropic.claude-opus-4-8", "opus-4-8"),
    ]
    for mid, expected in cases:
        got = resolve(mid)["profile"]
        check(f"{mid:28}", got == expected, got)
    check("no model + unknown host", resolve(None)["profile"] == GENERIC_PROFILE)
    check("no model + claude-code", resolve(None, "claude-code")["profile"] == CLAUDE_DEFAULT)
    check("no model + codex", resolve(None, "codex")["profile"] == OPENAI_DEFAULT)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    missing = [f for p in ALL_PROFILES for f in profile_files(p)
               if not os.path.isfile(os.path.join(here, f))]
    check("every profile file exists", not missing, ", ".join(sorted(set(missing))))

    print("\ndetect() against temp dirs:")
    with tempfile.TemporaryDirectory(prefix="pa-detect-") as tmp:
        # Claude Code transcript with a malformed line, a synthetic record and a partial tail
        proj = os.path.join(tmp, ".claude", "projects", "-tmp-my.project_dir with space")
        os.makedirs(proj)
        sid = "11111111-2222-3333-4444-555555555555"
        with open(os.path.join(proj, f"{sid}.jsonl"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "assistant", "message": {"model": "claude-opus-5"}}) + "\n")
            fh.write("{not json\n")
            fh.write(json.dumps({"type": "assistant", "effort": "xhigh",
                                 "message": {"model": "claude-haiku-5-5"}}) + "\n")
            fh.write(json.dumps({"type": "assistant", "message": {"model": "<synthetic>"}}) + "\n")
            fh.write('{"type": "assistant", "message": {"model": "claude-op')
        r = detect({"CLAUDECODE": "1", "CLAUDE_CODE_SESSION_ID": sid, "CLAUDE_EFFORT": "low"}, tmp)
        check("claude host + haiku-5-5 + CLAUDE_EFFORT",
              (r["host"], r["model"], r["effort"], r["profile"]) ==
              ("claude-code", "claude-haiku-5-5", "low", "haiku-5-5"), json.dumps(r["profile"]))
        r = detect({"CLAUDE_CODE_SESSION_ID": sid}, tmp)
        check("claude effort falls back to transcript", r["effort"] == "xhigh", str(r["effort"]))
        r = detect({"CLAUDECODE": "1", "CLAUDE_CODE_SESSION_ID": "missing"}, tmp)
        check("claude host, no transcript -> default",
              (r["source"], r["profile"]) == ("default", CLAUDE_DEFAULT))

        # Codex rollout; Codex wins even when CLAUDE_* vars are inherited
        codex_home = os.path.join(tmp, "codex-home")
        day = os.path.join(codex_home, "sessions", "2026", "11", "02")
        os.makedirs(day)
        tid = "019a-test-thread"
        with open(os.path.join(day, f"rollout-2026-11-02T10-00-00-{tid}.jsonl"), "w") as fh:
            fh.write(json.dumps({"type": "turn_context",
                                 "payload": {"model": "gpt-5.6-terra", "effort": "low"}}) + "\n")
            fh.write("garbage\n")
            fh.write(json.dumps({"type": "turn_context",
                                 "payload": {"model": "gpt-6.1-sol", "effort": "high"}}) + "\n")
            fh.write(json.dumps({"type": "response_item", "payload": {}}) + "\n")
        env = {"CODEX_THREAD_ID": tid, "CODEX_HOME": codex_home,
               "CLAUDECODE": "1", "CLAUDE_CODE_SESSION_ID": sid}
        r = detect(env, tmp)
        check("codex host + gpt-6.1-sol + effort",
              (r["host"], r["model"], r["effort"], r["profile"]) ==
              ("codex", "gpt-6.1-sol", "high", "gpt-sol"), r["model"] or "")
        with open(os.path.join(codex_home, "config.toml"), "w") as fh:
            fh.write('model = "gpt-5.6-terra"\nmodel_reasoning_effort = "medium"\n[tui]\nmodel = "x"\n')
        r = detect({"CODEX_THREAD_ID": "no-such-thread", "CODEX_HOME": codex_home}, tmp)
        check("codex falls back to config.toml",
              (r["source"], r["model"], r["effort"], r["profile"]) ==
              ("config", "gpt-5.6-terra", "medium", "gpt-terra"), r["source"])

        # large file: model only near the top, forcing several tail windows
        big = os.path.join(day, "rollout-2026-11-02T11-00-00-bigthread.jsonl")
        with open(big, "w") as fh:
            fh.write(json.dumps({"type": "turn_context", "payload": {"model": "gpt-6-luna"}}) + "\n")
            filler = json.dumps({"type": "response_item", "payload": {"text": "x" * 500}}) + "\n"
            fh.write(filler * 2000)
        r = detect({"CODEX_THREAD_ID": "bigthread", "CODEX_HOME": codex_home}, tmp)
        check("tail reader widens window on large files", r["model"] == "gpt-6-luna", str(r["model"]))

        r = detect({"CODEX_THREAD_ID": tid, "CODEX_HOME": codex_home,
                    "PROMPT_ARCHITECT_MODEL": "claude-sonnet-5-5",
                    "PROMPT_ARCHITECT_EFFORT": "max"}, tmp)
        check("override env wins", (r["source"], r["profile"], r["effort"]) ==
              ("override", "sonnet-5-5", "max"), r["source"])
        r = detect({}, tmp)
        check("unknown host -> generic", (r["host"], r["profile"]) == ("unknown", GENERIC_PROFILE))

        # both hosts' vars present: newest session file decides
        rollout = os.path.join(day, f"rollout-2026-11-02T10-00-00-{tid}.jsonl")
        transcript = os.path.join(proj, f"{sid}.jsonl")
        both = {"CODEX_THREAD_ID": tid, "CODEX_HOME": codex_home,
                "CLAUDECODE": "1", "CLAUDE_CODE_SESSION_ID": sid}
        os.utime(rollout, (1_800_000_000, 1_800_000_000))
        os.utime(transcript, (1_800_000_100, 1_800_000_100))
        r = detect(both, tmp)
        check("Claude inside Codex (transcript newer) -> claude-code",
              (r["host"], r["model"]) == ("claude-code", "claude-haiku-5-5"), r["host"])
        os.utime(rollout, (1_800_000_200, 1_800_000_200))
        r = detect(both, tmp)
        check("Codex inside Claude (rollout newer) -> codex",
              (r["host"], r["model"]) == ("codex", "gpt-6.1-sol"), r["host"])
        r = detect({**both, "CODEX_THREAD_ID": "gone"}, tmp)
        check("both vars, only Claude transcript exists -> claude-code", r["host"] == "claude-code", r["host"])
        r = detect({**both, "PROMPT_ARCHITECT_MODEL": "gpt-6-astra"}, tmp)
        check("override still wins with both hosts", (r["source"], r["profile"]) == ("override", "gpt-astra"))

        # CLAUDE_CONFIG_DIR
        cfg = os.path.join(tmp, "alt-claude-config")
        os.makedirs(os.path.join(cfg, "projects", "-x"))
        sid2 = "99999999-aaaa-bbbb-cccc-dddddddddddd"
        with open(os.path.join(cfg, "projects", "-x", f"{sid2}.jsonl"), "w") as fh:
            fh.write(json.dumps({"type": "assistant", "message": {"model": "claude-sonnet-5-5"}}) + "\n")
        r = detect({"CLAUDE_CODE_SESSION_ID": sid2, "CLAUDE_CONFIG_DIR": cfg}, tmp)
        check("CLAUDE_CONFIG_DIR is honoured", r["model"] == "claude-sonnet-5-5", str(r["model"]))

    total_note = "all passed" if not failures else f"{failures} failed"
    print(f"\nself-test: {total_note}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve host, model, effort and prompt profile (local reads only).")
    parser.add_argument("--model", help="resolve an explicit target model or alias instead of detecting")
    parser.add_argument("--self-test", action="store_true", help="run built-in checks")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.model:
        live = detect()
        out = {"host": live["host"], "model": args.model, "effort": live["effort"],
               "source": "explicit"}
        out.update(resolve(args.model, live["host"]))
        out["session_model"] = live["model"]
        print(json.dumps(out, ensure_ascii=False))
        return 0
    print(json.dumps(detect(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
