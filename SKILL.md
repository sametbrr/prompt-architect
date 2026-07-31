---
name: prompt-architect
description: Architects any user input (in any language) into a structured, domain-aware, model-aware expert prompt — resolves the target Claude model, classifies the domain, selects the right prompting patterns, drafts a refined English prompt tuned to that model's behaviour, runs an 11-gate self-review, and optionally executes the deliverable. Use this skill whenever the user wants to turn a rough idea or request into a professionally engineered prompt, especially when the input involves strategy, UX, product, marketing, technical writing, business analysis, or any specialized domain. Also use it when the user wants a prompt tuned for a specific Claude model ("Opus 5 için prompt", "write this for Sonnet 5", "Fable 5'e göre ayarla"). Trigger this skill when the user says things like "prompt yaz", "refine my prompt", "turn this into an expert prompt", "domain analizi yap", "strateji hazırla", "plan oluştur", or provides a task description in any language and wants it elevated into a structured, actionable expert-level output. Always use this skill when the request involves multi-step domain classification + prompt generation + optional execution.
compatibility: Designed for Claude Code and other Agent Skills-compatible clients. Model-specific tuning covers Anthropic models only (Opus 5, Opus 4.8, Sonnet 5, Fable 5/Mythos 5); refined prompt outputs remain portable to any modern instruction-tuned LLM, but are not tailored for non-Anthropic providers.
metadata:
  version: "3.0.0"
  author: sametbrr@gmail.com
  created: "2026-05-21"
  changelog: CHANGELOG.md
---

# Prompt Architect Skill

Transforms any user input — Turkish or English — into a domain-classified, **model-aware**, pattern-aware, quality-reviewed expert prompt, and optionally executes it. Built on Anthropic's current prompting canon and the user's CLAUDE.md global rules.

Since v3.0.0 the refined prompt is tuned to the **target Anthropic model**: Opus 5 gets an explicit conciseness block and no verification instruction, Fable 5 gets a lighter scaffold and an intent block, Sonnet 5 and Opus 4.8 get the closest thing to the classic shape. See [references/models/_matrix.md](references/models/_matrix.md).

---

## Reference Library (read these when needed)

**Always read** `references/models/_matrix.md` first — it resolves the target model and tells you which single profile to load.

- [references/models/_matrix.md](references/models/_matrix.md) — resolution order, model-ID → profile map, the behavioural matrix. Always read.
- [references/models/_shared-canon.md](references/models/_shared-canon.md) — model-independent principles, effort/thinking mechanics, the prefill replacements, scope containment, guardrails. Always read.
- `references/models/{opus-5,opus-4-8,sonnet-5,fable-5}.md` — load **exactly one**, the resolved target.
- [references/claude-prompting-patterns.md](references/claude-prompting-patterns.md) — 14 patterns. 1–9 are the portable core (role, XML structuring, positive guidance, operational sequencing, few-shot, step ordering, output framing, long-context hierarchy, iterative refinement); 10–14 cover the Claude 5 generation (intent framing, scope boundaries, verbosity control, delegation policy, checkpoint policy). Plus harness-level controls: effort, thinking, Structured Outputs.
- [references/quality-gates.md](references/quality-gates.md) — 11 self-review gates (4 model-conditional) with the insurance-claim case study.
- [references/domain-taxonomy.md](references/domain-taxonomy.md) — 25 domains with TR/EN signal keywords and conflict-resolution table.
- [references/mode-inference.md](references/mode-inference.md) — decision tree and precedence rules for `prompt_only` vs `prompt_and_execute`.
- [references/claude-md-rules.md](references/claude-md-rules.md) — how the 7 CLAUDE.md global rules apply both to the skill flow AND to the refined prompt itself.

Templates:
- [assets/templates/refined-prompt-xml.tmpl](assets/templates/refined-prompt-xml.tmpl) — XML scaffold (default for moderate/complex tasks). Carries `<why>`, `<scope_boundaries>` and `<tone_preference>` slots.
- [assets/templates/refined-prompt-compact.tmpl](assets/templates/refined-prompt-compact.tmpl) — bullet scaffold (simple tasks, 500–1000 chars). **Preferred for Fable 5 targets.**
- `assets/templates/domain-*.tmpl` — 6 domain packs (strategy, engineering, marketing, legal, finance, hr) with role phrasings, default steps, output formats.

Scripts:
- [scripts/detect_model.py](scripts/detect_model.py) — resolves the active model + effort from the Claude Code session transcript. Local file read only; no network, no cache, no hook.
- [scripts/validate_prompt.py](scripts/validate_prompt.py) — runs the quality gates against a draft. Pass `--target-model <profile>` so the conditional gates apply correctly.

---

## Workflow (7 stages)

### Stage 0 — Resolve the Target Model

Run before anything else; every later stage depends on it.

