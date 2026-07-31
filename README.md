[![GitHub release](https://img.shields.io/github/v/release/sametbrr/prompt-architect?display_name=tag&sort=semver)](https://github.com/sametbrr/prompt-architect/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/agentskills.io-compatible-blue)](https://agentskills.io)

[Quick Start](#quick-start) • [Features](#features) • [Installation](#installation) • [Usage](#usage) • [How It Works](#how-it-works) • [Limitations](#limitations)

# Prompt Architect

An Agent Skill that turns any rough idea into a domain-classified, model-aware, quality-reviewed expert prompt. Accepts Turkish and English input.

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

| Feature | What it does |
|---|---|
| Target model resolution | Reads the active Claude model and effort level from the session, or takes an explicit target. Falls back to `opus-5` |
| Model-specific tuning | Injects, omits, or trims prompt blocks per model — Opus 5 gets a conciseness block and no verification instruction, Fable 5 gets a lighter scaffold |
| Domain classification | Matches input against a 25-domain taxonomy with Turkish and English signal keywords |
| Pattern selection | Picks the minimum viable subset of 14 prompting patterns for the task at hand |
| Two scaffolds | Compact bullet body for simple tasks, full XML body for complex ones |
| 11-gate self-review | Seven universal gates plus four that change behaviour with the target model |
| Bilingual input | Turkish or English in; the refined prompt body is always English for portability |
| Optional execution | Generates the deliverable and writes structured output to a file — only when asked |

The refined prompt body is always written in English. Section labels follow the user's input language.

---

## Requirements

- Python 3.10+ — for the two scripts. Standard library only, no `pip install`
- Claude Code, or any [agentskills.io](https://agentskills.io)-compatible agent

Model detection reads the Claude Code session transcript. Other agents still run the skill; they fall back to the default model profile.

---

## Installation

```bash
git clone https://github.com/sametbrr/prompt-architect.git ~/.claude/skills/prompt-architect
```

Claude Code auto-discovers skills under `~/.claude/skills/`. Restart your session after cloning.

For a project-scoped install, clone into `.claude/skills/` inside the repository instead.

### Uninstall

```bash
rm -rf ~/.claude/skills/prompt-architect
```

The skill writes nothing outside its own directory — no hooks, no config files, no PATH changes. Removing the directory is a complete uninstall.

---

## Usage

```bash
# Validate a drafted prompt against the quality gates
python3 scripts/validate_prompt.py --stdin --target-model opus-5 < draft-prompt.txt

# Resolve the active model and effort from the current session
python3 scripts/detect_model.py

# Run built-in checks for either script
python3 scripts/validate_prompt.py --self-test
python3 scripts/detect_model.py --self-test
```

### Modes

| You want… | Say something like… | Mode |
|---|---|---|
| Just the refined prompt | `just the prompt`, `prompt only`, `don't run it` | `prompt_only` (default) |
| Prompt + the actual deliverable | `run it`, `execute it`, `generate the output too` | `prompt_and_execute` |

### Targeting a specific model

The skill resolves the target in this order: an explicit target you name, then the session model, then `opus-5`.

```
> "Write this prompt for Opus 4.8: summarize quarterly financials"
> "Fable 5'e göre ayarla"
```

An unrecognised model falls back to the `opus-5` profile rather than to generic advice — a current flagship profile fits an unknown new model better than no profile at all.

### `validate_prompt.py`

Scores a prompt against the quality gates and exits non-zero on failure.

```bash
python3 scripts/validate_prompt.py draft.txt --target-model fable-5
```

| Flag | Purpose |
|---|---|
| `--stdin` | Read the prompt from standard input |
| `--target-model` | One of `opus-5` (default), `opus-4-8`, `sonnet-5`, `fable-5` |
| `--self-test` | Run the built-in cases, including proof that the inverted gates fire |

Gates 1–6 and 8 always apply. Gates 7, 9, 10 and 11 change behaviour with the target, so the score is `N/N` where `N` is the applicable count.

### `detect_model.py`

Prints the active model as JSON. Local file read only — no network, no cache file, no hook.

```bash
$ python3 scripts/detect_model.py
{"id": "claude-opus-5", "effort": "xhigh", "profile": "opus-5", "source": "session", "transcript": "..."}
```

When no transcript is readable it returns `{"source": "default", "profile": "opus-5"}` and exits 0 — an undetectable model is a normal outcome, not an error.

### Example

**Input:**
> build an onboarding strategy for a B2B SaaS, and run it

**Output (abbreviated):**

```
Target Model: Opus 5 (detected from session · effort: xhigh) — profile: opus-5
Detected Domain: Product Growth Strategy
Complexity: moderate
Selected Patterns: Role, XML Structuring, Positive Guidance, Scope Boundaries,
                   Verbosity Control, Output Framing
Model-Specific Adjustments: conciseness block added; scope_boundaries added;
                   verification instruction deliberately omitted (Opus 5 over-verifies)

Refined English Prompt:
<role>You are a senior product growth strategist...</role>
<task>Design a B2B SaaS onboarding strategy...</task>
...

Self-Review: 11/11 gates passed
Final Output: Saved to ./onboarding-strategy-output.md
```

---

## How It Works

Seven stages run in order. Stage 0 gates everything after it, because the target model decides which patterns apply and which quality gates fire.

| Stage | What happens |
|---|---|
| 0 — Resolve Target Model | Explicit target → session detection → `opus-5`. Loads the routing matrix, the shared canon, and exactly one model profile |
| 1 — Analyze | Objective, constraints, and a complexity score (simple / moderate / complex) |
| 2 — Classify Domain | Single dominant domain from the 25-domain taxonomy, plus a supporting one if it shapes the deliverable |
| 3 — Select Patterns | The minimum viable subset of 14 patterns, filtered by both task and target model |
| 4 — Draft | Compact or XML scaffold, enriched with the matching domain pack |
| 5 — Self-Review | The applicable gates, then one revision pass |
| 6 — Execute | Only in `prompt_and_execute` mode |

Three files load per run regardless of how many models are supported: the routing matrix, the shared canon, and one profile. Context cost stays flat as profiles are added.

### Model profiles

| Profile | Defining behaviour |
|---|---|
| `opus-5` ★ default | Runs long and `effort` does not shorten visible output, so conciseness must be prompted. Self-verifies — adding a verification instruction causes over-verification |
| `opus-4-8` | Calibrates length to task complexity. Start at `xhigh` effort, minimum `high` |
| `sonnet-5` | Closest to `opus-4-8`, but effort already defaults to `high` and the source guide has no subagent section |
| `fable-5` | Covers Mythos 5. Never instruct it to echo its reasoning, and keep the scaffold light — over-prescriptive prompts degrade its output |

---

## Project Structure

```
prompt-architect/
├── SKILL.md                          # Skill entrypoint + 7-stage workflow
├── references/
│   ├── models/
│   │   ├── _matrix.md                # Routing + behavioural matrix (always read)
│   │   ├── _shared-canon.md          # Model-independent canon (always read)
│   │   └── {opus-5,opus-4-8,sonnet-5,fable-5}.md
│   ├── claude-prompting-patterns.md  # 14 patterns + harness-level controls
│   ├── quality-gates.md              # 11 gates, 4 model-conditional
│   ├── domain-taxonomy.md            # 25 domains, TR + EN signals
│   ├── mode-inference.md             # prompt_only vs prompt_and_execute
│   └── claude-md-rules.md            # Authoring rules applied dual-layer
├── assets/templates/
│   ├── refined-prompt-xml.tmpl       # XML scaffold (moderate/complex tasks)
│   ├── refined-prompt-compact.tmpl   # Bullet scaffold (simple tasks, Fable 5)
│   └── domain-*.tmpl                 # 6 domain packs
└── scripts/
    ├── detect_model.py               # Session model + effort resolution
    └── validate_prompt.py            # Quality-gate validator (stdlib only)
```

---

## Limitations

- **Model tuning is Anthropic-only.** Refined prompts remain portable to GPT, Gemini and other models, but carry no provider-specific tuning. When you name a non-Anthropic target, the skill produces the generic form and says so rather than guessing at another vendor's behaviour.
- **Profiles do not refresh themselves.** Each carries a `last_verified` date as provenance; nothing checks or updates it. Anthropic's docs move quickly — 125 URL changes in 12 days during July 2026, with `adaptive-thinking` deleted and prefill turned into a 400. Re-derive the profiles by hand when it matters, and bump the date. In exchange, the skill has zero network dependency at runtime.
- **Model detection is Claude Code specific.** `detect_model.py` reads the Claude Code session transcript. Other agents fall back to the default profile, which is intended behaviour rather than a failure. With several concurrent sessions in one directory, newest-by-modification-time can pick the wrong transcript — name the target explicitly if that matters.
- **Gate checks are heuristic.** Regex and structural scanning, designed to catch common omissions cheaply. Not a substitute for reading the prompt.

---

## Troubleshooting

**The skill doesn't trigger** — Confirm the directory sits at `~/.claude/skills/prompt-architect` with `SKILL.md` at its root, then restart the session. Skills are discovered at startup.

**`detect_model.py` always returns `"source": "default"`** — Either you are not running inside Claude Code, or no transcript exists for the current working directory yet. Name the target model explicitly in your request instead.

**A prompt that passed under v2.x now fails** — Expected. v3.0.0 inverted Gate 7 and added Gates 9–11. A `<scratchpad>` directive, a "review your output" reminder, or a missing scope block will now be flagged. See the [CHANGELOG](CHANGELOG.md) for the reasoning behind each.

**`validate_prompt.py` reports a gate count below 11** — Correct behaviour. Gate 9 applies only to `opus-5` and Gate 11 only to `opus-5` and `fable-5`, so the denominator varies by target.

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
<a href="https://github.com/sametbrr/prompt-architect/issues">Report Bug</a> ·
<a href="https://github.com/sametbrr/prompt-architect/issues">Request Feature</a>
</div>
