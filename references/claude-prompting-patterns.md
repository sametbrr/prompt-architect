# Claude Prompting Patterns

Source: Anthropic's current prompting canon (`claude-prompting-best-practices`, `prompt-engineering/overview`, the per-model prompting guides), the "Prompting 101 | Code w/ Claude" video, and the interactive prompt-engineering tutorial. Last reconciled against the live docs **2026-07-31**.

Patterns 1–9 are the portable core: they are text-level, so they work identically in the API and in chat clients. Patterns 10–14 were added in v3.0.0 to cover behaviours the Claude 5 generation introduced. **Model-specific deltas live in [`models/`](models/) — read `models/_matrix.md` before selecting patterns.**

> **v3.0.0 note.** The earlier "API-only, out of scope" framing was retired. Prefill was not merely unavailable in chat — it has been **removed** (a 400 on Claude 4.6+). `thinking` and `effort` are not API trivia either; they are surfaced in Claude Code and change how a prompt should be written. See [Harness-level controls](#harness-level-controls).

---

## 1. Role Prompting

**When to use:** Always. Setting a domain-specific role is the single highest-leverage pattern.

**How to apply (UI):** First sentence/tag of the prompt assigns a role with three components — specialty + seniority + tone.

**Mini example:**
```
<role>You are a senior SaaS growth strategist with 10 years of B2B SaaS onboarding experience. Communicate in concise, executive tone.</role>
```

**Anti-pattern:** "You are a helpful assistant."

---

## 2. Inline XML/Tag Structuring

**When to use:** Always when the prompt has more than ~3 distinct sections (instructions, data, rules, examples, output format).

**How to apply (UI):** Replace markdown bold/headings with semantic tags. Use lowercase snake_case tag names that describe the section's purpose.

**Mini example:**
```
<task>...</task>
<content>...static data, references, background...</content>
<detailed_instructions>...how to proceed step by step...</detailed_instructions>
<reminders>...critical rules restated at the end...</reminders>
```

**Why:** Claude was fine-tuned to attend to XML structure. Markdown headings are ambiguous (Claude may treat `## Rules` as content rather than a delimiter).

---

## 3. Positive Guidance

**When to use:** Whenever you have a constraint to express.

**How to apply (UI):** Rewrite every negative instruction as a positive directive describing what TO do.

| Negative (avoid) | Positive (use) |
|---|---|
| "Don't add explanations" | "Return only the JSON object, with no surrounding prose" |
| "Don't use markdown" | "Format the response as plain text paragraphs" |
| "Don't guess" | "Only answer if you are confident; otherwise state that you are uncertain" |

**Why:** Negatives are easy to miss in long prompts; positives are actionable.

---

## 4. Operational Reasoning Sequence

**When to use:** Multi-step analysis, classification with edge cases, anything where the model has historically hallucinated.

**How to apply:** Inside `<detailed_instructions>`, dictate the reasoning sequence explicitly ("first analyze X, then proceed to Y"). State *why* the order matters when it isn't obvious.

**Mini example:**
```
<detailed_instructions>
1. First, read the form fields and identify which checkboxes are marked.
2. Then, examine the sketch and identify visual elements.
3. Finally, cross-reference the two, treating the form as ground truth.
</detailed_instructions>
```

> ### ⚠️ Do not ask the model to echo its reasoning
>
> Until v2.2.1 this pattern ended with *"write your intermediate reasoning inside `<scratchpad>` tags."* **That instruction is now removed**, for two reasons:
>
> - On **Fable 5 / Mythos 5** it is a hazard. Instructions telling the model to echo, transcribe, or explain its internal reasoning as response text can trigger the `reasoning_extraction` refusal category and cause elevated fallback to Opus 4.8.
> - On **Opus 5** thinking is on by default, so a scratchpad directive duplicates work the model already does and inflates output.
>
> Dictating the *order* of operations is still valuable — that is what this pattern now is. If an application needs reasoning visibility, read the structured `thinking` blocks from adaptive thinking rather than asking for them in prose.

---

## 5. In-Context Few-Shot

**When to use:** When format, tone, or edge-case handling must be learned by demonstration rather than description.

**How to apply:** Provide **3–5** input/output pairs inside `<examples>` tags (the canon's recommended range). Each example is an `<example>` with `<input>` and `<output>` sub-tags. Make them *relevant* (mirror the real use case), *diverse* (vary enough that no unintended pattern is learned), and cover gray-area cases — not just happy paths.

**Tip from the canon:** you can ask Claude to evaluate your examples for relevance and diversity, or to generate more from an initial set.

**Mini example:**
```
<examples>
  <example>
    <input>"3 nights, family of 4, prefers beach"</input>
    <output>{"nights": 3, "guests": 4, "preference": "beach"}</output>
  </example>
  <example>
    <input>"weekend getaway"</input>
    <output>{"nights": 2, "guests": null, "preference": null}</output>
  </example>
</examples>
```

---

## 6. Step-by-Step Operational Sequencing

**When to use:** When the ORDER of operations affects correctness (e.g., analyze clear data before ambiguous data).

**How to apply (UI):** Numbered list inside `<detailed_instructions>`. State explicitly why the order matters when it's non-obvious.

**Canonical example (from Prompting 101 video — insurance claim analysis):**
> First read the structured form fields (checkboxes labeled in Swedish). Only after extracting all form data, look at the freehand accident sketch. Use the form data as ground truth and the sketch as supporting evidence — not the other way around.

Without this sequencing, Claude mis-classified a car accident as a skiing accident because it read the sketch first.

---

## 7. Output Framing with Closing Tags

**When to use:** Whenever the output will be parsed, piped, or extracted downstream.

**How to apply (UI):** Specify both the format (JSON, markdown table, prose) and a closing wrapper tag (`<final_plan>...</final_plan>`, `<verdict>...</verdict>`). The wrapper makes regex extraction trivial.

**Mini example:**
```
<output_format>
Return your final answer wrapped in <onboarding_plan>...</onboarding_plan> tags.
Use markdown headings inside the wrapper. Do not include any prose outside the wrapper.
</output_format>
```

> ### Prefill is gone — this is its replacement
>
> Until v2.2.1 this pattern described assistant-message prefilling as an "API-only variant". That was wrong in a way that matters: **prefilled assistant messages on the final turn are unsupported from Claude 4.6 onward and return a 400.**
>
> Anthropic's prescribed migrations, by original purpose:
>
> | Was prefilled to… | Use instead |
> |---|---|
> | Force a JSON/YAML/classification shape | **Structured Outputs** (schema-constrained), or a tool with an enum field for labels. Newer models also match complex schemas reliably when simply told to |
> | Skip preambles | *"Respond directly without preamble. Do not start with phrases like 'Here is…' or 'Based on…'"* — or the wrapper tag above. Strip stragglers in post-processing |
> | Steer around bad refusals | Nothing needed; refusal behaviour is much better |
> | Continue an interrupted response | Move it to the user turn: *"Your previous response was interrupted and ended with [text]. Continue from where you left off."* |
> | Re-inject context in long chats | Put the reminder in the user turn; in agentic systems hydrate through tools or during context compaction |
>
> The wrapper-tag instruction remains the right default for parseable output. Reach for Structured Outputs when the schema is strict.

---

## 8. Long-Context Hierarchy

**When to use:** Any prompt with >2000 tokens of reference data (documents, code, schemas).

**How to apply (UI):** Put bulky static data at the TOP of the prompt inside `<content>` or `<reference>` tags. Put the task description and reminders at the BOTTOM (closest to the model's "recent attention"). The user's actual ask should be the last thing the model reads before generating.

**Layout:**
```
<role>...</role>
<content>...thousands of tokens of reference docs...</content>
<task>The actual ask, kept concise.</task>
<reminders>Critical rules restated.</reminders>
```

---

## 9. Iterative Gray-Area Capture

**When to use:** When the same prompt is used repeatedly in production and edge cases emerge.

**How to apply (UI):** Maintain a running list of cases where the model erred. Convert each into a few-shot example with the correct output. Add to `<examples>`. Over time the prompt becomes self-correcting.

**Operational tip:** When the model gets something right that you wouldn't have expected, ask it (in a separate session) to articulate its reasoning. Lift that reasoning into the next version of `<detailed_instructions>` as a permanent rule.

---

---

# Claude 5 generation patterns (10–14)

These address behaviours the Claude 5 generation introduced. Whether each applies — and how strongly — is decided by the target model's profile in [`models/`](models/). Do not apply them blindly; two of them are mutually exclusive across models.

## 10. Intent Framing

**When to use:** Always worthwhile; **weighted heavily on Fable 5**, which connects a task to relevant information better when it understands the intent behind it.

**How to apply:** A `<why>` block before `<task>`, naming the larger goal, the audience, and what the output enables.

```
<why>
I'm working on [the larger task] for [who it's for]. They need [what the output enables].
</why>
```

Also applies at the constraint level: *"Your response will be read aloud by a text-to-speech engine, so never use ellipses"* outperforms *"NEVER use ellipses"*. Claude generalises from the explanation.

## 11. Scope Boundaries

**When to use:** Any execute-mode prompt. **Required for Opus 5** (which can widen a task on its own) **and Fable 5** (which can take unrequested actions).

**How to apply:** A `<scope_boundaries>` block stating what to deliver and what to stop short of.

```
Deliver what was asked, at the scope intended. Make routine judgment calls yourself, and
check in only when different readings of the request would lead to materially different
work. Finish the whole task, and stop short of actions clearly beyond what was asked.
```

For assessment-type requests, Fable 5's sharper form: *"When the user is describing a problem or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop."*

**Note on framing:** this pattern legitimately uses negative constraints. Anthropic's own scope-containment block is almost entirely negative. Gate 3 exempts constraint lists for exactly this reason.

## 12. Verbosity Control

**When to use:** **Mandatory on Opus 5** — its default responses run long and `effort` does not reliably shorten visible output. Optional elsewhere, where length already tracks task complexity.

**How to apply:** A `<tone_preference>` block, plus a short restatement near the end of a long prompt.

```
Keep responses focused, brief, and concise. Keep disclaimers and caveats short, and spend
most of the response on the main answer. When asked to explain something, give a high-level
summary unless an in-depth explanation is specifically requested.
```

**On Sonnet 5 and Opus 4.8, show rather than forbid** — a positive example of the right concision beats an instruction naming the verbosity to avoid.

## 13. Delegation Policy

**When to use:** Any prompt whose harness supports subagents, targeting **Opus 5** (delegates readily), **Opus 4.8**, or **Fable 5** (parallel subagents). Sonnet 5's guide has no subagent section — skip it there.

```
Delegate to a subagent only for large tasks that are genuinely independent and
parallelizable. Do not delegate work you can finish yourself in a handful of tool calls,
and do not use subagents to verify or double-check your own work. Keep spawn counts low.
```

**⚠️ Model-divergent.** On **Opus 5**, also *remove* any verification instruction — it self-verifies, and asking causes over-verification. On **Fable 5**, do the opposite: add interval self-verification with fresh-context verifier subagents. These two are direct opposites; the profile decides.

## 14. Checkpoint Policy

**When to use:** Long-running or agentic prompts. Strongest signal on Fable 5, where a brief instruction replaces an enumerated list of stop conditions.

```
Pause for the user only when the work genuinely requires them: a destructive or irreversible
action, a real scope change, or input that only they can provide. If you hit one of these,
ask and end the turn, rather than ending on a promise.
```

---

# Harness-level controls

Not prompt text, but they change how the prompt should be written. Formerly (and wrongly) filed as "API-only, out of scope".

| Control | Why it matters here |
|---|---|
| **`effort`** | The primary intelligence/latency/cost lever, surfaced in Claude Code. Higher effort means more unrequested thoroughness — pair it with Pattern 11. Defaults differ per model; see the profile |
| **`thinking`** | On by default on Opus 5; disable only at effort `high` or below. Prefer thinking-on at `low` effort over thinking-off. Never instruct the model *not* to think — that increases tag leakage |
| **`budget_tokens`** | **Removed.** Deprecated on 4.6, returns a 400 on Claude 4.7+. Lower `effort` or cap `max_tokens` instead |
| **Structured Outputs** | The schema-constrained replacement for prefill-based formatting. Prefer it over prose format instructions when the schema is strict |
| **Prefill** | **Unsupported from Claude 4.6 onward** (400). See Pattern 7 for migrations |
| **`stop_sequences`** | Still API-level. Structure output via Pattern 7 instead |