1. **Explicit target wins.** If the user names a model ("Opus 5 için", "target: sonnet-5", "for Opus 4.8"), use it.
2. **Otherwise detect the session model:** `python3 scripts/detect_model.py` → `{"id": "claude-opus-5", "effort": "xhigh", "profile": "opus-5", "source": "session"}`.
3. **Otherwise default to `opus-5`.**

Then read `references/models/_matrix.md` + `_shared-canon.md` + the one matching profile. If the model has no profile (a newer release, an unknown alias), use `opus-5` and say so — a current flagship profile fits an unknown new model better than generic advice.

If the target differs from the session model, state both and build for the **target**. If the user says the prompt will run on GPT, Gemini or another provider, skip profiles entirely, produce the portable generic form, and say that no provider-specific tuning was applied.

**Effort matters too.** When the detected effort is `xhigh` or `max` and the task is narrow, add a scope-containment block regardless of model — higher effort means more unrequested thoroughness.

### Stage 1 — Analyze the Input
- Identify: primary objective, expected output, constraints, implied requirements.
- Compute a **complexity score**: simple / moderate / complex based on (a) input length, (b) number of distinct constraints, (c) presence of multi-step process signals, (d) need for reference data.
- Apply **CLAUDE.md Rule #2** (Think Step by Step): never skip this stage.
- **Belirsizlik kapısı:** Only if input is *completely unusable* — single word, internally contradictory, or zero domain signal — ask one (and only one) clarifying question. Otherwise, infer.

### Stage 2 — Classify the Domain
- Match input against [references/domain-taxonomy.md](references/domain-taxonomy.md) signal keywords (TR + EN).
- Pick the **single dominant domain**. Note a supporting domain only if it materially shapes the deliverable.
- Use the conflict-resolution cheat sheet for ambiguous cases.

### Stage 3 — Select Patterns
- From [references/claude-prompting-patterns.md](references/claude-prompting-patterns.md), pick the patterns this specific task warrants — not all 14.
- Defaults that almost always apply: #1 Role, #2 XML/Tag Structuring, #3 Positive Guidance, #7 Output Framing.
- Add conditionally by **task**: #4 Operational sequencing (multi-step), #5 Few-shot (format/edge-case learning), #6 Step ordering, #8 Long-context hierarchy (bulky data).
- Add conditionally by **target model** — the profile's *Injection checklist* is authoritative:
  - **Opus 5** → #11 Scope Boundaries and #12 Verbosity Control are **required**; #13 Delegation if the harness has subagents; **omit any verification instruction**.
  - **Fable 5 / Mythos 5** → #10 Intent Framing weighted, #11 Scope Boundaries, #14 Checkpoint Policy; **add** interval self-verification; **never** a reasoning-echo directive.
  - **Sonnet 5 / Opus 4.8** → closest to the classic set; verbosity control only if the product needs a fixed style; no delegation cap on Sonnet 5.
- **Prescriptiveness budget.** Apply **CLAUDE.md Rule #5** (Simplest Solution First) with extra force on Fable 5: over-prescriptive scaffolding degrades its output. Pick the minimum that makes the prompt complete.

### Stage 4 — Draft the Refined Prompt
- Pick template by complexity **and target**:
  - **simple**, or **any Fable 5 target** → [assets/templates/refined-prompt-compact.tmpl](assets/templates/refined-prompt-compact.tmpl) (500–1000 chars, bullet body, adherence footer)
  - **moderate or complex** → [assets/templates/refined-prompt-xml.tmpl](assets/templates/refined-prompt-xml.tmpl) (XML body: `<role>` / `<why>` / `<task>` / `<content>` / `<detailed_instructions>` / `<examples>` / `<scope_boundaries>` / `<output_format>` / `<tone_preference>` / `<reminders>`)
  - On Fable 5, reach for XML only when the task genuinely has 4+ distinct content types, and trim `<reminders>` to what the task needs.
- Drop the optional slots that don't apply — an empty `<why>` or `<tone_preference>` is worse than none.
- Enrich with the matching `assets/templates/domain-*.tmpl` for role phrasing, default steps, and output structure.
- Prompt body is **always in English**, regardless of user's input language.

### Stage 5 — Self-Review
- Apply **CLAUDE.md Rule #4** (Self-Review): run the prompt through the applicable gates in [references/quality-gates.md](references/quality-gates.md). Gates 1–6 and 8 always apply; 7, 9, 10 and 11 depend on the target model.
- For complex prompts, invoke `python3 scripts/validate_prompt.py --stdin --target-model <profile>` with the drafted prompt for an automated report.
- If any gate fails, do one revision pass. If a gate still fails after revision, surface it honestly in the `Self-Review:` line.

### Stage 6 — Execute (only if mode is `prompt_and_execute`)

