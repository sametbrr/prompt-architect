# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-07-31

Reconciled the skill against Anthropic's current prompting canon and made the refined prompt **model-aware**. Major bump: two patterns changed meaning and one quality gate inverted, so prompts produced by 2.x will not all pass 3.0.0's review.

### Added
- **Model profiles** — `references/models/` with `_matrix.md` (routing + behavioural matrix), `_shared-canon.md` (model-independent canon) and one profile each for `opus-5`, `opus-4-8`, `sonnet-5`, `fable-5` (covers Mythos 5). Exactly three files load per run, so context cost stays flat as models are added.
- **Stage 0 — Resolve Target Model**, with precedence: explicit target → session model → `opus-5` default. An unrecognised model falls back to `opus-5` rather than to generic advice.
- **`scripts/detect_model.py`** — reads the active model and effort level straight from the Claude Code session transcript (`message.model`, top-level `effort`). No cache file, no hook, no network. Falls back cleanly to the default profile when no transcript exists.
- **Patterns 10–14** — Intent Framing, Scope Boundaries, Verbosity Control, Delegation Policy, Checkpoint Policy.
- **Gates 9, 10, 11** — No Over-Verification (Opus 5 only), No Reasoning Echo (hard fail on Fable 5), Scope Boundary Present (Opus 5 and Fable 5).
- **`validate_prompt.py --target-model`** — applies the conditional gates for a chosen profile; self-test now proves the inverted gates fire on a v2.2.1-style prompt.
- Template slots `<why>`, `<scope_boundaries>`, `<tone_preference>`; a `Context:` and `Scope:` line in the compact template.
- Output block now reports **Target Model** and **Model-Specific Adjustments**.

### Changed
- **Pattern 4 no longer asks for a `<scratchpad>`.** It is now *Operational Reasoning Sequence* — ordering the steps, not narrating the reasoning. Telling the model to echo its reasoning can trigger the `reasoning_extraction` refusal on Fable 5 and cause elevated fallback to Opus 4.8.
- **Pattern 7 rewritten.** Assistant prefill was described as an "API-only variant"; it is in fact **unsupported from Claude 4.6 onward and returns a 400**. The pattern now documents Anthropic's five migrations, led by Structured Outputs.
- **Gate 7 inverted** — was "numbered steps AND a scratchpad directive", now "numbered steps", with the scratchpad directive a failure under Gate 10.
- **Gate 3 threshold 75% → 60%, with `<scope_boundaries>` exempt.** The old rule would have failed Anthropic's own recommended scope-containment block, which is almost entirely negative — and correctly so.
- The "API-only, out of scope" section became **Harness-level controls** (`effort`, `thinking`, `budget_tokens`, Structured Outputs, prefill, `stop_sequences`), because these now shape how a prompt should be written rather than being irrelevant to it.
- Few-shot guidance 2–5 examples → **3–5**, matching the canon.
- Canonical case study reworked: the old "best prompt" fails Gates 9, 10 and 11 as written.
- `claude-md-rules.md` gained model-conditional adherence guidance — the Rule #4 reminder is dropped on Opus 5 and replaced by real verifier subagents on Fable 5.
- `compatibility:` narrowed: model-specific tuning is **Anthropic-only**. Outputs stay portable to other providers but are not tailored for them, and the skill says so when a non-Anthropic target is named.

### Removed
- `budget_tokens` guidance (returns a 400 on Claude 4.7+; use `effort` or `max_tokens`).
- The claim that request-level `thinking` has an in-context equivalent.

### Notes
- **No auto-refresh.** Profiles carry a `last_verified` date as provenance only; nothing in the skill checks or updates it. Runtime dependency is zero network — local file reads only.
- Source manifest: the *Claude Prompting* NotebookLM notebook (45 sources), verified 2026-07-31.

## [2.2.1] - 2026-06-11

### Fixed
- Gate 7 (`validate_prompt.py`) no longer fails single-step prompts: when a prompt has neither numbered steps nor a `<detailed_instructions>` block, the gate now passes as "Single-step task — N/A" instead of demanding a reasoning directive.
- Gate 3 docstring corrected to match the implemented threshold (≥75%, not ≥80%).
- SKILL.md `changelog:` frontmatter now points to this file (previously referenced a non-existent `references/CHANGELOG.md`).

### Added
- `LICENSE` file (MIT) — the README badge previously pointed at a missing file.

## [2.2.0] - 2026-05-31

### Added
- Turkish README (`README.tr.md`).

### Changed
- Bumped version to 2.2.0; restructured `README.md`.

## [2.1.0] - 2026-05-21

### Added
- Initial public release: domain classification, prompting-pattern selection, refined English prompt drafting, 8-gate self-review (`scripts/validate_prompt.py`), optional execution.
- Reference docs: `domain-taxonomy.md`, `claude-prompting-patterns.md`, `quality-gates.md`, `mode-inference.md`, `claude-md-rules.md`.
- CI: auto-release workflow on SKILL.md version bump.

[3.0.0]: https://github.com/sametbrr/prompt-architect/compare/v2.2.1...v3.0.0
[2.2.1]: https://github.com/sametbrr/prompt-architect/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/sametbrr/prompt-architect/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/sametbrr/prompt-architect/releases/tag/v2.1.0
