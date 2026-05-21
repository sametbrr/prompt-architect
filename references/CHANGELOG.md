# Changelog

All notable changes to the `prompt-architect` skill (formerly `prompt-refiner`). Versioning follows [SemVer](https://semver.org/):
- **MAJOR**: workflow stages change, refined-prompt format breaks downstream consumers, skill renamed, or trigger description shifts meaning
- **MINOR**: new patterns added, new domain in taxonomy, new template, new quality gate (additive)
- **PATCH**: typo fixes, threshold tuning, clarifications, doc-only changes

---

## [2.0.0] — 2026-05-21

### Changed (breaking)
- **Renamed skill** from `prompt-refiner` to `prompt-architect`. Reflects the broader scope: domain classification + pattern selection + quality gating + optional execution, not just refining. Old invocation `/prompt-refiner` no longer works — use `/prompt-architect` or trigger phrases ("prompt yaz", "strateji hazırla", etc.).
- Directory renamed: `~/.claude/skills/prompt-refiner` → `~/.claude/skills/prompt-architect`.
- Skill display title updated: "Prompt Refiner Skill" → "Prompt Architect Skill".
- `description:` field rewritten to lead with "Architects ... — classifies the domain, selects the right prompting patterns, drafts a refined English prompt, runs an 8-gate self-review, and optionally executes the deliverable."

### Unchanged
- All trigger phrases ("prompt yaz", "refine my prompt", "domain analizi yap", "strateji hazırla", "plan oluştur", "turn this into an expert prompt") still fire the skill.
- 6-stage workflow, dual-mode output (compact/XML), 8 quality gates, references, templates, validator — all preserved from 1.0.0.

---

## [1.0.0] — 2026-05-21

### Added
- Modular skill structure: `references/`, `assets/templates/`, `scripts/`.
- `references/claude-prompting-patterns.md` — 9 UI/chat-compatible patterns distilled from Anthropic's "Prompting 101" video and best-practices docs. API-only patterns (assistant prefill, request-level `thinking` parameter, `stop_sequences`, `tool_choice`) explicitly marked out of scope.
- `references/quality-gates.md` — 8 self-review gates with insurance-claim canonical case study.
- `references/domain-taxonomy.md` — 25 domains across Strategy/Product, Marketing, Engineering, Finance/Legal, People/Ops, with TR + EN signal keywords and conflict resolution.
- `references/mode-inference.md` — decision tree + precedence rules for `prompt_only` vs `prompt_and_execute`.
- `references/claude-md-rules.md` — dual-layer application (skill flow + refined prompt) of the 7 CLAUDE.md global rules.
- `assets/templates/refined-prompt-xml.tmpl` — XML scaffold (default for complex tasks, 1500–3000 chars).
- `assets/templates/refined-prompt-compact.tmpl` — bullet scaffold (simple tasks, 500–1000 chars).
- 6 domain templates: strategy, engineering, marketing, legal, finance, hr.
- `scripts/validate_prompt.py` — automated 8-gate validator with `--self-test` mode (stdlib only, Python 3.10+).
- AgentSkills spec frontmatter compliance: `compatibility`, `metadata.version`, `metadata.author`, `metadata.created`.

### Changed
- Workflow expanded from 4 stages (analyze → classify → refine → execute) to 6 stages (added "Select Patterns" before drafting, and "Self-Review" before execute).
- Refined prompt format expanded from single mode (500–1000 char bullet only) to dual mode (compact OR XML structured) chosen by complexity score.
- Section header `Refined English Prompt` now optionally followed by `Self-Review: N/8 gates passed` line.
- Gate 3 (positive guidance ratio) threshold tuned to 75% (accounts for two unavoidable negatives in the standard adherence block from CLAUDE.md Rules #5 and #6).

### Sources
- "Prompting 101 | Code w/ Claude" YouTube — primary structural source (5-component prompt: Task → Content → Detailed Instructions → Examples → Reminders).
- Anthropic Claude API Docs (prompt engineering overview, prompting best practices, console prompting tools).
- `anthropics/prompt-eng-interactive-tutorial` repo.
- User's `~/.claude/CLAUDE.md` (7 global rules).

---

## [0.1.0] — 2026-05-08 *(pre-modular baseline)*

- Single-file `SKILL.md` (5.6 KB).
- 4-stage workflow.
- Single output mode (500–1000 char bullet, no XML).
- No references/, no templates, no validation script.
- TR + EN language handling, file output rule, mode inference table.
