---
name: prompt-architect
description: Architects any user input (in any language) into a structured, domain-aware expert prompt — classifies the domain, selects the right prompting patterns, drafts a refined English prompt, runs an 8-gate self-review, and optionally executes the deliverable. Use this skill whenever the user wants to turn a rough idea or request into a professionally engineered prompt, especially when the input involves strategy, UX, product, marketing, technical writing, business analysis, or any specialized domain. Trigger this skill when the user says things like "prompt yaz", "refine my prompt", "turn this into an expert prompt", "domain analizi yap", "strateji hazırla", "plan oluştur", or provides a task description in any language and wants it elevated into a structured, actionable expert-level output. Always use this skill when the request involves multi-step domain classification + prompt generation + optional execution.
compatibility: Designed for Claude Code and other Agent Skills-compatible clients. Refined prompt outputs are portable to any modern instruction-tuned LLM (Claude, GPT, Gemini).
metadata:
  version: "2.2.1"
  author: sametbrr@gmail.com
  created: "2026-05-21"
  changelog: CHANGELOG.md
---

# Prompt Architect Skill

Transforms any user input — Turkish or English — into a domain-classified, pattern-aware, quality-reviewed expert prompt, and optionally executes it. Built on Anthropic's official Claude prompting practices (UI/chat-compatible only) and the user's CLAUDE.md global rules.

---

## Reference Library (read these when needed)

When working through a request, consult the relevant reference file(s):

- [references/claude-prompting-patterns.md](references/claude-prompting-patterns.md) — 9 UI-compatible prompting patterns (role, XML structuring, positive guidance, in-context CoT, in-context few-shot, step ordering, output framing, long-context hierarchy, iterative refinement). API-only patterns are explicitly out of scope.
- [references/quality-gates.md](references/quality-gates.md) — 8 self-review gates with the insurance-claim case study showing bad → better → best progression.
- [references/domain-taxonomy.md](references/domain-taxonomy.md) — 25 domains with TR/EN signal keywords and conflict-resolution table.
- [references/mode-inference.md](references/mode-inference.md) — decision tree and precedence rules for `prompt_only` vs `prompt_and_execute`.
- [references/claude-md-rules.md](references/claude-md-rules.md) — how the 7 CLAUDE.md global rules apply both to the skill flow AND to the refined prompt itself.

Templates:
- [assets/templates/refined-prompt-xml.tmpl](assets/templates/refined-prompt-xml.tmpl) — XML scaffold (default for complex tasks).
- [assets/templates/refined-prompt-compact.tmpl](assets/templates/refined-prompt-compact.tmpl) — bullet scaffold (simple tasks, 500–1000 chars).
- `assets/templates/domain-*.tmpl` — 6 domain packs (strategy, engineering, marketing, legal, finance, hr) with role phrasings, default steps, output formats.

Optional automation:
- [scripts/validate_prompt.py](scripts/validate_prompt.py) — runs the 8 quality gates against a draft. Useful for self-testing during development.

---

## Workflow (6 stages)

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
- From [references/claude-prompting-patterns.md](references/claude-prompting-patterns.md), pick **3–6 patterns** that this specific task warrants — not all 9.
- Defaults that almost always apply: #1 Role, #2 XML/Tag Structuring, #3 Positive Guidance, #8 Output Framing.
- Add conditionally: #4 CoT (multi-step analysis), #5 Few-shot (format/edge-case learning), #6 Step ordering (when order matters), #7 Long-context hierarchy (bulky data).
- Apply **CLAUDE.md Rule #5** (Simplest Solution First): pick the minimum that makes the prompt complete.

### Stage 4 — Draft the Refined Prompt
- Pick template by complexity:
  - **simple** → [assets/templates/refined-prompt-compact.tmpl](assets/templates/refined-prompt-compact.tmpl) (500–1000 chars, bullet body, adherence footer)
  - **moderate or complex** → [assets/templates/refined-prompt-xml.tmpl](assets/templates/refined-prompt-xml.tmpl) (1500–3000 chars, XML body with `<role>` / `<task>` / `<content>` / `<detailed_instructions>` / `<examples>` / `<output_format>` / `<reminders>`)
- Enrich with the matching `assets/templates/domain-*.tmpl` for role phrasing, default steps, and output structure.
- Prompt body is **always in English**, regardless of user's input language.

### Stage 5 — Self-Review
- Apply **CLAUDE.md Rule #4** (Self-Review): run the prompt mentally through the 8 gates in [references/quality-gates.md](references/quality-gates.md).
- For complex prompts, optionally invoke `python3 scripts/validate_prompt.py --stdin` with the drafted prompt to get an automated report.
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
**Detected Domain:** [domain name] (supporting: [if any])

**Complexity:** simple | moderate | complex

**Selected Patterns:** [comma-separated subset from the 9 patterns]

**Rationale:** [1–2 sentence evidence-based explanation]

**Assumptions / Uncertainty:** [include whenever assumptions were made, mode was ambiguous, or technical details are uncertain — Rule #7]

**Refined English Prompt:**
[compact bullet body OR XML-structured body, per Stage 4]

**Self-Review:** 8/8 gates passed | gates failed: [list]

**Final Output:** [only if mode is prompt_and_execute]
[full deliverable inline, OR a 2–4 sentence summary + saved file path if written to disk]
```

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

- Never skip Stage 1 (Analyze) or Stage 2 (Classify Domain).
- Never produce a generic prompt — make it specific to the detected domain and selected patterns.
- Never ask follow-up questions unless the input is **completely unusable** (CLAUDE.md Rule #1 narrowed scope).
- Always include the adherence directives in the refined prompt:
  - XML mode: full `<reminders>` block (6 bullets covering Rules #1, #7 / #2 / #3 / #4 / #5 / #6).
  - Compact mode: single-line `Adherence:` footer condensing the same six rules.
  - See [references/claude-md-rules.md](references/claude-md-rules.md) for the exact phrasings.
- Keep rationale concise and evidence-based.
- Keep assumptions minimal — but include them whenever genuinely uncertain (Rule #7).
- Supported input languages: **Turkish and English only**. If input is in another language, politely inform the user and ask them to resubmit in Turkish or English.
- Always respond in the **same language the user used** for surrounding text and section labels (Turkish input → Turkish section headers; English input → English section headers).
- The **Refined English Prompt body** is always written in English, regardless of input language.
- Apply CLAUDE.md Rule #3 (Give Only the Result): no preamble like "Here is your refined prompt..." — produce the structured output directly.
