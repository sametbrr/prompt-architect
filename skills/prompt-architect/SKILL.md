---
name: prompt-architect
description: Turns a rough Turkish or English request into a structured, domain-aware expert prompt tuned to the model that will run it, and delivers the finished work when the request asks for a concrete deliverable. Detects the host (Claude Code or Codex) and active model, loads the matching Claude or OpenAI GPT profile, classifies the domain, drafts an English prompt and runs a quality-gate self-review. Use when the user wants to write, refine or upgrade a prompt, tune one for a specific model (Opus 5.5, Sonnet 5.5, Haiku 5.5, Fable 5.1, GPT-6.1 Sol, GPT-6 Astra, GPT-5.6 Terra, GPT-6 Luna), write instructions for a Claude or Codex agent, or get an expert strategy, plan or analysis, which it returns as finished work, not only a prompt. Triggers include prompt yaz, promptu iyileştir, expert prompta çevir, Opus 5.5 için prompt, Codex için prompt hazırla, strateji hazırla, domain analizi yap, refine my prompt, turn this into an expert prompt, write this for GPT-6.1 Sol.
compatibility: Claude Code and OpenAI Codex plugin; works in any Agent Skills client. Model detection reads local session files (Claude Code transcript, Codex rollout or config.toml); other clients use an explicit target or the generic profile. Profiles cover Claude Opus, Sonnet and Haiku 5.5, Fable 5.1, legacy Claude 5 models, and OpenAI GPT-6.x and GPT-5.6 Codex models. Scripts need Python 3.10+ (standard library only).
metadata:
  version: "4.0.1"
  author: sametbrr@gmail.com
  created: "2026-05-21"
---

# Prompt Architect

Turns Turkish or English input into a domain-classified, **model-aware**, pattern-aware, quality-reviewed expert prompt, and optionally executes it.

The refined prompt is tuned to the **target model**, Claude or OpenAI. Opus 5.5 gets a scope block and no verification line; Sonnet 5.5 and Haiku 5.5 get completion and real-check lines; Fable 5.1 gets a light scaffold; Codex models get markdown sections with constraints, a done-when line and a check command. See [references/models/_matrix.md](references/models/_matrix.md). All paths below are relative to this skill's directory (the folder containing this SKILL.md, written `<skill-dir>` in commands); run scripts by that path, for example `python3 <skill-dir>/scripts/detect_model.py`.

---

## Reference library (read when needed)

- [references/models/_matrix.md](references/models/_matrix.md): resolution order, model ID → profile map, Claude and OpenAI matrices. **Always read.**
- The other files listed in `profile_files` by `scripts/detect_model.py`: one canon plus one profile. Read exactly those, never all profiles:
  - Claude: [references/models/_shared-canon.md](references/models/_shared-canon.md) + `references/models/{opus-5-5,sonnet-5-5,haiku-5-5,fable-5-1}.md` (legacy profiles in `references/models/legacy/`)
  - OpenAI: [references/models/openai/_openai-canon.md](references/models/openai/_openai-canon.md) + `references/models/openai/{gpt-sol,gpt-astra,gpt-terra,gpt-luna}.md`
  - Neither: [references/models/_generic.md](references/models/_generic.md)
- [references/claude-prompting-patterns.md](references/claude-prompting-patterns.md): 14 patterns. 1–9 are the portable core; 10–14 cover the Claude 5 generation (intent framing, scope boundaries, verbosity control, delegation policy, checkpoint policy). Includes notes on OpenAI equivalents and harness-level controls.
- [references/quality-gates.md](references/quality-gates.md): 12 self-review gates, which ones apply per target, and N/A handling.
- [references/domain-taxonomy.md](references/domain-taxonomy.md): 25 domains with TR/EN signal keywords and a conflict-resolution table.
- [references/mode-inference.md](references/mode-inference.md): `prompt_only` vs `prompt_and_execute`.
- [references/working-rules.md](references/working-rules.md): the seven working rules, applied to the skill flow and condensed into the refined prompt.

