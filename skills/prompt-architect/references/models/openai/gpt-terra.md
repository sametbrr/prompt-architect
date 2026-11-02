---
model: GPT Terra tier (balanced)
model_ids: [gpt-6.1-terra, gpt-5.6-terra]
last_verified: 2026-11-02
source: codex debug models catalog (codex-cli 0.166.0); ChatGPT Learn notebooks
---

# Profile: GPT Terra (balanced)

The Codex docs describe Terra as balancing strong reasoning with lower cost: practical everyday coding and routine engineering, and agents that favour speed and cost over depth, such as read-heavy scans, large-file reviews, and parallel worker subagents that return distilled summaries.

| Model | Catalog description | Default effort | Levels | Context |
|---|---|---|---|---|
| `gpt-6.1-terra` | GPT-6.1 Terra Codex model | `low` | low…max, **ultra** | 500k (max 872k) |
| `gpt-5.6-terra` | Older balanced model for straightforward work | `medium` | low…max, **ultra** | 272k (max 872k) |

---

## Injection checklist

| Section | Action |
|---|---|
| Goal | Concrete and bounded |
| Constraints | **Required** |
| Done when | **Required** (both modes) |
| Verification | **Required** when code changes |
| Output | **Specify a distilled return format** when Terra runs as a worker subagent (for example, "return a list of file:line findings, at most 10, no prose") so the parent gets a summary instead of a dump |
| Exploration mode | For scans: "stay in exploration mode, prefer targeted reads, make no code changes" |

## Guidance

- **Effort.** `medium` to `high` is the recommended range. gpt-6.1-terra defaults to `low` *(catalog)*; raise it for anything beyond a scan.
- **Large inputs.** gpt-6.1-terra has the 500k window *(catalog)*, which suits large-file reviews. Still point to files with `@path` instead of pasting them.
- **When to move up.** If the task needs open-ended design judgment, note in Assumptions that Sol or Astra fits better.

## Gate implications

Same as [`gpt-sol.md`](gpt-sol.md): 2 and 9 N/A, 10 warning, 11 and 12 required.
