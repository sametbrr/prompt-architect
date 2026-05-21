# Claude Prompting Patterns (UI/Chat-Compatible)

Source: distilled from Anthropic's "Prompting 101 | Code w/ Claude" video transcript, Claude API docs (overview, best practices), and the interactive prompt-engineering tutorial — filtered to patterns that work in chat/UI environments (Claude Code, claude.ai, Claude Desktop). Request-level API features (assistant prefill, `thinking` parameter, `stop_sequences`, `tool_choice`) are NOT covered here.

XML/tag-based patterns work in BOTH API and UI because the tags are part of the prompt text content — Claude is fine-tuned to respect them regardless of where the text comes from.

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

## 4. In-Context Chain-of-Thought

**When to use:** Multi-step analysis, classification with edge cases, anything where the model has historically hallucinated.

**How to apply (UI):** Inside `<detailed_instructions>`, explicitly dictate the reasoning sequence ("first analyze X, then proceed to Y"). For deeper reasoning, instruct the model to write its analysis inside a `<scratchpad>` or `<thinking>` tag before producing the final answer.

**Mini example:**
```
<detailed_instructions>
1. First, read the form fields and identify which checkboxes are marked.
2. Then, examine the sketch and identify visual elements.
3. Finally, cross-reference the two and write your verdict inside <final_verdict> tags.
Write your intermediate reasoning inside <scratchpad> tags before the final verdict.
</detailed_instructions>
```

**API-only variant (out of scope):** Request-level `thinking: {type: "enabled", budget_tokens: ...}` parameter — used via the API only. The in-context tag version above is the UI equivalent and works everywhere.

---

## 5. In-Context Few-Shot

**When to use:** When format, tone, or edge-case handling must be learned by demonstration rather than description.

**How to apply (UI):** Provide 2–5 input/output pairs inside `<examples>` tags. Each example should be a `<example>` with `<input>` and `<output>` sub-tags. Cover gray-area cases (the ones where the model historically erred), not just happy paths.

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

**API-only variant (out of scope):** Assistant-message prefilling (starting the assistant's response with `<onboarding_plan>` so Claude continues from there) — API only. The wrapper-tag instruction above is the UI equivalent.

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

## Patterns Explicitly Out of Scope (API-only)

The following are powerful but unavailable in chat/UI environments. Skip them entirely when refining prompts for Claude Code, claude.ai, or Claude Desktop:

- **Assistant-message prefill** — Starting the assistant turn with partial content in the API request. Replaced by Pattern #7 (closing-tag instruction).
- **Request-level `thinking` parameter** — Enabling extended thinking via API. Replaced by Pattern #4 (in-context `<scratchpad>` instruction).
- **`stop_sequences`** — Premature termination tokens. No UI equivalent; structure output via Pattern #7 instead.
- **`tool_choice` / structured tool schemas** — API-managed tool routing. Not applicable to standalone prompts.
- **Batch API / Files API** — Bulk processing endpoints. Out of scope for single-prompt refinement.
