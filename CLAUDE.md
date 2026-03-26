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

> **Theme origin: `/axon-landing`.** This app inherits its design language from the landing site. Palette, typography, and token changes should originate there and be mirrored here via `frontend/src/theme.css`.

### Users
Mixed audience — technical founders self-hosting AI tools alongside non-technical team members managing AI workflows. The app is a command center for orchestrating AI advisors. Users need information density and fast interactions without the interface feeling intimidating or cold.

### Brand Personality
**Warm, Intelligent, Grounded.** Axon is a capable command center that projects quiet confidence and approachable authority. It should feel like a thoughtful tool — not a cold dashboard or a flashy toy.

### Aesthetic Direction
- **Visual tone:** Clean, warm, confident. Approachable authority — professional without being cold.
- **References:** Linear — clean layouts, fast interactions, developer-grade polish, information density without clutter.
- **Anti-references:** Generic SaaS (blue gradients, stock photos). Matrix/hacker aesthetic (neon-on-black, terminal-heavy). Chatbot-style UIs, rounded/bubbly consumer apps, anything toy-like.
- **Theme:** Light mode default (`axon`), dark mode alternate (`axon-dark`). Warm neutral backgrounds, muted teal primary, terracotta secondary, olive accent. Theme tokens in `frontend/src/theme.css`.
- **Dark mode:** Must stay in the warm teal/terracotta family — no violet or neon. Adapt the brand palette for dark surfaces with appropriate contrast.
- **Typography:** DM Sans (body), Fraunces (display headings). Tight tracking on headings, `text-sm` default body size for density.

### Design Principles
1. **Density over decoration** — Pack useful information into every pixel. No filler sections or decorative whitespace in the app. Every element earns its space.
2. **Speed is a feature** — Interactions should feel instant. Favor keyboard shortcuts, minimal clicks, and snappy transitions. Animations serve feedback, not spectacle.
3. **Warmth over cold precision** — The earthy palette (cream, teal, terracotta) is intentional. Maintain organic warmth. Avoid sterile whites and clinical blues.
4. **Hierarchy through restraint** — Use color sparingly and with intent. Neutrals for structure, teal for primary actions, semantic colors for status. Let contrast and spacing create hierarchy, not visual noise.
5. **Consistency is trust** — The app and landing site must feel like one product. Same colors, type scale, component patterns. Status colors, spacing scales, and interaction patterns should be predictable across all views.
6. **Operator-grade clarity** — Labels are precise, states are unambiguous, actions are obvious. The user should never wonder "what does this do?" or "what state is this in?"

### Accessibility
- WCAG AA compliance — sufficient contrast ratios, keyboard navigation, screen reader support
- Respect `prefers-reduced-motion` for animations
- Focus states visible on all interactive elements (primary ring pattern)
- Opacity-based text hierarchy must maintain readable contrast (minimum `/60` on base backgrounds)
