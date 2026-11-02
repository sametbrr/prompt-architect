#!/usr/bin/env python3
"""Validate a refined prompt against the prompt-architect quality gates.

Usage:
    python3 scripts/validate_prompt.py <prompt_file> [--target-model PROFILE_OR_MODEL]
    python3 scripts/validate_prompt.py --stdin --target-model gpt-6.1-sol
    python3 scripts/validate_prompt.py --self-test

``--target-model`` takes a profile stem (opus-5-5, sonnet-5-5, haiku-5-5,
fable-5-1, opus-5, sonnet-5, opus-4-8, fable-5, claude-canon, gpt-sol,
gpt-astra, gpt-terra, gpt-luna, generic) or any model id / alias that
detect_model.py can resolve ("claude-haiku-5-5", "GPT-6 Astra", "gpt-5.6-terra").
Default: opus-5-5.

Every gate reports PASS, FAIL, WARN (passed with a warning) or N/A. N/A gates
are listed but never counted as passes. Exit code: 0 when no gate FAILs,
1 when any gate fails, 2 on usage errors.

Heuristic regex and structure checks. They catch common omissions cheaply and
are not a substitute for reading the prompt.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detect_model import ALL_PROFILES, OPENAI_PROFILES, resolve  # noqa: E402

DEFAULT_TARGET = "opus-5-5"
HARD, WARN = "hard", "warn"

# Conditional gate severity per profile. Missing key or None = N/A.
#   9  no over-verification   10 no reasoning echo
#   11 scope boundary         12 completion criteria
#   xml: Gate 2 applies (Claude targets expect XML sections)
_CLAUDE_CURRENT = {"xml": True, 10: HARD}
GATE_RULES: dict[str, dict] = {
    "opus-5-5": {**_CLAUDE_CURRENT, 9: WARN, 11: HARD},
    "sonnet-5-5": {**_CLAUDE_CURRENT, 11: HARD},
    "haiku-5-5": {**_CLAUDE_CURRENT},
    "fable-5-1": {**_CLAUDE_CURRENT, 11: HARD},
    "opus-5": {"xml": True, 9: HARD, 10: WARN, 11: HARD},
    "sonnet-5": {"xml": True, 10: WARN},
    "opus-4-8": {"xml": True, 10: WARN},
    "fable-5": {"xml": True, 10: HARD, 11: HARD},
    "claude-canon": {"xml": True, 10: WARN},
    "generic": {10: WARN},
    **{p: {10: WARN, 11: HARD, 12: HARD, "openai": True} for p in OPENAI_PROFILES},
}
assert set(GATE_RULES) == set(ALL_PROFILES), "GATE_RULES out of sync with detect_model"


@dataclass
class GateResult:
    gate: int
    name: str
    status: str  # PASS | FAIL | WARN | N/A
    note: str = ""

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


def _r(gate: int, name: str, ok: bool, note: str = "", warn_only: bool = False) -> GateResult:
    if ok:
        return GateResult(gate, name, "PASS", note)
    return GateResult(gate, name, "WARN" if warn_only else "FAIL", note)


def _na(gate: int, name: str, note: str) -> GateResult:
    return GateResult(gate, name, "N/A", note)


# ---------- helpers ----------

XML_TAG_RE = re.compile(r"<([a-z][a-z0-9_]*)>", re.IGNORECASE)
MD_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.MULTILINE)
MD_BOLD_LABEL_RE = re.compile(r"^\s*\*\*[A-Z][A-Za-z ]+:\*\*\s*$", re.MULTILINE)
NEGATIVE_RE = re.compile(
    r"\b(do not|don't|never|avoid|refrain from|must not|shouldn't|should not|no preamble)\b",
    re.IGNORECASE)
POSITIVE_RE = re.compile(
    r"\b(return|produce|deliver|generate|provide|wrap|format|use|prefer|state|write|"
    r"include|specify|cite|enumerate|tabulate|summarize|run|list|keep|report)\b",
    re.IGNORECASE)
ROLE_GENERIC_RE = re.compile(
    r"\b(helpful assistant|ai assistant|expert (helper|assistant)|chatbot)\b", re.IGNORECASE)
ROLE_SENIORITY_RE = re.compile(
    r"\b(senior|lead|principal|staff|chief|head of|director of|"
    r"\d+\s*\+?\s*(years?|yrs?)\s*(of\s*)?(experience|exp)?)\b", re.IGNORECASE)
GUARD_RE = re.compile(
    r"(only answer if (you are|you're)? ?confident|state.{0,40}uncertain|do not guess|"
    r"don't guess|if you (are|'re) unsure|otherwise (return|state|say)|"
    r"if (the )?(input|evidence|data|sources?|form data)\b.{0,30}\b(doesn't|does not|don't|do not)"
    r" (clearly )?support)", re.IGNORECASE)
REASONING_ECHO_RE = re.compile(
    r"(<\s*(scratchpad|thinking|reasoning|analysis)\s*>"
    r"|\b(write|show|explain|describe|narrate|transcribe|echo|output|include)\b"
    r"[^.\n]{0,40}\b(your )?(intermediate |internal |step[- ]by[- ]step )?"
    r"(reasoning|thought process|thinking|chain of thought)\b)", re.IGNORECASE)
VERIFICATION_RE = re.compile(
    r"\b(verif(y|ication)|double[- ]check|re-?review|check your (own )?work|"
    r"review your (output|work|answer)|sanity[- ]check)\b", re.IGNORECASE)
SCOPE_RE = re.compile(
    r"(<scope_boundaries>|^\s*[-*]?\s*(scope|boundaries)\s*:"
    r"|^\s{0,3}#{1,6}\s*(scope|constraints|boundaries)\b)", re.IGNORECASE | re.MULTILINE)
SCOPE_BLOCK_RE = re.compile(r"<scope_boundaries>.*?</scope_boundaries>", re.IGNORECASE | re.DOTALL)
MD_SCOPE_SECTION_RE = re.compile(
    r"^\s{0,3}#{1,6}\s*(scope|constraints|boundaries)\b.*?(?=^\s{0,3}#{1,6}\s|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL)
DONE_RE = re.compile(
    r"(\bdone when\b|\bdone looks like\b|\bdefinition of done\b|\b(success|acceptance|completion)"
    r" criteria\b|^\s{0,3}#{1,6}\s*done\b|\bfinished when\b|\bcomplete when\b)",
    re.IGNORECASE | re.MULTILINE)
CHECK_CMD_RE = re.compile(r"(`[^`]+`|\b(run|execute)\b.{0,40}\b(test|build|lint|check)s?\b)",
                          re.IGNORECASE)


def is_xml_mode(prompt: str) -> bool:
    return len({t.lower() for t in XML_TAG_RE.findall(prompt)}) >= 3


def md_headings(prompt: str) -> list[str]:
    return [h.lower() for h in MD_HEADING_RE.findall(prompt)]


def is_md_mode(prompt: str) -> bool:
    return not is_xml_mode(prompt) and len(md_headings(prompt)) >= 3


def is_structured(prompt: str) -> bool:
    return is_xml_mode(prompt) or is_md_mode(prompt)


def _first_pos(text: str, needles: list[str]) -> int:
    hits = [text.find(n) for n in needles if text.find(n) != -1]
    return min(hits) if hits else -1


# ---------- gates ----------

def gate_1(prompt: str, rules: dict) -> GateResult:
    head = prompt[:600].lower()
    markers = ("and also design", "and also build", "summarize and elaborate",
               "brief and comprehensive")
    bad = any(m in head for m in markers)
    return _r(1, "Single-Objective Clarity", not bad, "Conflicting top-level goals." if bad else "")


def gate_2(prompt: str, rules: dict) -> GateResult:
    name = "XML/Tag Isolation"
    if not rules.get("xml"):
        return _na(2, name, "markdown or XML sections are both fine on this target")
    if is_md_mode(prompt):
        return _r(2, name, False, "markdown headings used as sections; Claude targets expect XML tags")
    if not is_xml_mode(prompt):
        return _na(2, name, "compact mode")
    heads = MD_HEADING_RE.findall(prompt)
    bold = MD_BOLD_LABEL_RE.findall(prompt)
    if heads or bold:
        return _r(2, name, False, f"{len(heads)} markdown heading(s), {len(bold)} bold label(s) inside the XML body")
    return _r(2, name, True)


def gate_3(prompt: str, rules: dict) -> GateResult:
    body = MD_SCOPE_SECTION_RE.sub("", SCOPE_BLOCK_RE.sub("", prompt))
    neg, pos = len(NEGATIVE_RE.findall(body)), len(POSITIVE_RE.findall(body))
    if neg + pos == 0:
        return _r(3, "Positive Guidance Ratio", True, "no directives detected")
    ratio = pos / (neg + pos)
    note = f"{pos} positive vs {neg} negative ({ratio:.0%}, threshold 60%; scope/constraints sections exempt)"
    return _r(3, "Positive Guidance Ratio", ratio >= 0.60, note)


def gate_4(prompt: str, rules: dict) -> GateResult:
    name = "Specific Role + Seniority + Tone"
    if ROLE_GENERIC_RE.search(prompt):
        return _r(4, name, False, "generic role phrasing (e.g. 'helpful assistant')")
    if not ROLE_SENIORITY_RE.search(prompt):
        return _r(4, name, False, "no seniority indicator (Senior/Lead/Principal/N years)")
    return _r(4, name, True)


def gate_5(prompt: str, rules: dict) -> GateResult:
    name = "In-Context Examples"
    if not is_structured(prompt):
        return _na(5, name, "compact mode")
    needs = re.search(r"\b(classify|categorize|extract|parse|format as|transform)\b", prompt, re.I)
    has = re.search(r"<examples?>|^\s{0,3}#{1,6}\s*examples?\b", prompt, re.I | re.M)
    if not needs:
        return _na(5, name, "task doesn't call for examples")
    return _r(5, name, bool(has), "" if has else "classification/extraction task without examples")


def gate_6(prompt: str, rules: dict) -> GateResult:
    name = "Long-Context Hierarchy"
    if not is_structured(prompt):
        return _na(6, name, "compact mode")
    text = prompt.lower()
    content = _first_pos(text, ["<content>", "<reference>", "# context", "# reference", "# background"])
    reminders = _first_pos(text, ["<reminders>", "# reminders"])
    if content == -1 or reminders == -1:
        return _na(6, name, "no reference block and reminders pair to order")
    ok = content < reminders
    return _r(6, name, ok, "" if ok else "reference data appears after the reminders; put static data first")


def gate_7(prompt: str, rules: dict) -> GateResult:
    name = "Operational Sequencing"
    if not is_structured(prompt):
        return _na(7, name, "compact mode")
    numbered = bool(re.search(r"^\s*\d+\.\s", prompt, re.M))
    detailed = "<detailed_instructions>" in prompt.lower() or "# steps" in prompt.lower()
    if not numbered and not detailed:
        return _na(7, name, "single-step task")
    return _r(7, name, numbered, "" if numbered else "missing numbered step order")


def gate_8(prompt: str, rules: dict) -> GateResult:
    name = "Output Framing + Hallucination Guard"
    low = prompt.lower()
    has_format = ("<output_format>" in low or "deliverable shape:" in low
                  or bool(re.search(r"^\s{0,3}#{1,6}\s*output\b", prompt, re.I | re.M)))
    closing = set(re.findall(r"</([a-z][a-z0-9_]*)>", prompt, re.I))
    standard = {"role", "why", "task", "content", "detailed_instructions", "examples", "example",
                "scope_boundaries", "output_format", "tone_preference", "reminders",
                "input", "output", "reference"}
    has_wrapper = bool(closing - standard) or "wrap" in low
    missing = []
    if not has_format:
        missing.append("output format spec")
    if not has_wrapper and not rules.get("openai"):
        missing.append("wrapper tag")
    if not GUARD_RE.search(prompt):
        missing.append("uncertainty guard ('only answer if confident; otherwise state your uncertainty')")
    return _r(8, name, not missing, ("missing: " + ", ".join(missing)) if missing else "")


def gate_9(prompt: str, rules: dict) -> GateResult:
    name = "No Over-Verification"
    sev = rules.get(9)
    if not sev:
        return _na(9, name, "verification instructions are fine or wanted on this target")
    hits = VERIFICATION_RE.findall(prompt)
    note = (f"{len(hits)} self-verification instruction(s); this target verifies on its own"
            + (" (carried over from Opus 5, unverified for this model)" if sev == WARN else ""))
    return _r(9, name, not hits, note if hits else "", warn_only=sev == WARN)


def gate_10(prompt: str, rules: dict) -> GateResult:
    name = "No Reasoning Echo"
    sev = rules.get(10)
    m = REASONING_ECHO_RE.search(prompt)
    if not m:
        return _r(10, name, True)
    note = f"reasoning-echo directive: {m.group(0)[:60]!r}. " + (
        "Hard fail: risks the reasoning_extraction refusal on current Claude models."
        if sev == HARD else "Adds length and no value; thinking is handled by the model.")
    return _r(10, name, False, note, warn_only=sev != HARD)


def gate_11(prompt: str, rules: dict) -> GateResult:
    name = "Scope Boundary Present"
    if not rules.get(11):
        return _na(11, name, "recommended, not enforced on this target")
    ok = bool(SCOPE_RE.search(prompt))
    return _r(11, name, ok, "" if ok else
              "no <scope_boundaries> block, Scope:/Boundaries: line or Constraints/Scope section")


def gate_12(prompt: str, rules: dict) -> GateResult:
    name = "Completion Criteria"
    if not rules.get(12):
        return _na(12, name, "applies to OpenAI/Codex targets")
    done = bool(DONE_RE.search(prompt))
    if not done:
        return _r(12, name, False, "no 'Done when' / success criteria; Codex prompts should say what finished looks like")
    note = "" if CHECK_CMD_RE.search(prompt) else "tip: name the check command (tests/build) if code changes"
    return _r(12, name, True, note)


GATES = [gate_1, gate_2, gate_3, gate_4, gate_5, gate_6, gate_7, gate_8,
         gate_9, gate_10, gate_11, gate_12]


def resolve_target(target: str) -> tuple[str, str | None]:
    info = resolve(target)
    return info["profile"], info["note"]


def validate(prompt: str, target: str = DEFAULT_TARGET) -> list[GateResult]:
    profile, _ = resolve_target(target)
    rules = GATE_RULES[profile]
    return [g(prompt, rules) for g in GATES]


def summary_line(results: list[GateResult], profile: str) -> str:
    applicable = [r for r in results if r.status != "N/A"]
    passed = sum(r.status in ("PASS", "WARN") for r in applicable)
    warns = sum(r.status == "WARN" for r in applicable)
    na = len(results) - len(applicable)
    return (f"Self-Review: {passed}/{len(applicable)} applicable gates passed"
            f" ({warns} warning{'s' if warns != 1 else ''}, {na} N/A)  target: {profile}")


def format_report(results: list[GateResult], profile: str) -> str:
    lines = [summary_line(results, profile)]
    for r in results:
        line = f"  [{r.status:4}] Gate {r.gate:>2} — {r.name}"
        if r.note:
            line += f" — {r.note}"
        lines.append(line)
    return "\n".join(lines)


# ---------- self-test ----------

GOOD_XML = """\
<role>You are a Senior Backend Architect with 12 years of experience in multi-tenant SaaS. Communicate in precise, technical tone.</role>

