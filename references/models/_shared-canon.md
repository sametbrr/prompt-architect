---
last_verified: 2026-07-31
source: platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices (+ thinking, effort, structured-outputs, test-and-evaluate)
---

# Shared Canon — model-independent

Everything here applies to **all current Claude models**, including Fable 5 and Mythos 5. Model-specific deltas live in the per-model profiles; this file is what stays constant. Load it alongside [`_matrix.md`](_matrix.md) on every run.

---

## 1. Core principles

**Be clear and direct.** Treat Claude as a brilliant new employee with no context on your norms. Be specific about the output format and constraints. If you want above-and-beyond behaviour, ask for it — don't expect it to be inferred from a vague prompt. Give sequential steps as a numbered list when order or completeness matters.

> **Golden rule:** show your prompt to a colleague with minimal context and ask them to follow it. If they'd be confused, Claude will be too.

**Give the reason, not just the rule.** Explaining *why* a constraint exists outperforms stating it. `"Your response will be read aloud by a text-to-speech engine, so never use ellipses"` beats `"NEVER use ellipses"` — Claude generalises from the explanation.

**Use examples deliberately.** 3–5 is the sweet spot. Make them *relevant* (mirror the real use case), *diverse* (cover edge cases, vary enough that no unintended pattern is learned), and *structured* (each in `<example>`, all inside `<examples>`).

**Structure with XML tags.** Wrap each content type in its own tag so instructions, context, examples, and variable input can't be confused. Use consistent descriptive names; nest when there's a natural hierarchy.

**Give a role.** One sentence changes behaviour and tone measurably.

## 2. Effort and thinking

`effort` is the primary lever for the intelligence / latency / cost trade-off. Levels: `max`, `xhigh`, `high`, `medium`, `low`. Defaults and recommendations differ per model — see the profile.

Facts that hold across models:

- **`budget_tokens` is gone.** Deprecated on Opus 4.6 / Sonnet 4.6; on Claude 4.7 and later it returns a **400**. Lower `effort`, or cap with `max_tokens`, instead.
- **Higher effort means more unrequested thoroughness** — extra context gathering, extra threads of research, tidying that wasn't asked for. Counter it with targeted instructions rather than blanket defaults: `"Use [tool] when it would enhance your understanding"` beats `"Default to using [tool]"`, and `"If in doubt, use [tool]"` now causes overtriggering.
- **Don't over-prompt for thoroughness.** Tools that undertriggered on older models trigger appropriately now.
- A useful commit-to-an-approach instruction when the model keeps re-deciding:
  > When you're deciding how to approach a problem, choose an approach and commit to it. Avoid revisiting decisions unless you encounter new information that directly contradicts your reasoning.

**Reasoning visibility.** Do not instruct the model to echo, transcribe, or explain its internal reasoning as response text. On Fable 5 this is a hard hazard (see profile); on other models it wastes tokens. Read structured `thinking` blocks from adaptive thinking instead.

## 3. Prefill is gone — what replaces it

Prefilled assistant messages on the final turn are **unsupported from Claude 4.6 onward** and return a **400**. This is not an "API-only" nicety the UI lacks; it is removed. Migration by original purpose:

| Was prefilled to… | Use instead |
|---|---|
| Force JSON/YAML/classification shape | **Structured Outputs** (schema-constrained), or a tool with an enum field for labels. Newer models also match complex schemas reliably when simply told to |
| Skip preambles (`"Here is the summary:\n"`) | A direct instruction: *"Respond directly without preamble. Do not start with phrases like 'Here is…' or 'Based on…'"*, or wrap the answer in XML tags. Strip stragglers in post-processing |
| Steer around bad refusals | Nothing — refusal behaviour is much better; clear prompting in the user message suffices |
| Continue an interrupted response | Move it to the user turn: *"Your previous response was interrupted and ended with [text]. Continue from where you left off."* Or just retry |
| Re-inject context in long chats | Put the reminder in the user turn; for agentic systems, hydrate through tools or during context compaction |

## 4. Output and formatting

Specify the format *and* a wrapper tag when the output will be parsed downstream — the wrapper makes extraction trivial. For strict schemas, prefer Structured Outputs over prose instructions.

Latest models are **more concise and less self-congratulatory** by default, and may skip verbal summaries after tool calls. If you want visibility, ask: *"After completing a task that involves tool use, provide a quick summary of the work you've done."* (Opus 5 is the exception on length — see its profile.)

## 5. Scope containment

Recent models tend to overengineer: extra files, unnecessary abstractions, unrequested flexibility. The canonical counter-block — note that it is deliberately negative-framed, and that this is correct:

> Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused:
> - **Scope:** Don't add features, refactor code, or make "improvements" beyond what was asked.
> - **Documentation:** Don't add docstrings, comments, or type annotations to code you didn't change.
> - **Defensive coding:** Don't add error handling or validation for scenarios that can't happen. Only validate at system boundaries.
> - **Abstractions:** Don't create helpers for one-time operations. Don't design for hypothetical future requirements.

## 6. Guardrails

From `test-and-evaluate/strengthen-guardrails/*` — reach for the matching page when the deliverable warrants it: increase consistency, mitigate jailbreaks, reduce hallucinations, reduce latency, reduce prompt leak, handle streaming refusals. Companion: `develop-tests` for building the eval harness that should exist before prompt-tuning starts.

Standing rule from the overview: **latency and cost problems are usually model-selection problems, not prompt-engineering problems.**

## 7. Model self-knowledge

If the deliverable needs Claude to identify itself or emit model strings:

```
The assistant is Claude, created by Anthropic. The current model is Claude Opus 5.
```
```
When an LLM is needed, please default to Claude Opus 5 unless the user requests
otherwise. The exact model string for Claude Opus 5 is claude-opus-5.
```