- Use the refined prompt as the internal instruction set; generate the deliverable.
- **File output rule (Claude Code / local CLI context):** If the deliverable is structured content (report, document, plan, code, schema, query, structured analysis) OR exceeds ~50 lines, save it to the current working directory as `<short-slug>-output.<ext>` and only show a concise summary + the saved file path inline. Extensions:
  - `.md` for strategy, plans, reports, prose, mixed content
  - `.ts` / `.py` / `.js` / `.cs` / etc. for code
  - `.sql` for queries, `.json` / `.yaml` for configs/schemas
  - `.txt` only as a last resort
  
  For short, conversational, single-answer outputs (<50 lines, no structure), keep everything inline and do NOT create a file. Never create a file silently — always state the path you wrote to.
- Apply **CLAUDE.md Rule #6** (Don't Touch Unrelated Code): scope strictly to the deliverable; do not refactor or modify adjacent files.

---

## Mode Handling

Infer mode from natural-language signals — see [references/mode-inference.md](references/mode-inference.md) for the full decision tree.

| Signal | Mode |
|---|---|
| No mode signal at all | `prompt_only` (default) |
| Literal `prompt_only`, or phrases like "sadece prompt", "just the prompt", "prompt yaz yeter", "don't run it", "execute etme" | `prompt_only` |
| Literal `prompt_and_execute`, or phrases like "çalıştır", "execute et", "tam çıktı ver", "sonucu da üret", "hem prompt hem sonuç", "run it", "and execute", "do it too", "generate the output too", "uygula" | `prompt_and_execute` |
| Mixed / unclear signals | `prompt_only` — note the ambiguity in **Assumptions / Uncertainty** (CLAUDE.md Rule #7) |

---

## Output Format

Always return results using this exact structure (section labels in the user's input language — Turkish or English):

```
**Target Model:** [model] ([explicit | detected from session · effort: X | default]) — profile: [stem]

**Detected Domain:** [domain name] (supporting: [if any])

**Complexity:** simple | moderate | complex

**Selected Patterns:** [comma-separated subset from the 14 patterns]

**Model-Specific Adjustments:** [what was injected, omitted, or trimmed because of the target — e.g. "conciseness block added; verification instruction deliberately omitted (Opus 5 over-verifies)"]

**Rationale:** [1–2 sentence evidence-based explanation]

**Assumptions / Uncertainty:** [include whenever assumptions were made, mode was ambiguous, or technical details are uncertain — Rule #7]

**Refined English Prompt:**
[compact bullet body OR XML-structured body, per Stage 4]

**Self-Review:** N/N gates passed | gates failed: [list]

**Final Output:** [only if mode is prompt_and_execute]
[full deliverable inline, OR a 2–4 sentence summary + saved file path if written to disk]
```

`N` is the applicable gate count, not always 11 — it depends on the target model.

---

## Domain Examples (selected — see [references/domain-taxonomy.md](references/domain-taxonomy.md) for full list)

- "Onboarding stratejisi hazırla" → **Product Growth Strategy**
- "SEO içerik planı oluştur" → **Content Marketing / SEO Strategy**
- "API tasarla" → **Backend Engineering** (supporting: Security if mentioned)
- "Çalışan bağlılığı programı kur" → **HR Strategy / Org Development**
- "Finansal projeksiyon yap" → **Financial Modeling / Corporate Finance**
- "Hukuki sözleşme taslağı hazırla" → **Legal / Contract Law**

---

## Rules

- Never skip Stage 0 (Resolve Target Model), Stage 1 (Analyze) or Stage 2 (Classify Domain).
- Never produce a generic prompt — make it specific to the detected domain, the target model, and the selected patterns.
- **Never instruct the model to echo its reasoning** (`<scratchpad>`, "show your thinking", "explain your reasoning"). On Fable 5 this risks the `reasoning_extraction` refusal and fallback to Opus 4.8; elsewhere it is wasted tokens.
- **Never add a self-verification instruction on an Opus 5 target** — it verifies its own work, and asking causes over-verification.
- **Never use assistant prefill** as a formatting device — unsupported from Claude 4.6 onward (400). Use Structured Outputs or a wrapper tag.
- Never ask follow-up questions unless the input is **completely unusable** (CLAUDE.md Rule #1 narrowed scope).
- Include the adherence directives in the refined prompt, sized to the target:
  - XML mode: `<reminders>` block. **Trim it on Fable 5 targets** — a long adherence list is exactly the over-prescriptive shape that degrades its output.
  - Compact mode: single-line `Adherence:` footer.
  - The "review your output before returning" bullet is **dropped on Opus 5 targets** (Gate 9).
  - See [references/claude-md-rules.md](references/claude-md-rules.md) for the exact phrasings.
- Keep rationale concise and evidence-based.
- Keep assumptions minimal — but include them whenever genuinely uncertain (Rule #7).
- Supported input languages: **Turkish and English only**. If input is in another language, politely inform the user and ask them to resubmit in Turkish or English.
- Always respond in the **same language the user used** for surrounding text and section labels (Turkish input → Turkish section headers; English input → English section headers).
- The **Refined English Prompt body** is always written in English, regardless of input language.
- Apply CLAUDE.md Rule #3 (Give Only the Result): no preamble like "Here is your refined prompt..." — produce the structured output directly.
