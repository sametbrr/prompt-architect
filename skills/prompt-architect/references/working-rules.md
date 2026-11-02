# Working Rules (dual-layer)

The skill runs on seven generic working rules. They apply in two layers:

- **Layer A (skill flow):** how prompt-architect itself behaves.
- **Layer B (refined prompt):** condensed into adherence lines so the downstream model behaves the same way.

**The user's own rules come first.** If the host loaded global or project instruction files (`AGENTS.md` in Codex, `CLAUDE.md` in Claude Code, or both), follow them. Where they conflict with a rule below, the user's file wins. Don't copy those files into the refined prompt; they already reach the model that reads them.

---

## The seven rules

| Rule | Meaning |
|---|---|
| **Ask only if unusable** | Infer from context. Ask one clarifying question only when the input is unusable |
| **Analyze first** | Understand the objective and constraints before drafting |
| **Result only** | No preamble or closing chit-chat; deliver the result |
| **Self-review** | Check the output for gaps and errors before returning it |
| **Simplest sufficient** | No abstractions or extras beyond what was asked |
| **Stay in scope** | Don't touch files, sections or topics outside the task |
| **State uncertainty** | Don't guess technical details; say what is assumed or unknown |

---

## Layer A: skill flow

| Rule | How the skill applies it |
|---|---|
| Ask only if unusable | No follow-up questions unless the input is a single word, self-contradictory, or has no domain signal. Then ask exactly one, and wait for the answer |
| Analyze first | Stage 1 always runs before drafting |
| Result only | Fixed output sections; no "Here is your refined prompt…" |
| Self-review | Stage 5 runs the applicable quality gates; failed gates get one revision pass |
| Simplest sufficient | Stage 3 picks the minimum pattern set; compact template for simple tasks |
| Stay in scope | Stage 6 writes only the deliverable; no edits to adjacent files |
| State uncertainty | The `Assumptions / Uncertainty` section appears whenever something was assumed, the mode was ambiguous, or a fact is unverified (including unverified profile facts) |

---

## Layer B: refined prompt

### XML mode: `<reminders>` block

```
<reminders>
- Only answer if you are confident; otherwise state your uncertainty explicitly.
- Deliver only the requested result; omit preamble and closing commentary.
- Review your output for completeness and correctness before returning.
- Prefer the simplest sufficient solution; do not add abstractions beyond what is asked.
- Scope your changes strictly to the task; do not modify unrelated code or content.
</reminders>
```

### Compact mode: one-line footer

```
Adherence: deliver only the result; state any uncertainty explicitly; prefer the simplest sufficient solution; do not modify unrelated scope; review your output before returning.
```

### Markdown mode (OpenAI / Codex targets)

The adherence lines go into `## Constraints`, `## Done when` and `## Output`, not into a reminders list. Replace "review your output" with a concrete check: *"Run `<check command>` and report the result."* Skip "result only" and "think step by step": the Codex harness already sets the writing style and reasoning is internal.

### Model-conditional adjustments

| Target | Adjustment |
|---|---|
| **Opus 5.5, legacy Opus 5** | **Drop the self-review bullet.** Opus 5 verifies on its own and an instruction causes over-verification (Gate 9 fails on Opus 5, warns on Opus 5.5) |
| **Sonnet 5.5, Haiku 5.5** | Keep self-review, and for code changes make it concrete: run the tests, type-checker or build before reporting done. Add the completion line at `low`/`medium` effort |
| **Fable 5.1, legacy Fable 5** | **Trim the block** to the uncertainty bullet plus one or two the task needs. A long adherence list is the over-prescriptive shape that degrades Fable output. Self-review becomes interval checks with fresh-context verifier subagents |
| **OpenAI profiles** | Markdown mode above |
| **Generic** | Full block; no provider-specific additions |

**Never satisfy "analyze first" with a reasoning-echo directive.** No `<scratchpad>`, no "show your reasoning". Asking the model to think is fine; asking it to write its thinking into the answer can trip the `reasoning_extraction` refusal on current Claude models. Gate 10 enforces this.

---

## Mapping reference

| Rule | XML reminder bullet | Compact footer phrase |
|---|---|---|
| State uncertainty | "Only answer if you are confident; otherwise state your uncertainty explicitly." | "state any uncertainty explicitly" |
| Result only | "Deliver only the requested result; omit preamble and closing commentary." | "deliver only the result" |
| Self-review | "Review your output for completeness and correctness before returning." | "review your output before returning" |
| Simplest sufficient | "Prefer the simplest sufficient solution; do not add abstractions beyond what is asked." | "prefer the simplest sufficient solution" |
| Stay in scope | "Scope your changes strictly to the task; do not modify unrelated code or content." | "do not modify unrelated scope" |

`validate_prompt.py` looks for the uncertainty phrasing as Gate 8's guard. The self-review phrasing is what Gate 9 matches on Opus targets, where it counts against the prompt.