Templates:
- [assets/templates/refined-prompt-xml.tmpl](assets/templates/refined-prompt-xml.tmpl): XML scaffold, the default for moderate or complex Claude tasks.
- [assets/templates/refined-prompt-compact.tmpl](assets/templates/refined-prompt-compact.tmpl): bullet scaffold for simple tasks (500–1000 chars). Preferred for Fable targets.
- [assets/templates/refined-prompt-markdown.tmpl](assets/templates/refined-prompt-markdown.tmpl): markdown scaffold (Goal / Context / Steps / Constraints / Done when / Output), the default for OpenAI and Codex targets.
- `assets/templates/domain-*.tmpl`: six domain packs (strategy, engineering, marketing, legal, finance, hr).

Scripts (local reads only; no network, cache or hooks):
- [scripts/detect_model.py](scripts/detect_model.py): resolves host, model, effort, profile and the files to read. `--model "<name>"` resolves an explicit target.
- [scripts/validate_prompt.py](scripts/validate_prompt.py): runs the gates against a draft. Pass `--target-model <profile or model id>`.

---

## Working rules

The user's own instruction files come first. If the host loaded `AGENTS.md` (Codex) or `CLAUDE.md` (Claude Code), global or project, follow them; where they conflict with a rule below, they win. Otherwise the skill follows seven rules (details in [references/working-rules.md](references/working-rules.md)):

1. **Ask only if unusable.** Infer from context; ask one question only when the input is unusable.
2. **Analyze first.** Understand objective and constraints before drafting.
3. **Result only.** No preamble or closing chit-chat.
4. **Self-review.** Check the output before returning it.
5. **Simplest sufficient.** Nothing beyond what was asked.
6. **Stay in scope.** Don't touch unrelated files or content.
7. **State uncertainty.** Say what is assumed or unverified; don't guess.

---

## Workflow (7 stages)

### Stage 0: Resolve the target model

Run before anything else; every later stage depends on it.

1. **Explicit target wins.** If the user names a model ("Opus 5.5 için", "for GPT-6.1 Sol", "target: haiku-5-5"), resolve it: `python3 <skill-dir>/scripts/detect_model.py --model "<name>"`.
2. **Otherwise detect the session:** `python3 <skill-dir>/scripts/detect_model.py` →
   `{"host": "codex", "model": "gpt-6.1-sol", "effort": "high", "family": "openai", "profile": "gpt-sol", "profile_files": [...], "source": "session", "note": null}`.
   It checks the `PROMPT_ARCHITECT_MODEL` override, then the host from `CODEX_THREAD_ID` / `CLAUDE_CODE_SESSION_ID` (if both are set, the host with the most recently written session file wins).
3. **Read the files in `profile_files`** (relative to `<skill-dir>`): the matrix, one canon, one profile.
4. **Fallbacks come from the script.** Claude Code host with an unreadable model → `opus-5-5`. Codex → `gpt-sol`. Unknown host or a non-Claude, non-OpenAI target (Gemini, Llama…) → `generic`: the portable form, stating that no provider tuning was applied. Unknown newer Claude or GPT models get the current flagship or workhorse profile plus a `note`; repeat that note in the output.

If the target differs from the session model (a Codex session writing for Claude, or the reverse), state both and build for the **target**. Facts marked *unverified* in a profile go into **Assumptions / Uncertainty** when they affect the prompt.

**Effort matters too.** When the effort is `xhigh`, `max` or `ultra` and the task is narrow, add a scope-containment block regardless of model. On Sonnet 5.5 and Haiku 5.5 at `low`/`medium`, also add the completion line (they can stop early). It never replaces a required scope block: Sonnet 5.5 always gets both.

### Stage 1: Analyze the input
- Identify the primary objective, expected output, constraints and implied requirements.
- Score complexity as simple / moderate / complex from (a) input length, (b) number of distinct constraints, (c) multi-step signals, (d) need for reference data.
- Never skip this stage (working rule 2).
- **Ambiguity gate:** only if the input is *unusable* (a single word, self-contradictory, or no domain signal), ask exactly one clarifying question and wait for the answer. Otherwise infer.

### Stage 2: Classify the domain
- Match the input against [references/domain-taxonomy.md](references/domain-taxonomy.md) signal keywords (TR + EN).
- Pick the **single dominant domain**. Note a supporting domain only if it shapes the deliverable.
- Use the conflict-resolution table for ambiguous cases.

