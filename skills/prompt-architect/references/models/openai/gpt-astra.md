---
model: GPT-6 Astra (frontier)
model_ids: [gpt-6-astra]
last_verified: 2026-11-02
source: codex debug models catalog (codex-cli 0.166.0); ChatGPT Learn notebooks
---

# Profile: GPT-6 Astra (frontier)

*Catalog:* "Frontier intelligence for the most demanding work." The Codex docs call Astra the most capable model for advanced reasoning, computer use and high-judgment work across code, apps and research, and recommend it for the most complex, ambiguous and ambitious projects. Fast mode is available at higher credit cost.

| Model | Default effort | Levels | Context |
|---|---|---|---|
| `gpt-6-astra` | `low` | low…max, **ultra** | 272k (max 872k) |

Its base instructions are the same as gpt-6.1-terra's and almost the same as gpt-6.1-sol's *(catalog)*. The prompting difference is about the kind of task, not syntax.

---

## Injection checklist

| Section | Action |
|---|---|
| Goal | State the outcome and why it matters. Astra gets ambiguous, ambitious work, so give intent rather than a step list |
| Context | Point to sources and constraints; let it plan |
| Constraints | **Required**: what stays untouched, what needs approval |
| Done when | **Required** (both modes) |
| Verification | **Required** when code or data changes |
| Step list | Keep it short or leave it out; over-specifying steps for a frontier model is wasted prompt (**unverified** for Astra specifically, carried from general Codex guidance to name destinations rather than script searches) |

## Guidance

- **Effort.** Defaults to `low` *(catalog)*. For the hard, open-ended work Astra is chosen for, recommend `high` or above, and `ultra` when the task splits into parallel parts. Say how the parts divide.
- **When not to use it.** Routine edits and scans cost less on Sol or Terra. If the user's task is narrow, say in Assumptions that a cheaper tier would do.
- **Ambiguity.** Let it ask clarifying questions early while it keeps working on what doesn't depend on the answer; the harness already supports this.

## Gate implications

Same as [`gpt-sol.md`](gpt-sol.md): 2 and 9 N/A, 10 warning, 11 and 12 required.
