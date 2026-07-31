---
model: Claude Opus 5
model_ids: [claude-opus-5, claude-opus-5[1m]]
role: default profile
last_verified: 2026-07-31
source: platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 + about-claude/models/whats-new-opus-5
---

# Profile — Claude Opus 5 ★ default

The fallback for any unresolved or unrecognised model. Thinking is **on by default**.

---

## Injection checklist

| Slot | Action |
|---|---|
| `<tone_preference>` | **Required.** Opus 5 writes longer than prior Opus models and effort does not reliably shorten visible output |
| `<scope_boundaries>` | **Required.** It can widen a task on its own initiative |
| Verification instruction | **Omit deliberately.** Adding one causes over-verification |
| Subagent policy | Add a cap whenever the harness supports delegation |
| Reasoning-echo directive | Never add |

## 1. Verbosity — conciseness is not optional

Effort controls how much the model *thinks*, not how much it *says*. Lowering effort reduces thinking volume without reliably shortening the response. Prompt for length explicitly.

For a user-facing multi-turn product:

> Keep responses focused, brief, and concise. Keep disclaimers and caveats short, and spend most of the response on the main answer. When asked to explain something, give a high-level summary unless an in-depth explanation is specifically requested.

In a long prompt, pair it with a short reminder near the end:

```xml
<tone_preference>
Keep outputs reasonably concise.
</tone_preference>
```

## 2. Task scope and over-verification

**Remove verification scaffolding.** Opus 5 verifies its own work unprompted. Instructions like *"include a final verification step for any non-trivial task"* or *"use a subagent to verify"* cause over-verification — deleting them cuts wasted tokens with no quality loss. The same goes for legacy harness steps that bolt on a separate verify stage.

For narrow tasks, constrain scope explicitly:

> Deliver what was asked, at the scope intended. Make routine judgment calls yourself, and check in only when different readings of the request would lead to materially different work. If the request seems mistaken or a better approach exists, say so in a sentence and continue with the task as asked rather than quietly narrowing, widening, or transforming it. Finish the whole task, and stop short of actions that are clearly beyond what was asked.

## 3. Subagent spawning

Opus 5 delegates more readily than prior models. Delegation pays on genuinely independent, sizeable tracks; it multiplies cost and time on small ones.

> Delegate to a subagent only for large tasks that are genuinely independent and parallelizable, such as a wide multi-file investigation. Do not delegate work you can finish yourself in a handful of tool calls, and do not use subagents to verify or double-check your own work. If one subagent can complete the task, use one rather than several, and keep spawn counts low.

## 4. Self-correction

Opus 5 self-corrects mid-task. Don't build retry-and-critique loops around behaviour the model already has.

## 5. Thinking disabled — two artifacts

Thinking can only be disabled at effort `high` or below. **Prefer thinking enabled at `low` effort over thinking disabled** — it performs better at comparable cost.

If it must be off, two artifacts can appear:

- **Tool calls rendered as text.** The model writes a tool call into visible output instead of emitting a `tool_use` block. The call never runs, and in agentic loops the leaked text pollutes later turns. Most common on tool-heavy workloads like search.
- **Internal XML tags leaking.** `<thinking>` and similar tags appear in the visible response. **If the prompt contains a rule telling the model not to think or not to reason, remove it** — that instruction *increases* leakage.

One combined mitigation covers both:

> When you use a tool, you may say a brief sentence first. If no tool can express what the user asked for, say so instead of guessing. Do not include internal or system XML tags in your response.

Naming the tags specifically is less effective than this general form.

## 6. Effort

Thinking on by default. Higher effort increases thinking volume, not response length. When detected effort is `xhigh` or `max` and the task is narrow, add the scope-containment block from [`_shared-canon.md`](_shared-canon.md#5-scope-containment).

## Gate implications

| Gate | Behaviour on this profile |
|---|---|
| 7 — reasoning directive | **Inverted** — a `<scratchpad>`/`<thinking>` echo directive is a failure |
| 9 — over-verification | **Active** — any "verify your work" instruction fails |
| 11 — scope boundary | **Required** in execute mode |
