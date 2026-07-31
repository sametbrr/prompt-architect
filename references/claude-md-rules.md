# CLAUDE.md Rules — Dual-Layer Application

The 7 user-global rules from `~/.claude/CLAUDE.md` apply in two layers:

- **Layer A (Skill flow):** Rules shape how the prompt-architect skill itself behaves.
- **Layer B (Refined prompt):** Rules are condensed into the refined prompt so the downstream model also adheres.

---

## The 7 Rules (verbatim)

1. **Ask If Ambiguous:** If any point is unclear, ask before answering.
2. **Think Step by Step:** First think, then write the answer.
3. **Give Only the Result:** No unnecessary explanation — give the result directly.
4. **Self-Review:** After answering, find incomplete/incorrect parts, fix, and return.
5. **Simplest Solution First:** No excessive abstractions. Write only what was asked.
6. **Don't Touch Unrelated Code:** Don't modify files or functions outside the task.
7. **Explicitly State Uncertainty:** Don't guess technical details — say you don't know.

---

## Layer A — Skill Flow Application

| Rule | How the skill applies it |
|---|---|
| #1 Ask If Ambiguous | The skill suppresses follow-up questions UNLESS input is "completely unusable" (one-word, contradictory, or zero domain signal). In that single case, ask one — and only one — clarifying question. |
| #2 Think Step by Step | Stage 1 (Analyze) is mandatory before any output. Never skip to drafting. |
| #3 Give Only the Result | Skill output uses fixed sections (Detected Domain, Rationale, etc.). No preamble, no closing chit-chat. |
| #4 Self-Review | Stage 5 runs the 8 quality gates before returning. Failed gates trigger one revision pass. |
| #5 Simplest Solution First | Stage 3 picks the MINIMUM patterns needed (3–6, not all 9). Compact mode is preferred for simple tasks. |
| #6 Don't Touch Unrelated Code | Stage 6 (Execute mode) — when generating a deliverable, restrict scope strictly to what the prompt asks; do not refactor or modify adjacent code/files. |
| #7 Explicitly State Uncertainty | The `**Assumptions / Uncertainty:**` section is required whenever assumptions were made, mode signals were ambiguous, or technical details are uncertain. |

---

## Layer B — Refined Prompt Application

Every refined prompt (both compact and XML modes) ends with adherence directives that mirror the rules. The downstream model receives these as binding instructions.

### XML mode — `<reminders>` block contains:

```
<reminders>
- Only answer if you are confident; otherwise state your uncertainty explicitly. (Rules #1, #7)
- Think through the problem step by step before producing the final output. (Rule #2)
- Deliver only the requested result; omit preamble and closing commentary. (Rule #3)
- Review your output for completeness and correctness before returning. (Rule #4)
- Prefer the simplest sufficient solution; do not add abstractions beyond what is asked. (Rule #5)
- Scope your changes strictly to the task; do not modify unrelated code or content. (Rule #6)
</reminders>
```

### Compact mode — single-line adherence footer:

```
Adherence: think step-by-step before answering; deliver only the result; state any uncertainty explicitly; prefer the simplest sufficient solution; do not modify unrelated scope; review your output before returning.
```

### ⚠️ Model-conditional adjustments (v3.0.0)

The block above is the **Sonnet 5 / Opus 4.8** form. Two bullets need adjusting on newer targets — see [models/_matrix.md](models/_matrix.md):

| Target | Adjustment |
|---|---|
| **Opus 5** | **Drop the Rule #4 bullet** ("Review your output…" / "review your output before returning"). Opus 5 verifies its own work; instructing it causes over-verification, and **Gate 9 fails on it**. Rule #4 is still honoured — by the model's own behaviour, not by an instruction. The Rule #2 bullet is harmless but redundant (thinking is on by default); dropping it is fine. |
| **Fable 5 / Mythos 5** | **Trim the whole block.** A six-bullet adherence list is the over-prescriptive shape Anthropic warns degrades Fable 5 output. Keep the uncertainty bullet and whichever one or two the task actually needs. Rule #4 goes the other way here: add explicit interval self-verification with fresh-context verifier subagents instead of a reminder bullet. |

Neither adjustment weakens the rules — it changes how they are enforced. Rule #4 on Opus 5 is satisfied by default behaviour; on Fable 5 it is satisfied by a stronger mechanism than a reminder line.

**Never add a reasoning-echo directive** to satisfy Rule #2 — no `<scratchpad>`, no "show your reasoning". "Think through the problem" asks the model to reason; "write your reasoning in tags" asks it to publish that reasoning, which trips the `reasoning_extraction` refusal on Fable 5. Gate 10 enforces the distinction.

---

## Mapping Reference (for templates)

| Rule | XML reminder bullet | Compact footer phrase |
|---|---|---|
| #1 + #7 | "Only answer if you are confident; otherwise state your uncertainty explicitly." | "state any uncertainty explicitly" |
| #2 | "Think through the problem step by step before producing the final output." | "think step-by-step before answering" |
| #3 | "Deliver only the requested result; omit preamble and closing commentary." | "deliver only the result" |
| #4 | "Review your output for completeness and correctness before returning." | "review your output before returning" |
| #5 | "Prefer the simplest sufficient solution; do not add abstractions beyond what is asked." | "prefer the simplest sufficient solution" |
| #6 | "Scope your changes strictly to the task; do not modify unrelated code or content." | "do not modify unrelated scope" |

`validate_prompt.py` greps for the Rule #1/#7 uncertainty phrasing as part of Gate 8's hallucination guard. The Rule #4 phrasing is what **Gate 9** matches on Opus 5 targets — there it is a failure, not a credit.
