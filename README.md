[![GitHub release](https://img.shields.io/github/v/release/sametbrr/prompt-architect?display_name=tag&sort=semver)](https://github.com/sametbrr/prompt-architect/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/agentskills.io-compatible-blue)](https://agentskills.io)

[Quick Start](#quick-start) • [Features](#features) • [Installation](#installation) • [Usage](#usage) • [How It Works](#how-it-works) • [Limitations](#limitations)

# Prompt Architect

An Agent Skill and plugin for Claude Code and OpenAI Codex that turns a rough idea into a domain-classified, model-aware, quality-reviewed expert prompt. It detects which host and model it is running on and tunes the prompt for Claude or OpenAI models. Accepts Turkish and English input.

> 🇹🇷 Türkçe için [README.tr.md](README.tr.md)

---

## Quick Start

```bash
claude plugin marketplace add sametbrr/skill-hub
claude plugin install prompt-architect@skill-hub
```

Then trigger it naturally, in Claude Code or Codex:

```
> "Turn this into an expert prompt: build an onboarding strategy for a B2B SaaS"
> "Write this prompt for GPT-6.1 Sol: add rate limiting to /search"
```

---

## Features

| Feature | What it does |
|---|---|
| Host + model detection | Detects Claude Code or Codex and reads the active model and effort from the local session file. Explicit targets always win |
| Claude profiles | Opus 5.5 (default), Sonnet 5.5, Haiku 5.5, Fable 5.1 / Mythos 5.1, plus legacy Opus 5, Sonnet 5, Opus 4.8 and Fable 5 |
| OpenAI profiles | Codex tiers from the live model catalog: Sol (gpt-6.1-sol, gpt-6-sol, gpt-5.6-sol), Astra (gpt-6-astra), Terra (gpt-6.1-terra, gpt-5.6-terra), Luna (gpt-6-luna, gpt-5.6-luna) |
| Model-specific tuning | Opus 5.5 gets a scope block and no verification line; Sonnet/Haiku 5.5 get completion and real-check lines; Fable 5.1 gets a light scaffold; Codex models get markdown sections with constraints, done-when and a check command |
| Domain classification | Matches input against a 25-domain taxonomy with Turkish and English signal keywords |
| Pattern selection | Picks the minimum subset of 14 prompting patterns for the task |
| Three scaffolds | Compact bullets for simple tasks, XML for complex Claude prompts, markdown sections for Codex |
| 12-gate self-review | Gates that don't apply are reported as N/A and never counted as passes |
| Bilingual input | Turkish or English in; the refined prompt body is always English |
| Optional execution | Generates the deliverable and writes structured output to a file, only when asked |

---

## Requirements

- Python 3.10+ for the two scripts. Standard library only, no `pip install`
- Claude Code, Codex, or any [agentskills.io](https://agentskills.io)-compatible agent

Model detection reads the Claude Code session transcript or the Codex rollout file. Other agents still run the skill; they use an explicit target or the generic profile.

---

## Installation

```bash
# Claude Code
claude plugin marketplace add sametbrr/skill-hub
claude plugin install prompt-architect@skill-hub
# Codex
codex plugin marketplace add sametbrr/skill-hub
codex plugin add prompt-architect@skill-hub
# Manual (any Agent Skills client): copy skills/prompt-architect into ~/.claude/skills/ or ~/.agents/skills/
```

Restart the session after installing; skills are discovered at startup.

### Uninstall

```bash
claude plugin uninstall prompt-architect@skill-hub   # Claude Code
codex plugin remove prompt-architect@skill-hub       # Codex
```

For a manual install, delete the copied `prompt-architect` folder. The skill writes nothing outside the files you ask it to create: no hooks, no config, no cache.

---

## Usage

Run the scripts from `skills/prompt-architect/`:

```bash
# Validate a drafted prompt against the quality gates
python3 scripts/validate_prompt.py --stdin --target-model opus-5-5 < draft-prompt.txt
python3 scripts/validate_prompt.py draft.md --target-model gpt-6.1-sol

# Resolve the active host, model and effort, or an explicit target
python3 scripts/detect_model.py
python3 scripts/detect_model.py --model "Sonnet 5.5"

# Built-in checks
python3 scripts/validate_prompt.py --self-test
python3 scripts/detect_model.py --self-test
```

### Modes

| You want… | Say something like… | Mode |
|---|---|---|
| Just the refined prompt | `just the prompt`, `prompt only`, `don't run it` | `prompt_only` (default) |
| Prompt + the actual deliverable | `run it`, `execute it`, `generate the output too`, or an imperative on the deliverable: `draft the strategy`, `strateji hazırla` | `prompt_and_execute` |

### Targeting a specific model

The skill resolves the target in this order: an explicit target you name, then the detected session model, then the host default (`opus-5-5` in Claude Code, `gpt-sol` in Codex, `generic` elsewhere).

```
> "Write this prompt for Haiku 5.5: classify support tickets"
> "GPT-6 Astra için ayarla"
> "Codex için AGENTS.md kuralı yaz: testleri her zaman çalıştır"
```

Unknown newer Claude models use the Opus 5.5 profile and unknown GPT models the Sol profile, with a note. Other providers (Gemini, Llama…) get the generic, untuned form.

### `detect_model.py`

Prints one JSON object. Local file reads only, no network.

```bash
$ python3 scripts/detect_model.py
{"host": "claude-code", "model": "claude-opus-5-5", "effort": "high", "source": "session",
 "family": "claude", "profile": "opus-5-5",
 "profile_files": ["references/models/_matrix.md", "references/models/_shared-canon.md", "references/models/opus-5-5.md"], ...}
```

Detection order: `PROMPT_ARCHITECT_MODEL` / `PROMPT_ARCHITECT_EFFORT` override → Codex (`CODEX_THREAD_ID`, last `turn_context` in the rollout file, then `config.toml`) → Claude Code (`CLAUDE_CODE_SESSION_ID` transcript under `CLAUDE_CONFIG_DIR` or `~/.claude`, effort from `CLAUDE_EFFORT`) → unknown host. If both hosts' variables are set, the host with the most recently written session file wins. Session files are read from the end and malformed lines are skipped.

### `validate_prompt.py`

| Flag | Purpose |
|---|---|
| `--stdin` | Read the prompt from standard input |
| `--target-model` | A profile (`opus-5-5`, `sonnet-5-5`, `haiku-5-5`, `fable-5-1`, `gpt-sol`, `gpt-astra`, `gpt-terra`, `gpt-luna`, `generic`, legacy stems) or any model ID such as `gpt-5.6-terra`. Default `opus-5-5` |
| `--self-test` | Run the built-in cases |

Each gate reports PASS, FAIL, WARN or N/A. The score is `passed / applicable`; N/A gates are listed but not counted. Exit code 1 when any gate fails.

### Example

**Input:**
> build an onboarding strategy for a B2B SaaS, and run it

**Output (abbreviated):**

```
Target Model: Opus 5.5 (detected · host: claude-code · effort: high) — profile: opus-5-5
Detected Domain: Product Growth Strategy
Complexity: moderate
Selected Patterns: Role, XML Structuring, Positive Guidance, Scope Boundaries,
                   Verbosity Control, Output Framing
Model-Specific Adjustments: scope_boundaries added; tone_preference added;
                   verification line omitted (Opus 5.5)
Refined English Prompt:
<role>You are a senior product growth strategist...</role>
...
Self-Review: 9/9 applicable gates passed (0 warnings, 3 N/A)
Final Output: Saved to ./onboarding-strategy-output.md
```

---

## Configuration

Optional environment variables, read by `detect_model.py`. When set, they override session detection.

| Variable | Effect |
|---|---|
| `PROMPT_ARCHITECT_MODEL` | Target model, by ID or name (e.g. `claude-sonnet-5-5`, `gpt-6-astra`) |
| `PROMPT_ARCHITECT_EFFORT` | Effort level reported with the target (e.g. `high`, `max`) |

---

## How It Works

| Stage | What happens |
|---|---|
| 0 — Resolve Target Model | Explicit target → session detection → host default. Loads the routing matrix, one canon and one profile |
| 1 — Analyze | Objective, constraints, and a complexity score |
| 2 — Classify Domain | Single dominant domain from the 25-domain taxonomy |
| 3 — Select Patterns | The minimum subset of 14 patterns, filtered by task and target |
| 4 — Draft | Compact, XML or markdown scaffold, enriched with the domain pack |
| 5 — Self-Review | The applicable gates, then one revision pass |
| 6 — Execute | Only in `prompt_and_execute` mode |

Three files load per run however many models are supported, so context cost stays flat.

### Model profiles

| Profile | Covers | Defining behaviour |
|---|---|---|
| `opus-5-5` ★ | claude-opus-5-5 | Effort defaults to `medium`; thinking can't be disabled; acts fast across apps, so scope it; no verification line |
| `sonnet-5-5` | claude-sonnet-5-5 | Checks in early at low effort, over-does at `xhigh`/`max`; wants a real check for code |
| `haiku-5-5` | claude-haiku-5-5 | First Haiku with effort; stops early on long agent prompts; needs rule-persistence lines in chat |
| `fable-5-1` | claude-fable-5-1, claude-mythos-5-1 | Light scaffold, never echo reasoning, append-only history, verifier subagents |
| `gpt-sol` ★ | gpt-6.1-sol, gpt-6-sol, gpt-5.6-sol | Workhorse; constraints, done-when and a check command |
| `gpt-astra` | gpt-6-astra | Frontier; intent over step lists |
| `gpt-terra` | gpt-6.1-terra, gpt-5.6-terra | Balanced; distilled return formats for worker subagents |
| `gpt-luna` | gpt-6-luna, gpt-5.6-luna | Fast; one narrow objective, exact format, examples |
| `generic` | everything else | Portable form, no provider tuning |

Legacy Claude profiles (`opus-5`, `sonnet-5`, `opus-4-8`, `fable-5`) live in `references/models/legacy/`.

---

## Project Structure

```
prompt-architect/
├── .claude-plugin/plugin.json        # Claude Code manifest
├── .codex-plugin/plugin.json         # Codex manifest
├── AGENTS.md / CLAUDE.md             # Repo guidance for agents
└── skills/prompt-architect/
    ├── SKILL.md                      # Entry point + 7-stage workflow
    ├── references/
    │   ├── models/
    │   │   ├── _matrix.md            # Routing + matrices (always read)
    │   │   ├── _shared-canon.md      # Claude canon
    │   │   ├── _generic.md           # Untuned portable form
    │   │   ├── {opus-5-5,sonnet-5-5,haiku-5-5,fable-5-1}.md
    │   │   ├── legacy/               # Opus 5, Sonnet 5, Opus 4.8, Fable 5
    │   │   └── openai/               # OpenAI canon + Sol/Astra/Terra/Luna
    │   ├── claude-prompting-patterns.md
    │   ├── quality-gates.md          # 12 gates, N/A handling
    │   ├── domain-taxonomy.md
    │   ├── mode-inference.md
    │   └── working-rules.md          # Generic rules, applied dual-layer
    ├── assets/templates/             # xml, compact, markdown + 6 domain packs
    └── scripts/
        ├── detect_model.py           # Host/model/effort → profile
        └── validate_prompt.py        # Quality-gate validator
```

---

## Limitations

- **Profiles do not refresh themselves.** Each carries a `last_verified` date (2026-11-02) as provenance. Re-derive them when models change. In exchange, the runtime needs no network. **Workaround:** check a profile's `last_verified` date before relying on it, and pick up new releases with `claude plugin marketplace update skill-hub` or `codex plugin marketplace upgrade skill-hub`.
- **Some IDs are inferred.** `claude-opus-5-5` is confirmed from a live session; the Sonnet 5.5, Haiku 5.5 and Fable/Mythos 5.1 IDs follow Anthropic's naming pattern. Profiles mark such facts as unverified. **Workaround:** if your model ID differs, pass it with `--target-model` or `PROMPT_ARCHITECT_MODEL`; any model ID is accepted.
- **OpenAI guidance is thinner than Claude's.** Tier behaviour comes from the Codex model catalog and docs; there is no per-model prompting guide for GPT-6.1. Unverified points are labelled. **Workaround:** check the points the profiles under `references/models/openai/` label as unverified before relying on them.
- **Detection needs Claude Code or Codex.** Other agents get the explicit target or the generic profile. **Workaround:** name the target model in your request, or set `PROMPT_ARCHITECT_MODEL`.
- **Gate checks are heuristic.** Regex and structure scans, not a substitute for reading the prompt. **Workaround:** read the refined prompt before using it, starting with gates reported as WARN or FAIL.

---

## Troubleshooting

**The skill doesn't trigger** — check that the plugin is installed (`claude plugin list` or `codex plugin list`) and restart the session.

**`detect_model.py` returns `"host": "unknown"`** — you are outside Claude Code and Codex, or the session env vars aren't passed to the script. Name the target model, or set `PROMPT_ARCHITECT_MODEL`.

**A prompt that passed under v3 now fails** — expected. v4 makes reasoning-echo a hard fail on every current Claude model, adds Gate 12 for Codex targets, and fails markdown sections on Claude targets. See the [CHANGELOG](CHANGELOG.md).

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

[Report Bug](https://github.com/sametbrr/prompt-architect/issues) · [Request Feature](https://github.com/sametbrr/prompt-architect/issues)

</div>
