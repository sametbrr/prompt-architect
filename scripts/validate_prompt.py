#!/usr/bin/env python3
"""Validate a refined prompt against the quality gates.

Usage:
    python3 validate_prompt.py <prompt_file>                     # validate a file
    python3 validate_prompt.py --stdin                            # read from stdin
    python3 validate_prompt.py --stdin --target-model fable-5     # model-aware run
    python3 validate_prompt.py --self-test                        # built-in test cases

Exit code: 0 if all applicable gates pass, 1 if any fails (non-self-test mode).

Gates 1-6 and 8 are universal. Gates 7, 9, 10 and 11 are model-conditional --
pass --target-model to apply them correctly. Valid values match the profile
stems in references/models/: opus-5 (default), opus-4-8, sonnet-5, fable-5.

Notes:
- Heuristic checks based on regex and structural scanning. Not a substitute for
  human review -- designed to catch common omissions cheaply.
- Mode B (XML) prompts are scored against all applicable gates. Mode A (compact
  bullet) prompts are scored against the subset that applies.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field

DEFAULT_PROFILE = "opus-5"
PROFILES = ("opus-5", "opus-4-8", "sonnet-5", "fable-5")

# Which model profiles each conditional gate applies to.
GATE_APPLICABILITY = {
    9: ("opus-5",),                        # over-verification
    10: PROFILES,                          # reasoning echo (severity varies)
    11: ("opus-5", "fable-5"),             # scope boundary
}
# Gate 10 is a hard failure only here; elsewhere it downgrades to a warning.
REASONING_ECHO_HARD_FAIL = ("fable-5",)


@dataclass
class GateResult:
    gate: int
    name: str
    passed: bool
    note: str = ""
    warning: bool = field(default=False)


# ---------- helpers ----------

XML_TAG_RE = re.compile(r"<([a-z][a-z0-9_]*)>", re.IGNORECASE)
MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s", re.MULTILINE)
MARKDOWN_BOLD_HEADING_RE = re.compile(r"^\s*\*\*[A-Z][A-Za-z ]+:\*\*\s*$", re.MULTILINE)
NEGATIVE_DIRECTIVE_RE = re.compile(
    r"\b(do not|don't|never|avoid|refrain from|must not|shouldn't|should not|no preamble)\b",
    re.IGNORECASE,
)
POSITIVE_VERBS = (
    r"\b(return|produce|deliver|generate|provide|wrap|format|use|prefer|state|"
    r"write|include|specify|cite|enumerate|tabulate|summarize)\b"
)
POSITIVE_DIRECTIVE_RE = re.compile(POSITIVE_VERBS, re.IGNORECASE)
ROLE_GENERIC_RE = re.compile(
    r"\b(helpful assistant|ai assistant|expert (helper|assistant)|chatbot)\b",
    re.IGNORECASE,
)
ROLE_SENIORITY_RE = re.compile(
    r"\b(senior|lead|principal|staff|chief|head of|director of|"
    r"\d+\s*\+?\s*(years?|yrs?)\s*(of\s*)?(experience|exp)?)\b",
    re.IGNORECASE,
)
HALLUCINATION_GUARD_RE = re.compile(
    r"(only answer if (you are|you're)? confident|state.*uncertainty|"
    r"do not guess|if you (are|'re)? unsure|otherwise (return|state))",
    re.IGNORECASE,
)
# Gate 10: any instruction to surface internal reasoning as response text.
REASONING_ECHO_RE = re.compile(
    r"(<\s*(scratchpad|thinking|reasoning|analysis)\s*>"
    r"|\b(write|show|explain|describe|narrate|transcribe|echo|output|include)\b"
    r"[^.\n]{0,40}\b(your )?(intermediate |internal |step[- ]by[- ]step )?"
    r"(reasoning|thought process|thinking|chain of thought)\b)",
    re.IGNORECASE,
)
# Gate 9: any instruction to self-verify.
VERIFICATION_RE = re.compile(
    r"\b(verif(y|ication)|double[- ]check|re-?review|check your (own )?work|"
    r"review your (output|work|answer)|sanity[- ]check)\b",
    re.IGNORECASE,
)
# Gate 11: an explicit scope statement.
SCOPE_BOUNDARY_RE = re.compile(
    r"(<scope_boundaries>|^\s*[-*]?\s*scope\s*:)", re.IGNORECASE | re.MULTILINE
)
SCOPE_BLOCK_RE = re.compile(
    r"<scope_boundaries>.*?</scope_boundaries>", re.IGNORECASE | re.DOTALL
)


def is_xml_mode(prompt: str) -> bool:
    """Heuristic: prompt is XML mode if it has 3+ distinct opening tags."""
    tags = {t.lower() for t in XML_TAG_RE.findall(prompt)}
    return len(tags) >= 3


# ---------- gate checks ----------


def gate_1_single_objective(prompt: str, profile: str) -> GateResult:
    """Flag obvious conjoined-task markers near the top of the prompt."""
    head = prompt[:600].lower()
    conflict_markers = ("and also design", "and also build", "summarize and elaborate",
                        "brief and comprehensive")
    failed = any(m in head for m in conflict_markers)
    return GateResult(
        1, "Single-Objective Clarity", not failed,
        "" if not failed else "Conflicting top-level goals detected.",
    )


def gate_2_xml_isolation(prompt: str, profile: str) -> GateResult:
    if not is_xml_mode(prompt):
        return GateResult(2, "XML/Tag Isolation", True, "Compact mode — N/A")
    md_headings = MARKDOWN_HEADING_RE.findall(prompt)
    md_bold_labels = MARKDOWN_BOLD_HEADING_RE.findall(prompt)
    if md_headings or md_bold_labels:
        return GateResult(
            2, "XML/Tag Isolation", False,
            f"Found {len(md_headings)} markdown heading(s) and "
            f"{len(md_bold_labels)} bold-label section(s) inside prompt body.",
        )
    return GateResult(2, "XML/Tag Isolation", True)


def gate_3_positive_guidance(prompt: str, profile: str) -> GateResult:
    """>=60% of behavioural directives positive. Constraint blocks are exempt.

    Anthropic's own scope-containment guidance is almost entirely negative
    ("Don't add features, refactor code..."), and correctly so -- enumerating
    limits is what a boundary block is for. So <scope_boundaries> is stripped
    before counting, and the threshold sits at 60% rather than the old 75%.
    """
    body = SCOPE_BLOCK_RE.sub("", prompt)
    negatives = len(NEGATIVE_DIRECTIVE_RE.findall(body))
    positives = len(POSITIVE_DIRECTIVE_RE.findall(body))
    total = negatives + positives
    if total == 0:
        return GateResult(3, "Positive Guidance Ratio", True, "No directives detected")
    ratio = positives / total
    exempted = len(SCOPE_BLOCK_RE.findall(prompt))
    note = f"{positives} positive vs {negatives} negative ({ratio:.0%}, threshold 60%)"
    if exempted:
        note += f"; {exempted} scope block(s) exempted"
    return GateResult(3, "Positive Guidance Ratio", ratio >= 0.60, note)


def gate_4_role_specificity(prompt: str, profile: str) -> GateResult:
    if ROLE_GENERIC_RE.search(prompt):
        return GateResult(
            4, "Specific Role + Seniority + Tone", False,
            "Generic role phrasing detected (e.g., 'helpful assistant').",
        )
    if not ROLE_SENIORITY_RE.search(prompt):
        return GateResult(
            4, "Specific Role + Seniority + Tone", False,
            "No seniority indicator found (Senior/Lead/Principal/Nyrs).",
        )
    return GateResult(4, "Specific Role + Seniority + Tone", True)


def gate_5_examples(prompt: str, profile: str) -> GateResult:
    if not is_xml_mode(prompt):
        return GateResult(5, "In-Context Examples", True, "Compact mode — N/A")
    needs_examples = bool(
        re.search(r"\b(classify|categorize|extract|parse|format as|transform)\b",
                  prompt, re.IGNORECASE)
    )
    has_examples = "<examples>" in prompt.lower() or "<example>" in prompt.lower()
    if needs_examples and not has_examples:
        return GateResult(
            5, "In-Context Examples", False,
            "Task involves classification/extraction/transformation but no <examples> block.",
        )
    return GateResult(5, "In-Context Examples", True)


def gate_6_long_context_hierarchy(prompt: str, profile: str) -> GateResult:
    if not is_xml_mode(prompt):
        return GateResult(6, "Long-Context Hierarchy", True, "Compact mode — N/A")
    text = prompt.lower()
    content_pos = text.find("<content>")
    if content_pos == -1:
        content_pos = text.find("<reference>")
    if content_pos == -1:
        return GateResult(6, "Long-Context Hierarchy", True, "No bulky content block")
    reminders_pos = text.find("<reminders>")
    if reminders_pos == -1:
        return GateResult(6, "Long-Context Hierarchy", True, "No <reminders> block")
    if content_pos > reminders_pos:
        return GateResult(
            6, "Long-Context Hierarchy", False,
            "<content>/<reference> appears AFTER <reminders>; static data should be on top.",
        )
    return GateResult(6, "Long-Context Hierarchy", True)


def gate_7_operational_sequencing(prompt: str, profile: str) -> GateResult:
    """Multi-step tasks should dictate order.

    v3.0.0: the scratchpad requirement was removed. Asking the model to narrate
    its reasoning is now Gate 10's concern, and a failure rather than a credit.
    """
    if not is_xml_mode(prompt):
        return GateResult(7, "Operational Sequencing", True, "Compact mode — N/A")
    has_numbered_steps = bool(re.search(r"^\s*\d+\.\s", prompt, re.MULTILINE))
    has_detailed = "<detailed_instructions>" in prompt.lower()
    if not has_numbered_steps and not has_detailed:
        return GateResult(7, "Operational Sequencing", True, "Single-step task — N/A")
    if not has_numbered_steps:
        return GateResult(7, "Operational Sequencing", False, "Missing: numbered step order")
    return GateResult(7, "Operational Sequencing", True)


def gate_8_output_framing(prompt: str, profile: str) -> GateResult:
    has_format_section = (
        "<output_format>" in prompt.lower() or "deliverable shape:" in prompt.lower()
    )
    closing_tags = set(re.findall(r"</([a-z][a-z0-9_]*)>", prompt, re.IGNORECASE))
    standard_tags = {
        "role", "why", "task", "content", "detailed_instructions", "examples", "example",
        "scope_boundaries", "output_format", "tone_preference", "reminders",
        "input", "output", "reference",
    }
    custom_wrappers = closing_tags - standard_tags
    has_wrapper = len(custom_wrappers) >= 1 or "wrap" in prompt.lower()
    has_guard = bool(HALLUCINATION_GUARD_RE.search(prompt))
    missing = []
    if not has_format_section:
        missing.append("output format spec")
    if not has_wrapper:
        missing.append("wrapper tag")
    if not has_guard:
        missing.append("hallucination guard ('only answer if confident')")
    if missing:
        return GateResult(8, "Output Framing + Hallucination Guard", False,
                          "Missing: " + ", ".join(missing))
    return GateResult(8, "Output Framing + Hallucination Guard", True)


def gate_9_no_over_verification(prompt: str, profile: str) -> GateResult:
    """Opus 5 verifies its own work; asking it to causes over-verification."""
    hits = VERIFICATION_RE.findall(prompt)
    if hits:
        return GateResult(
            9, "No Over-Verification", False,
            f"{len(hits)} self-verification instruction(s) found — Opus 5 already "
            "verifies its own work; remove them.",
        )
    return GateResult(9, "No Over-Verification", True)


def gate_10_no_reasoning_echo(prompt: str, profile: str) -> GateResult:
    """Reasoning-echo directives risk the reasoning_extraction refusal on Fable 5."""
    match = REASONING_ECHO_RE.search(prompt)
    if not match:
        return GateResult(10, "No Reasoning Echo", True)
    hard = profile in REASONING_ECHO_HARD_FAIL
    note = f"Reasoning-echo directive found: {match.group(0)[:60]!r}. "
    note += ("Hard fail on Fable 5 — risks the reasoning_extraction refusal and "
             "fallback to Opus 4.8." if hard else
             "Adds no value on this target; thinking is handled by the harness.")
    return GateResult(10, "No Reasoning Echo", not hard, note, warning=not hard)


def gate_11_scope_boundary(prompt: str, profile: str) -> GateResult:
    """Opus 5 can widen a task; Fable 5 can take unrequested actions."""
    if SCOPE_BOUNDARY_RE.search(prompt):
        return GateResult(11, "Scope Boundary Present", True)
    return GateResult(
        11, "Scope Boundary Present", False,
        "No <scope_boundaries> block or 'Scope:' line — this target can widen "
        "the task on its own.",
    )


UNIVERSAL_GATES = [
    gate_1_single_objective,
    gate_2_xml_isolation,
    gate_3_positive_guidance,
    gate_4_role_specificity,
    gate_5_examples,
    gate_6_long_context_hierarchy,
    gate_7_operational_sequencing,
    gate_8_output_framing,
]
CONDITIONAL_GATES = {
    9: gate_9_no_over_verification,
    10: gate_10_no_reasoning_echo,
    11: gate_11_scope_boundary,
}


def validate(prompt: str, profile: str = DEFAULT_PROFILE) -> list[GateResult]:
    results = [gate(prompt, profile) for gate in UNIVERSAL_GATES]
    for number, gate in CONDITIONAL_GATES.items():
        if profile in GATE_APPLICABILITY[number]:
            results.append(gate(prompt, profile))
    return results


def format_report(results: list[GateResult], profile: str) -> str:
    lines = []
    passed = sum(1 for r in results if r.passed)
    lines.append(f"Self-Review: {passed}/{len(results)} gates passed  (target: {profile})")
    for r in results:
        mark = "WARN" if (r.passed and r.warning) else ("PASS" if r.passed else "FAIL")
        line = f"  [{mark}] Gate {r.gate} — {r.name}"
        if r.note:
            line += f" — {r.note}"
        lines.append(line)
    return "\n".join(lines)


# ---------- self-test ----------

GOOD_PROMPT = """\
<role>You are a Senior Backend Architect with 12 years of experience in multi-tenant SaaS. Communicate in precise, technical tone.</role>

