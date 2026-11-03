<template>
  <header class="app-topbar">
    <button
      type="button"
      class="menu-button"
      :aria-expanded="mobileOpen"
      aria-controls="app-sidebar"
      :aria-label="mobileOpen ? t('nav.closeMenu') : t('nav.openMenu')"
      @click="$emit('toggle-menu')"
    >
      <svg viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
        <path d="M3 5h14M3 10h14M3 15h14" />
      </svg>
    </button>

    <!-- Breadcrumb rather than a second big title: the view's own page header
         already carries the heading, so repeating it here looked duplicated. -->
    <nav class="topbar-title" aria-label="Breadcrumb">
      <span v-if="section" class="crumb-section">{{ section }}</span>
      <span v-if="section" class="crumb-sep" aria-hidden="true">/</span>
      <span class="crumb-current" aria-current="page">{{ title }}</span>
    </nav>

    <div v-if="showFilters" class="topbar-filters" role="group" :aria-label="t('nav.filtersLabel')">
      <FilterBar />
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../../composables/useI18n'
import FilterBar from '../FilterBar.vue'

defineProps({
  mobileOpen: { type: Boolean, default: false }
})
defineEmits(['toggle-menu'])

const { t } = useI18n()
const route = useRoute()

// Title and filter visibility come from route meta (see main.js)
const title = computed(() => (route.meta.titleKey ? t(route.meta.titleKey) : ''))
const section = computed(() => (route.meta.sectionKey ? t(route.meta.sectionKey) : ''))
const showFilters = computed(() => route.meta.showFilters === true)
</script>

<style scoped>
.app-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  min-height: var(--topbar-height);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) var(--page-padding);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.topbar-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
  white-space: nowrap;
  letter-spacing: -0.01em;
}
.topbar-filters {
  flex: 1;
  min-width: 0;
  display: flex;
  justify-content: flex-end;
}
.menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  flex-shrink: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
}
.menu-button:hover { background: var(--color-surface-muted); }
.menu-button:focus-visible { outline: none; box-shadow: var(--focus-ring); }

@media (max-width: 768px) {
  .menu-button { display: inline-flex; }
  /* Filters drop below the title row and scroll horizontally if they do not fit */
  .app-topbar { flex-wrap: wrap; row-gap: var(--space-2); }
  .topbar-filters { flex-basis: 100%; justify-content: flex-start; overflow-x: auto; padding-bottom: var(--space-1); }
  .topbar-title { flex: 1; }
}
.crumb-section { color: var(--color-text-muted); }
.crumb-sep { color: var(--color-text-subtle); }
.crumb-current { font-weight: var(--weight-semibold); }
</style>
