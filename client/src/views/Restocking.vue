<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// NOTE: This view deliberately does NOT use useFilters/FilterBar. Restocking is
// planned against the full forecast and the full inventory; time period,
// warehouse, category and status filters would silently shrink the candidate
// list and make the budget math misleading.

const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

const forecasts = ref([])
const inventory = ref([])
const loading = ref(true)
const error = ref(null)

const budget = ref(0)
// Per-SKU editable state: { [sku]: { include: boolean, quantity: number } }
const selection = ref({})

const submitting = ref(false)
const submitError = ref(null)
const placedOrder = ref(null)

const TREND_RANK = { increasing: 3, stable: 2, decreasing: 1 }

// Work in integer cents to avoid floating point drift in budget comparisons.
const toCents = (amount) => Math.round(amount * 100)

// Budget (slider) is shown in whole currency units; every computed money total
// (selected, remaining, line totals, order total) shows cents in USD so values
// like $3,099.60 are not misleadingly rounded. JPY is always whole yen.
const formatBudget = (amount) => formatCurrency(amount, currentCurrency.value)
const formatMoney = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)
const formatUnit = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)

const formatDate = (dateString) => {
  const d = new Date(dateString)
  if (isNaN(d.getTime())) return dateString
  return d.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

// Demand growth % of forecast vs. current demand (0 when current demand is 0).
const growthPct = (f) => (f.current_demand > 0 ? (f.forecasted_demand - f.current_demand) / f.current_demand : 0)

// Candidates: recommended qty = forecast - on hand (on hand matched by SKU, 0 if
// no match). Zero-qty items are dropped. Ranked by trend, then growth % desc.
const candidates = computed(() => {
  const onHandBySku = new Map()
  for (const item of inventory.value) {
    onHandBySku.set(item.sku, (onHandBySku.get(item.sku) || 0) + (item.quantity_on_hand || 0))
  }
  return forecasts.value
    .map(f => {
      const onHand = onHandBySku.get(f.item_sku) || 0
      return {
        sku: f.item_sku,
        name: f.item_name,
        trend: f.trend,
        forecasted: f.forecasted_demand,
        onHand,
        growth: growthPct(f),
        unitCost: f.unit_cost,
        leadTime: f.lead_time_days,
        recommendedQty: Math.max(f.forecasted_demand - onHand, 0)
      }
    })
    .filter(c => c.recommendedQty > 0)
    .sort((a, b) => (TREND_RANK[b.trend] || 0) - (TREND_RANK[a.trend] || 0) || b.growth - a.growth)
})

// Slider max = cost of every candidate at full qty, rounded up to the step.
const sliderStep = computed(() => {
  const total = fullCost.value
  if (total >= 100000) return 1000
  if (total >= 10000) return 100
  return 10
})
const fullCost = computed(() =>
  candidates.value.reduce((sum, c) => sum + c.recommendedQty * c.unitCost, 0)
)
const sliderMax = computed(() => Math.ceil(fullCost.value / sliderStep.value) * sliderStep.value)

// Greedy fill: walk the ranked list; take the full qty if it fits in the
// remaining budget, otherwise take as many units as still fit (if >= 1). We keep
// going after a partial/skipped item because later, cheaper items may still fit.
const greedyQuantities = (budgetAmount) => {
  let remaining = toCents(budgetAmount)
  const result = {}
  for (const c of candidates.value) {
    const unitCents = toCents(c.unitCost)
    const fullCents = unitCents * c.recommendedQty
    let qty = 0
    if (unitCents <= 0) {
      qty = c.recommendedQty
    } else if (fullCents <= remaining) {
      qty = c.recommendedQty
    } else {
      qty = Math.floor(remaining / unitCents)
    }
    result[c.sku] = qty
    remaining -= qty * unitCents
  }
  return result
}

// Seed the editable table from the greedy recommendation. Called whenever the
// budget changes, so manual edits only persist until the next budget change.
const reseed = () => {
  const greedy = greedyQuantities(budget.value)
  const next = {}
  for (const c of candidates.value) {
    const qty = greedy[c.sku] || 0
    next[c.sku] = { include: qty > 0, quantity: qty }
  }
  selection.value = next
}

// Only fires when the budget value actually changes (Vue skips identical
// values). flush: 'sync' means the re-seed happens immediately on assignment,
// so callers (loadData, planAnother) can rely on ordering: assign budget, then
// optionally override the seeded selection.
watch(budget, reseed, { flush: 'sync' })

// Empty plan: every row unticked with quantity 0.
const clearSelection = () => {
  const next = {}
  for (const c of candidates.value) next[c.sku] = { include: false, quantity: 0 }
  selection.value = next
}

// Default budget = 50% of slider max, snapped to the step.
const defaultBudget = computed(() => Math.round(sliderMax.value / 2 / sliderStep.value) * sliderStep.value)

// Effective quantity for a row: 0 if unchecked or the input is invalid/empty.
const effectiveQty = (sku) => {
  const row = selection.value[sku]
  if (!row || !row.include) return 0
  const q = Math.floor(Number(row.quantity))
  return Number.isFinite(q) && q > 0 ? q : 0
}

const rows = computed(() =>
  candidates.value.map(c => ({ ...c, lineTotal: effectiveQty(c.sku) * c.unitCost }))
)

const selectedRows = computed(() => rows.value.filter(r => effectiveQty(r.sku) > 0))
const selectedTotal = computed(() => selectedRows.value.reduce((s, r) => s + r.lineTotal, 0))
const remaining = computed(() => (toCents(budget.value) - toCents(selectedTotal.value)) / 100)
const overBudget = computed(() => remaining.value < 0)
const maxLeadTime = computed(() => selectedRows.value.reduce((m, r) => Math.max(m, r.leadTime), 0))
const canPlace = computed(() => !submitting.value && !overBudget.value && selectedRows.value.length > 0)

const blockReason = computed(() => {
  if (overBudget.value) return t('restocking.overBudget')
  if (selectedRows.value.length === 0) return t('restocking.nothingSelected')
  return ''
})

const placeOrder = async () => {
  // Guard in the handler itself (not only :disabled) so a double-click, or a
  // click right after success, can never submit the same order twice.
  if (submitting.value || placedOrder.value || !canPlace.value) return
  submitting.value = true
  submitError.value = null
  try {
    placedOrder.value = await api.createRestockingOrder({
      budget: budget.value,
      items: selectedRows.value.map(r => ({ item_sku: r.sku, quantity: effectiveQty(r.sku) }))
    })
  } catch (err) {
    const detail = err.response?.data?.detail
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail) ? detail.map(d => d.msg).join('; ') : err.message
    submitError.value = t('restocking.placeError', { message })
  } finally {
    submitting.value = false
  }
}

