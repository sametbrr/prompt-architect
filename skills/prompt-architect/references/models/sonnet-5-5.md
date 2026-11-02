---
model: Claude Sonnet 5.5
model_ids: [claude-sonnet-5-5]
last_verified: 2026-11-02
source: Claude Prompting notebook — "Prompting Claude Sonnet 5.5" guide; reviewer-subagent and display-updates lines verified by NotebookLM quote 2026-11-02
---

# Profile: Claude Sonnet 5.5

Its behaviour depends heavily on effort: at `low`/`medium` it can stop to check in before the work is done, and at `xhigh`/`max` it can do more than asked (unrequested reviewer subagents, cleanup refactors). Pick the steering line that matches the effort the prompt will run at.

**Model ID:** `claude-sonnet-5-5` follows Anthropic's naming pattern; the guide does not print it, **unverified**. Context window and max output: not stated (Sonnet 5 had 1M / 128k), **unverified**.

---

## Injection checklist

| Slot | Action |
|---|---|
| Completion line | **Required at `low`/`medium` effort** (§2) |
| `<scope_boundaries>` | **Required at every effort.** At `low`/`medium` it sits alongside the completion line; at `xhigh`/`max` add the stop-and-report line (§2); for open-ended asks use §3 |
| Verification instruction | **Add for code changes**, especially at `low` effort (§4). The opposite of the Opus 5 habit |
| `<tone_preference>` | Only when the product needs a fixed style |
| Subagent policy | At `xhigh`/`max`: forbid unrequested reviewer subagents |
| Reasoning-echo directive | **Forbidden** |

## 1. Effort and thinking

- Effort defaults to **`high`** on the API. For well-specified agentic coding start at **`medium`** (raise to `high` for harder tasks); for chat and latency-sensitive work start at `medium` or `low`.
- Adaptive thinking is on by default. Its lowest thinking mode is `thinking: {"type": "between_tools"}` (accepted at `high` effort or below), for integrations that run without up-front reasoning.
- Without thinking at `low`/`medium`, JSON-output tasks can skip needed tool calls. Use Structured Outputs or adaptive thinking, or add: *"The JSON output format applies to your final answer only. When you need a tool, call it first, with no text before the call, and write the JSON once you have the results."*

## 2. Carry-through versus scope, by effort

At `low`/`medium` effort:

> Carry the work through to completion. Do not stop to ask permission, confirm a plan, or ask whether to continue unless you hit an error you cannot resolve yourself.

At `xhigh`/`max` effort it can start extra review rounds and launch reviewer sub-agents nobody asked for. The guide's line ("In testing on coding tasks at max effort, this stopped the model from launching reviewer subagents and cut session cost by about a third, with no change in quality"):

> When the work the user asked for is done and its checks pass, stop and report. Don't start extra rounds of review or hardening on your own, and don't launch reviewer sub-agents unless the user asked for a review. If you think a deeper review is worth doing, say so at the end.

## 3. Open-ended requests

On prompts like "show me what you can do" it can start building when only ideas were wanted:

> When the user asks for ideas, options or a plan, give them that and stop. Don't start building or changing anything until they say to go ahead.

## 4. Verification

At `low` effort it can report code changes as done without running tests or builds. Add:

> When you change code that can be run, built, or type-checked, run a real check that exercises the change before reporting it done: the project's tests, type-checker, or build, or the changed command itself. Only if no real check can run here, say which one you did not run and why instead of reporting the change as done.

## 5. Tools and knowledge

- Tool calls tolerate minor casing and parameter-name mismatches.
- In chat it may answer from training data when facts have changed. For research-style work: *"Use the search tool to check specifics that may have changed since your training, such as what is allowed, required or charged, even when you feel confident."*
- For dense charts or drawings, give it a crop/zoom tool.
- Deliver mid-turn user input as a user turn appended after the `tool_result`, not inside it.
- Progress notes longer than a sentence come back as progress-update thinking blocks; set `thinking.display: "updates"` (beta, `thinking-display-updates-2026-08-18` header) to read them.

Frontend design: the 5.5 guide is silent and points back to the Sonnet 5 guide.

## Gate implications

| Gate | Behaviour on this profile |
|---|---|
| 7 Operational sequencing | Standard |
| 9 No over-verification | Not applied; verification is wanted |
| 10 No reasoning echo | **Hard fail** |
| 11 Scope boundary | **Required** |
