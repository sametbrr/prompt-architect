# Prompt Quality Gates (Self-Review Checklist)

Eight UI-compatible checks. Run after drafting a refined prompt. Any failing gate triggers a single revision pass.

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
- ≥75% of constraints are stated positively ("do X") rather than negatively ("don't do Y").
- Threshold is 75% (not 80%) because the standard adherence block carries two unavoidable negatives from CLAUDE.md Rules #5 and #6 ("do not add abstractions", "do not modify unrelated code").
- Where additional negatives appear, they should be paired with a positive alternative.

**Failure example:** Prompt has 5 "do not" directives and 1 positive instruction.
**Fix:** Rewrite each negative as a positive (see Pattern 3 table in `claude-prompting-patterns.md`).

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

## Gate 7 — In-Context Reasoning Directive

**Pass criteria:** ONE of the following:
- Task is single-step / trivial → no directive needed, OR
- `<detailed_instructions>` numbers the steps in operational order AND, for complex reasoning, instructs the model to write intermediate thoughts inside `<scratchpad>` or `<thinking>` tags before producing the final answer.

**Failure example:** Multi-step analysis with no order dictated.
**Fix:** Add numbered steps; add scratchpad directive if reasoning is non-trivial.

---

## Gate 8 — Output Framing + Hallucination Guard

**Pass criteria — BOTH must hold:**
- Output format is specified (JSON shape, markdown structure, prose length) AND a closing wrapper tag is named (`<final_plan>`, `<verdict>`, etc.).
- A hallucination guard is present in `<reminders>`: a phrase equivalent to "Only answer if you are confident; otherwise state your uncertainty explicitly."

**Failure example:** "Return a plan." with no format and no uncertainty clause.
**Fix:** Add `<output_format>...wrap in <plan>...</plan>...</output_format>` and add the certainty clause to `<reminders>`.

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

### Best prompt (passes all 8 gates)
```
<role>You are a senior claims adjuster specializing in Swedish auto-accident forms. Communicate in precise, formal tone.</role>
<reference>Form structure: 17 rows, each row meaning ... [enumerated].</reference>
<detailed_instructions>
1. First, read all 17 form rows and extract checked checkboxes for both Driver A and Driver B.
2. Tabulate the extracted data inside <form_data>...</form_data>.
3. Only after step 2, examine the freehand accident sketch.
4. Cross-reference sketch with form data; treat form as ground truth, sketch as supporting evidence.
5. Write reasoning inside <scratchpad>...</scratchpad>.
</detailed_instructions>
<output_format>Return your final answer wrapped in <verdict>...</verdict>. Inside: a single sentence naming the at-fault driver, then a bulleted list of supporting evidence.</output_format>
<reminders>
- Only answer if the form data clearly supports a verdict; otherwise return <verdict>insufficient evidence</verdict>.
- Treat form data as ground truth over the sketch.
</reminders>
```
- All 8 gates ✓

**Result:** Reliable correct classification, easy downstream parsing of `<verdict>`.

---

## Quick Self-Review Loop

After drafting:
1. Walk the 8 gates in order.
2. Note any FAIL.
3. Apply the fix from this document.
4. Re-check only the previously-failing gates.
5. Output `Self-Review: 8/8 gates passed` or `Self-Review: failed [gate-list]`.

If after one revision pass any gate still fails, surface the failure in the `Self-Review:` line rather than hiding it — honesty over false-pass.