<why>
This API will be handed to a partner team next sprint, so the contract has to be stable before they build against it.
</why>

<task>
Design a REST API for inventory tracking across tenants.
</task>

<content>
The system has 500 tenants, 1M SKUs per tenant, and 100 req/s peak per tenant.
</content>

<detailed_instructions>
1. First, define tenant scoping (path param vs header vs subdomain).
2. Then enumerate endpoints with HTTP verbs and idempotency expectations.
3. Finally specify the schema with indexes and constraints.
</detailed_instructions>

<scope_boundaries>
Deliver the API design only. Don't implement handlers, don't pick a web framework,
and don't design the deployment topology.
</scope_boundaries>

<output_format>
Wrap your final answer in <api_design>...</api_design>. Use markdown tables for endpoint enumeration.
</output_format>

<tone_preference>
Keep prose tight; let the tables carry the detail.
</tone_preference>

<reminders>
- Only answer if you are confident; otherwise state your uncertainty explicitly.
- Deliver only the requested result; omit preamble and closing commentary.
- Prefer the simplest sufficient solution.
</reminders>
"""

GOOD_MD = """\
You are a senior backend engineer with 10 years of experience in Python services. Write in a direct, technical tone.

## Goal
Add rate limiting to the public `/search` endpoint in `@api/search.py`.

