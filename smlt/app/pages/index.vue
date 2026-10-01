<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container mx-auto px-4 py-8">
      <!-- Header -->
      <div class="mb-8 flex items-center justify-between">
        <h1 class="text-3xl font-bold text-gray-900">Huan - Spark Job Manager</h1>
        <div v-if="isAuthenticated" class="flex items-center gap-4">
          <span class="text-sm text-gray-600">{{ user?.email }}</span>
          <Button @click="handleLogout" variant="outline" size="sm">Logout</Button>
        </div>
      </div>

      <!-- Login Section -->
      <div v-if="!isAuthenticated" class="mx-auto max-w-md rounded-lg bg-white p-8 shadow">
        <h2 class="mb-4 text-xl font-semibold">Login with Authentik</h2>
        <p class="mb-6 text-sm text-gray-600">
          Please login with your Authentik account to manage Spark jobs.
        </p>
        <Button @click="handleAuthentikLogin" class="w-full" :disabled="loading">
          {{ loading ? 'Redirecting...' : 'Login with Authentik' }}
        </Button>
        <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
      </div>

      <!-- Main Content -->
      <div v-else class="space-y-6">
        <!-- Create Job Button -->
        <div class="rounded-lg bg-white p-6 shadow">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">Spark Jobs</h2>
              <p class="mt-1 text-sm text-gray-600">
                Click the button to trigger a Spark job that will run in the background.
              </p>
            </div>
            <Button
              @click="handleCreateJob"
              :disabled="jobStore.loading"
              size="lg"
            >
              {{ jobStore.loading ? 'Creating...' : 'Run Spark Job' }}
            </Button>
          </div>

          <!-- Success Message -->
          <div v-if="successMessage" class="mt-4 rounded-md bg-green-50 p-4">
            <p class="text-sm text-green-800">{{ successMessage }}</p>
          </div>

          <!-- Error Message -->
          <div v-if="jobStore.error" class="mt-4 rounded-md bg-red-50 p-4">
            <p class="text-sm text-red-800">{{ jobStore.error }}</p>
          </div>
        </div>

        <!-- Jobs List -->
        <div class="rounded-lg bg-white shadow">
          <div class="border-b border-gray-200 px-6 py-4">
            <h3 class="text-lg font-semibold text-gray-900">Job History</h3>
          </div>

          <div v-if="jobStore.loading && jobStore.jobs.length === 0" class="p-6 text-center">
            <p class="text-gray-500">Loading jobs...</p>
          </div>

          <div v-else-if="jobStore.jobs.length === 0" class="p-6 text-center">
            <p class="text-gray-500">No jobs yet. Click the button above to create one!</p>
          </div>

          <div v-else class="divide-y divide-gray-200">
            <div
              v-for="job in jobStore.jobs"
              :key="job.id"
              class="px-6 py-4 hover:bg-gray-50"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-3">
                    <code class="text-sm font-mono text-gray-900">{{ job.job_id }}</code>
                    <span
                      class="inline-flex rounded-full px-2 py-1 text-xs font-semibold"
                      :class="{
                        'bg-yellow-100 text-yellow-800': job.status === 'pending',
                        'bg-blue-100 text-blue-800': job.status === 'running',
                        'bg-green-100 text-green-800': job.status === 'completed',
                        'bg-red-100 text-red-800': job.status === 'failed',
                      }"
                    >
                      {{ job.status }}
                    </span>
                  </div>
                  <p class="mt-1 text-sm text-gray-500">
                    Created: {{ formatDate(job.created_at) }}
                  </p>
                  <p v-if="job.completed_at" class="text-sm text-gray-500">
                    Completed: {{ formatDate(job.completed_at) }}
                  </p>
                  <div v-if="job.result" class="mt-2 rounded bg-gray-50 p-2">
                    <p class="text-xs font-semibold text-gray-700">Result:</p>
                    <pre class="mt-1 text-xs text-gray-600 whitespace-pre-wrap">{{ job.result }}</pre>
                  </div>
                  <div v-if="job.error_message" class="mt-2 rounded bg-red-50 p-2">
                    <p class="text-xs font-semibold text-red-700">Error:</p>
                    <pre class="mt-1 text-xs text-red-600 whitespace-pre-wrap">{{ job.error_message }}</pre>
                  </div>
                </div>
                <Button
                  @click="refreshJob(job.job_id)"
                  variant="ghost"
                  size="sm"
                  v-if="job.status === 'pending' || job.status === 'running'"
                >
                  Refresh
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthentik } from '../../composables/useAuthentik'
import { useJobStore } from '../../stores'
import { Button } from '~/components/ui/button'

const { isAuthenticated, user, login, logout, initialize, error, loading } = useAuthentik()
const jobStore = useJobStore()
const successMessage = ref<string | null>(null)
let intervalId: NodeJS.Timeout | null = null

onMounted(() => {
  // Initialize auth from localStorage
  initialize()

  // If authenticated, fetch jobs
  if (isAuthenticated.value) {
    jobStore.fetchJobs()

    // Auto-refresh jobs every 5 seconds if there are active jobs
    intervalId = setInterval(() => {
      const hasActiveJobs = jobStore.jobs.some(
        job => job.status === 'pending' || job.status === 'running'
      )
      if (hasActiveJobs && isAuthenticated.value) {
        jobStore.fetchJobs()
      }
    }, 5000)
  }
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})

const handleAuthentikLogin = () => {
  login()
}

const handleLogout = () => {
  logout()
}

const handleCreateJob = async () => {
  try {
    successMessage.value = null
    await jobStore.createJob()
    successMessage.value = 'Spark job created successfully and is now running in the background!'

    // Clear success message after 5 seconds
    setTimeout(() => {
      successMessage.value = null
    }, 5000)
  } catch (error) {
    console.error('Failed to create job:', error)
  }
}

const refreshJob = async (jobId: string) => {
  try {
    await jobStore.getJob(jobId)
  } catch (error) {
    console.error('Failed to refresh job:', error)
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}
</script>
