import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import { useSessionStore } from '../stores/useSessionStore'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: {
      title: '语音日历 - 登录'
    }
  },
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: {
      title: '语音日历 - 首页'
    }
  },
  {
    path: '/conversation',
    name: 'conversation',
    component: () => import('../views/ConversationView.vue'),
    meta: {
      title: '语音助手'
    }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
    meta: {
      title: '设置'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const sessionStore = useSessionStore()
  
  if (to.name !== 'login' && !sessionStore.isLoggedIn) {
    next({ name: 'login' })
  } else if (to.name === 'login' && sessionStore.isLoggedIn) {
    next({ name: 'home' })
  } else {
    if (to.meta.title) {
      document.title = to.meta.title as string
    }
    next()
  }
})

export default router
