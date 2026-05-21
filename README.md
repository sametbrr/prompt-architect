# Prompt Architect

An Agent Skill that turns any rough idea into a domain-classified, pattern-aware, quality-reviewed expert prompt. Optionally executes the prompt and writes the deliverable to disk. Supports input in Turkish and English.

**Purpose-built for Claude.** This skill is designed specifically for the Claude family (Claude Code, claude.ai, and Agent Skills-compatible clients) and follows Anthropic's official prompting practices end-to-end — taxonomy, patterns, quality gates, and adherence rules. Refined prompt outputs remain portable to other instruction-tuned LLMs, but the skill's internal workflow is tuned for Claude.

---

## What it does

Given a vague input like `"build an onboarding strategy"` or `"design an API for X"`, the skill:

1. **Analyzes** the input — objective, constraints, complexity score (simple / moderate / complex).
2. **Classifies** the domain against a 25-domain taxonomy with TR + EN signal keywords.
3. **Selects 3–6 prompting patterns** (out of 9 UI-compatible ones) appropriate for the task.
4. **Drafts** a refined English prompt using either a compact bullet scaffold or a full XML scaffold.
5. **Self-reviews** the prompt against 8 quality gates.
6. **Executes** the prompt and writes structured output to a file — only if the user asked for it.

The refined prompt body is always written in English so it stays portable across Claude, GPT, Gemini, and other instruction-tuned LLMs. Section labels around it follow the user's input language.

---

## Quick start

### Install (Claude Code)

```bash
git clone https://github.com/<your-username>/prompt-architect.git ~/.claude/skills/prompt-architect
```

That's it. Claude Code auto-discovers skills under `~/.claude/skills/`. Restart your session and the skill becomes available.

### Trigger phrases

The skill fires on natural-language triggers (no slash command required):

- `refine my prompt`, `turn this into an expert prompt`, `write a prompt for…`
- `do a domain analysis`, `build a strategy`, `create a plan`
- Or just describe a task and ask for it to be elevated

### Modes

| You want… | Say something like… | Mode |
|---|---|---|
| Just the refined prompt | `just the prompt`, `prompt only`, `don't run it` | `prompt_only` (default) |
| Prompt + the actual deliverable | `run it`, `execute it`, `generate the output too`, `do it as well` | `prompt_and_execute` |

---

## Example

**Input:**
> build an onboarding strategy for a B2B SaaS, and run it

**Output (abbreviated):**

```
**Detected Domain:** Product Growth Strategy

**Complexity:** moderate

**Selected Patterns:** Role, XML Structuring, Positive Guidance, CoT, Output Framing

**Rationale:** Multi-step strategic deliverable for a defined audience (B2B SaaS),
benefits from explicit reasoning steps and structured output.

**Refined English Prompt:**
<role>You are a senior product growth strategist...</role>
<task>Design a B2B SaaS onboarding strategy...</task>
...

**Self-Review:** 8/8 gates passed

**Final Output:** Saved to ./onboarding-strategy-output.md (full deliverable inside).
```

---

## Repository layout

```
prompt-architect/
├── SKILL.md                          # Skill entrypoint + 6-stage workflow
├── references/                       # Knowledge base — read on demand
│   ├── claude-prompting-patterns.md  # 9 UI-compatible patterns
│   ├── quality-gates.md              # 8 self-review gates + case study
│   ├── domain-taxonomy.md            # 25 domains, TR + EN signals
│   ├── mode-inference.md             # prompt_only vs prompt_and_execute
│   ├── claude-md-rules.md            # Authoring rules applied dual-layer
│   └── CHANGELOG.md
├── assets/templates/                 # Drafting scaffolds
│   ├── refined-prompt-xml.tmpl       # Full XML scaffold (default complex)
│   ├── refined-prompt-compact.tmpl   # Bullet scaffold (simple tasks)
│   └── domain-*.tmpl                 # 6 domain packs
└── scripts/
    └── validate_prompt.py            # Optional 8-gate validator (stdlib only)
```

---

## Key design choices

- **UI-compatible only.** Patterns that require API-level access (assistant prefill, request-level `thinking`, `stop_sequences`, `tool_choice`) are explicitly out of scope. Everything here works in a regular chat window.
- **Bilingual input, English body.** The skill accepts Turkish or English input and mirrors section labels in the user's language; the refined prompt body is always written in English for cross-model portability.
- **Minimum-viable patterns.** The skill picks 3–6 patterns per task, not all 9. Simplicity wins.
- **Don't over-ask.** A clarifying question is allowed only if the input is genuinely unusable (single word, internally contradictory, zero domain signal). Otherwise, infer and state assumptions.
- **File output discipline.** In execute mode, structured deliverables (>~50 lines or document-shaped content) are saved to disk with a short slug; only summaries print inline.

---

## Validator (optional)

For automated checks against the 8 gates:

```bash
python3 scripts/validate_prompt.py --stdin < draft-prompt.txt
python3 scripts/validate_prompt.py --self-test
```

Pure stdlib, Python 3.10+.

---

## Compatibility

- **Primary:** Claude Code and any Agent Skills-compatible client.
- **Portable output:** The refined English prompt is plain text / XML — paste it into any modern instruction-tuned LLM.

---

## Versioning

SemVer. See [references/CHANGELOG.md](references/CHANGELOG.md). Current: **2.0.0** (skill renamed from `prompt-refiner`; workflow and outputs preserved).

---

## License

MIT.

---

## Sources

The full source library used while building this skill is available as a NotebookLM notebook — you can browse, query, and chat with the underlying documents directly:

**[Prompt Architect — Source Notebook (NotebookLM)](https://notebooklm.google.com/notebook/a491d060-7049-4279-8c37-f0e6ad58fc67)**

Primary sources include:

- *Prompting 101 | Code w/ Claude* — primary structural source (5-component prompt model).
- Anthropic Claude API docs — prompt engineering overview and best practices.
- `anthropics/prompt-eng-interactive-tutorial` repo.
