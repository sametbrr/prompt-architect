---
last_verified: 2026-11-02
source: Claude Prompting notebook (claude-prompting-best-practices, thinking, effort, structured-outputs, refusals, per-model guides)
---

# Claude Shared Canon (model-independent)

Everything here applies to **all current Claude models** (Opus 5.5, Sonnet 5.5, Haiku 5.5, Fable/Mythos 5.1, and the legacy 5-generation profiles). Model-specific deltas live in the per-model profiles; this file is what stays constant. Load it with [`_matrix.md`](_matrix.md) whenever the target is a Claude model. OpenAI targets use [`openai/_openai-canon.md`](openai/_openai-canon.md) instead.

---

## 1. Core principles

**Be clear and direct.** Treat Claude as a brilliant new employee with no context on your norms. Be specific about the output format and constraints. If you want above-and-beyond behaviour, ask for it — don't expect it to be inferred from a vague prompt. Give sequential steps as a numbered list when order or completeness matters.

> **Golden rule:** show your prompt to a colleague with minimal context and ask them to follow it. If they'd be confused, Claude will be too.

**Give the reason, not just the rule.** Explaining *why* a constraint exists outperforms stating it. `"Your response will be read aloud by a text-to-speech engine, so never use ellipses"` beats `"NEVER use ellipses"` — Claude generalises from the explanation.

**Use examples deliberately.** 3–5 is the sweet spot. Make them *relevant* (mirror the real use case), *diverse* (cover edge cases, vary enough that no unintended pattern is learned), and *structured* (each in `<example>`, all inside `<examples>`).

**Structure with XML tags.** Wrap each content type in its own tag so instructions, context, examples, and variable input can't be confused. Use consistent descriptive names; nest when there's a natural hierarchy.

**Give a role.** One sentence changes behaviour and tone measurably.

## 2. Request parameters that changed (write prompts that don't depend on them)

| Parameter | Status on current models | What to do instead |
|---|---|---|
| **Adaptive thinking** | Default on all Claude 5-generation models (`thinking: {"type": "adaptive"}`) | Nothing; don't ask for thinking in prose |
| **`effort`** | Primary control for thinking depth, tool-call frequency and token spend: `low`, `medium`, `high`, `xhigh`, `max`. Defaults differ per model | Recommend a level from the profile |
| **`budget_tokens`** | Fixed thinking budgets (`thinking: {"type": "enabled", "budget_tokens": N}`) return a **400** on Claude 5 / 5.1 / 5.5 | Lower `effort`, or cap `max_tokens` |
| **Disabling thinking** | **400** on Opus 5.5 and Fable 5 / 5.1 at any effort; Haiku 5.5 and Opus 5 only at `high` or below; Sonnet 5.5's lowest mode is `between_tools` | Use `low` effort to keep thinking short |
| **Prefill** | A prefilled final assistant turn returns a **400** | See section 3 |
| **Sampling params** | Non-default `temperature`, `top_p` or `top_k` return a **400** on Opus 4.7+, Opus 5+, Sonnet 5+ and Haiku 5.5 | Steer style with instructions and examples |
| **Forced `tool_choice`** | `{"type": "any"}` and `{"type": "tool", "name": …}` **work with adaptive thinking**. They error only with the legacy manual mode (`thinking: {"type": "enabled"}`), which itself now returns a 400. The Haiku 5.5 guide suggests forced `tool_choice` to guarantee a tool call alongside JSON output | Force the tool in the request when a call is mandatory, rather than pleading in prose |
| **Thinking display** | Raw chain of thought is not returned on Fable; `display: "summarized"` gives summaries, `display: "updates"` (beta, `thinking-display-updates-2026-08-18` header; documented in the Opus 5.5 and Sonnet 5.5 guides) gives progress notes | Read those blocks instead of asking for reasoning in text |

Facts that hold across models:

- **Higher effort means more unrequested thoroughness**: extra context gathering, extra research threads, cleanup nobody asked for. Counter it with targeted instructions rather than blanket defaults. `"Use [tool] when it would enhance your understanding"` beats `"Default to using [tool]"`, and `"If in doubt, use [tool]"` now causes overtriggering.
- **Don't over-prompt for thoroughness.** Tools that undertriggered on older models trigger appropriately now.
- A useful commit-to-an-approach instruction when the model keeps re-deciding:
  > When you're deciding how to approach a problem, choose an approach and commit to it. Avoid revisiting decisions unless you encounter new information that directly contradicts your reasoning.

**Reasoning extraction.** Asking the model to reproduce, transcribe or explain its internal chain of thought in the visible response (as a workaround for thinking) is deprecated on current Claude models and can stop the request with `stop_reason: "refusal"` and `stop_details.category: "reasoning_extraction"`. Other refusal categories from the real-time safety classifiers are `cyber`, `bio`, `frontier_llm` and `general_harms`. This is why Gate 10 is a hard fail on every current Claude profile. Asking the model to *think* is fine; asking it to *publish* the thinking is not.

## 3. Prefill is gone — what replaces it

Prefilled assistant messages on the final turn are **unsupported from Claude 4.6 onward** and return a **400** ("Starting with Claude 4.6 models and Claude Mythos Preview, prefilled responses on the last assistant turn are no longer supported", Prompting best practices). It is removed, not merely missing from the UI. Use system prompt instructions, Structured Outputs (`output_config.format`) or a tool enum instead. Migration by original purpose:

| Was prefilled to… | Use instead |
|---|---|
| Force JSON/YAML/classification shape | **Structured Outputs** (schema-constrained), or a tool with an enum field for labels. Newer models also match complex schemas reliably when simply told to |
| Skip preambles (`"Here is the summary:\n"`) | A direct instruction: *"Respond directly without preamble. Do not start with phrases like 'Here is…' or 'Based on…'"*, or wrap the answer in XML tags. Strip stragglers in post-processing |
| Steer around bad refusals | Nothing — refusal behaviour is much better; clear prompting in the user message suffices |
| Continue an interrupted response | Move it to the user turn: *"Your previous response was interrupted and ended with [text]. Continue from where you left off."* Or just retry |
| Re-inject context in long chats | Put the reminder in the user turn; for agentic systems, hydrate through tools or during context compaction |

## 4. Output and formatting

Specify the format *and* a wrapper tag when the output will be parsed downstream — the wrapper makes extraction trivial. For strict schemas, prefer Structured Outputs over prose instructions.

Latest models are **more concise and less self-congratulatory** by default, and may skip verbal summaries after tool calls. If you want visibility, ask: *"After completing a task that involves tool use, provide a quick summary of the work you've done."* (Opus 5 is the exception on length: effort does not shorten its visible answer. See its legacy profile.)

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
The assistant is Claude, created by Anthropic. The current model is Claude Opus 5.5.
```
```
When an LLM is needed, please default to Claude Opus 5.5 unless the user requests
otherwise. The exact model string for Claude Opus 5.5 is claude-opus-5-5.
```
