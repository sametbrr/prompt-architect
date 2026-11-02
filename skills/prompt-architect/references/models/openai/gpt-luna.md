---
model: GPT Luna tier (fast)
model_ids: [gpt-6-luna, gpt-5.6-luna, gpt-reserve]
last_verified: 2026-11-02
source: codex debug models catalog (codex-cli 0.166.0); ChatGPT Learn notebooks
---

# Profile: GPT Luna (fast)

The fastest, cheapest tier. The Codex docs recommend it for fast, narrowly scoped agents doing clear, repeatable, high-volume work: classification, extraction, transformation, read-only codebase mapping, and tasks with clear boundaries.

| Model | Catalog description | Default effort | Levels | Context |
|---|---|---|---|---|
| `gpt-6-luna` | Fast and affordable model for easier tasks | `medium` | low…max (**no ultra**) | 272k (max 872k) |
| `gpt-5.6-luna` | Older fast and efficient model | `medium` | low…max (**no ultra**) | 272k (max 872k) |
| `gpt-reserve` | Hidden entry: "Fast and affordable agentic coding model" | `medium` | low…max | 272k. Mapped here from its description, **unverified** |

---

## Injection checklist

| Section | Action |
|---|---|
| Goal | One narrow, unambiguous objective. Split multi-objective requests and say so |
| Examples | **Add 2–5 input/output examples** for classification, extraction or format work |
| Output | **Exact format** (schema, field list, or example output) |
| Constraints | **Required** |
| Done when | **Required** |
| Verification | On gpt-6-luna, **ask explicitly** if tests or checks are wanted: its harness says "Do not add or run tests unless the user asks you to test or verify" *(catalog)* |

## Guidance

- **Effort.** `low` or `medium`. Don't recommend `ultra`; the catalog doesn't list it for Luna.
- **Fit check.** If the request is open-ended, ambiguous or needs design judgment, keep the prompt but say in Assumptions that Sol (or Astra) is the better target.
- **Determinism.** Fixed formats and examples matter more here than on the larger tiers. Prefer one fixed output shape over "use your judgment".

## Gate implications

Same as [`gpt-sol.md`](gpt-sol.md): 2 and 9 N/A, 10 warning, 11 and 12 required. Gate 5 (examples) matters most on this tier.
