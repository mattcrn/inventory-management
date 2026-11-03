<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">Inventory Shortage Details</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="shortage-header">
              <div class="shortage-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <path d="M24 8L24 28M24 34L24 36" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                  <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="3"/>
                </svg>
              </div>
              <div class="shortage-title-section">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="badge priority-badge" :class="backlogItem.priority">
                {{ backlogItem.priority }} Priority
              </span>
            </div>

            <div class="shortage-summary">
              <div class="summary-card danger">
                <div class="summary-label">Shortage Amount</div>
                <div class="summary-value">{{ shortage }} units</div>
              </div>
              <div class="summary-card warning">
                <div class="summary-label">Days Delayed</div>
                <div class="summary-value">{{ backlogItem.days_delayed }} days</div>
              </div>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">Order ID</div>
                <div class="info-value order-id">{{ backlogItem.order_id }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Item SKU</div>
                <div class="info-value sku">{{ backlogItem.item_sku }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Quantity Needed</div>
                <div class="info-value">{{ backlogItem.quantity_needed }} units</div>
              </div>

              <div class="info-item">
                <div class="info-label">Quantity Available</div>
                <div class="info-value">{{ backlogItem.quantity_available }} units</div>
              </div>

              <div class="info-item">
                <div class="info-label">Expected Date</div>
                <div class="info-value">{{ formatDate(backlogItem.expected_date) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Status</div>
                <div class="info-value">
                  <span class="badge danger">Backordered</span>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">Close</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const { translateProductName } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
/* Base modal look comes from the global modal primitives; only size and stacking differ. */
.modal-overlay { z-index: 2000; } /* above the app shell / sidebar drawer */
.modal-container { max-width: 700px; }
.modal-body { flex: 1; }

.shortage-header {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-6);
}
.shortage-icon {
  width: 64px;
  height: 64px;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.shortage-title-section { flex: 1; min-width: 0; }
.item-name {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-1);
  overflow-wrap: anywhere;
}
.item-sku {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-family: ui-monospace, 'SFMono-Regular', Menlo, monospace;
}
/* Header priority uses the global .badge (high/medium/low modifiers) */
.priority-badge { flex-shrink: 0; text-transform: capitalize; }

.shortage-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}
.summary-card {
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid;
  min-width: 0;
}
.summary-card.danger { border-color: var(--color-danger); background: var(--color-danger-soft); }
.summary-card.warning { border-color: var(--color-warning); background: var(--color-warning-soft); }
.summary-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  margin-bottom: var(--space-2);
}
.summary-value {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}
.summary-card.danger .summary-value { color: var(--color-danger-text); }
.summary-card.warning .summary-value { color: var(--color-warning-text); }

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(160px, 100%), 1fr));
  gap: var(--space-6);
}
.info-item { display: flex; flex-direction: column; gap: var(--space-2); min-width: 0; }
.info-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}
.info-value {
  font-size: var(--text-base);
  color: var(--color-text);
  font-weight: var(--weight-medium);
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}
.info-value.order-id,
.info-value.sku {
  font-family: ui-monospace, 'SFMono-Regular', Menlo, monospace;
  color: var(--color-accent);
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active { transition: opacity var(--duration) var(--ease); }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
.modal-enter-active .modal-container,
.modal-leave-active .modal-container { transition: transform var(--duration) var(--ease); }
.modal-enter-from .modal-container,
.modal-leave-to .modal-container { transform: scale(0.95); }
</style>
