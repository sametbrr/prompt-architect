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

The validate_prompt.py script greps for these phrases as part of Gate 8.