// Start a fresh plan from an empty selection so the user must make a
// deliberate choice instead of re-submitting the identical recommendation.
const planAnother = () => {
  placedOrder.value = null
  submitError.value = null
  budget.value = defaultBudget.value // may trigger the sync re-seed...
  clearSelection() // ...which we then override with an empty plan
}

const loadData = async () => {
  loading.value = true
  error.value = null
  try {
    const [forecastData, inventoryData] = await Promise.all([
      api.getDemandForecasts(),
      api.getInventory()
    ])
    forecasts.value = forecastData
    inventory.value = inventoryData
    // Setting the budget triggers the (sync) watcher, which seeds the table.
    // Only seed explicitly if the value did not change and the watcher skipped.
    const before = budget.value
    budget.value = defaultBudget.value
    if (budget.value === before) reseed()
  } catch (err) {
    console.error(err)
    error.value = t('restocking.loadError', { message: err.message })
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="placedOrder" class="card success-panel">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.success.title') }}</h3>
      </div>
      <div class="success-grid">
        <div>
          <div class="stat-label">{{ t('restocking.success.orderNumber') }}</div>
          <div class="success-value">{{ placedOrder.order_number }}</div>
        </div>
        <div>
          <div class="stat-label">{{ t('restocking.success.total') }}</div>
          <div class="success-value">{{ formatMoney(placedOrder.total_cost) }}</div>
        </div>
        <div>
          <div class="stat-label">{{ t('restocking.success.expectedDelivery') }}</div>
          <div class="success-value">{{ formatDate(placedOrder.expected_delivery) }}</div>
        </div>
      </div>
      <div class="actions">
        <router-link to="/orders" class="btn-primary">{{ t('restocking.success.viewOrders') }}</router-link>
        <button type="button" class="btn-secondary" @click="planAnother">{{ t('restocking.success.newOrder') }}</button>
      </div>
    </div>

    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-value">{{ formatBudget(budget) }}</span>
        </div>
        <input
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="sliderMax"
          :step="sliderStep"
          :aria-label="t('restocking.budget')"
        />
        <div class="slider-scale">
          <span>{{ formatBudget(0) }}</span>
          <span>{{ formatBudget(sliderMax) }}</span>
        </div>
        <p class="hint">{{ t('restocking.budgetHint') }}</p>
        <p class="hint hint-warning">{{ t('restocking.resetHint') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatBudget(budget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.selectedTotal') }}</div>
          <div class="stat-value">{{ formatMoney(selectedTotal) }}</div>
        </div>
        <div :class="['stat-card', overBudget ? 'danger' : 'success']">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatMoney(remaining) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemCount') }}</div>
          <div class="stat-value">{{ selectedRows.length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.leadTime') }}</div>
          <div class="stat-value">{{ t('restocking.days', { count: maxLeadTime }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.candidates') }} ({{ rows.length }})</h3>
        </div>
        <div v-if="rows.length === 0" class="empty-state">{{ t('restocking.noCandidates') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th class="col-include">{{ t('restocking.table.include') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="numeric">{{ t('restocking.table.recommended') }}</th>
                <th class="numeric">{{ t('restocking.table.quantity') }}</th>
                <th class="numeric">{{ t('restocking.table.unitCost') }}</th>
                <th class="numeric">{{ t('restocking.table.lineTotal') }}</th>
                <th class="numeric">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.sku">
                <td class="col-include">
                  <input
                    v-model="selection[row.sku].include"
                    type="checkbox"
                    :aria-label="`${t('restocking.table.include')} ${row.sku}`"
                  />
                </td>
                <td>
                  <strong>{{ translateProductName(row.name) }}</strong>
                  <div class="sku">{{ row.sku }}</div>
                </td>
                <td>
                  <span :class="['badge', row.trend]">{{ t(`restocking.trend.${row.trend}`) }}</span>
                </td>
                <td class="numeric">{{ row.recommendedQty.toLocaleString() }}</td>
                <td class="numeric">
                  <input
                    v-model.number="selection[row.sku].quantity"
                    type="number"
                    min="0"
                    step="1"
                    class="input qty-input"
                    :aria-label="`${t('restocking.table.quantity')} ${row.sku}`"
                  />
                </td>
                <td class="numeric">{{ formatUnit(row.unitCost) }}</td>
                <td class="numeric"><strong>{{ formatMoney(row.lineTotal) }}</strong></td>
                <td class="numeric">{{ t('restocking.days', { count: row.leadTime }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="order-actions">
        <button type="button" class="btn-primary" :disabled="!canPlace" @click="placeOrder">
          {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
        <span v-if="blockReason" class="block-reason">{{ blockReason }}</span>
      </div>
      <div v-if="submitError" class="error">{{ submitError }}</div>
    </div>
  </div>
</template>

<style scoped>
.budget-value {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

/* Custom range: accent-colored track and thumb. Native appearance is removed so
   Chromium/Firefox/Safari render the same; the thumb keeps the global focus ring. */
.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  display: block;
  width: 100%;
  height: var(--space-6);
  background: transparent;
  cursor: pointer;
}

.budget-slider::-webkit-slider-runnable-track {
  height: var(--space-2);
  border-radius: var(--radius-full);
  background: var(--color-border-strong);
}

.budget-slider::-moz-range-track {
  height: var(--space-2);
  border-radius: var(--radius-full);
  background: var(--color-border-strong);
}

.budget-slider::-moz-range-progress {
  height: var(--space-2);
  border-radius: var(--radius-full);
  background: var(--color-accent);
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: var(--space-5);
  height: var(--space-5);
  /* (track height - thumb height) / 2 centers the thumb on the track */
  margin-top: calc((var(--space-2) - var(--space-5)) / 2);
  border-radius: var(--radius-full);
  background: var(--color-accent);
  border: 2px solid var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.budget-slider::-moz-range-thumb {
  width: var(--space-5);
  height: var(--space-5);
  box-sizing: border-box;
  border-radius: var(--radius-full);
  background: var(--color-accent);
  border: 2px solid var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.budget-slider:focus-visible {
  outline: none;
}

.budget-slider:focus-visible::-webkit-slider-thumb {
  box-shadow: var(--focus-ring);
}

.budget-slider:focus-visible::-moz-range-thumb {
  box-shadow: var(--focus-ring);
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
}

.hint {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  margin: var(--space-2) 0 0;
}

.hint-warning {
  color: var(--color-warning-text);
}

.sku {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.col-include {
  width: var(--space-10);
}

.col-include input {
  accent-color: var(--color-accent);
}

.qty-input {
  width: 96px;
  height: var(--control-height-sm);
  font-size: var(--text-sm);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.order-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
  margin-top: var(--space-6);
}

.block-reason {
  color: var(--color-danger-text);
  font-size: var(--text-sm);
}

/* router-link renders an anchor with .btn-primary; strip the underline */
.btn-primary,
.btn-secondary {
  text-decoration: none;
}

.success-panel {
  border-color: var(--color-success);
}

.success-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

.success-value {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-success-text);
  font-variant-numeric: tabular-nums;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}
</style>
