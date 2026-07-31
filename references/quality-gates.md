# Prompt Quality Gates (Self-Review Checklist)

Eleven checks. Run after drafting a refined prompt. Any failing gate triggers a single revision pass.

**Gates 7, 9, 10 and 11 are model-conditional** — they behave differently depending on the resolved target model. Read [`models/_matrix.md`](models/_matrix.md) first; each profile's *Gate implications* table states which apply. `validate_prompt.py --target-model <profile>` applies the same logic mechanically.

| Gate | Scope |
|---|---|
| 1–6, 8 | Universal |
| 7 — reasoning directive | **Inverted** on Opus 5 and Fable 5 |
| 9 — over-verification | Opus 5 only |
| 10 — reasoning echo | Hard fail on Fable 5, warning elsewhere |
| 11 — scope boundary | Required on Opus 5 and Fable 5 in execute mode |

---

## Gate 1 — Single-Objective Clarity

**Pass criteria:**
- The prompt has exactly one primary deliverable.
- No conflicting goals (e.g., "summarize AND elaborate", "be brief AND comprehensive").
- Sub-goals are explicitly subordinated to the primary one.

**Failure example:** "Write a marketing plan and also design the database schema."
**Fix:** Split into two prompts, or pick one as primary with the other as supporting context.

---

## Gate 2 — XML/Tag Isolation

**Pass criteria:**
- Each distinct concern (role, task, data, instructions, examples, output format, reminders) lives inside its own tag.
- Markdown headings (`##`, `###`) are NOT used as section delimiters inside the prompt body.
- Tag names are semantic (`<task>`, `<reminders>`) not generic (`<section1>`).

**Failure example:** Prompt uses `**Rules:**` followed by bullet points.
**Fix:** Wrap as `<rules>\n- ...\n</rules>`.

---

## Gate 3 — Positive Guidance Ratio

**Pass criteria:**
- ≥60% of *behavioural directives* are stated positively ("do X") rather than negatively ("don't do Y").
- **Constraint blocks are exempt** — `<scope_boundaries>` and anti-overengineering lists are counted separately and may be entirely negative.
- Where a negative appears outside a constraint block, it should be paired with a positive alternative.

**Why the threshold moved (v3.0.0):** the old ≥75% rule over all text would fail Anthropic's own recommended prompts. Its canonical scope-containment block reads *"Don't add features, refactor code… Don't add docstrings… Don't add error handling… Don't create helpers…"* — almost entirely negative, and correct that way. Enumerating what to stop short of is precisely what a boundary block is for. Positive framing still matters for *behaviour* ("return only the JSON object" over "don't add explanations"); it does not for *limits*.

**Failure example:** Prompt has 5 "do not" directives scattered through `<detailed_instructions>` and 1 positive instruction.
**Fix:** Rewrite the behavioural negatives as positives (see Pattern 3 table in `claude-prompting-patterns.md`); move genuine limits into `<scope_boundaries>`.

---

## Gate 4 — Specific Role + Seniority + Tone

**Pass criteria:**
- Role names a concrete domain (not "expert" or "assistant").
- Role includes seniority indicator ("Senior", "Lead", "Principal", "with N years experience").
- Role specifies communication tone (executive, technical, conversational).

**Failure example:** `<role>You are an expert helper.</role>`
**Fix:** `<role>You are a Senior Backend Architect with 12 years of experience in multi-tenant SaaS systems. Communicate in precise, technical tone.</role>`

---

## Gate 5 — In-Context Examples (when warranted)

**Pass criteria:** ONE of the following is true:
- The task is simple enough that examples are unnecessary (single-step transformation, common format), OR
- `<examples>` contains 2–5 input/output pairs covering at least one edge/gray-area case.

**Failure example:** Classification task with 7 output categories, no examples shown.
**Fix:** Add 3–5 `<example>` entries inside `<examples>`, including borderline cases.

---

## Gate 6 — Long-Context Hierarchy

**Pass criteria (when prompt has bulky reference data):**
- Static/reference data appears in the TOP half of the prompt (inside `<content>` or `<reference>`).
- Active instructions, task description, and reminders appear in the BOTTOM half.
- The user's actual ask is among the last elements before the model generates.

**Failure example:** Task description at the top, 5000 tokens of reference docs at the bottom right before model output begins.
**Fix:** Move reference docs above the task.

---

## Gate 7 — Operational Sequencing

**Pass criteria:** ONE of the following:
- Task is single-step / trivial → no directive needed, OR
- `<detailed_instructions>` numbers the steps in operational order.

**Failure example:** Multi-step analysis with no order dictated.
**Fix:** Add numbered steps, and state why the order matters when it isn't obvious.

> **Inverted in v3.0.0.** This gate previously *required* a `<scratchpad>`/`<thinking>` directive for non-trivial reasoning. It now requires the opposite: on Opus 5 and Fable 5 targets, the presence of a reasoning-echo directive is a **failure** (see Gate 10). Ordering the steps is still valuable; asking the model to narrate its thinking is not.

---

## Gate 8 — Output Framing + Hallucination Guard

**Pass criteria — BOTH must hold:**
- Output format is specified (JSON shape, markdown structure, prose length) AND a closing wrapper tag is named (`<final_plan>`, `<verdict>`, etc.).
- A hallucination guard is present in `<reminders>`: a phrase equivalent to "Only answer if you are confident; otherwise state your uncertainty explicitly."

**Failure example:** "Return a plan." with no format and no uncertainty clause.
**Fix:** Add `<output_format>...wrap in <plan>...</plan>...</output_format>` and add the certainty clause to `<reminders>`.

---

## Gate 9 — No Over-Verification *(Opus 5 targets only)*

