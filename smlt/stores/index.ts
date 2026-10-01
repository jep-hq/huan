import { defineStore } from 'pinia'
import axios from 'axios'

export interface User {
  id: number
  email: string
  username: string
  authentik_id: string
}

export interface SparkJob {
  id: number
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  result?: string
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export const useJobStore = defineStore('job', {
  state: () => ({
    jobs: [] as SparkJob[],
    loading: false,
    error: null as string | null,
  }),

  actions: {
    async fetchJobs() {
      this.loading = true
      this.error = null
      const config = useRuntimeConfig()

      // Get token from localStorage
      const token = localStorage.getItem('auth_token')
      if (!token) {
        this.error = 'Not authenticated'
        this.loading = false
        return
      }

      try {
        const response = await axios.get(
          `${config.public.apiUrl}/spark/jobs`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        this.jobs = response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch jobs'
      } finally {
        this.loading = false
      }
    },

    async createJob() {
      this.loading = true
      this.error = null
      const config = useRuntimeConfig()

      // Get token from localStorage
      const token = localStorage.getItem('auth_token')
      if (!token) {
        this.error = 'Not authenticated'
        this.loading = false
        return
      }

      try {
        const response = await axios.post(
          `${config.public.apiUrl}/spark/jobs`,
          {},
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        this.jobs.unshift(response.data)
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to create job'
        throw error
      } finally {
        this.loading = false
      }
    },

    async getJob(jobId: string) {
      const config = useRuntimeConfig()

      // Get token from localStorage
      const token = localStorage.getItem('auth_token')
      if (!token) {
        this.error = 'Not authenticated'
        return
      }

      try {
        const response = await axios.get(
          `${config.public.apiUrl}/spark/jobs/${jobId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        // Update job in list if it exists
        const index = this.jobs.findIndex((j) => j.job_id === jobId)
        if (index !== -1) {
          this.jobs[index] = response.data
        }

        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch job'
        throw error
      }
    },
  },
})
