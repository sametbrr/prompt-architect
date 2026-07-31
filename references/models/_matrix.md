---
default_profile: opus-5
last_verified: 2026-07-31
source: Anthropic platform docs — build-with-claude/prompt-engineering/* and about-claude/models/*
---

# Model Routing Matrix

Read this file on **every** run. Then load exactly two more files: [`_shared-canon.md`](_shared-canon.md) and the one profile that matches the resolved target model. Never load all profiles — context cost stays flat as models are added.

Scope: **Anthropic models only.** Refined prompts remain portable to other providers, but this skill does not tailor for them. See [Non-Anthropic targets](#non-anthropic-targets).

---

## Resolution order

1. **Explicit target** — the user names a model ("Opus 5 için", "target: sonnet-5", "for Claude Opus 4.8"). Always wins.
2. **Session model** — `python3 scripts/detect_model.py` reads the live Claude Code transcript and returns `{"id": ..., "effort": ...}`.
3. **Default** — `opus-5`.

If the resolved model has no profile below (a newer release, an unfamiliar alias), use **`opus-5`** and say so in the output. A current flagship profile is a closer fit for an unknown new model than generic advice is.

When the target differs from the session model, state both and build for the **target**.

## Model ID → profile

| Matches | Profile |
|---|---|
| `claude-opus-5*` | [`opus-5.md`](opus-5.md) ★ default |
| `claude-opus-4-8*` | [`opus-4-8.md`](opus-4-8.md) |
| `claude-sonnet-5*` | [`sonnet-5.md`](sonnet-5.md) |
| `claude-fable-5*`, `claude-mythos-5*`, `claude-mythos-preview` | [`fable-5.md`](fable-5.md) |
| `claude-opus-4-7*`, `claude-sonnet-4-6*`, `claude-haiku-4-5*`, anything older | `_shared-canon.md` only — the per-model deltas below do not apply |
| anything else | `opus-5.md` + a note that no profile matched |

A trailing `[1m]` marks the 1M-token context variant. It changes the context budget, not the prompting behaviour — strip it before matching.

---

## The matrix

| Axis | **Opus 5** ★ | **Opus 4.8** | **Sonnet 5** | **Fable 5 / Mythos 5** |
|---|---|---|---|---|
| **Verbosity default** | Longer than prior Opus models. **Effort does not reliably shorten visible output** | Calibrates length to judged task complexity | Calibrates length to judged task complexity | Long turns by default |
| **→ inject** | Conciseness block **required**, plus a short `<tone_preference>` reminder near the end | Only if the product needs a fixed style | Same; **positive examples beat negative instructions** | "Lead with the outcome" block; forbid fragment/arrow-chain compression |
| **Effort** | Thinking on by default; can be disabled only at `high` or below | **Start at `xhigh`**; minimum `high` for intelligence-sensitive work; `max` can overthink | Defaults to `high`; raise to `xhigh` for the hardest coding/agentic work | `high` default, `xhigh` for capability-sensitive; low effort still strong |
| **Self-verification** | **Do not add** verification instructions — it already verifies, and telling it to causes over-verification | Normal | Normal | **Add explicitly** — interval checks with fresh-context verifier subagents |
| **Reasoning echo** | Avoid | Tolerated | Tolerated | **Forbidden** — triggers the `reasoning_extraction` refusal category and elevated fallback to Opus 4.8 |
| **Subagent delegation** | Delegates readily → cap it | Cap it | No guidance in source | Parallel subagents supported → give boundaries |
| **Instruction style** | Explicit scope block (it can widen a task on its own) | Enumerating behaviours is fine | Positive examples over negative instructions | **Brief instruction beats enumeration**; over-prescriptive scaffolding degrades output |
| **Prefill** | Unsupported (400 on 4.6+) | Unsupported | Unsupported | Unsupported |

## Effort as a second axis

`detect_model.py` also returns the session `effort` level. Where a profile's guidance changes with effort, the profile says so. The recurring pattern: **higher effort increases unrequested thoroughness** — more context gathering, more tidying, more refactoring beyond the ask. When the detected effort is `xhigh` or `max` and the task is narrow, add a scope-containment block regardless of model.

## Non-Anthropic targets

If the user says the prompt will run on GPT, Gemini, or another provider, skip model profiles entirely and produce the portable generic form. State plainly in the output that no provider-specific tuning was applied. Do not guess at another vendor's behavioural quirks from Anthropic's docs.

## Freshness

`last_verified` above is **provenance, not behaviour** — nothing in the skill refreshes these files or checks their age. Anthropic's docs move fast (a measured 125 URL changes in 12 days during July 2026; `adaptive-thinking` deleted; prefill turned into a 400). Re-derive these profiles by hand when it matters to you, and bump the date.

Source manifest: the *Claude Prompting* NotebookLM notebook (45 sources). `notebooklm source list -n a491d060 --json` prints the current URL list; appending `.md` to any `platform.claude.com` doc URL returns clean markdown.
