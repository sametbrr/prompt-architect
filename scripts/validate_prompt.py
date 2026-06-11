#!/usr/bin/env python3
"""Validate a refined prompt against the 8 UI-compatible quality gates.

Usage:
    python3 validate_prompt.py <prompt_file>          # validate a file
    python3 validate_prompt.py --stdin                 # read prompt from stdin
    python3 validate_prompt.py --self-test             # run built-in test cases

Exit code: 0 if all gates pass, 1 if any gate fails (non-self-test mode).

Notes:
- Heuristic checks based on regex and structural scanning. Not a substitute for
  human review — designed to catch common omissions cheaply.
- Mode B (XML) prompts are scored against all 8 gates. Mode A (compact bullet)
  prompts are scored against the subset that applies (gates 1, 3, 4, 8).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from typing import Callable


@dataclass
class GateResult:
    gate: int
    name: str
    passed: bool
    note: str = ""


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
SCRATCHPAD_RE = re.compile(
    r"<\s*(scratchpad|thinking|reasoning|analysis)\s*>", re.IGNORECASE
)


def is_xml_mode(prompt: str) -> bool:
    """Heuristic: prompt is XML mode if it has 3+ distinct opening tags."""
    tags = set(t.lower() for t in XML_TAG_RE.findall(prompt))
    return len(tags) >= 3


# ---------- gate checks ----------


def gate_1_single_objective(prompt: str) -> GateResult:
    """Crude heuristic: look for the count of distinct primary verbs in <task> or
    the first paragraph. Conflicting goals are hard to detect mechanically — we
    flag obvious conflicts ("AND ALSO", "both X and Y where X≠Y in domain).
    """
    # Look for obvious conjoined-task markers near the top
    head = prompt[:600].lower()
    conflict_markers = ("and also design", "and also build", "summarize and elaborate",
                        "brief and comprehensive")
    failed = any(m in head for m in conflict_markers)
    return GateResult(
        1,
        "Single-Objective Clarity",
        not failed,
        "" if not failed else "Conflicting top-level goals detected.",
    )


def gate_2_xml_isolation(prompt: str) -> GateResult:
    """Check XML tags exist and markdown headings/bold-labels aren't used as
    section delimiters inside the prompt body."""
    if not is_xml_mode(prompt):
        return GateResult(2, "XML/Tag Isolation", True, "Compact mode — N/A")
    md_headings = MARKDOWN_HEADING_RE.findall(prompt)
    md_bold_labels = MARKDOWN_BOLD_HEADING_RE.findall(prompt)
    if md_headings or md_bold_labels:
        return GateResult(
            2,
            "XML/Tag Isolation",
            False,
            f"Found {len(md_headings)} markdown heading(s) and "
            f"{len(md_bold_labels)} bold-label section(s) inside prompt body.",
        )
    return GateResult(2, "XML/Tag Isolation", True)


def gate_3_positive_guidance(prompt: str) -> GateResult:
    """≥75% of constraints positive."""
    negatives = len(NEGATIVE_DIRECTIVE_RE.findall(prompt))
    positives = len(POSITIVE_DIRECTIVE_RE.findall(prompt))
    total = negatives + positives
    if total == 0:
        return GateResult(3, "Positive Guidance Ratio", True, "No directives detected")
    positive_ratio = positives / total
    # 75% threshold accounts for two unavoidable negatives in the standard
    # adherence block ("do not add abstractions", "do not modify unrelated code")
    # which come from CLAUDE.md Rules #5 and #6.
    passed = positive_ratio >= 0.75
    return GateResult(
        3,
        "Positive Guidance Ratio",
        passed,
        f"{positives} positive vs {negatives} negative "
        f"({positive_ratio:.0%} positive, threshold 75%)",
    )


def gate_4_role_specificity(prompt: str) -> GateResult:
    """Role must be specific (not generic) and include seniority indicator."""
    if ROLE_GENERIC_RE.search(prompt):
        return GateResult(
            4,
            "Specific Role + Seniority + Tone",
            False,
            "Generic role phrasing detected (e.g., 'helpful assistant').",
        )
    if not ROLE_SENIORITY_RE.search(prompt):
        return GateResult(
            4,
            "Specific Role + Seniority + Tone",
            False,
            "No seniority indicator found (Senior/Lead/Principal/Nyrs).",
        )
    return GateResult(4, "Specific Role + Seniority + Tone", True)


def gate_5_examples(prompt: str) -> GateResult:
    """Examples present OR task is simple enough to skip. We can't reliably
    detect 'simple enough', so we only fail when prompt mentions classification/
    extraction with many categories but no <examples> block.
    """
    if not is_xml_mode(prompt):
        return GateResult(5, "In-Context Examples", True, "Compact mode — N/A")
    needs_examples = bool(
        re.search(
            r"\b(classify|categorize|extract|parse|format as|transform)\b",
            prompt,
            re.IGNORECASE,
        )
    )
    has_examples = "<examples>" in prompt.lower() or "<example>" in prompt.lower()
    if needs_examples and not has_examples:
        return GateResult(
            5,
            "In-Context Examples",
            False,
            "Task involves classification/extraction/transformation but no <examples> block.",
        )
    return GateResult(5, "In-Context Examples", True)


def gate_6_long_context_hierarchy(prompt: str) -> GateResult:
    """If prompt has bulky <content> or <reference>, it should appear above the
    main <task> and <reminders>."""
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
            6,
            "Long-Context Hierarchy",
            False,
            "<content>/<reference> appears AFTER <reminders>; static data should be on top.",
        )
    return GateResult(6, "Long-Context Hierarchy", True)


def gate_7_reasoning_directive(prompt: str) -> GateResult:
    """Multi-step tasks should dictate order AND provide scratchpad space.
    Single-step tasks (no numbered steps, no <detailed_instructions>) pass as N/A.
    """
    if not is_xml_mode(prompt):
        return GateResult(7, "In-Context Reasoning Directive", True, "Compact mode — N/A")
    has_numbered_steps = bool(re.search(r"^\s*\d+\.\s", prompt, re.MULTILINE))
    has_detailed = "<detailed_instructions>" in prompt.lower()
    has_scratchpad = bool(SCRATCHPAD_RE.search(prompt))
    if not has_numbered_steps and not has_detailed:
        return GateResult(
            7, "In-Context Reasoning Directive", True, "Single-step task — N/A"
        )
    missing = []
    if not has_numbered_steps:
        missing.append("numbered step order")
    if not has_scratchpad:
        missing.append("<scratchpad>/<thinking> directive")
    if missing:
        return GateResult(
            7,
            "In-Context Reasoning Directive",
            False,
            "Missing: " + ", ".join(missing),
        )
    return GateResult(7, "In-Context Reasoning Directive", True)


def gate_8_output_framing(prompt: str) -> GateResult:
    """Output format specified, wrapper tag named, hallucination guard present."""
    has_format_section = (
        "<output_format>" in prompt.lower() or "deliverable shape:" in prompt.lower()
    )
    # Wrapper tag: any custom closing tag like </final_plan> or </verdict>
    closing_tags = set(re.findall(r"</([a-z][a-z0-9_]*)>", prompt, re.IGNORECASE))
    standard_tags = {
        "role", "task", "content", "detailed_instructions", "examples", "example",
        "output_format", "reminders", "scratchpad", "thinking", "input", "output",
        "reference",
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
        return GateResult(
            8,
            "Output Framing + Hallucination Guard",
            False,
            "Missing: " + ", ".join(missing),
        )
    return GateResult(8, "Output Framing + Hallucination Guard", True)


GATES: list[Callable[[str], GateResult]] = [
    gate_1_single_objective,
    gate_2_xml_isolation,
    gate_3_positive_guidance,
    gate_4_role_specificity,
    gate_5_examples,
    gate_6_long_context_hierarchy,
    gate_7_reasoning_directive,
    gate_8_output_framing,
]


def validate(prompt: str) -> list[GateResult]:
    return [gate(prompt) for gate in GATES]


def format_report(results: list[GateResult]) -> str:
    lines = []
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    lines.append(f"Self-Review: {passed}/{total} gates passed")
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        line = f"  [{mark}] Gate {r.gate} — {r.name}"
        if r.note:
            line += f" — {r.note}"
        lines.append(line)
    return "\n".join(lines)


# ---------- self-test ----------

GOOD_PROMPT = """\
<role>You are a Senior Backend Architect with 12 years of experience in multi-tenant SaaS. Communicate in precise, technical tone.</role>

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
Write intermediate reasoning inside <scratchpad>...</scratchpad> before the final answer.
</detailed_instructions>

<output_format>
Wrap your final answer in <api_design>...</api_design>. Use markdown tables for endpoint enumeration.
</output_format>

<reminders>
- Only answer if you are confident; otherwise state your uncertainty explicitly.
- Think through the problem step by step before producing the final output.
- Deliver only the requested result; omit preamble and closing commentary.
- Review your output for completeness and correctness before returning.
- Prefer the simplest sufficient solution; do not add abstractions beyond what is asked.
- Scope your changes strictly to the task; do not modify unrelated code or content.
</reminders>
"""

BAD_PROMPT = """\
You are a helpful assistant.

## Rules
Don't be too verbose. Don't make stuff up. Don't use jargon.

Analyze this accident report and tell me who is at fault.
"""


def self_test() -> int:
    print("=== GOOD prompt ===")
    good_results = validate(GOOD_PROMPT)
    print(format_report(good_results))
    good_passed = all(r.passed for r in good_results)

    print("\n=== BAD prompt ===")
    bad_results = validate(BAD_PROMPT)
    print(format_report(bad_results))
    bad_failed_count = sum(1 for r in bad_results if not r.passed)

    print("\n=== Self-test summary ===")
    ok = good_passed and bad_failed_count >= 3
    if good_passed:
        print("GOOD prompt: all gates passed (expected) ✓")
    else:
        print("GOOD prompt: SOME gates failed (unexpected) ✗")
    if bad_failed_count >= 3:
        print(f"BAD prompt: {bad_failed_count} gates failed (expected ≥3) ✓")
    else:
        print(f"BAD prompt: only {bad_failed_count} gates failed (expected ≥3) ✗")
    return 0 if ok else 1


# ---------- CLI ----------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", help="prompt file path")
    parser.add_argument("--stdin", action="store_true", help="read from stdin")
    parser.add_argument("--self-test", action="store_true", help="run built-in tests")
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

    results = validate(prompt)
    print(format_report(results))
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
