# Mode Inference

Two modes:
- `prompt_only` (default): produce the refined prompt; do not execute.
- `prompt_and_execute`: produce the refined prompt AND generate the deliverable.

Users almost never type the literal flag names. Infer from natural language.

---

## Decision Tree

```
Did the user mention any execute-intent signal? ─── No ──→ prompt_only (default)
                                                │
                                                Yes
                                                │
Did the user also mention any "just the prompt" signal?
                                                │
                          ┌─────────────────────┼──────────────────┐
                          │                     │                  │
                         Yes                    No              Mixed
                          │                     │                  │
                          ▼                     ▼                  ▼
                     prompt_only          prompt_and_execute   prompt_only
                   (explicit signal       (execute the task)   + note ambiguity
                    wins over execute)                          in Assumptions
```

---

## Signal Tables

### prompt_only signals (override execute signals)

| Turkish | English |
|---|---|
| "sadece prompt" | "just the prompt" |
| "prompt yaz yeter" | "prompt only" |
| "çalıştırma" / "execute etme" | "don't run it" / "don't execute" |
| "uygulama yap" (when contradicted by "no need to do it") | "no need to do it" |
| "promptu görmek istiyorum" | "I want to see the prompt" |
| "sadece refine et" | "just refine it" |

### prompt_and_execute signals

| Turkish | English |
|---|---|
| "çalıştır" / "yürüt" | "run it" / "execute it" |
| "uygula" | "apply it" / "do it" |
| "tam çıktı ver" | "give the full output" |
| "sonucu da üret" | "produce the result too" |
| "hem prompt hem sonuç" | "both prompt and result" |
| "promptu hazırla ve uygula" | "prepare the prompt and execute" |
| "yap" (when paired with a deliverable noun) | "do it too" / "generate the output" |
| "bana planı ver" | "give me the plan" |

### Ambiguous patterns (default to prompt_only, note in Assumptions)

| Pattern | Why ambiguous |
|---|---|
| User says "yap" alone with no execute-context | Could mean "create the prompt" or "execute" |
| User says "ver" / "give me" without "prompt" or "output" qualifier | Could mean either |
| User says "show me" without specifying prompt vs output | Ambiguous |
| User provides a multi-stage request mentioning both "prompt'u hazırla" AND "ama önce göster" | Mixed; show first, then ask before execute |

---

## Precedence Rules

1. **Explicit prompt_only > implicit prompt_and_execute.**
   If both signals appear, the prompt_only signal wins.
   Example: "Refine the prompt and run it, but just show me the prompt first" → `prompt_only`.

2. **Literal flag > natural language.**
   If the user types literal `prompt_and_execute` or `prompt_only`, that wins over any contradicting natural-language signal.

3. **Imperative-verb-on-deliverable > generic verb.**
   "Onboarding planı hazırla" (imperative on a concrete deliverable) → `prompt_and_execute`.
   "Onboarding hakkında bir prompt yaz" (imperative on the meta-task) → `prompt_only`.

4. **Empty / no signal → `prompt_only` default.**

---

## When to Surface Ambiguity

If signals are genuinely mixed (not just precedence-resolvable), choose `prompt_only` and add a one-line note under `**Assumptions / Uncertainty:**`:

> Mode signal was ambiguous; defaulted to prompt_only. Reply "uygula" or "run it" if you want execution.

This satisfies CLAUDE.md Rule #7 (state uncertainty explicitly) without breaking flow with a question.
