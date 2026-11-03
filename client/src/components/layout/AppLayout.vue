<template>
  <div class="app-layout" :class="{ 'sidebar-collapsed': collapsed }">
    <AppSidebar
      :collapsed="collapsed && !isMobile"
      :mobile-open="mobileOpen"
      @toggle-collapsed="toggleCollapsed"
    >
      <template #footer>
        <slot name="sidebar-footer" />
      </template>
    </AppSidebar>
    <!-- Mobile backdrop: clicking it closes the drawer -->
    <div v-if="mobileOpen" class="sidebar-backdrop" @click="closeMobile" />

    <div class="app-main">
      <AppTopbar :mobile-open="mobileOpen" @toggle-menu="mobileOpen = !mobileOpen" />
      <main class="app-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'

const STORAGE_KEY = 'sidebar-collapsed'

// Storage can throw (private mode, blocked cookies); the UI must still work without it.
const readCollapsed = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

const collapsed = ref(readCollapsed())
const mobileOpen = ref(false)

// The icon rail only applies on desktop; the mobile drawer always shows full labels.
const mobileQuery = window.matchMedia('(max-width: 768px)')
const isMobile = ref(mobileQuery.matches)
const onMediaChange = (event) => {
  isMobile.value = event.matches
  if (!event.matches) mobileOpen.value = false
}
const route = useRoute()

const toggleCollapsed = () => {
  collapsed.value = !collapsed.value
  try {
    localStorage.setItem(STORAGE_KEY, collapsed.value ? '1' : '0')
  } catch {
    // ignore: preference just won't persist
  }
}

const closeMobile = () => {
  mobileOpen.value = false
}

// Navigating closes the drawer on phones
watch(() => route.fullPath, closeMobile)

const onKeydown = (event) => {
  if (event.key === 'Escape' && mobileOpen.value) closeMobile()
}
onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  mobileQuery.addEventListener('change', onMediaChange)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  mobileQuery.removeEventListener('change', onMediaChange)
})
</script>

<style scoped>
.app-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  transition: grid-template-columns var(--duration) var(--ease);
}
.app-layout.sidebar-collapsed { grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr); }

/* min-width: 0 stops wide tables from forcing page-level horizontal scroll */
.app-main { min-width: 0; display: flex; flex-direction: column; }
.app-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--page-padding);
}

@media (max-width: 768px) {
  .app-layout,
  .app-layout.sidebar-collapsed { grid-template-columns: minmax(0, 1fr); }
  .sidebar-backdrop {
    position: fixed;
    inset: 0;
    z-index: 40;
    background: rgba(15, 23, 42, 0.5);
  }
}
</style>
