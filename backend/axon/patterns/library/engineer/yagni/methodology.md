# YAGNI (You Ain't Gonna Need It)

YAGNI is the discipline of not building features, abstractions, or infrastructure until there is a concrete, present need. Engineers love to anticipate future requirements and build for them today, but predicted requirements are wrong far more often than they are right. Every line of speculative code carries maintenance cost, increases complexity, and may actively interfere with the actual future requirement when it arrives.

Apply this whenever you catch yourself saying "we might need this later," "let's make it configurable just in case," or "what if we need to support X someday?"

**Steps to apply:**
1. Ask: "Do I need this right now to ship the current requirement?"
2. If no, do not build it. Write a comment or ticket noting the potential future need.
3. If yes, build the simplest version that meets the current need.
4. Trust that you can add complexity later when the real requirement is clear — and it will be cheaper then because you will know more.

**Common mistakes:** Building plugin architectures before you have two plugins. Adding configuration options nobody has asked for. Creating abstractions for hypothetical future variants. Confusing YAGNI with ignoring known requirements — it applies to speculative work, not confirmed upcoming needs.
