# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[2.2.1]: https://github.com/sametbrr/prompt-architect/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/sametbrr/prompt-architect/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/sametbrr/prompt-architect/releases/tag/v2.1.0
