# prompt-architect — agent guide

Agent Skill + plugin (Claude Code and Codex) that turns rough requests into model-aware expert prompts.

## Layout
- `skills/prompt-architect/SKILL.md`: the skill (body under 500 lines, description at most 1024 chars, no angle brackets).
- `skills/prompt-architect/references/models/`: `_matrix.md` (routing), `_shared-canon.md` (Claude canon), Claude profiles, `legacy/` (superseded Claude profiles), `openai/` (OpenAI canon + tier profiles), `_generic.md`.
- `skills/prompt-architect/scripts/detect_model.py`: host/model/effort detection and the model ID → profile map (single source; `validate_prompt.py` imports it).
- `skills/prompt-architect/scripts/validate_prompt.py`: quality gates; `GATE_RULES` must list every profile.
- `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`: manifests. Keep `version` identical in both and in SKILL.md `metadata.version`.
- `.github/workflows/release.yml`: tags `v<version>` from `.claude-plugin/plugin.json` on push to main.

## Rules
- Host-neutral wording in the skill. No hardcoded `~/.claude/...` paths, no host tool names, no personal rules from any one user.
- Profile facts come from sources (Claude Prompting notebook, `codex debug models`, ChatGPT Learn notebooks). Mark anything else **unverified** and bump `last_verified` when re-deriving.
- Adding a model: add its prefix to `CLAUDE_MAP` / `OPENAI_MAP` in `detect_model.py`, a profile file if behaviour differs, a row in `_matrix.md`, a `GATE_RULES` entry if it is a new profile, and a self-test case.
- Update `CHANGELOG.md` and both READMEs (EN + TR mirror) with every version bump.
- Never commit or push without explicit approval from the maintainer.

## Checks
- `claude plugin validate .`
- `python3 -I skills/prompt-architect/scripts/detect_model.py --self-test`
- `python3 -I skills/prompt-architect/scripts/validate_prompt.py --self-test`
- Codex: install from a local marketplace in an isolated `CODEX_HOME` and confirm `prompt-architect:prompt-architect` appears in `codex debug prompt-input`.