**Pass criteria:** The prompt does **not** instruct the model to verify, double-check, or re-review its own work.

**Why:** Opus 5 verifies its own work unprompted. Explicit verification instructions — *"include a final verification step for any non-trivial task"*, *"use a subagent to verify"* — cause over-verification. Removing them cuts wasted tokens with no loss in quality. This also applies to legacy harness scaffolding that bolts on a separate verify stage.

**Failure example:** `<reminders>` contains *"Review your output for completeness and correctness before returning."*
**Fix:** Delete it. On other target models the same line is harmless; on **Fable 5 it is actively wanted** — there, add interval self-verification with fresh-context verifier subagents instead.

---

## Gate 10 — No Reasoning Echo

**Pass criteria:** The prompt does **not** instruct the model to write, transcribe, echo, or explain its internal reasoning as response text. No `<scratchpad>`, `<thinking>`, or "show your reasoning" directives.

**Severity:** hard fail on **Fable 5 / Mythos 5**; warning on all other targets.

**Why:** on Fable 5 this can trigger the `reasoning_extraction` refusal category, causing elevated fallback to Opus 4.8 — a silent quality and cost regression. On Opus 5, thinking is on by default, so the directive duplicates work and inflates output.

**Failure example:** *"Write intermediate reasoning inside `<scratchpad>`…`</scratchpad>` before producing the final answer."*
**Fix:** Delete the directive; keep the numbered ordering (Gate 7). If reasoning visibility is genuinely required, read structured `thinking` blocks from adaptive thinking instead of asking for prose.

---

## Gate 11 — Scope Boundary Present *(Opus 5 and Fable 5, execute mode)*

**Pass criteria:** The prompt contains an explicit statement of what to deliver and what to stop short of — a `<scope_boundaries>` block in XML mode, or a `Scope:` line in compact mode.

**Why:** Opus 5 can widen a task on its own initiative, adding steps that weren't requested. Fable 5 can take unrequested actions outright — drafting an email nobody asked for, creating defensive git-branch backups.

**Failure example:** An execute-mode prompt targeting Opus 5 with no scope statement anywhere.
**Fix:** Add the boundary block from Pattern 11. Negative framing is fine here and is exempt from Gate 3.

---

## Canonical Case Study — Insurance Claim Analysis

From "Prompting 101 | Code w/ Claude". Illustrates Gates 4, 6, 7, 8 in one progression.

### Bad prompt
```
Analyze this accident report and tell me who is at fault.
```
- Gate 4: ✗ no role
- Gate 6: ✗ no hierarchy
- Gate 7: ✗ no order
- Gate 8: ✗ no format, no hallucination guard

**Result:** Claude misread the form word "ski" (Swedish field label) and concluded it was a skiing accident, despite the form clearly indicating a car crash.

### Better prompt
```
<role>You are an expert in analyzing Swedish auto insurance claim forms.</role>
<reference>The form has 17 numbered rows. Row 1 = date, Row 2 = location, ..., Row 17 = signature.</reference>
<task>Determine which driver is at fault based on the form.</task>
```
- Gate 4: ✓ role
- Gate 6: ✓ reference at top
- Gate 7: ✗ no operational order
- Gate 8: ✗ no format/guard

**Result:** Better accuracy but still occasional misclassification.

### Best prompt (passes all applicable gates, Opus 5 target)
```
<role>You are a senior claims adjuster specializing in Swedish auto-accident forms. Communicate in precise, formal tone.</role>
<why>This verdict feeds a settlement decision, so a wrong at-fault call is expensive to reverse.</why>
<reference>Form structure: 17 rows, each row meaning ... [enumerated].</reference>
<detailed_instructions>
1. First, read all 17 form rows and extract checked checkboxes for both Driver A and Driver B.
2. Tabulate the extracted data inside <form_data>...</form_data>.
3. Only after step 2, examine the freehand accident sketch.
4. Cross-reference sketch with form data; treat form as ground truth, sketch as supporting evidence.
</detailed_instructions>
<scope_boundaries>Produce the verdict for this one claim. Don't recommend settlement amounts or draft correspondence.</scope_boundaries>
<output_format>Return your final answer wrapped in <verdict>...</verdict>. Inside: a single sentence naming the at-fault driver, then a bulleted list of supporting evidence.</output_format>
<tone_preference>Keep the evidence list to the rows that actually decide the verdict.</tone_preference>
<reminders>
- Only answer if the form data clearly supports a verdict; otherwise return <verdict>insufficient evidence</verdict>.
- Treat form data as ground truth over the sketch.
</reminders>
```
- All applicable gates ✓

**Result:** Reliable correct classification, easy downstream parsing of `<verdict>`.

> **What changed in v3.0.0.** The previous "best prompt" ended `<detailed_instructions>` with *"Write reasoning inside `<scratchpad>`…"*. That line now **fails Gate 10** and was removed — the operational ordering in steps 1–4 was carrying the accuracy gain, not the scratchpad. Three slots were added: `<why>` (Pattern 10), `<scope_boundaries>` (Gate 11), `<tone_preference>` (Pattern 12). The `<reminders>` block keeps its two task-specific rules and no longer carries a "review your output" line, which would fail Gate 9 on this target.

---

## Quick Self-Review Loop

After drafting:
1. Resolve the target model first — the applicable gate set depends on it.
2. Walk the applicable gates in order.
3. Note any FAIL.
4. Apply the fix from this document.
5. Re-check only the previously-failing gates.
6. Output `Self-Review: N/N gates passed` (N = applicable count, not always 11) or `Self-Review: failed [gate-list]`.

If after one revision pass any gate still fails, surface the failure in the `Self-Review:` line rather than hiding it — honesty over false-pass.
