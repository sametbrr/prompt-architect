---
model: Claude Opus 4.8
model_ids: [claude-opus-4-8]
last_verified: 2026-07-31
source: platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8
---

# Profile — Claude Opus 4.8

The closest model to the skill's original (Opus 4.7-era) assumptions. Fewer overrides than Opus 5 or Fable 5.

---

## Injection checklist

| Slot | Action |
|---|---|
| `<tone_preference>` | Only when the product needs a fixed style — length already tracks task complexity |
| `<scope_boundaries>` | Recommended for narrow tasks, not mandatory |
| Verification instruction | Normal — keep if the task warrants it |
| Subagent policy | Add a cap when the harness supports delegation |
| Reasoning-echo directive | Tolerated, but adds no value — prefer omitting |

## 1. Verbosity

Opus 4.8 calibrates response length to how complex it judges the task to be, rather than defaulting to a fixed verbosity: shorter on simple lookups, much longer on open-ended analysis. Tune only if your product depends on a particular style.

> Provide concise, focused responses. Skip non-essential context, and keep examples minimal.

For a specific kind of verbosity (over-explaining, say), add a targeted instruction. **Positive examples showing the right level of concision work better than negative instructions telling the model what not to do.**

## 2. Effort — start high

Unlike Sonnet 5, the recommended starting point is not the default:

- **`max`** — real gains on some tasks, but diminishing returns and sometimes prone to overthinking. Test before adopting.
- **`xhigh`** — **the best setting for most coding and agentic use cases. Start here.**
- **`high`** — balanced; the minimum for intelligence-sensitive work.
- **`medium`** — cost-sensitive work, trading intelligence for tokens.
- **`low`** — short scoped tasks and latency-sensitive workloads that aren't intelligence-sensitive.

## 3. Subagent spawning

Opus 4.8 has explicit subagent-control guidance. Cap delegation when the harness supports it — the same block as Opus 5 applies:

> Delegate to a subagent only for large tasks that are genuinely independent and parallelizable. Do not delegate work you can finish yourself in a handful of tool calls. Keep spawn counts low.

## 4. Overeagerness

Opus 4.5 and 4.6 tend to overengineer, and 4.8 inherits some of it: extra files, unnecessary abstractions, unrequested flexibility. Use the scope-containment block in [`_shared-canon.md`](_shared-canon.md#5-scope-containment) when the task is narrow or the detected effort is `xhigh`/`max`.

## 5. Other axes

Also covered by the source guide, apply as the task warrants: tool-use triggering, user-facing progress updates, more literal instruction following, tone and writing style, design/frontend defaults, interactive coding products, code-review harnesses, computer use.

**More literal instruction following** is the one most likely to bite: 4.8 will not silently generalise an instruction to unlisted items. State scope explicitly — *"apply to every section, not just the first"*.

## Gate implications

| Gate | Behaviour on this profile |
|---|---|
| 7 — reasoning directive | Standard (numbered steps expected); echo directive not required |
| 9 — over-verification | Inactive |
| 11 — scope boundary | Recommended, not enforced |
