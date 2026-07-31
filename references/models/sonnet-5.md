---
model: Claude Sonnet 5
model_ids: [claude-sonnet-5]
last_verified: 2026-07-31
source: platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5 + about-claude/models/whats-new-sonnet-5
---

# Profile — Claude Sonnet 5

Behaviourally the closest sibling to Opus 4.8. The one structural difference: **the source guide has no subagent-spawning section**, so this profile adds no delegation cap.

---

## Injection checklist

| Slot | Action |
|---|---|
| `<tone_preference>` | Only when the product needs a fixed style |
| `<scope_boundaries>` | Recommended for narrow tasks |
| Verification instruction | Normal |
| Subagent policy | **Skip** — no guidance in the source |
| Reasoning-echo directive | Tolerated, but prefer omitting |

## 1. Verbosity

Calibrates response length to task complexity rather than defaulting to a fixed verbosity — shorter on simple lookups, longer on open-ended analysis. To reduce it:

> Provide concise, focused responses. Skip non-essential context, and keep examples minimal.

**Positive examples beat negative instructions.** When you see a specific verbosity pattern (over-explaining, restating the question), show the concise version rather than forbidding the verbose one. This is the sharpest steering difference on Sonnet 5.

## 2. Effort — default is already right

- **`max`** — absolute maximum capability, no constraint on token spend.
- **`xhigh`** — recommended for the hardest coding and agentic use cases.
- **`high`** — **the default.** Balances tokens and intelligence for most use cases.
- **`medium`** — cost-sensitive work.
- **`low`** — short scoped tasks, latency-sensitive and not intelligence-sensitive.

Unchanged from Sonnet 4.6. Raise to `xhigh` only for the hardest work; there is no "start higher" recommendation as there is on Opus 4.8.

## 3. Other axes

From the source guide, apply as the task warrants: tool-use triggering, user-facing progress updates, more literal instruction following, tone and writing style, design/frontend defaults, interactive coding products, code-review harnesses, computer use.

**More literal instruction following:** state scope explicitly rather than relying on generalisation.

## Gate implications

| Gate | Behaviour on this profile |
|---|---|
| 7 — reasoning directive | Standard (numbered steps expected); echo directive not required |
| 9 — over-verification | Inactive |
| 11 — scope boundary | Recommended, not enforced |