## Context
Traffic spikes from one client degrade search for everyone. Redis is already available as `app.redis`.

## Steps
1. Read `@api/search.py` and the middleware in `@api/middleware/`.
2. Add a per-API-key token bucket (60 requests/minute) using Redis.
3. Return HTTP 429 with a Retry-After header when the bucket is empty.

## Constraints
- Do not change the response schema of `/search`.
- Do not refactor unrelated middleware.

## Done when
- Requests over the limit get 429 with Retry-After.
- Run `pytest tests/test_search.py -q` and report the result.

## Output
Summarize the change in three sentences and list the files you touched. If the code doesn't support a clean middleware hook, state your uncertainty and stop.
"""

BAD_PROMPT = """\
You are a helpful assistant.

## Rules
Don't be too verbose. Don't make stuff up. Don't use jargon.

Analyze this accident report and tell me who is at fault.
"""

LEGACY_PROMPT = """\
<role>You are a senior claims adjuster specializing in Swedish auto-accident forms. Communicate in precise, formal tone.</role>
<reference>Form structure: 17 rows, each row meaning ... [enumerated].</reference>
<detailed_instructions>
1. First, read all 17 form rows and extract checked checkboxes.
2. Tabulate the extracted data.
3. Only after step 2, examine the freehand accident sketch.
Write intermediate reasoning inside <scratchpad>...</scratchpad> before the final verdict.
</detailed_instructions>
<output_format>Return your final answer wrapped in <verdict>...</verdict>.</output_format>
<reminders>
- Only answer if the form data clearly supports a verdict; otherwise state your uncertainty.
- Review your output for completeness and correctness before returning.
</reminders>
"""

COMPACT = """\
- Act as a senior copywriter with deep expertise in B2B SaaS landing pages
- Objective: write three headline options for a time-tracking product
- Scope: headlines only; no body copy
- Deliverable shape: a numbered list wrapped in <headlines>...</headlines>
- Adherence: deliver only the result; state any uncertainty explicitly.
"""


def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def get(results, n):
        return next(r for r in results if r.gate == n)

    def show(title, prompt, target):
        res = validate(prompt, target)
        print(f"\n=== {title} (target: {target}) ===")
        print(format_report(res, resolve_target(target)[0]))
        return res

    r = show("GOOD xml", GOOD_XML, "opus-5-5")
    checks.append(("GOOD xml passes every applicable gate on opus-5-5", not any(x.failed for x in r)))
    checks.append(("Gate 12 is N/A on a Claude target", get(r, 12).status == "N/A"))

    r = show("GOOD markdown", GOOD_MD, "gpt-6.1-sol")
    checks.append(("GOOD markdown passes every applicable gate on gpt-6.1-sol", not any(x.failed for x in r)))
    checks.append(("Gate 2 is N/A on an OpenAI target", get(r, 2).status == "N/A"))
    checks.append(("Gate 12 passes with Done when", get(r, 12).status == "PASS"))

    r = validate(GOOD_MD, "opus-5-5")
    checks.append(("markdown sections fail Gate 2 on a Claude target", get(r, 2).failed))

    r = validate(GOOD_XML, "gpt-5.6-terra")
    checks.append(("XML prompt without done criteria fails Gate 12 on gpt-5.6-terra", get(r, 12).failed))

    r = show("BAD", BAD_PROMPT, "opus-5-5")
    checks.append(("BAD fails >= 3 gates", sum(x.failed for x in r) >= 3))

    r = show("LEGACY v2.2.1", LEGACY_PROMPT, "opus-5")
    checks += [("legacy opus-5: Gate 9 flags 'review your output'", get(r, 9).failed),
               ("legacy opus-5: Gate 10 warns on <scratchpad>", get(r, 10).status == "WARN"),
               ("legacy opus-5: Gate 11 flags missing scope", get(r, 11).failed)]

    r = validate(LEGACY_PROMPT, "opus-5-5")
    checks += [("opus-5-5: Gate 9 is a warning, not a failure", get(r, 9).status == "WARN"),
               ("opus-5-5: Gate 10 hard-fails on <scratchpad>", get(r, 10).failed)]
    for target in ("claude-fable-5-1", "claude-haiku-5-5", "sonnet-5-5", "fable-5"):
        r = validate(LEGACY_PROMPT, target)
        checks.append((f"{target}: Gate 10 hard-fails", get(r, 10).failed))
        checks.append((f"{target}: Gate 9 is N/A", get(r, 9).status == "N/A"))
    r = validate(LEGACY_PROMPT, "gpt-6-astra")
    checks.append(("gpt-6-astra: Gate 10 only warns", get(r, 10).status == "WARN"))

    r = show("COMPACT", COMPACT, "opus-5-5")
    na = {x.gate for x in r if x.status == "N/A"}
    checks.append(("compact prompt: gates 2,5,6,7 are N/A", {2, 5, 6, 7} <= na))
    line = summary_line(r, "opus-5-5")
    applicable = len([x for x in r if x.status != "N/A"])
    checks.append(("N/A gates are not counted as passes", f"/{applicable} applicable" in line
                   and applicable < len(r)))

    for p in ALL_PROFILES:
        checks.append((f"profile accepted: {p}", resolve_target(p)[0] == p))

    print("\n=== Self-test summary ===")
    ok = True
    for label, result in checks:
        print(f"  [{'PASS' if result else 'FAIL'}] {label}")
        ok = ok and result
    print(f"\nOverall: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


# ---------- CLI ----------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a refined prompt against the quality gates.",
        epilog="Profiles: " + ", ".join(ALL_PROFILES) + ". Model ids and aliases are resolved too.")
    parser.add_argument("file", nargs="?", help="prompt file path")
    parser.add_argument("--stdin", action="store_true", help="read the prompt from stdin")
    parser.add_argument("--self-test", action="store_true", help="run built-in tests")
    parser.add_argument("--target-model", default=DEFAULT_TARGET,
                        help=f"profile stem or model id (default: {DEFAULT_TARGET})")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.stdin:
        prompt = sys.stdin.read()
    elif args.file:
        try:
            with open(args.file, encoding="utf-8") as fh:
                prompt = fh.read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        parser.print_help()
        return 2
    if not prompt.strip():
        print("error: empty prompt", file=sys.stderr)
        return 2

    profile, note = resolve_target(args.target_model)
    results = validate(prompt, profile)
    if note:
        print(f"note: {note}")
    print(format_report(results, profile))
    return 1 if any(r.failed for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
