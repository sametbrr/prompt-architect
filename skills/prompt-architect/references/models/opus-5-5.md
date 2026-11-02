---
model: Claude Opus 5.5
model_ids: [claude-opus-5-5, claude-opus-5-5[1m]]
role: default Claude profile
last_verified: 2026-11-02
source: Claude Prompting notebook — "Prompting Claude Opus 5.5" guide; model ID confirmed from a live Claude Code session
---

# Profile: Claude Opus 5.5 ★ default Claude profile

Used for any Claude target that resolves to Opus 5.5, and for unknown newer Claude models. Anthropic's guide says Opus 5 prompts are a reasonable starting point, so the Opus 5 habits carry over unless a line below says otherwise. Where the guide is silent, the line says **unverified**.

**Specs:** max output 128,000 tokens (the guide calls it "the model's maximum"). Context window: not stated in the guide (Opus 5 had 1M), **unverified**.

---

## Injection checklist

| Slot | Action |
|---|---|
| `<scope_boundaries>` | **Required** in both modes (the refined prompt is run either way). Carried over from Opus 5, plus the guide's own warning that it starts acting quickly across connected apps |
| `<tone_preference>` | **Optional.** Only when the product needs a fixed length. The 5.5 guide says it finishes tasks with fewer output tokens than Opus 5; the "effort doesn't shorten the answer" rule is documented for Opus 5, not 5.5 |
| Verification instruction | **Omit by default** (carried over from Opus 5, where it causes over-verification). The 5.5 guide is silent, so the validator only warns. For unattended runs, track open items in a checklist (§4) rather than adding a verify step |
| Subagent policy | Add a cap whenever the harness supports delegation |
| Reasoning-echo directive | **Forbidden.** Remove legacy "write your reasoning out" lines |
| "Think carefully" lines | Remove from chat prompts; they add latency |

## 1. Thinking and effort

- Adaptive thinking is **always on**. `thinking: {"type": "disabled"}` returns a **400**. To keep thinking short, use `low` effort; for a fast chat answer the guide's line is *"Answer directly without deliberating."*
- Effort defaults to **`medium`**, down from Opus 5's `high`. At `medium` it matches or beats Opus 5 at `high` on coding and knowledge work, at lower cost.
- `xhigh` and `max` think more per turn than Opus 5 did. Reserve them for capability-critical work; the guide reports `max_tokens` 128000 working well for long agentic turns.
- To get less thinking, the guide says to lower the effort level first: it reduces thinking, cost and latency more reliably than prompt instructions.
- Output generation is more than 30% faster than Opus 5, and the same task usually takes fewer output tokens.

## 2. Length

The guide says Opus 5.5 completes the same task with fewer output tokens than Opus 5, and gives no length rule of its own. Add a `<tone_preference>` only when the product needs a fixed length. (The Effort docs' warning that effort doesn't shorten visible responses is stated for Opus 5.)

In multi-turn chat, add the guide's two sentences so it doesn't re-derive earlier answers:

> Earlier answers in this conversation are settled. Do not re-examine or re-derive them unless the user asks you to update them.

## 3. Scope and context gathering

When it works across connected apps (email, docs, sheets, CRM) it tends to start acting quickly. Ask it to look first:

> Look through relevant emails, documents, and records to find applicable policies or context before taking action on a request across connected apps.

For narrow tasks, keep the Opus 5 scope block from [`legacy/opus-5.md`](legacy/opus-5.md) §2 ("Deliver what was asked, at the scope intended…").

Mark pasted text in user messages (for example, wrap it in a tag) so it is read as data, which guards against indirect prompt injection.

## 4. Long and unattended runs

- Opus 5.5 delegates readily and sustains multi-hour autonomous work (audits, repository migrations with parallel subagents) better than Opus 5. It also paces itself from elapsed-time signals (`elapsed Xs / Ys`) when a multi-agent harness provides them.
- In long multi-part tasks, a text-only end of turn is a progress report, not proof of completion. Keep open items in a checklist file or tool, and have the prompt tell it to work through that list.
- Progress notes between tool calls arrive as progress-update thinking blocks; set `thinking.display: "updates"` (beta) to see them. For verbatim mid-turn deliverables, declare a client-side `send_to_user` tool from the first request.
- For long silent turns the guide suggests: *"The user hasn't heard from you in a while — say in a few words what you're doing, then continue."*

## 5. Frontend design

Un-steered, it falls back to default styles. Name the anti-patterns to avoid, for example: *"Do not use a cream or off-white background, italic accent words in headlines, numbered 01/02/03 section labels, monospace labels, or pill-shaped buttons."*

## 6. Vision

Reads dense charts, diagrams and screenshots well even at `low` effort. For the densest technical drawings at higher effort, give it a crop or zoom tool.

## Gate implications

| Gate | Behaviour on this profile |
|---|---|
| 7 Operational sequencing | Standard |
| 9 No over-verification | **Warning** (carried over from Opus 5; unverified for 5.5) |
| 10 No reasoning echo | **Hard fail** (`reasoning_extraction` refusal applies to all current Claude models) |
| 11 Scope boundary | **Required** |
