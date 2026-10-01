<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50">
    <div class="text-center">
      <div v-if="loading" class="space-y-4">
        <div class="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
        <p class="text-lg text-gray-600">Completing authentication...</p>
      </div>

      <div v-else-if="error" class="space-y-4">
        <div class="text-red-600">
          <svg class="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 class="text-xl font-semibold text-gray-900">Authentication Failed</h2>
        <p class="text-gray-600">{{ error }}</p>
        <button
          @click="goHome"
          class="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          Return Home
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthentik } from '../../../composables/useAuthentik'

const router = useRouter()
const { handleCallback } = useAuthentik()
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search)
  const code = urlParams.get('code')
  const state = urlParams.get('state')
  const errorParam = urlParams.get('error')

  if (errorParam) {
    error.value = urlParams.get('error_description') || 'Authentication error'
    loading.value = false
    return
  }

  if (!code || !state) {
    error.value = 'Missing authentication parameters'
    loading.value = false
    return
  }

  try {
    const redirectPath = await handleCallback(code, state)
    router.push(redirectPath)
  } catch (err: any) {
    error.value = err.message || 'Authentication failed'
    loading.value = false
  }
})

const goHome = () => {
  router.push('/')
}
</script>
