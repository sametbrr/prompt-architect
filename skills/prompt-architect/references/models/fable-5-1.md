---
model: Claude Fable 5.1 / Claude Mythos 5.1
model_ids: [claude-fable-5-1, claude-mythos-5-1]
last_verified: 2026-11-02
source: Claude Prompting notebook — "Prompting Claude Fable 5.1" guide ("Behavioral differences and prompting patterns for Claude Fable 5.1 and Claude Mythos 5.1"); verified by NotebookLM quote 2026-11-02
---

# Profile: Claude Fable 5.1 / Mythos 5.1

The Fable 5.1 guide covers Claude Mythos 5.1 with the same prompting patterns. For the previous generation the docs say Mythos 5 shares Fable 5's capabilities, is available only through Project Glasswing, and lacks Fable's safety classifiers; whether that availability and classifier difference carries over to Mythos 5.1 is **unverified**. Everything in the Fable 5 profile ([`legacy/fable-5.md`](legacy/fable-5.md)) still holds unless this file changes it.

**Model IDs:** `claude-fable-5-1` / `claude-mythos-5-1` follow Anthropic's naming pattern; the guide does not print them, **unverified**. Context window and max output for 5.1 are not stated (Fable 5: 1M context, up to 128k output), **unverified**.

---

## Two hard rules (unchanged from Fable 5)

1. **Never ask it to reproduce its reasoning** as response text. That can trigger the `reasoning_extraction` refusal. Raw chain of thought is never returned; with `thinking.display: "summarized"` the thinking blocks carry a summary.
2. **Keep the scaffold light.** Older, prescriptive skills and instructions degrade its output; give high-level goals. Prefer the compact template, use XML only for four or more distinct content types, and trim `<reminders>` to what the task needs.

## Injection checklist

| Slot | Action |
|---|---|
| `<why>` | **Weighted.** Intent context improves results |
| `<scope_boundaries>` | **Required.** Add "prefer targeted edits over whole-file rewrites" for code |
| Checkpoint line | **Required** for long work (§2) |
| Verification | **Add** for long runs: separate verifier subagents, and audit progress claims against tool results |
| `<tone_preference>` | Lead with the outcome; say when formatting is wanted (§3) |
| Reasoning-echo directive | **Forbidden** |
| `<reminders>` | Shorten aggressively |

## 1. Thinking, effort, history

- Adaptive thinking is **always on**. `thinking: {"type": "disabled"}` and manual `budget_tokens` both return a **400**.
- Effort defaults to **`high`**. `medium` matches Fable 5 capability at lower cost; `low` is competitive on cost per task with the Opus and Sonnet models. At `low` effort it calls search less often, so raise effort or nudge toward checking facts.
- **History must be append-only.** Thinking blocks are bound to the exact conversation prefix. Replaying them after editing the system prompt or earlier turns returns a **400** (`prefix_mismatch_behavior`). Prompts for a 5.1 harness must not rewrite earlier turns.

## 2. Finishing the task and staying in scope

It can end a turn early ("Next, I'll…") or ask permission it doesn't need:

> Pause for the user only when the work genuinely requires them: a destructive or irreversible action, a real scope change, or input that only they can provide. If you hit one of these, ask and end the turn, rather than ending on a promise.

For code: prefer targeted edits over whole-file rewrites, and no unrequested refactoring or extra committed test files.

## 3. Writing and formatting

- Prose can be denser than Fable 5 (longer sentences, fewer paragraph breaks). The guide's fix is short: *"Please remove all mannered prose."*
- In chat it leans away from bold, headers and lists. Remove old anti-formatting rules, or say explicitly when formatting is wanted.
- Summaries can reuse source wording without quotation marks. Tell it to quote sources explicitly.

## 4. Tools, subagents, progress

- In custom coding or computer-use loops it can issue one tool per turn: *"Where you have multiple independent tool calls to make, issue them in parallel in a single turn rather than one per turn."*
- The lead agent can sit idle while subagents run: *"Delegate independent subtasks to subagents and keep working while they run. Intervene if a subagent goes off track or is missing relevant context."*
- It writes fewer user-facing updates than Fable 5 during long tool-calling turns. If the UI hides tool output: *"Only you see that command's output — the user's terminal shows at most a few lines of it. If the user needs to read any of it, put it in your reply."* A client-side `send_to_user` tool lets it deliver progress verbatim mid-turn.
- Have it check progress claims against actual tool results, which removes invented status reports.
- To avoid safeguard false positives, phrase code questions as *"Are there any bugs in this program?"* rather than *"Does this program compile without errors?"*, and keep base64 blobs out of tool output.

## Gate implications

| Gate | Behaviour on this profile |
|---|---|
| 7 Operational sequencing | Standard |
| 9 No over-verification | Not applied; verification is wanted |
| 10 No reasoning echo | **Hard fail** |
| 11 Scope boundary | **Required** |
| Template | Compact preferred; XML only for genuinely multi-part tasks |
