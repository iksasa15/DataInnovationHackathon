import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: { name: 'home' },
    },
  ],
})

export default router
