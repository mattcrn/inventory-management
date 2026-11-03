# Design system reference

Recommended tokens and the sidebar pattern for the SaaS redesign. Treat the values as a solid default: if the app already has a palette or brand color, map it onto these roles instead of replacing it.

## Contents
1. Token file
2. Why these values
3. Shared primitives checklist
4. Sidebar component skeleton
5. Layout CSS

---

## 1. Token file

```css
/* src/styles/tokens.css */
:root {
  /* Spacing: 4px base. Use only these for padding, margin, and gap. */
  --space-1: 4px;   --space-2: 8px;   --space-3: 12px;  --space-4: 16px;
  --space-5: 20px;  --space-6: 24px;  --space-8: 32px;  --space-10: 40px;
  --space-12: 48px;

  /* Color roles (slate base, blue accent) */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-muted: #f1f5f9;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-text-subtle: #94a3b8;

  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-soft: #eff6ff;
  --color-on-accent: #ffffff;

  --color-success: #16a34a;  --color-success-soft: #f0fdf4;
  --color-info: #2563eb;     --color-info-soft: #eff6ff;
  --color-warning: #d97706;  --color-warning-soft: #fffbeb;
  --color-danger: #dc2626;   --color-danger-soft: #fef2f2;

  /* Sidebar (a darker surface gives the shell a clear frame) */
  --sidebar-bg: #0f172a;
  --sidebar-text: #cbd5e1;
  --sidebar-text-muted: #64748b;
  --sidebar-item-hover: rgba(255, 255, 255, 0.06);
  --sidebar-item-active: rgba(255, 255, 255, 0.10);
  --sidebar-indicator: #60a5fa;

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --text-xs: 12px; --text-sm: 13px; --text-base: 14px; --text-md: 16px;
  --text-lg: 18px; --text-xl: 22px; --text-2xl: 28px;
  --leading-tight: 1.25; --leading-normal: 1.5;
  --weight-regular: 400; --weight-medium: 500; --weight-semibold: 600;

  /* Radius and elevation */
  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px; --radius-full: 999px;
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.12);

  /* Layout */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 68px;
  --topbar-height: 60px;
  --content-max-width: 1440px;
  --page-padding: var(--space-8);

  /* Motion */
  --duration: 180ms;
  --ease: cubic-bezier(0.2, 0, 0, 1);
}

@media (max-width: 768px) {
  :root { --page-padding: var(--space-4); }
}

@media (prefers-reduced-motion: reduce) {
  :root { --duration: 0ms; }
}
```

If the app supports dark mode (or the user wants it), redefine only the color roles under `[data-theme="dark"]` and/or `@media (prefers-color-scheme: dark)`. Components must not need to change.

## 2. Why these values

- **4px spacing scale:** most "unpolished" UIs come from arbitrary paddings (13px here, 18px there). A small fixed scale makes rhythm automatic. Use `--space-6` (24px) for card padding and grid gaps, and `--space-8` (32px) for page padding and between page sections.
- **14px base text:** this is the standard size for data-dense SaaS. Use 13px for table cells and meta text, and keep 12px for labels and badges only.
- **Dark sidebar, light content:** this frames the content and makes the navigation unmistakable. If the brand is light-first, a white sidebar with a right border is the alternative; then use `--color-accent-soft` for the active item.
- **Soft status backgrounds:** a badge with a tinted background and colored text reads calmer and more professional than solid saturated pills.
- **Restrained shadows:** cards rely on a 1px border plus `--shadow-xs`. Reserve heavier shadows for floating layers (menus, modals, the mobile drawer).

## 3. Shared primitives checklist

Define each once in a global stylesheet, built from tokens only:

| Primitive | Key details |
|---|---|
| `.page-header` | Flex row. Title at `--text-2xl`/semibold, description in muted text, actions on the right. Margin-bottom `--space-8`. |
| `.card` | Surface, 1px border, `--radius-lg`, `--shadow-xs`, padding `--space-6`. Optional `.card-header` with title and actions. |
| `.stat-card` | Label (xs, uppercase, muted), value (`--text-2xl`, tabular-nums), optional delta/trend line. Place stat cards in a responsive grid: `repeat(auto-fit, minmax(200px, 1fr))`. |
| Tables | Wrapper with `overflow-x: auto`. Header in `--color-surface-muted`, xs uppercase muted. Rows 44–48px high with 1px dividers and a hover tint. Numeric cells right-aligned. |
| `.badge` | `--radius-full`, xs semibold, soft background + strong text per status. |
| Buttons | Heights 32/36px. Variants: primary (accent), secondary (surface + border), ghost, danger. Visible `:focus-visible` ring (`box-shadow: 0 0 0 3px var(--color-accent-soft)` plus a border). Disabled at 50% opacity with `cursor: not-allowed`. |
| Inputs and selects | 36px high, 1px border, `--radius-md`, accent focus ring. Use the same height as buttons so they align in toolbars. |
| Modal | Centered, `--radius-lg`, `--shadow-lg`, backdrop `rgba(15,23,42,.5)`. Header, body, and footer use consistent padding. |
| Empty, loading, and error states | Centered in the card. Muted icon, one-line title, and a short hint. Loading uses a skeleton or spinner, not just the word "Loading". |