### Stage 3: Select patterns
- From [references/claude-prompting-patterns.md](references/claude-prompting-patterns.md), pick only the patterns this task needs.
- Usual defaults: #1 Role, #2 Structuring (XML for Claude, markdown sections for OpenAI), #3 Positive Guidance, #7 Output Framing.
- Add by **task**: #4 Operational sequence (multi-step), #5 Few-shot (format or edge cases), #6 Step ordering, #8 Long-context hierarchy (bulky data).
- Add by **target**; the profile's *Injection checklist* is authoritative:
  - **Opus 5.5** → #11 Scope Boundaries required, #12 Verbosity only if the product needs a fixed length, #13 Delegation cap if the harness has subagents; **omit verification lines**.
  - **Sonnet 5.5** → #11 required at every effort; plus the completion line at `low`/`medium`, or the stop-and-report line (no unrequested review rounds or reviewer subagents) at `xhigh`/`max`; **add a real-check line** for code.
  - **Haiku 5.5** → completion line, real-check line for code, rule-persistence line for chatbots; compact template for simple tasks.
  - **Fable 5.1** → #10 Intent Framing weighted, #11, #14 Checkpoint Policy, verifier subagents for long runs; **light scaffold**.
  - **OpenAI (Sol, Astra, Terra, Luna)** → markdown sections, Constraints, **Done when**, a check command, an explicit plan-only line when no edits are wanted; examples on Luna, intent over steps on Astra, distilled return format on Terra.
- **Never** add a reasoning-echo directive on any target.
- **Prescriptiveness budget:** pick the minimum that makes the prompt complete (working rule 5), with extra force on Fable.

### Stage 4: Draft the refined prompt
- Pick the template by target and complexity:
  - **OpenAI target** → [assets/templates/refined-prompt-markdown.tmpl](assets/templates/refined-prompt-markdown.tmpl). Use XML only if the output will be parsed downstream.
  - **Simple task, or a Fable target with fewer than four distinct content types** → [assets/templates/refined-prompt-compact.tmpl](assets/templates/refined-prompt-compact.tmpl).
  - **Moderate or complex Claude task** → [assets/templates/refined-prompt-xml.tmpl](assets/templates/refined-prompt-xml.tmpl) (`<role>` / `<why>` / `<task>` / `<content>` / `<detailed_instructions>` / `<examples>` / `<scope_boundaries>` / `<output_format>` / `<tone_preference>` / `<reminders>`). Fable targets use XML only with four or more distinct content types, and with a trimmed `<reminders>`.
- Drop optional slots that don't apply; an empty `<why>` is worse than none.
- Enrich with the matching `assets/templates/domain-*.tmpl`.
- If the user wants standing instructions for an agent rather than a one-off prompt, produce an `AGENTS.md` section (Codex) or a `CLAUDE.md` section (Claude Code) and say which.
- The prompt body is **always in English**, whatever the input language.

### Stage 5: Self-review
- Run the applicable gates in [references/quality-gates.md](references/quality-gates.md) (working rule 4). The target decides which of gates 2 and 9–12 apply.
- For complex prompts, run `python3 <skill-dir>/scripts/validate_prompt.py --stdin --target-model <profile>` on the draft.
- If a gate fails, do one revision pass. If it still fails, report it honestly in the `Self-Review:` line. N/A gates are never counted as passed.

### Stage 6: Execute (only in `prompt_and_execute` mode)
- Use the refined prompt as the internal instruction set and generate the deliverable.
- **File output rule (when you can write local files):** if the deliverable is structured (report, document, plan, code, schema, query, structured analysis) or longer than ~50 lines, save it in the current working directory as `<short-slug>-output.<ext>` and show only a short summary plus the path. Extensions: `.md` for strategy, plans, reports and prose; `.ts` / `.py` / `.js` / `.cs` etc. for code; `.sql` for queries; `.json` / `.yaml` for configs and schemas; `.txt` as a last resort.
- Keep short conversational answers (under ~50 lines, no structure) inline. Never create a file silently; always state the path.
- Stay strictly within the deliverable (working rule 6).

---

## Mode handling

Infer the mode from natural language; see [references/mode-inference.md](references/mode-inference.md).

