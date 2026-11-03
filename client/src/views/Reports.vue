<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('reports.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="quarterlyData.length === 0 && monthlyData.length === 0" class="empty-state">
      {{ t('reports.noData') }}
    </div>
    <div v-else>
      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.totalRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.totalOrders') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>

      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterlyPerformance') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.table.quarter') }}</th>
                <th class="numeric">{{ t('reports.table.totalOrders') }}</th>
                <th class="numeric">{{ t('reports.table.totalRevenue') }}</th>
                <th class="numeric">{{ t('reports.table.avgOrderValue') }}</th>
                <th class="numeric">{{ t('reports.table.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td class="numeric">{{ q.total_orders }}</td>
                <td class="numeric">{{ formatMoney(q.total_revenue) }}</td>
                <td class="numeric">{{ formatMoney(q.avg_order_value) }}</td>
                <td class="numeric">
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyRevenueTrend') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="formatMoney(month.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonth') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.table.month') }}</th>
                <th class="numeric">{{ t('reports.table.orders') }}</th>
                <th class="numeric">{{ t('reports.table.revenue') }}</th>
                <th class="numeric">{{ t('reports.table.change') }}</th>
                <th class="numeric">{{ t('reports.table.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in monthOverMonthRows" :key="row.month">
                <td><strong>{{ formatMonth(row.month) }}</strong></td>
                <td class="numeric">{{ row.order_count }}</td>
                <td class="numeric">{{ formatMoney(row.revenue) }}</td>
                <td class="numeric">
                  <span v-if="row.change !== null" :class="row.changeClass">
                    {{ formatChange(row.change) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td class="numeric">
                  <span v-if="row.change !== null" :class="row.changeClass">
                    {{ formatGrowth(row.growth) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

export default {
  name: 'Reports',
  setup() {
    const { t, currentCurrency } = useI18n()
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])
        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        console.error('Failed to load reports:', err)
        error.value = t('reports.loadError', { message: err.message })
      } finally {
        loading.value = false
      }
    }

    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    onMounted(() => loadData())

    // Summary stats derived from the fetched data
    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.revenue, 0)
    )

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length > 0 ? totalRevenue.value / monthlyData.value.length : 0
    )

    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.order_count, 0)
    )

    const bestQuarter = computed(() => {
      let best = null
      for (const q of quarterlyData.value) {
        if (best === null || q.total_revenue > best.total_revenue) best = q
      }
      return best ? best.quarter : '-'
    })

    const maxRevenue = computed(() =>
      monthlyData.value.reduce((max, m) => Math.max(max, m.revenue), 0)
    )

    // Precompute change vs. previous month so the template needs no index lookups
    const monthOverMonthRows = computed(() =>
      monthlyData.value.map((month, index) => {
        if (index === 0) {
          return { ...month, change: null, growth: null, changeClass: '' }
        }
        const previous = monthlyData.value[index - 1].revenue
        const change = month.revenue - previous
        let changeClass = ''
        if (change > 0) changeClass = 'positive-change'
        else if (change < 0) changeClass = 'negative-change'
        return {
          ...month,
          change,
          // previous === 0 gives no meaningful percentage
          growth: previous === 0 ? null : (change / previous) * 100,
          changeClass
        }
      })
    )

    const formatMoney = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)

    // Format the absolute value and prefix the sign to avoid output like "$-123"
    const formatChange = (change) => {
      if (change > 0) return '+' + formatMoney(change)
      if (change < 0) return '-' + formatMoney(Math.abs(change))
      return formatMoney(0)
    }

    const formatGrowth = (growth) => {
      if (growth === null) return t('reports.notAvailable')
      const sign = growth > 0 ? '+' : ''
      return sign + growth.toFixed(1) + '%'
    }

    const formatMonth = (monthStr) => {
      const match = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(String(monthStr))
      if (!match) return monthStr
      const label = t(`months.${MONTH_KEYS[parseInt(match[2], 10) - 1]}`)
      return t('reports.monthLabel', { month: label, year: match[1] })
    }

    // Bar height scaled to 200px against the max computed once
    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0
      return (revenue / maxRevenue.value) * 200
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    return {
      t,
      loading,
      error,
      quarterlyData,
      monthlyData,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      monthOverMonthRows,
      formatMoney,
      formatChange,
      formatGrowth,
      formatMonth,
      getBarHeight,
      getFulfillmentClass
    }
  }
}
</script>

<style scoped>
/* min-width:0 lets this view shrink inside the shell instead of being
   stretched by its widest child (tables / chart). */
.reports { min-width: 0; }

/* Tables scroll inside their container; keep a min width so columns stay legible */
.reports-table { min-width: 560px; }
.reports-table tbody tr:hover { background: var(--color-surface-muted); }

/* Chart: the container scrolls horizontally on narrow screens rather than
   squeezing 12 rotated labels into the viewport. */
.chart-container {
  padding: var(--space-4) var(--space-2) var(--space-8);
  overflow-x: auto;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: var(--space-2);
  min-width: 480px;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1 1 0;
  min-width: 0;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: var(--chart-1);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: opacity var(--duration) var(--ease);
  cursor: pointer;
}

.bar:hover { opacity: 0.8; }

.bar-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: var(--space-6);
}

.positive-change {
  color: var(--color-success-text);
  font-weight: var(--weight-semibold);
}

.negative-change {
  color: var(--color-danger-text);
  font-weight: var(--weight-semibold);
}
</style>
