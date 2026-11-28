# Design System (UI UX Pro Max — Modern Interactive Study Handbook)

## Direction
- **Style:** Modern EdTech / Interactive Engineering Handbook (inspired by Stripe Docs, Linear, and interactive CS textbooks — warm, high-craft, spacious, zero clutter).
- **Typography:**
  - Headings: `Plus Jakarta Sans` (weights 600–700, tight negative tracking `-0.025em`)
  - Body: `Inter` (`16.5px` / `1.75` line-height, comfortable `74ch` reading width)
  - Code & Technical Tokens: `JetBrains Mono` (`13.5px` / `1.7` line-height)
- **Three-Layer Color Tokens (WCAG AA/AAA):**
  - **Light:** Canvas `#f8fafc`, Elevated Card `#ffffff`, Subtle Surface `#f1f5f9`, Hairline `#e2e8f0`, Ink `#0f172a`, Muted `#475569`, Primary Indigo `#4f46e5`, Emerald `#059669`, Amber `#d97706`, Violet `#7c3aed`, Rose `#e11d48`.
  - **Dark:** Canvas `#090d16`, Elevated Card `#111827`, Subtle Surface `#1a2335`, Hairline `#253047`, Ink `#f1f5f9`, Muted `#94a3b8`, Primary Indigo `#818cf8`, Emerald `#34d399`, Amber `#fbbf24`, Violet `#a78bfa`, Rose `#fb7185`.
- **Study UX Features:**
  - Top reading-progress bar while scrolling chapters
  - Local personal study tracker (`Mark as studied`) synced across homepage progress bar and sidebar
  - Semantic callout cards (`concept`, `mental-model`, `warning`, `tip`) and interactive recall accordions (`question`)
  - Client-side syntax highlighting with one-click copy
  - Scroll-spy right TOC + grouped chapter cards with reading-time estimates and `Visual` badges
  - Zero external JS frameworks; pure static HTML/CSS/JS built via `build.py` and verified via `check.py`
