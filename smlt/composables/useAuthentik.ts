import { ref, computed } from 'vue'
import axios from 'axios'

interface AuthentikUser {
  sub: string
  email: string
  name: string
  preferred_username: string
  given_name?: string
  family_name?: string
}

interface AuthState {
  user: AuthentikUser | null
  token: string | null
  loading: boolean
  error: string | null
}

const state = ref<AuthState>({
  user: null,
  token: null,
  loading: false,
  error: null,
})

export function useAuthentik() {
  const config = useRuntimeConfig()
  const authentikUrl = config.public.authentikUrl
  const clientId = config.public.authentikClientId
  console.log('Authentik Client ID:', clientId, config.public.test)

  const isAuthenticated = computed(() => !!state.value.token)
  const user = computed(() => state.value.user)
  const loading = computed(() => state.value.loading)
  const error = computed(() => state.value.error)

  /**
   * Redirect to Authentik login page
   */
  const login = () => {
    const redirectUri = `${window.location.origin}/auth/callback`
    const authUrl = new URL(`${authentikUrl}/application/o/authorize/`)

    // Generate and store state for CSRF protection
    const stateParam = Math.random().toString(36).substring(7)
    sessionStorage.setItem('auth_state', stateParam)
    sessionStorage.setItem('auth_redirect', window.location.pathname)

    authUrl.searchParams.set('client_id', clientId)
    authUrl.searchParams.set('redirect_uri', redirectUri)
    authUrl.searchParams.set('response_type', 'code')
    authUrl.searchParams.set('scope', 'openid email profile')
    authUrl.searchParams.set('state', stateParam)

    window.location.href = authUrl.toString()
  }

  /**
   * Handle OAuth callback
   */
  const handleCallback = async (code: string, stateParam: string) => {
    state.value.loading = true
    state.value.error = null

    try {
      // Verify state
      const storedState = sessionStorage.getItem('auth_state')
      if (stateParam !== storedState) {
        throw new Error('Invalid state parameter')
      }

      // Exchange code for token via backend
      const response = await axios.post(`${config.public.apiUrl}/auth/callback`, {
        code,
        redirect_uri: `${window.location.origin}/auth/callback`,
      })

      state.value.token = response.data.access_token
      state.value.user = response.data.user

      // Store in localStorage
      localStorage.setItem('auth_token', response.data.access_token)
      localStorage.setItem('auth_user', JSON.stringify(response.data.user))

      // Clear session storage
      sessionStorage.removeItem('auth_state')

      // Get redirect path
      const redirectPath = sessionStorage.getItem('auth_redirect') || '/'
      sessionStorage.removeItem('auth_redirect')

      return redirectPath
    } catch (err: any) {
      state.value.error = err.response?.data?.detail || err.message || 'Authentication failed'
      throw err
    } finally {
      state.value.loading = false
    }
  }

  /**
   * Logout
   */
  const logout = async () => {
    // Clear local state
    state.value.token = null
    state.value.user = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')

    // Redirect to Authentik logout
    const logoutUrl = new URL(`${authentikUrl}/application/o/huan/end-session/`)
    logoutUrl.searchParams.set('post_logout_redirect_uri', window.location.origin)
    window.location.href = logoutUrl.toString()
  }

  /**
   * Initialize from localStorage
   */
  const initialize = () => {
    const token = localStorage.getItem('auth_token')
    const userStr = localStorage.getItem('auth_user')

    if (token && userStr) {
      state.value.token = token
      state.value.user = JSON.parse(userStr)
    }
  }

  /**
   * Refresh user info
   */
  const refreshUser = async () => {
    if (!state.value.token) return

    try {
      const response = await axios.get(`${config.public.apiUrl}/users/me`, {
        headers: {
          Authorization: `Bearer ${state.value.token}`,
        },
      })
      state.value.user = response.data
      localStorage.setItem('auth_user', JSON.stringify(response.data))
    } catch (err) {
      console.error('Failed to refresh user:', err)
      // If token is invalid, logout
      logout()
    }
  }

  return {
    // State
    isAuthenticated,
    user,
    loading,
    error,
    // Methods
    login,
    logout,
    handleCallback,
    initialize,
    refreshUser,
    // Raw token for API calls
    getToken: () => state.value.token,
  }
}
