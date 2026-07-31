---
model: Claude Fable 5 / Claude Mythos 5
model_ids: [claude-fable-5, claude-mythos-5, claude-mythos-preview]
last_verified: 2026-07-31
source: platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5 + about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
---

# Profile — Claude Fable 5 / Mythos 5

The profile that most contradicts this skill's defaults. Read the hazard first.

**Specs (both models):** `claude-fable-5` / `claude-mythos-5`, 1M-token context by default, up to 128k output per request, $10 / $50 per Mtok. Mythos 5 has the same capabilities without safety classifiers, available through Project Glasswing.

---

## ⚠️ Two hard rules

**1. Never instruct the model to reproduce its reasoning.** Prompts, skills, or harness instructions telling the model to echo, transcribe, or explain its internal reasoning as response text can trigger the `reasoning_extraction` refusal category, causing elevated fallback to Opus 4.8. This voids the skill's legacy `<scratchpad>` pattern entirely on this model. If the application needs reasoning visibility, read structured `thinking` blocks from adaptive thinking, and use a send-to-user tool for progress during long runs.

**2. Keep the scaffold light.** Anthropic's own guidance: *"Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality. Review and consider removing older instructions if default performance is better."* Prefer the compact template. Use the XML template only when the task genuinely has four or more distinct content types. Trim `<reminders>` to what the task actually needs — a six-bullet adherence block is the shape being warned against.

---

## Injection checklist

| Slot | Action |
|---|---|
| `<why>` | **Weighted.** Intent context measurably improves results |
| `<tone_preference>` | "Lead with the outcome" block |
| `<scope_boundaries>` | Boundary block — it can take unrequested actions |
| Verification instruction | **Add explicitly** — opposite of Opus 5 |
| Reasoning-echo directive | **Forbidden** |
| `<reminders>` | Shorten aggressively |

## 1. Strong instruction following — brief beats exhaustive

Instruction-following is good enough that a short instruction steers as well as an enumerated list. Un-steered, Fable 5 elaborates beyond the task at higher effort: surveying options it won't pursue, explaining root causes at length, heavily-structured PR descriptions, comments narrating the next line.

> Lead with the outcome. Your first sentence after finishing should answer "what happened" or "what did you find": the thing the user would ask for if they said "just give me the TLDR." Supporting detail and reasoning come after. Being readable and being concise are different things, and readability matters more.
>
> The way to keep output short is to be selective about what you include (drop details that don't change what the reader would do next), not to compress the writing into fragments, abbreviations, arrow chains like A → B → fails, or jargon.

Same for checkpoints in long-running work — no need to enumerate every case:

> Pause for the user only when the work genuinely requires them: a destructive or irreversible action, a real scope change, or input that only they can provide. If you hit one of these, ask and end the turn, rather than ending on a promise.

## 2. Give the reason, not only the request

Fable 5 performs better when it understands intent — context lets it connect the task to relevant information instead of inferring intent alone. This is why `<why>` carries weight here.

> I'm working on [the larger task] for [who it's for]. They need [what the output enables]. With that in mind: [request].

## 3. State the boundaries

Fable 5 can take unrequested actions — drafting an email nobody asked for, creating defensive git-branch backups.

> When the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one. Before running a command that changes system state (restarts, deletes, config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.

## 4. Effort

Primary control for the intelligence / latency / cost trade-off. **`high` is the default**, `xhigh` for the most capability-sensitive workloads, `medium` or `low` for routine work — low effort here often exceeds `xhigh` on prior models. Reduce effort if a task finishes but takes longer than necessary, or when you want a quicker interactive style.

At higher effort on routine work it gathers context and deliberates beyond the need. To prevent unrequested tidying:

> Don't add features, refactor, or introduce abstractions beyond what the task requires. A bug fix doesn't need surrounding cleanup and a one-shot operation usually doesn't need a helper. Don't design for hypothetical future requirements: do the simplest thing that works well. Avoid premature abstraction and half-finished implementations. Don't add error handling, fallbacks, or validation for scenarios that cannot happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs). Don't use feature flags or backwards-compatibility shims when you can just change the code.

## 5. Self-verification — add it, unlike Opus 5

For long-running tasks, fresh-context verifier subagents outperform self-critique:

> Establish a method for checking your own work at an interval of [X] as you build. Run this every [X interval], verifying your work with subagents against the specification.

## 6. Long runs

Also in the source guide, apply when the deliverable is a long-horizon agent: longer turns by default, grounding progress claims, parallel subagents, constructing a memory system, rare early stopping, rare context-budget concern, readability when communicating with the user, and creating a send-to-user tool that delivers messages verbatim without ending the turn.

**Start at the top of your difficulty range** — pick a task harder than you'd assign to prior models and have Fable 5 scope it, ask clarifying questions, and execute.

## Gate implications

| Gate | Behaviour on this profile |
|---|---|
| 7 — reasoning directive | **Inverted** — echo directive is a failure |
| 9 — over-verification | Inactive — verification is *wanted* here |
| 10 — reasoning echo | **Hard fail** |
| 11 — scope boundary | **Required** |
| Template choice | Compact preferred; XML only for genuinely multi-part tasks |
