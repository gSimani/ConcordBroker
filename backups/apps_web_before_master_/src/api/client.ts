import axios from 'axios'
import type { AuthResponse, PropertyData, PropertySearchParams } from '@/types/api'

// Dynamic API configuration based on environment
const IS_LOCALHOST = typeof window !== 'undefined' && window.location.hostname === 'localhost'
const IS_PRODUCTION = typeof window !== 'undefined' && (
  window.location.hostname.includes('concordbroker.com') ||
  window.location.hostname.includes('vercel.app')
)

const API_BASE_URL = IS_LOCALHOST ? 'http://localhost:8000' : ''

console.log('API Base URL:', API_BASE_URL);

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // For localhost development
})

// Request interceptor for auth
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => {
    const data = response.data;

    // Handle fast API response format for search endpoint
    if (data && data.success === true && data.data && Array.isArray(data.data)) {
      // Fast API returns { success: true, data: [...], pagination: {...} }
      // Transform to expected format { properties: [...], pagination: {...}, total: n }
      return {
        properties: data.data,
        data: data.data,
        pagination: data.pagination,
        total: data.pagination?.total || data.data.length,
        success: true
      };
    }

    // Handle fast API response for property detail endpoint
    if (data && data.property) {
      return data; // Return as-is for property detail
    }

    // Return original data for other responses
    return data;
  },
  (error) => {
    console.error('API Error:', error.config?.url, error.message);

    // Don't redirect to login for public property endpoints
    const isPropertyEndpoint = error.config?.url?.includes('/properties') || error.config?.url?.includes('/fast');

    if (error.response?.status === 401 && !isPropertyEndpoint) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const api = {
  // Authentication
  signUp: (email: string, password: string, fullName?: string, company?: string): Promise<AuthResponse> =>
    client.post('/api/v1/auth/signup', {
      email,
      password,
      full_name: fullName,
      company
    }),

  signIn: (email: string, password: string): Promise<AuthResponse> =>
    client.post('/api/v1/auth/signin', { email, password }),
  
  signOut: () =>
    client.post('/api/v1/auth/signout'),
  
  refreshToken: (refreshToken: string): Promise<AuthResponse> =>
    client.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
  
  resetPassword: (email: string) =>
    client.post('/api/v1/auth/reset-password', { email }),
  
  updatePassword: (newPassword: string) =>
    client.post('/api/v1/auth/update-password', { new_password: newPassword }),

  getCurrentUser: () =>
    client.get('/api/v1/auth/me'),

  sendVerificationCode: (phone: string): Promise<AuthResponse> =>
    client.post('/api/v1/auth/send-verification', { phone }),

  verifyCode: (phone: string, code: string): Promise<AuthResponse> =>
    client.post('/api/v1/auth/verify-code', { phone, code }),
  
  // Properties - Fast API endpoints
  searchProperties: (params: URLSearchParams) =>
    client.get(`/api/properties/search?${params.toString()}`),

  getProperty: (id: string) =>
    client.get(`/api/properties/${id}`),

  getEnhancedPropertyDetail: (parcelId: string) =>
    IS_LOCALHOST
      ? client.get(`http://localhost:8005/api/enhanced/property/${parcelId}`)
      : client.get(`/api/properties/${parcelId}`), // Use standard endpoint in production

  getPropertyByAddress: (address: string, city?: string) => {
    const url = city
      ? `/api/properties/address/${encodeURIComponent(address)}?city=${encodeURIComponent(city)}`
      : `/api/properties/address/${encodeURIComponent(address)}`;
    return client.get(url);
  },

  getPropertyByParcel: (parcelId: string) =>
    client.get(`/api/properties/${parcelId}`),
  
  // Dashboard Statistics - Works in both environments
  getOverviewStats: () =>
    IS_LOCALHOST
      ? axios.get('http://localhost:8001/api/fast/stats')
      : client.get('/api/properties/stats'),

  getCityStats: () =>
    IS_LOCALHOST
      ? axios.get('http://localhost:8001/api/fast/cities')
      : client.get('/api/properties/cities'),

  getTypeStats: () =>
    IS_LOCALHOST
      ? axios.get('http://localhost:8001/api/properties/stats/by-type')
      : client.get('/api/properties/stats/by-type'),

  getRecentSales: (days: number = 30, limit: number = 10) =>
    IS_LOCALHOST
      ? axios.get(`http://localhost:8001/api/properties/recent-sales?days=${days}&limit=${limit}`)
      : client.get(`/api/properties/recent-sales?days=${days}&limit=${limit}`),

  getHighValueProperties: (minValue: number = 1000000) =>
    IS_LOCALHOST
      ? axios.get(`http://localhost:8001/api/properties/high-value?min_value=${minValue}`)
      : client.get(`/api/properties/high-value?min_value=${minValue}`),
  
  // Entities
  searchEntities: (params: URLSearchParams) =>
    client.get(`/api/v1/entities/search?${params.toString()}`),
  
  getEntity: (id: string) =>
    client.get(`/api/v1/entities/${id}`),
  
  getEntityNetwork: (id: string) =>
    client.get(`/api/v1/entities/${id}/network`),
  
  // Analytics
  getMarketTrends: (params?: URLSearchParams) =>
    client.get(`/api/v1/analytics/market-trends${params ? '?' + params.toString() : ''}`),
  
  getTopOpportunities: (params?: URLSearchParams) =>
    client.get(`/api/v1/analytics/top-opportunities${params ? '?' + params.toString() : ''}`),
  
  getCityStatistics: () =>
    client.get('/api/v1/analytics/city-statistics'),
  
  getUseCodeAnalysis: () =>
    client.get('/api/v1/analytics/use-code-analysis'),
  
  getRecentActivity: (days: number = 7) =>
    client.get(`/api/v1/analytics/recent-activity?days=${days}`),
  
  // Health
  getHealth: () =>
    client.get('/api/fast/health'),
  
  getDetailedHealth: () =>
    client.get('/health/detailed'),
  
  getSystemStatus: () =>
    client.get('/status'),
  
  // Autocomplete endpoints - Fast API
  getAddressSuggestions: (query: string, limit: number = 10) =>
    client.get(`/api/autocomplete/addresses?q=${encodeURIComponent(query)}&limit=${limit}`),

  getOwnerSuggestions: (query: string, limit: number = 10) =>
    client.get(`/api/autocomplete/owners?q=${encodeURIComponent(query)}&limit=${limit}`),

  // Helper methods for token management
  setAuthToken: (token: string) => {
    localStorage.setItem('access_token', token)
  },

  clearAuthToken: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }
}

export default client
// Updated to use fast API
// Force reload
