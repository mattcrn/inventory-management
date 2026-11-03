<template>
  <aside
    id="app-sidebar"
    class="sidebar"
    :class="{ 'is-collapsed': collapsed, 'is-open': mobileOpen }"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
      <div v-if="!collapsed" class="brand-text">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-sub">{{ t('nav.subtitle') }}</span>
      </div>
    </div>

    <nav class="sidebar-nav" :aria-label="t('nav.mainNavigation')">
      <div v-for="section in sections" :key="section.id" class="nav-section">
        <p v-if="!collapsed" class="nav-section-title">{{ section.title }}</p>
        <hr v-else class="nav-section-divider" />
        <router-link
          v-for="item in section.items"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          active-class=""
          exact-active-class="is-active"
          :title="collapsed ? item.label : undefined"
          :aria-label="collapsed ? item.label : undefined"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path v-for="d in item.icon" :key="d" :d="d" />
          </svg>
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
        aria-controls="app-sidebar"
        :title="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        :aria-label="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        @click="$emit('toggle-collapsed')"
      >
        <svg class="nav-icon" :class="{ 'is-flipped': collapsed }" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M11.5 5L6.5 10l5 5" />
          <path d="M15 4v12" />
        </svg>
        <span v-if="!collapsed" class="nav-label">{{ t('nav.collapseSidebar') }}</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'

defineProps({
  collapsed: { type: Boolean, default: false },
  mobileOpen: { type: Boolean, default: false }
})
defineEmits(['toggle-collapsed'])

const { t } = useI18n()

const brandInitial = computed(() => t('nav.companyName').charAt(0))

// Each icon is a list of SVG path strings drawn on a 20x20 grid (stroke style).
// Overview is matched exactly via exact-active-class, so "/" is never active on other routes.
const sections = computed(() => [
  {
    id: 'operations',
    title: t('nav.sectionOperations'),
    items: [
      { to: '/', label: t('nav.overview'), icon: ['M3 3h6v6H3z', 'M11 3h6v6h-6z', 'M3 11h6v6H3z', 'M11 11h6v6h-6z'] },
      { to: '/inventory', label: t('nav.inventory'), icon: ['M3 6.5L10 3l7 3.5v7L10 17l-7-3.5z', 'M3 6.5L10 10l7-3.5', 'M10 10v7'] },
      { to: '/orders', label: t('nav.orders'), icon: ['M5 3h10v14H5z', 'M8 7h4', 'M8 10h4', 'M8 13h2'] },
      { to: '/restocking', label: t('nav.restocking'), icon: ['M16 10a6 6 0 11-1.76-4.24', 'M16 3v3.5h-3.5', 'M10 7v6', 'M7 10h6'] }
    ]
  },
  {
    id: 'insights',
    title: t('nav.sectionInsights'),
    items: [
      { to: '/demand', label: t('nav.demandForecast'), icon: ['M3 14l4-4 3 3 7-7', 'M12 6h5v5'] },
      { to: '/spending', label: t('nav.finance'), icon: ['M10 3v14', 'M13.5 6.5C13.5 5.4 12 4.5 10 4.5S6.5 5.4 6.5 6.8 8 9 10 9.5s3.5 1.1 3.5 2.7S12 15.5 10 15.5s-3.5-.9-3.5-2'] },
      { to: '/reports', label: t('nav.reports'), icon: ['M6 3h6l4 4v10H6z', 'M12 3v4h4', 'M8.5 11h5', 'M8.5 14h5'] }
    ]
  }
])
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 30;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  /* Visible (not auto) so footer dropdowns can extend beyond the sidebar edge; only the nav scrolls. */
  overflow: visible;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}
.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  background: var(--color-accent);
  color: var(--color-on-accent);
  font-weight: var(--weight-bold);
  font-size: var(--text-md);
}
.brand-text { display: flex; flex-direction: column; min-width: 0; line-height: var(--leading-tight); }
.brand-name {
  color: var(--sidebar-text-strong);
  font-weight: var(--weight-semibold);
  font-size: var(--text-base);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.brand-sub {
  color: var(--sidebar-text-muted);
  font-size: var(--text-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-4) 0;
}
.nav-section + .nav-section { margin-top: var(--space-4); }
.nav-section-title {
  padding: 0 var(--space-6);
  margin-bottom: var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--sidebar-text-muted);
}
.nav-section-divider {
  border: none;
  border-top: 1px solid var(--sidebar-border);
  margin: 0 var(--space-4) var(--space-2);
}
.nav-section:first-child .nav-section-divider { display: none; }

.nav-item,
.collapse-toggle {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: calc(100% - var(--space-6));
  height: var(--control-height);
  padding: 0 var(--space-3);
  margin: 0 var(--space-3) var(--space-1);
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--sidebar-text);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  text-decoration: none;
  cursor: pointer;
  text-align: left;
  transition: background-color var(--duration) var(--ease), color var(--duration) var(--ease);
}
.nav-item:hover,
.collapse-toggle:hover { background: var(--sidebar-item-hover); color: var(--sidebar-text-strong); }
.nav-item.is-active { background: var(--sidebar-item-active); color: var(--sidebar-text-strong); }
.nav-item.is-active::before {
  content: '';
  position: absolute;
  left: calc(-1 * var(--space-3));
  top: var(--space-2);
  bottom: var(--space-2);
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--sidebar-indicator);
}
.nav-item:focus-visible,
.collapse-toggle:focus-visible {
  outline: 2px solid var(--sidebar-indicator);
  outline-offset: 0;
}
.nav-icon { width: 20px; height: 20px; flex-shrink: 0; transition: transform var(--duration) var(--ease); }
.nav-icon.is-flipped { transform: rotate(180deg); }
.nav-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }

.sidebar-footer {
  flex-shrink: 0;
  padding: var(--space-3) 0;
  border-top: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

/* Collapsed rail: icon-only items, centered */
.is-collapsed .nav-item,
.is-collapsed .collapse-toggle {
  justify-content: center;
  padding: 0;
}
.is-collapsed .sidebar-brand { justify-content: center; padding: 0; }

/* Collapsed footer widgets: hide their text and chevrons (their markup is owned by the child components) */
.is-collapsed :deep(.language-label),
.is-collapsed :deep(.profile-name),
.is-collapsed :deep(.chevron) { display: none; }
.is-collapsed :deep(.language-button),
.is-collapsed :deep(.profile-button) { justify-content: center; padding: 0; }

@media (max-width: 768px) {
  /* Off-canvas drawer; the parent layout renders the backdrop */
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 50;
    width: var(--sidebar-width);
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform var(--duration) var(--ease), visibility 0s linear var(--duration);
    box-shadow: var(--shadow-lg);
  }
  .sidebar.is-open {
    transform: translateX(0);
    visibility: visible;
    transition: transform var(--duration) var(--ease), visibility 0s;
  }
  /* The collapse toggle is meaningless in the drawer */
  .collapse-toggle { display: none; }
}
</style>
