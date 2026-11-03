import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './styles/tokens.css'
import './styles/components.css'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'
import Restocking from './views/Restocking.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard, meta: { sectionKey: 'nav.sectionOperations', titleKey: 'nav.overview', showFilters: true } },
    { path: '/inventory', component: Inventory, meta: { sectionKey: 'nav.sectionOperations', titleKey: 'nav.inventory', showFilters: true } },
    { path: '/orders', component: Orders, meta: { sectionKey: 'nav.sectionOperations', titleKey: 'nav.orders', showFilters: true } },
    { path: '/demand', component: Demand, meta: { sectionKey: 'nav.sectionInsights', titleKey: 'nav.demandForecast', showFilters: true } },
    { path: '/restocking', component: Restocking, meta: { sectionKey: 'nav.sectionOperations', titleKey: 'nav.restocking', showFilters: false } },
    { path: '/spending', component: Spending, meta: { sectionKey: 'nav.sectionInsights', titleKey: 'nav.finance', showFilters: true } },
    { path: '/reports', component: Reports, meta: { sectionKey: 'nav.sectionInsights', titleKey: 'nav.reports', showFilters: true } }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
