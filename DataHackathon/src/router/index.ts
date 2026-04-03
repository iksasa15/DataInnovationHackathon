import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

/** GitHub Pages: روابط مباشرة مثل /REPO/analysis تعطي 404 بدون hash */
const useHash =
  import.meta.env.VITE_GH_PAGES === 'true'

const router = createRouter({
  history: useHash
    ? createWebHashHistory()
    : createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/survey',
      name: 'survey',
      component: () => import('../views/SurveyView.vue'),
    },
    {
      path: '/analysis',
      name: 'analysis',
      component: () => import('../views/ExcelView.vue'),
    },
    { path: '/excel', redirect: '/analysis' },
    { path: '/csv', redirect: '/analysis' },
    {
      path: '/tests',
      name: 'tests',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: () => import('../views/PrivacyView.vue'),
    },
    { path: '/about', redirect: '/tests' },
    {
      path: '/:pathMatch(.*)*',
      redirect: { name: 'home' },
    },
  ],
})

export default router