| Signal | Mode |
|---|---|
| Imperative on a concrete deliverable: "strateji hazırla", "onboarding planı hazırla", "domain analizi yap", "draft the contract", "give me the plan" | `prompt_and_execute`: deliver the strategy or analysis itself, with the prompt shown above it |
| No mode signal (e.g. "prompt yaz", "refine my prompt", a bare topic) | `prompt_only` (default) |
| Literal `prompt_only`, or "sadece prompt", "just the prompt", "prompt yaz yeter", "don't run it", "execute etme" | `prompt_only` |
| Literal `prompt_and_execute`, or "çalıştır", "execute et", "tam çıktı ver", "sonucu da üret", "hem prompt hem sonuç", "run it", "and execute", "do it too", "generate the output too", "uygula" | `prompt_and_execute` |
| Mixed or unclear | `prompt_only`, noting the ambiguity under **Assumptions / Uncertainty** |

---

## Output format

Always use this structure, with section labels in the user's language (Turkish or English):

```
**Target Model:** [model] ([explicit | detected · host: claude-code/codex · effort: X | host default | generic]) — profile: [stem] — files: [profile_files]

**Detected Domain:** [domain] (supporting: [if any])

**Complexity:** simple | moderate | complex

**Selected Patterns:** [subset of the 14 patterns]

**Model-Specific Adjustments:** [what was injected, omitted or trimmed for this target, e.g. "Done when + pytest command added; markdown sections (Codex)" or "verification line omitted (Opus 5.5)"]

**Rationale:** [1–2 evidence-based sentences]

**Assumptions / Uncertainty:** [whenever something was assumed, the mode was ambiguous, a profile fact is unverified, or the script returned a note]

**Refined English Prompt:**
[compact, XML or markdown body, per Stage 4]

**Self-Review:** P/A applicable gates passed (W warnings, K N/A) | failed: [gates]

**Final Output:** [only in prompt_and_execute mode]
[the deliverable inline, or a 2–4 sentence summary plus the saved file path]
```

---

## Domain examples (full list in [references/domain-taxonomy.md](references/domain-taxonomy.md))

- "Onboarding stratejisi hazırla" → **Product Growth Strategy**
- "SEO içerik planı oluştur" → **Content Marketing / SEO Strategy**
- "API tasarla" → **Backend Engineering** (supporting: Security if mentioned)
- "Çalışan bağlılığı programı kur" → **HR Strategy / Org Development**
- "Finansal projeksiyon yap" → **Financial Modeling / Corporate Finance**
- "Hukuki sözleşme taslağı hazırla" → **Legal / Contract Law**

---

## Rules

- Never skip Stage 0, Stage 1 or Stage 2.
- Never produce a generic prompt for a known target: make it specific to the domain, the target profile and the selected patterns. Say which profile and files you used.
- **Never instruct the model to echo its reasoning** (`<scratchpad>`, "show your thinking", "explain your reasoning"). On current Claude models it can trigger the `reasoning_extraction` refusal; elsewhere it wastes tokens.
- **Opus 5.5 / Opus 5:** no self-verification instruction. **Sonnet 5.5, Haiku 5.5, OpenAI:** name a real check instead of "review your work". **Fable 5.1:** verifier subagents for long runs.
- **Never use assistant prefill** for Claude 4.6+ targets (400), and no non-default `temperature` / `top_p` / `top_k` on Opus 4.7+, Opus 5+, Sonnet 5+ or Haiku 5.5 (400). Use Structured Outputs, a wrapper tag or an explicit output section.
- Don't ask follow-up questions unless the input is unusable (working rule 1).
- Include adherence lines sized to the target (exact phrasings in [references/working-rules.md](references/working-rules.md)):
  - XML mode: a `<reminders>` block, trimmed hard on Fable targets.
  - Compact mode: one `Adherence:` line.
  - Markdown mode (OpenAI): adherence lives in Constraints, Done when and Output.
- Keep the rationale short and evidence-based; keep assumptions minimal but always state real uncertainty.
- Supported input languages: **Turkish and English only.** For other languages, say so politely and ask the user to resubmit in Turkish or English.
- Reply in the **user's language** for surrounding text and section labels. The **Refined English Prompt** body is always English.
- No preamble such as "Here is your refined prompt…"; produce the structured output directly (working rule 3).
