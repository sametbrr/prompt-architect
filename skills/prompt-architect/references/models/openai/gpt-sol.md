---
model: GPT Sol tier (workhorse)
model_ids: [gpt-6.1-sol, gpt-6-sol, gpt-5.6-sol]
role: default OpenAI profile
last_verified: 2026-11-02
source: codex debug models catalog (codex-cli 0.166.0); Codex CLI notebook
---

# Profile: GPT Sol (workhorse) ★ default OpenAI profile

The default for Codex sessions and for unknown OpenAI models. The catalog calls gpt-6.1-sol the "latest workhorse model for coding and everyday work". The Codex docs recommend Sol for complex coding, cybersecurity, writing, deep analysis, and open-ended tasks that need strong verification.

| Model | Catalog description | Default effort | Levels | Context |
|---|---|---|---|---|
| `gpt-6.1-sol` ★ | Latest workhorse | `low` | low…max, **ultra** | 500k (max 872k) |
| `gpt-6-sol` | Previous-generation workhorse | `medium` | low…max, **ultra** | 272k (max 872k) |
| `gpt-5.6-sol` | Older-generation workhorse | `low` | low…max, **ultra** | 272k (max 872k) |

---

## Injection checklist

| Section | Action |
|---|---|
| Goal | One or two sentences |
| Constraints | **Required.** Name what stays untouched |
| Done when | **Required** (both modes) |
| Verification | **Required** when code changes: name the command |
| Output | Say when headings, tables or a schema are needed (the harness defaults to prose) |
| Plan-only line | Add when the user wants a plan or review rather than changes |
| Reasoning-echo directive | Omit |

## Guidance

- **Effort.** gpt-6.1-sol defaults to `low` *(catalog)*. Recommend `medium` for everyday multi-step coding, `high`/`xhigh` for logic tracing, security audits and edge-case review, and `ultra` when the task splits into independent parallel parts. If you recommend `ultra`, add how the work divides and what each part returns.
- **Large context.** The 6.1 models have a 500k window *(catalog)*. Point to files with `@path` instead of pasting them; the agent reads them itself.
- **Tests.** The GPT-6 harness tells the model not to write tests for reversible, low-impact changes. If tests are part of the deliverable, say so.
- **gpt-5.6-sol.** Same prompt shape. Its harness prefers minimal formatting and a conversational tone, so state structure requirements explicitly.

## Gate implications

| Gate | Behaviour on this profile |
|---|---|
| 2 XML isolation | N/A (markdown sections are fine) |
| 9 No over-verification | N/A (verification is wanted) |
| 10 No reasoning echo | Warning |
| 11 Scope boundary | **Required** (a `Constraints`/`Scope` section counts) |
| 12 Completion criteria | **Required** |
