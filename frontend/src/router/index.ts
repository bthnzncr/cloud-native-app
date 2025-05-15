import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import PoliticsView from '@/views/PoliticsView.vue'
import BusinessView from '@/views/BusinessView.vue'
import EntertainmentView from '@/views/EntertainmentView.vue'
import SearchView from '@/views/SearchView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/politics',
      name: 'politics',
      component: PoliticsView
    },
    {
      path: '/business',
      name: 'business',
      component: BusinessView
    },
    {
      path: '/entertainment',
      name: 'entertainment',
      component: EntertainmentView
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView
    }
  ],
  scrollBehavior(to, from, savedPosition) {
    // If the user has a saved position (e.g., they hit back), use that
    if (savedPosition) {
      return savedPosition;
    }
    
    // If the user is navigating between category pages, don't scroll
    const categoryRoutes = ['/politics', '/business', '/entertainment', '/'];
    if (categoryRoutes.includes(from.path) && categoryRoutes.includes(to.path)) {
      return { top: window.pageYOffset || document.documentElement.scrollTop };
    }
    
    // Otherwise, scroll to the top
    return { top: 0 };
  }
})

export default router