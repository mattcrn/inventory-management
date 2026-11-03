<template>
  <div class="language-switcher">
    <button
      class="language-button"
      :aria-label="localeName"
      :title="localeName"
      aria-haspopup="true"
      :aria-expanded="isDropdownOpen"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        class="globe-icon"
      >
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
      </svg>
      <span class="language-label">{{ localeName }}</span>
      <svg
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        class="dropdown-item"
        :class="{ active: currentLocale === locale }"
        @mousedown.prevent="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg
          v-if="currentLocale === locale"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          class="check-icon"
        >
          <path d="M4 9L7.5 12.5L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const handleBlur = () => {
  // Delay to allow mousedown events on dropdown items to fire first
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

const selectLanguage = (locale) => {
  setLocale(locale)
  isDropdownOpen.value = false
}
</script>

<style scoped>
.language-switcher {
  position: relative;
}

/* Styled for the dark sidebar; the dropdown itself stays a light floating panel */
.language-button {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: calc(100% - var(--space-6));
  height: var(--control-height);
  margin: 0 var(--space-3);
  padding: 0 var(--space-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--duration) var(--ease);
  font-family: inherit;
  font-size: var(--text-sm);
  color: var(--sidebar-text);
}

.language-button:hover {
  background: var(--sidebar-item-hover);
  color: var(--sidebar-text-strong);
}

.language-button:focus-visible {
  outline: 2px solid var(--sidebar-indicator);
}

.globe-icon {
  color: var(--sidebar-text-muted);
  flex-shrink: 0;
}

.language-label {
  font-weight: 500;
  white-space: nowrap;
}

.chevron {
  color: var(--sidebar-text-muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
  margin-left: auto;
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  /* Opens upward: the switcher lives at the bottom of the sidebar */
  bottom: calc(100% + 0.5rem);
  left: var(--space-3);
  min-width: 160px;
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.dropdown-item:hover {
  background: var(--color-bg);
}

.dropdown-item.active {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.language-name {
  flex: 1;
}

.check-icon {
  color: var(--color-accent);
  flex-shrink: 0;
}
</style>
