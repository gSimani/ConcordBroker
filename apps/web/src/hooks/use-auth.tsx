import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'

interface User {
  id: string
  email: string
  metadata?: Record<string, any>
}

interface AuthContextType {
  isAuthenticated: boolean
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  loading: boolean
  login: (accessToken: string, refreshToken: string, user: User) => void
  logout: () => void
  refreshSession: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [refreshToken, setRefreshToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for stored tokens on mount
    const storedAccessToken = localStorage.getItem('access_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user')
    
    if (storedAccessToken && storedRefreshToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser)
        setAccessToken(storedAccessToken)
        setRefreshToken(storedRefreshToken)
        setUser(parsedUser)
        setIsAuthenticated(true)
        api.setAuthToken(storedAccessToken)
      } catch (error) {
        console.error('Failed to parse stored user data:', error)
        // Clear invalid data
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
      }
    }
    
    setLoading(false)
  }, [])

  const login = (newAccessToken: string, newRefreshToken: string, userData: User) => {
    // Store tokens and user data
    localStorage.setItem('access_token', newAccessToken)
    localStorage.setItem('refresh_token', newRefreshToken)
    localStorage.setItem('user', JSON.stringify(userData))
    
    // Update state
    setAccessToken(newAccessToken)
    setRefreshToken(newRefreshToken)
    setUser(userData)
    setIsAuthenticated(true)
    
    // Set token in API client
    api.setAuthToken(newAccessToken)
  }

  const logout = async () => {
    try {
      // Call signout endpoint if we have a token
      if (accessToken) {
        await api.signOut()
      }
    } catch (error) {
      console.error('Signout error:', error)
    }
    
    // Clear storage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    
    // Clear state
    setAccessToken(null)
    setRefreshToken(null)
    setUser(null)
    setIsAuthenticated(false)
    
    // Clear token in API client
    api.clearAuthToken()
    
    // Redirect to login
    navigate('/login')
  }

  const refreshSession = async () => {
    if (!refreshToken) {
      logout()
      return
    }
    
    try {
      const response = await api.refreshToken(refreshToken)
      if (response.success && response.access_token) {
        // Update tokens
        localStorage.setItem('access_token', response.access_token)
        localStorage.setItem('refresh_token', response.refresh_token)
        
        setAccessToken(response.access_token)
        setRefreshToken(response.refresh_token)
        
        // Update API client
        api.setAuthToken(response.access_token)
      } else {
        logout()
      }
    } catch (error) {
      console.error('Failed to refresh token:', error)
      logout()
    }
  }

  // Set up token refresh interval (refresh every 50 minutes for 1-hour tokens)
  useEffect(() => {
    if (isAuthenticated && accessToken) {
      const interval = setInterval(() => {
        refreshSession()
      }, 50 * 60 * 1000) // 50 minutes in milliseconds
      
      return () => clearInterval(interval)
    }
  }, [isAuthenticated, accessToken])

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      user,
      accessToken,
      refreshToken,
      loading,
      login,
      logout,
      refreshSession
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}