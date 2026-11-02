---
last_verified: 2026-11-02
source: codex-cli 0.166.0 `codex debug models` catalog (slugs, reasoning levels, defaults, context windows, per-model base instructions); ChatGPT Learn notebooks "Prompting & Agent Configuration" and "Codex CLI & Developer Tools"
---

# OpenAI / Codex canon (model-independent)

Load this with [`../_matrix.md`](../_matrix.md) and exactly one OpenAI profile. It covers what holds for every current Codex model. Facts taken from the model catalog are marked *(catalog)*; anything the sources don't cover is marked **unverified**.

---

## 1. Where the prompt lands

A prompt for a Codex model usually sits on top of a large harness prompt that the model already receives *(catalog: `base_instructions`, 17–22k characters per model)*. That harness already tells the model to:

- act on requests instead of stopping at a plan ("can you…" is treated as an instruction to do the work), persist until the goal is complete, and skip asking permission for reversible or read-only steps;
- write in plain connected prose, lead with the outcome, avoid filler words, and (on GPT-6.x) avoid section headings in conversational answers;
- give the user's explicit instructions precedence over skill or file guidance;
- prefer `rg` for search and `apply_patch` for edits.

Consequences for the refined prompt:

- **Don't restate the harness.** "Be persistent", "don't ask for permission", "use rg" add nothing.
- **State non-action explicitly.** Because the default is to act, a plan-only or review-only request needs a line like *"Deliver the plan only; don't edit files."*
- **Ask for structure when you need it.** The harness pushes prose. If the deliverable needs headings, tables or a fixed schema, say so in the output section.

## 2. Instruction layering (AGENTS.md)

- Persistent guidance belongs in `AGENTS.md`, not in every prompt. Codex reads the global `~/.codex/AGENTS.md` (or `AGENTS.override.md`), then walks from the repository root down to the working directory, checking `AGENTS.override.md` then `AGENTS.md` in each folder. Closer files override broader ones.
- The combined instruction size is capped at 32 KiB by default (`project_doc_max_bytes`). Other filenames can be added with `project_doc_fallback_filenames`.
- Keep AGENTS.md rules short and repo-specific: build, test and lint commands, review expectations, style rules, folder-specific rules. Leave mechanical checks to CI. When the agent repeats a mistake, add a rule.
- When the user asks for "instructions for Codex" that should apply to every session, produce an AGENTS.md section instead of a one-off prompt, and say so.

## 3. Prompt shape

Plain English with markdown headings or bullets works; XML is not required. The four parts the Codex docs name, plus two that make agent runs finish cleanly:

1. **Goal**: what to accomplish, in one or two sentences.
2. **Context**: relevant files (`@path`), sources, background.
3. **Constraints / boundaries**: what must stay untouched, what needs approval. Explicit negatives are expected here ("Do not refactor unrelated files").
4. **Done when**: what finished looks like.
5. **Verification**: the command or check that proves it, for example *"run `npm test --silent` and confirm it passes"*. This is the **opposite** of the Claude Opus 5 habit; Codex guidance asks for it.
6. **Output**: format, length, level of detail.

Use [`assets/templates/refined-prompt-markdown.tmpl`](../../../assets/templates/refined-prompt-markdown.tmpl) for this shape. The XML template still works when the content has many distinct parts or will be parsed downstream. Whether GPT models attend to XML tags as strongly as Claude does is **unverified**.

For tool-connected agents, name the destination and the findings you expect instead of scripting each search. For subagent prompts: explorers "stay in exploration mode, prefer targeted reads, make no code changes"; implementers "make the smallest defensible change and keep unrelated files untouched".

## 4. Reasoning effort and verbosity

`model_reasoning_effort` is set in `config.toml`, in a custom agent file, or per prompt.

| Level | Meaning |
|---|---|
| `low` | Fast, lighter reasoning. Narrow edits, simple extraction |
| `medium` | Balanced default for everyday work |
| `high` | Complex, multi-step problems, logic tracing, security review |
| `xhigh` | Extra depth: detailed code or security review, careful data validation |
| `max` | The most reasoning a single agent run gets; accuracy over speed and cost |
| `ultra` | Goes past one agent: automatically delegates parallel parts to subagents |

Defaults differ per model *(catalog)*; see the profile. `ultra` is listed only for the Sol, Astra and Terra models, not for Luna. A prompt that runs at `ultra` should state how the work splits and what each part returns.

`model_verbosity` (`low` | `medium` | `high`) controls answer length on Responses-API models. Every current Codex model supports it and defaults to `low` *(catalog)*. Ask for more detail in the prompt when you need it. Chat Completions providers ignore the setting.

## 5. Differences from Claude prompting

| Topic | Claude (this skill's Claude canon) | OpenAI / Codex |
|---|---|---|
| Structure | XML tags preferred | Markdown headings or bullets; XML optional |
| Verification line | Omit on Opus 5 / 5.5; add on Sonnet 5.5, Haiku 5.5, Fable 5.1 | **Add**: name the check command and the done criteria |
| Effort levels | `low`…`max` | `low`…`max` plus `ultra` (auto-delegation) |
| Prefill | Removed (400) | Not a technique here; use structured outputs or an explicit format section |
| Reasoning echo | Hard fail (`reasoning_extraction`) | Reasoning stays hidden (`default_reasoning_summary: none`, catalog). Asking for written-out reasoning only adds length; whether it triggers refusals is **unverified**. The validator warns |
| Persistent rules | CLAUDE.md | AGENTS.md (Claude Code can import it with `@AGENTS.md`) |
| Default posture | Varies by model | Acts by default; say "plan only" explicitly |

## 6. Generation deltas (from the catalog's base instructions)

- **GPT-6.x** (gpt-6.1-sol, gpt-6.1-terra, gpt-6-astra, gpt-6-sol, gpt-6-luna): a dedicated autonomy section, prose-first writing rules (no headings in conversational answers, lists only for parallel items), and test restraint: "do not write tests for reversible, low-impact changes". gpt-6-luna goes further: "Do not add or run tests unless the user asks you to test or verify." So a Luna prompt that needs tests must ask for them.
- **GPT-5.6** (gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna share one base prompt): a warmer, personality-led style and "avoid over-formatting". It has an explicit destructive-actions section. Prompts that need tables or headings must ask for them.
- GPT-5.5 retired from Codex on 2026-10-14. Treat it as an unknown OpenAI model (workhorse profile plus a note).

## 7. Writing skills for Codex

If the deliverable is a SKILL.md: front-load trigger words in `description` (Codex spends at most 2% of context, about 8,000 characters, on skill metadata), keep one job per skill, use imperative instructions, and define inputs, outputs and verification steps.
