[![GitHub release](https://img.shields.io/github/v/release/sametbrr/prompt-architect?display_name=tag&sort=semver)](https://github.com/sametbrr/prompt-architect/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/agentskills.io-compatible-blue)](https://agentskills.io)

# Prompt Architect

An Agent Skill that turns any rough idea into a domain-classified, pattern-aware, quality-reviewed expert prompt. Supports input in Turkish and English.

> 🇹🇷 Türkçe için [README.tr.md](README.tr.md)

---

## Quick Start

```bash
git clone https://github.com/sametbrr/prompt-architect.git ~/.claude/skills/prompt-architect
```

Restart your Claude Code session, then trigger naturally:

```
> "Turn this into an expert prompt: build an onboarding strategy for a B2B SaaS"
```

---

## Features

Given a vague input like `"build an onboarding strategy"` or `"design an API for X"`, the skill:

1. **Analyzes** the input — objective, constraints, complexity score (simple / moderate / complex).
2. **Classifies** the domain against a 25-domain taxonomy with TR + EN signal keywords.
3. **Selects 3–6 prompting patterns** (out of 9 UI-compatible ones) appropriate for the task.
4. **Drafts** a refined English prompt using either a compact bullet scaffold or a full XML scaffold.
5. **Self-reviews** the prompt against 8 quality gates.
6. **Executes** the prompt and writes structured output to a file — only if the user asked for it.

The refined prompt body is always written in English for cross-model portability. Section labels follow the user's input language.

---

## Requirements

- Python 3.10+ (for the optional validator script — no pip install needed)
- Claude Code or any [agentskills.io](https://agentskills.io)-compatible agent

---

## Installation

```bash
git clone https://github.com/sametbrr/prompt-architect.git ~/.claude/skills/prompt-architect
```

Claude Code auto-discovers skills under `~/.claude/skills/`. Restart your session after cloning.

---

## Usage

### Modes

| You want… | Say something like… | Mode |
|---|---|---|
| Just the refined prompt | `just the prompt`, `prompt only`, `don't run it` | `prompt_only` (default) |
| Prompt + the actual deliverable | `run it`, `execute it`, `generate the output too` | `prompt_and_execute` |

### Example

**Input:**
> build an onboarding strategy for a B2B SaaS, and run it

**Output (abbreviated):**

```
Detected Domain: Product Growth Strategy
Complexity: moderate
Selected Patterns: Role, XML Structuring, Positive Guidance, CoT, Output Framing

Refined English Prompt:
<role>You are a senior product growth strategist...</role>
<task>Design a B2B SaaS onboarding strategy...</task>
...

Self-Review: 8/8 gates passed
Final Output: Saved to ./onboarding-strategy-output.md
```

---

## Repository layout

```
prompt-architect/
├── SKILL.md                          # Skill entrypoint + 6-stage workflow
├── references/
│   ├── claude-prompting-patterns.md  # 9 UI-compatible patterns
│   ├── quality-gates.md              # 8 self-review gates + case study
│   ├── domain-taxonomy.md            # 25 domains, TR + EN signals
│   ├── mode-inference.md             # prompt_only vs prompt_and_execute
│   └── claude-md-rules.md            # Authoring rules applied dual-layer
├── assets/templates/
│   ├── refined-prompt-xml.tmpl       # Full XML scaffold (default for complex tasks)
│   ├── refined-prompt-compact.tmpl   # Bullet scaffold (simple tasks)
│   └── domain-*.tmpl                 # 6 domain packs
└── scripts/
    └── validate_prompt.py            # Optional 8-gate validator (stdlib only)
```

---

## Key design choices

- **Purpose-built for Claude.** Designed specifically for Claude Code, claude.ai, and Agent Skills-compatible clients, following Anthropic's official prompting practices end-to-end. Refined prompt outputs remain portable to other LLMs.
- **UI-compatible only.** Patterns requiring API-level access (assistant prefill, `thinking`, `stop_sequences`, `tool_choice`) are out of scope. Everything works in a regular chat window.
- **Bilingual input, English body.** The skill accepts Turkish or English input; the refined prompt body is always English for cross-model portability.
- **Minimum-viable patterns.** 3–6 patterns per task, not all 9. Simplicity wins.
- **Don't over-ask.** A clarifying question is allowed only if the input is genuinely unusable. Otherwise, infer and state assumptions.
- **File output discipline.** In execute mode, structured deliverables (>~50 lines) are saved to disk; only summaries print inline.

---

## Validator

```bash
python3 scripts/validate_prompt.py --stdin < draft-prompt.txt
python3 scripts/validate_prompt.py --self-test
```

Pure stdlib, Python 3.10+.

---

## Compatibility

| Tool | Skills path | Notes |
|---|---|---|
| Claude Code | `~/.claude/skills/` or `.claude/skills/` | Global or project-level |
| GitHub Copilot (VS Code) | `.vscode/skills/` | Agent mode required |
| OpenAI Codex | `~/.codex/skills/` | Same SKILL.md format |
| Cursor | `.cursor/skills/` | Project-level |
| Gemini CLI | `~/.gemini/skills/` | |

---

## License

MIT — see [LICENSE](LICENSE).
