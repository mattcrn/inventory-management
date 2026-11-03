---
name: vue-saas-redesign
description: Redesign a Vue 3 application's UI into a modern, polished SaaS-style interface — replaces a top navigation bar with a collapsible vertical sidebar on the left, introduces a consistent design-token system (spacing, color, type, radius, elevation), restyles shared UI primitives, and gives every view a consistent page structure. Use this skill whenever the user wants to modernize, restyle, refresh, re-skin or "make professional" a Vue (3 / Vite / Nuxt-free SPA) frontend, move navigation into a sidebar, add an app shell/layout, fix inconsistent spacing or styling across pages, or make the app "look like Linear / Stripe / Vercel dashboard" — even if they don't say "redesign" or "SaaS".
---

# Vue 3 SaaS Redesign

Turn an existing Vue 3 app into a cohesive SaaS-style product: left sidebar navigation, a slim top bar, a token-driven design system, and every view rebuilt on the same page skeleton. The default scope is a **full overhaul** (shell + tokens + primitives + every view). If the user asks for less ("just the sidebar"), stop after the relevant phase.

The redesign is visual. Behaviour must survive untouched: same routes, same data flow, same API calls, same i18n keys, same reactivity. A redesign that looks great but silently breaks a filter or a modal is a failed redesign — that's why recon and verification are half of this workflow.

## Phase 0 — Ground rules for this codebase

Before touching anything, read the project's own instructions (`CLAUDE.md` at the root and in the client folder, `.claude/agents/`, `README`). They override this skill where they conflict. Typical things to pick up:

- **Delegation rules** — e.g. "all .vue edits go through the vue-expert agent". If such an agent exists, hand it the phase-by-phase briefs below instead of editing yourself.
- **Design constraints** — existing palette, "no emojis", chart conventions, brand colors. Evolve the existing palette rather than replacing it unless the user asks for a new brand look.
- **Conventions** — v-for keys, i18n usage, comment rules, test locations.

Work on a branch (create one if on the default branch) — the diff will be large and the user needs an easy way back.

## Phase 1 — Recon (read-only)

Build a map of the UI before designing anything. Find:

1. **The shell** — where the current top nav lives (usually `App.vue` or a `layouts/` component), what else sits in the header (logo, language switcher, profile menu, global filters, notifications).
2. **Routes and nav items** — from the router config and the nav markup. Note routes that exist but aren't linked, and nav labels that are hard-coded instead of translated.
3. **Global styles** — where they live (`App.vue` unscoped `<style>`, `main.css`, `style.css`), and which classes are shared across views (`.card`, `.stat-card`, `.page-header`, tables, badges, buttons).
4. **Styling stack** — plain CSS, Tailwind, a component library (Vuetify, PrimeVue, Element Plus, Naive UI)? Adapt to it: with Tailwind, express tokens in `tailwind.config` / CSS variables; with a component library, theme it rather than fighting it. Don't introduce a new styling framework or icon library unless one is already present — inline SVG icons are fine and dependency-free.
5. **Hard-coded values** — grep for raw hex colors, `px` paddings/margins, font sizes and `box-shadow`s in `.vue` files. This tells you how much token migration each view needs and catches inconsistencies (five different grays, three card radii).
6. **i18n** — if the app has locales, note the longest-string language (German, Japanese with long katakana). The sidebar width and labels must survive it.
7. **Anything tests or scripts target** — class names or `data-testid`s used by e2e tests must keep working.

**Baseline screenshots:** if Playwright (MCP or CLI) is available and the dev server can run, capture every route at desktop (1440px) and mobile (390px) width before changing anything. These are your regression reference in Phase 6.

## Phase 2 — Plan and confirm

Present a short plan to the user before writing code:

- **Navigation structure** — the sidebar items, grouped into sections if there are more than ~6 (e.g. "Operations", "Finance", "Insights"), each with a chosen icon. Include previously unlinked routes only if the user wants them surfaced.
- **What moves where** — e.g. "global filters move from under the nav into the top bar of data views; language switcher and profile menu move to the sidebar footer".
- **Palette direction** — evolve the existing palette (default) or a new accent color.
- **Order of work** and which files change.

Ask only about genuine choices (grouping, accent color, what to do with global filters). Then proceed.

## Phase 3 — Design tokens

Create one token file (e.g. `src/styles/tokens.css`, imported once in `main.js`) with CSS custom properties. Read `references/design-system.md` for the full recommended token set, values, and the reasoning behind them. The essentials:

- **Spacing** on a 4px base scale (`--space-1` … `--space-12`). Every padding, margin and gap in the app should come from this scale — this single rule is what makes a layout feel "consistent".
- **Color** as semantic roles (`--color-bg`, `--color-surface`, `--color-border`, `--color-text`, `--color-text-muted`, `--color-accent`, status colors with `-soft` background variants), not raw palette names, so dark mode or a rebrand is a token swap.
- **Typography** scale, **radius**, **elevation** (shadows), **layout** constants (`--sidebar-width`, `--sidebar-width-collapsed`, `--topbar-height`, `--content-max-width`), and **motion** (one duration + easing).

Then extract the shared primitives into a global stylesheet (`src/styles/components.css` or similar) built only from tokens: page header, card, stat card, table, badge/status pill, buttons (primary / secondary / ghost / danger), form controls, empty state, modal. Where the app duplicates the same component CSS in many scoped blocks, consolidate it here and delete the copies.

## Phase 4 — App shell

Replace the top nav with this layout (details and a reference component skeleton in `references/design-system.md`):

```
┌──────────┬─────────────────────────────────────┐
│ Logo     │ Top bar: page title · global actions │
│──────────│─────────────────────────────────────│
│ Section  │                                     │
│  • Item  │   <router-view />                   │
│  • Item  │   (max-width content, consistent    │
│ Section  │    page padding)                    │
│  • Item  │                                     │
│──────────│                                     │
│ Lang     │                                     │
│ Profile  │                                     │
└──────────┴─────────────────────────────────────┘
```

Requirements, each with a reason:

- **Fixed sidebar, independently scrolling content** — navigation stays reachable on long pages.
- **Collapsible to an icon rail** (persist the choice in `localStorage`, wrapped in try/catch) — power users reclaim width for tables and charts. Show labels as tooltips/`title` when collapsed.
- **Mobile (< 768px): off-canvas drawer** behind a hamburger in the top bar, with a backdrop, closing on route change and on Escape — a 240px sidebar would eat a phone screen.
- **Active state from the router** (`router-link`'s `active-class` / `exact-active-class`, or `useRoute()`), with a clear indicator (accent bar or tinted background), not just bold text.
- **Accessibility** — `<nav aria-label>`, real `router-link`/`button` elements, visible `:focus-visible` rings, `aria-expanded` on the collapse and drawer toggles, `aria-current="page"` on the active item.
- **Translated labels** — reuse existing i18n keys; add keys for any new strings (section titles, "Collapse sidebar") to every locale.
- **Top bar** shows the current page title (from route meta or the view) and hosts page-level controls such as global filters. Keep components that hold shared state (filter bars, profile menus, modals) — move them, don't rewrite their logic.

Put the shell in its own components (`AppSidebar.vue`, `AppTopbar.vue`, optionally `AppLayout.vue`) and keep `App.vue` thin.

## Phase 5 — View-by-view overhaul

Go through every view and the components it uses, one at a time. For each:

1. Rebuild it on the common page skeleton: page header (title, description, primary action on the right) → KPI/stat row (if any) → content cards in a CSS grid.
2. Replace hard-coded colors, spacings, font sizes, radii and shadows with tokens; switch local one-off styles to the shared primitives.
3. Tables: sticky header, comfortable row height, right-aligned numeric columns with tabular figures (`font-variant-numeric: tabular-nums`), subtle row hover, horizontal scroll wrapper on small screens.
4. Charts: take colors from tokens so they match the theme; keep the chart logic untouched.
5. Empty, loading and error states: give each a consistent, designed treatment instead of bare text.
6. Do not change script logic, props, emits, API calls, computed properties or i18n keys. If a view's markup must be restructured, keep every binding, `v-if`, `v-for` (and its key) and event handler intact.

**Ordering matters.** Land tokens + primitives + shell first, verify, then do views. If you parallelize views across subagents, only do so after the shared foundation is merged, give each agent a disjoint set of files, and hand each the token/primitive class reference so they converge on the same vocabulary instead of inventing their own.

## Phase 6 — Verify

A redesign is done when it is both better-looking and provably not broken:

- **Build** passes (`npm run build` / `vite build`) with no new warnings.
- **Every route** renders at 1440px, 1024px and 390px with no horizontal page scroll, overlapping elements, or clipped text. Compare against the Phase 1 screenshots.
- **Sidebar**: collapse/expand, persisted state, mobile drawer open/close (button, backdrop, Escape, route change), active item correct on every route including nested ones.
- **Behaviour unchanged**: filters still filter, modals open/close, forms submit, language switch still works and the longest locale still fits.
- **Console**: no new errors or Vue warnings (pre-existing ones may stay — report them, don't hide them).
- **Contrast**: body text and muted text meet WCAG AA against their backgrounds; focus rings are visible.
- **Existing tests** still pass.

## Reporting back

Summarize for the user: what the new shell looks like, the token file location, which primitives were consolidated, a per-view list of notable changes, anything you deliberately didn't change and why, verification results (including what you could not verify), and before/after screenshots if you took them.
