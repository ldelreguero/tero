import { createRouter, createWebHistory, type RouteLocationNormalized, type NavigationGuardNext } from 'vue-router'
import auth from '@/services/auth'
import { useChatStore } from '@/composables/useChatStore'
import { useAgentStore } from '@/composables/useAgentStore'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/landing',
      component: () => import('@/pages/LandingPage.vue'),
      beforeEnter: async (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
        if (await auth.getUser()) {
          next('/')
          return
        }
        next()
      }
    },
    {
      path: '/',
      component: () => import('@/pages/MainPage.vue'),
      meta: {
        requiresAuth: true
      },
      children: [
        {
          path: 'discover',
          component: () => import('@/components/discover/DiscoverPanel.vue')
        },
        {
          path: 'dashboard', // remove this route in a future release
          redirect: '/console'
        },
        {
          path: 'console',
          component: () => import('@/pages/DashboardPage.vue'),
        }
      ]
    },
    {
      path: '/chat/:threadId',
      component: () => import('@/pages/MainPage.vue'),
      meta: {
        requiresAuth: true
      },
      children: [
        {
          path: '',
          component: () => import('@/pages/ChatPage.vue')
        }
      ]
    },
    {
      path: '/chat/:threadId/files/:fileId',
      component: () => import('@/pages/FilePreviewPage.vue'),
      meta: {
        requiresAuth: true
      }
    },
    {
      path: '/agents/:agentId/tools/:toolId/files/:fileId',
      component: () => import('@/pages/FilePreviewPage.vue'),
      meta: {
        requiresAuth: true
      }
    },
    {
      path: '/tools/:toolId/oauth-callback',
      component: () => import('@/pages/ToolAuthPage.vue'),
    },
    {
      path: '/agents/:agentId',
      component: () => import('@/pages/AgentEditorPage.vue'),
      meta: {
        requiresAuth: true
      }
    },
    {
      path: '/callback',
      component: () => import('@/pages/CallbackPage.vue')
    },
    {
      path: '/silent-renew',
      component: () => import('@/pages/SilentRenewPage.vue')
    },
    {
      path: '/logout',
      component: () => import('@/pages/LogoutPage.vue')
    },
    {
      path: '/unauthorized',
      component: () => import('@/pages/UnauthorizedPage.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/pages/NotFoundPage.vue')
    }
  ]
})

class VersionManager {
  private currentETag: string | null = null;
  private lastCheck: number = 0;
  private readonly CHECK_INTERVAL_MS: number = 10000;

  async updateETag() {
    if (Date.now() - this.lastCheck < this.CHECK_INTERVAL_MS) {
      return
    }
    try {
      const response = await fetch('/', { method: 'HEAD', cache: 'no-cache' })
      this.currentETag = response.headers.get('etag') || ''
      this.lastCheck = Date.now()
    } catch (error) {
      console.warn('Failed to get initial ETag:', error)
    }
  }

  async hasNewVersion(): Promise<boolean> {
    const lastETag = this.currentETag;
    await this.updateETag()
    return lastETag !== this.currentETag;
  }
}

const versionManager = new VersionManager();
versionManager.updateETag();

router.beforeEach(async (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  if (requiresAuth) {
    const user = await auth.getUser()
    if (!user) {
      next('/landing')
      return
    }
  }

  // This logic avoids 404 errors when the app is already loaded and a new version is deployed
  // due to assets paths changing in deployments since they include file hashes for proper caching
  // Check for from.matched to skip version check on initial load
  if (from.matched.length > 0 && await versionManager.hasNewVersion()) {
    sessionStorage.setItem('pendingNavigation', to.fullPath)
    window.location.reload()
  } else {
    next()
  }
})

// Restore intended navigation after reload
router.isReady().then(() => {
  const pendingPath = sessionStorage.getItem('pendingNavigation')
  if (pendingPath && pendingPath !== router.currentRoute.value.fullPath) {
    sessionStorage.removeItem('pendingNavigation')
    router.push(pendingPath)
  }
})

router.beforeResolve(async (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  if (to.path === "/") {
    try {
      const { addDefaultAgent } = useAgentStore();
      const { newChat } = useChatStore();
      const defaultAgent = await addDefaultAgent();
      await newChat(defaultAgent);
      next();
    } catch (error) {
      console.error(error);
      next('/discover');
    }
  } else {
    next();
  }
});

export default router
