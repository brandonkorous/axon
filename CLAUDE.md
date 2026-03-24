# Code Rules

- Max ~200 lines per file — split into multiple files/components if larger
- Technical debt paydown — if you see something wrong, fix it immediately
- Don't leave unused code — delete it, don't comment it out
- Follow existing patterns — look at how similar features were built before inventing new ones
- Architectural correctness over quick fixes
- Single responsibility — each function/module does one thing. If you can't name it clearly, it's doing too much
- Fail fast, fail loud — errors should surface immediately at the boundary, not silently propagate
- No magic strings/numbers — use constants or enums
- Tests live in dedicated test directories — frontend: `*.test.ts` colocated, backend: `backend/tests/` mirroring `backend/axon/` structure
- Imports stay clean — no circular dependencies, no barrel files that re-export everything

## Design Context

### Users
Startup founder/CEO operating an AI executive advisory board. Using Axon as a command center to orchestrate multiple AI advisors (Marcus, Raj, Diana) for strategic decision-making. Context is focused, high-stakes work — the user needs information density and fast interactions, not hand-holding.

### Brand Personality
**Sleek, Fast, Powerful.** Axon is a mission control center — it should project confidence, authority, and precision. The interface should feel like a high-performance tool that puts the operator in command.

### Aesthetic Direction
- **Visual tone:** Dark, sharp, performance-oriented. Command & control energy.
- **Reference:** Linear — clean layouts, fast interactions, developer-grade polish, information density without clutter.
- **Anti-references:** Chatbot-style UIs, rounded/bubbly consumer apps, anything that feels toy-like or casual.
- **Theme:** Dark mode primary. Gray-950/900/800 backgrounds, violet accent, semantic status colors.
- **Typography:** System fonts, tight tracking on headings, `text-sm` default body size for density.

### Design Principles
1. **Density over decoration** — Pack useful information into every pixel. No filler sections, hero banners, or decorative whitespace. Every element earns its space.
2. **Speed is a feature** — Interactions should feel instant. Favor keyboard shortcuts, minimal clicks, and snappy transitions. Animations serve feedback, not spectacle.
3. **Hierarchy through restraint** — Use color sparingly and with intent. Gray for structure, violet for primary actions, semantic colors for status. Let contrast and spacing create hierarchy, not visual noise.
4. **Consistency is trust** — Same patterns everywhere. Status colors, spacing scales, component shapes, and interaction patterns should be predictable across all views.
5. **Operator-grade clarity** — Labels are precise, states are unambiguous, actions are obvious. The user should never wonder "what does this do?" or "what state is this in?"

### Accessibility
- WCAG AA compliance — sufficient contrast ratios, keyboard navigation, screen reader support
- Respect `prefers-reduced-motion` for animations
- Focus states visible on all interactive elements (violet ring pattern)
