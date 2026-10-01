# Frontend Migration Checklist

## Files to Update

### 1. Update nuxt.config.ts

Change runtime config to use Zitadel:

```typescript
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8001',
      zitadelUrl: process.env.NUXT_PUBLIC_ZITADEL_URL || 'https://your-zitadel-instance.com',
      zitadelClientId: process.env.NUXT_PUBLIC_ZITADEL_CLIENT_ID || '',
    }
  }
})
```

### 2. Update all Vue components using authentication

Replace all instances of `useAuthentik` with `useZitadel`:

**Example - layouts/default.vue:**

```vue
<script setup lang="ts">
import { useZitadel } from '~/composables/useZitadel'

const { isAuthenticated, user, login, logout, initialize } = useZitadel()

// Initialize auth on mount
onMounted(() => {
  initialize()
})
</script>

<template>
  <div>
    <header>
      <nav>
        <div v-if="isAuthenticated">
          <span>Welcome, {{ user?.name || user?.email }}</span>
          <button @click="logout">Logout</button>
        </div>
        <div v-else>
          <button @click="login">Login</button>
        </div>
      </nav>
    </header>
    <main>
      <slot />
    </main>
  </div>
</template>
```

**Example - pages/auth/callback.vue:**

```vue
<script setup lang="ts">
import { useZitadel } from '~/composables/useZitadel'

const route = useRoute()
const router = useRouter()
const { handleCallback } = useZitadel()

onMounted(async () => {
  const code = route.query.code as string
  const state = route.query.state as string

  if (!code || !state) {
    console.error('Missing code or state parameter')
    await router.push('/')
    return
  }

  try {
    const redirectPath = await handleCallback(code, state)
    await router.push(redirectPath)
  } catch (error) {
    console.error('Authentication failed:', error)
    await router.push('/')
  }
})
</script>

<template>
  <div class="flex items-center justify-center min-h-screen">
    <div class="text-center">
      <h2 class="text-xl mb-4">Authenticating...</h2>
      <div class="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent mx-auto"></div>
    </div>
  </div>
</template>
```

### 3. Update API client/middleware

If you have axios interceptors or middleware using auth tokens:

```typescript
// plugins/axios.ts or similar
import axios from 'axios'
import { useZitadel } from '~/composables/useZitadel'

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()
  const { getToken } = useZitadel()

  const api = axios.create({
    baseURL: config.public.apiUrl,
  })

  // Add token to requests
  api.interceptors.request.use((config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  return {
    provide: {
      api,
    },
  }
})
```

### 4. Update protected route middleware

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { isAuthenticated } = useZitadel()

  if (!isAuthenticated.value) {
    return navigateTo('/')
  }
})
```

Usage in pages:
```vue
<script setup lang="ts">
definePageMeta({
  middleware: ['auth']
})
</script>
```

## Testing Checklist

- [ ] Login redirects to Zitadel
- [ ] Successful login returns to app
- [ ] User info is displayed correctly
- [ ] Protected routes require authentication
- [ ] API calls include Bearer token
- [ ] Logout clears session and redirects to Zitadel
- [ ] Token refresh works (if implemented)
- [ ] State parameter validates correctly
- [ ] Error handling works for failed auth

## Optional: Remove old Authentik composable

After verifying everything works:

```bash
rm smlt/composables/useAuthentik.ts
```

## Search for references

Find all files that might still reference Authentik:

```bash
# In smlt directory
grep -r "authentik" --include="*.vue" --include="*.ts" --include="*.js"
grep -r "useAuthentik" --include="*.vue" --include="*.ts" --include="*.js"
```
