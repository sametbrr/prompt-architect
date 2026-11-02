---
last_verified: 2026-11-02
---

# Generic profile (no provider tuning)

Used when the host is unknown and no target was named, or when the target is neither a Claude nor an OpenAI model (Gemini, Llama, Mistral, a local model…). Say in the output that no provider-specific tuning was applied. Don't guess another vendor's quirks from Anthropic's or OpenAI's docs.

## What to produce

- The portable core only: patterns 1–9 from [`../claude-prompting-patterns.md`](../claude-prompting-patterns.md) (role, clear sections, positive guidance, ordered steps, few-shot examples, output format with a wrapper, long-context ordering).
- Sections as either XML tags or markdown headings. Both are widely understood. Pick XML when the content will be parsed or has many distinct parts, markdown otherwise.
- An explicit scope line, a done-when line when the target will act on files or systems, and an uncertainty line ("If the input doesn't support an answer, say so").
- No effort, thinking, verbosity or tool-choice settings. Those are provider-specific.
- No reasoning-echo directive. It is unnecessary on reasoning models and harmful on some.

## Gate implications

Gates 1 and 3–8 apply (5–7 only for structured prompts). Gate 2 is N/A (XML or markdown are both fine), 9 N/A, 10 warning, 11 recommended (N/A), 12 N/A.