## 4. Sidebar component skeleton

A starting point to adapt. Wire it to the app's real router, i18n, and icons, and keep the comments that explain non-obvious behaviour.

```vue
<!-- src/components/layout/AppSidebar.vue -->
<template>
  <aside
    class="sidebar"
    :class="{ 'is-collapsed': collapsed, 'is-open': mobileOpen }"
    aria-label="Primary"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
      <span v-if="!collapsed" class="brand-name">{{ brandName }}</span>
    </div>

    <nav class="sidebar-nav" aria-label="Main navigation">
      <div v-for="section in sections" :key="section.id" class="nav-section">
        <p v-if="!collapsed && section.title" class="nav-section-title">{{ section.title }}</p>
        <router-link
          v-for="item in section.items"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          active-class=""
          exact-active-class="is-active"
          :title="collapsed ? item.label : undefined"
        >
          <component :is="item.icon" class="nav-icon" aria-hidden="true" />
          <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </div>
    </nav>

    <div class="sidebar-footer">
      <slot name="footer" :collapsed="collapsed" />
      <button
        type="button"
        class="collapse-toggle"
        :aria-expanded="!collapsed"
        @click="toggleCollapsed"
      >
        {{ collapsed ? expandLabel : collapseLabel }}
      </button>
    </div>
  </aside>
  <!-- Mobile backdrop: clicking it closes the drawer -->
  <div v-if="mobileOpen" class="sidebar-backdrop" @click="$emit('close-mobile')" />
</template>
```

Script notes:
- Read and write `collapsed` from `localStorage` inside try/catch. Storage can throw in private mode, and the UI must still work.
- Use `exact-active-class` for leaf routes. For sections with nested routes, compute the active state from `route.path.startsWith(item.to)`, but not for `/`, which would match everything.
- Watch `route.fullPath` and emit `close-mobile`, so navigating closes the drawer on phones.
- Add a `keydown` Escape listener while `mobileOpen` is true, and remove it on unmount.

## 5. Layout CSS

```css
.app-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
  transition: grid-template-columns var(--duration) var(--ease);
}
.app-layout.sidebar-collapsed { grid-template-columns: var(--sidebar-width-collapsed) 1fr; }

.sidebar {
  position: sticky; top: 0; height: 100vh;
  display: flex; flex-direction: column;
  background: var(--sidebar-bg); color: var(--sidebar-text);
  overflow-y: auto;
}
.nav-item {
  position: relative;
  display: flex; align-items: center; gap: var(--space-3);
  height: 36px; padding: 0 var(--space-3); margin: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--sidebar-text); text-decoration: none;
  font-size: var(--text-sm); font-weight: var(--weight-medium);
}
.nav-item:hover { background: var(--sidebar-item-hover); }
.nav-item.is-active { background: var(--sidebar-item-active); color: #fff; }
.nav-item.is-active::before {
  content: ''; position: absolute; left: calc(-1 * var(--space-3)); top: 8px; bottom: 8px;
  width: 3px; border-radius: 0 3px 3px 0; background: var(--sidebar-indicator);
}
.nav-item:focus-visible { outline: 2px solid var(--sidebar-indicator); outline-offset: 2px; }

.app-main { min-width: 0; display: flex; flex-direction: column; }
.app-topbar {
  position: sticky; top: 0; z-index: 10;
  height: var(--topbar-height);
  display: flex; align-items: center; gap: var(--space-4);
  padding: 0 var(--page-padding);
  background: color-mix(in srgb, var(--color-surface) 85%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--color-border);
}
.app-content {
  width: 100%; max-width: var(--content-max-width);
  margin: 0 auto; padding: var(--page-padding);
}

@media (max-width: 768px) {
  .app-layout, .app-layout.sidebar-collapsed { grid-template-columns: 1fr; }
  .sidebar {
    position: fixed; inset: 0 auto 0 0; z-index: 50;
    width: var(--sidebar-width);
    transform: translateX(-100%);
    transition: transform var(--duration) var(--ease);
    box-shadow: var(--shadow-lg);
  }
  .sidebar.is-open { transform: translateX(0); }
  .sidebar-backdrop { position: fixed; inset: 0; z-index: 40; background: rgba(15, 23, 42, 0.5); }
}
```

`min-width: 0` on `.app-main` matters. Without it, a wide table inside a grid child forces the whole page to scroll horizontally instead of scrolling within its own wrapper.