<why>
This API will be handed to a partner team next sprint, so the contract has to be stable before they build against it.
</why>

<task>
Design a REST API for inventory tracking across tenants.

Operational steps:
1. Define authentication and tenant isolation model.
2. Specify resource endpoints with verbs and paths.
3. Define data model and schema constraints.
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

BAD_PROMPT = """\
You are a helpful assistant.

## Rules
Don't be too verbose. Don't make stuff up. Don't use jargon.

Analyze this accident report and tell me who is at fault.
"""

# The v2.2.1 "best prompt" — used to prove the inverted gates actually fire.
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


def self_test() -> int:
    ok = True

    print("=== GOOD prompt (target: opus-5) ===")
    good = validate(GOOD_PROMPT, "opus-5")
    print(format_report(good, "opus-5"))
    if all(r.passed for r in good):
        print("  -> all gates passed (expected) OK")
    else:
        print("  -> SOME gates failed (unexpected) FAIL")
        ok = False

    print("\n=== BAD prompt (target: opus-5) ===")
    bad = validate(BAD_PROMPT, "opus-5")
    print(format_report(bad, "opus-5"))
    bad_fails = sum(1 for r in bad if not r.passed)
    print(f"  -> {bad_fails} gates failed (expected >=3)"
          f" {'OK' if bad_fails >= 3 else 'FAIL'}")
    ok = ok and bad_fails >= 3

    print("\n=== LEGACY v2.2.1 prompt (target: opus-5) — inverted gates should fire ===")
    legacy5 = validate(LEGACY_PROMPT, "opus-5")
    print(format_report(legacy5, "opus-5"))
    g9 = next(r for r in legacy5 if r.gate == 9)
    g10 = next(r for r in legacy5 if r.gate == 10)
    g11 = next(r for r in legacy5 if r.gate == 11)
    checks = [
        ("Gate 9 flags 'review your output'", not g9.passed),
        ("Gate 10 warns on <scratchpad> for opus-5", g10.passed and g10.warning),
        ("Gate 11 flags the missing scope block", not g11.passed),
    ]

    print("\n=== LEGACY v2.2.1 prompt (target: fable-5) — Gate 10 should hard-fail ===")
    legacy_f = validate(LEGACY_PROMPT, "fable-5")
    print(format_report(legacy_f, "fable-5"))
    g10f = next(r for r in legacy_f if r.gate == 10)
    g9f = [r for r in legacy_f if r.gate == 9]
    checks += [
        ("Gate 10 hard-fails on fable-5", not g10f.passed and not g10f.warning),
        ("Gate 9 does not apply to fable-5", not g9f),
    ]

    print("\n=== Self-test summary ===")
    for label, result in checks:
        print(f"  [{'PASS' if result else 'FAIL'}] {label}")
        ok = ok and result
    print(f"\nOverall: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


# ---------- CLI ----------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", help="prompt file path")
    parser.add_argument("--stdin", action="store_true", help="read from stdin")
    parser.add_argument("--self-test", action="store_true", help="run built-in tests")
    parser.add_argument(
        "--target-model", default=DEFAULT_PROFILE, choices=PROFILES,
        help=f"target model profile (default: {DEFAULT_PROFILE})",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.stdin:
        prompt = sys.stdin.read()
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            prompt = f.read()
    else:
        parser.print_help()
        return 2

    results = validate(prompt, args.target_model)
    print(format_report(results, args.target_model))
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
