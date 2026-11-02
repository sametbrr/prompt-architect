---
default_profile: opus-5-5
default_profile_openai: gpt-sol
default_profile_unknown_host: generic
last_verified: 2026-11-02
source: Claude Prompting notebook (per-model guides for Opus 5.5, Sonnet 5.5, Haiku 5.5, Fable 5.1); codex-cli 0.166.0 `codex debug models` catalog; ChatGPT Learn notebooks
---

# Model Routing Matrix

Read this file on **every** run. Then read the other files that `scripts/detect_model.py` lists in `profile_files`: one canon and one profile. Never load all profiles; context cost stays flat as models are added.

---

## Resolution order

1. **Explicit target.** The user names a model ("Opus 5.5 için", "for GPT-6.1 Sol", "target: haiku-5-5"). It always wins. Resolve the alias with `python3 <skill-dir>/scripts/detect_model.py --model "<name>"`.
2. **Detected session model.** `python3 <skill-dir>/scripts/detect_model.py` checks, in this order:
   1. `PROMPT_ARCHITECT_MODEL` / `PROMPT_ARCHITECT_EFFORT` override env vars;
   2. **Codex** (`CODEX_THREAD_ID` set): last `turn_context` in the rollout file, then `config.toml`;
   3. **Claude Code** (`CLAUDECODE=1` or `CLAUDE_CODE_SESSION_ID`): last assistant `message.model` in the session transcript (under `CLAUDE_CONFIG_DIR`, then `~/.claude`); effort from `CLAUDE_EFFORT`.
   When both hosts' variables are set, the host whose session file was written most recently wins.
3. **Host default.** Claude Code host with an unreadable model → `opus-5-5`. Codex host → `gpt-sol`. Unknown host → `generic`.

When the target differs from the session model, state both and build for the **target**. A Codex session can target a Claude model and the reverse; the target decides the profile, the host only decides defaults.

## Model ID → profile

Matching is case-insensitive, accepts dots or dashes ("opus-5.5" = "opus-5-5"), and the longest matching prefix wins. A trailing `[1m]` (1M-context variant) is stripped first.

| Matches | Profile | Files |
|---|---|---|
| `claude-opus-5-5*` | [`opus-5-5`](opus-5-5.md) ★ Claude default | `_shared-canon.md` + profile |
| `claude-sonnet-5-5*` | [`sonnet-5-5`](sonnet-5-5.md) | same |
| `claude-haiku-5-5*` | [`haiku-5-5`](haiku-5-5.md) | same |
| `claude-fable-5-1*`, `claude-mythos-5-1*` | [`fable-5-1`](fable-5-1.md) | same |
| `claude-opus-5*` | [`legacy/opus-5`](legacy/opus-5.md) | same |
| `claude-sonnet-5*` | [`legacy/sonnet-5`](legacy/sonnet-5.md) | same |
| `claude-opus-4-8*` | [`legacy/opus-4-8`](legacy/opus-4-8.md) | same |
| `claude-fable-5*`, `claude-mythos-5*`, `claude-mythos-preview` | [`legacy/fable-5`](legacy/fable-5.md) | same |
| older Claude (`claude-opus-4-7`, `claude-haiku-4-5`, 3.x …) | `claude-canon` | `_shared-canon.md` only |
| unknown newer `claude-*` | `opus-5-5` + a note | |
| `gpt-6.1-sol`, `gpt-6-sol`, `gpt-5.6-sol` | [`gpt-sol`](openai/gpt-sol.md) ★ OpenAI default | `openai/_openai-canon.md` + profile |
| `gpt-6-astra` | [`gpt-astra`](openai/gpt-astra.md) | same |
| `gpt-6.1-terra`, `gpt-5.6-terra` | [`gpt-terra`](openai/gpt-terra.md) | same |
| `gpt-6-luna`, `gpt-5.6-luna`, `gpt-reserve` (unverified) | [`gpt-luna`](openai/gpt-luna.md) | same |
| unknown `gpt-*`, `o*`, `codex-*` | `gpt-sol` + a note | |
| anything else (Gemini, Llama, …) | [`generic`](_generic.md) | `_generic.md` only |

Profile IDs for Sonnet 5.5, Haiku 5.5 and Fable/Mythos 5.1 follow Anthropic's naming pattern but are not printed in the guides (**unverified**). `claude-opus-5-5` is confirmed from a live session. OpenAI slugs come from the live catalog.

---

## Claude matrix (current generation)

| Axis | **Opus 5.5** ★ | **Sonnet 5.5** | **Haiku 5.5** | **Fable 5.1 / Mythos 5.1** (Mythos availability details unverified) |
|---|---|---|---|---|
| **Default effort** | `medium` (Opus 5 was `high`) | `high` on API; start `medium` for agentic coding, `medium`/`low` for chat | `medium` | `high`; `medium` ≈ Fable 5 |
| **Thinking off?** | **No**, 400 | Lowest mode `between_tools` (≤ `high`) | Yes at `low`/`medium`/`high`; 400 at `xhigh`/`max` | **No**, 400 |
| **Typical failure** | Acts fast across apps before gathering context; ends long tasks with a progress report rather than finishing | Checks in early at low effort; over-does at `xhigh`/`max` | Stops early; drifts from chat rules | Ends turns early; dense prose; one tool per turn |
| **Verification line** | Omit (carried from Opus 5, unverified) | **Add** for code | **Add** for code | **Add** (verifier subagents, audit claims) |
| **Scope block** | Required | Required | Recommended | Required |
| **Scaffold** | Normal | Normal | Compact for simple tasks | **Light**: compact preferred |
| **Reasoning echo** | Forbidden | Forbidden | Forbidden | Forbidden |

Legacy profiles (Opus 5, Sonnet 5, Opus 4.8, Fable 5) keep their own tables in `legacy/`.

## OpenAI matrix (Codex models, from the catalog)

| Axis | **Sol** ★ | **Astra** | **Terra** | **Luna** |
|---|---|---|---|---|
| **Use for** | Complex coding, analysis, everyday work | Hardest, most ambiguous work | Routine coding, scans, worker subagents | Narrow, repeatable, high-volume tasks |
| **Default effort** | 6.1: `low`; 6: `medium`; 5.6: `low` | `low` | 6.1: `low`; 5.6: `medium` | `medium` |
| **`ultra`** | Yes | Yes | Yes | No |
| **Context** | 500k (6.1) / 272k | 272k | 500k (6.1) / 272k | 272k |
| **Prompt emphasis** | Constraints, done-when, check command | Intent over steps | Distilled return format | Exact format + examples |

All OpenAI profiles: markdown sections are fine, verification is wanted, `model_verbosity` defaults to `low`.

## Effort as a second axis

`detect_model.py` also returns the session `effort`. Higher effort brings more unrequested thoroughness on both families (extra context gathering, cleanup, reviewer subagents). When the effort is `xhigh`, `max` or `ultra` and the task is narrow, add a scope-containment block regardless of model. On Sonnet 5.5 and Haiku 5.5, low effort brings the opposite risk: stopping early. Add the completion line there.

## Freshness

`last_verified` is provenance, not behaviour. Nothing in the skill refreshes these files or checks their age, and the runtime makes no network calls. Re-derive the profiles by hand when it matters (Claude: the *Claude Prompting* NotebookLM notebook; OpenAI: `codex debug models` plus the ChatGPT Learn notebooks) and bump the date.
