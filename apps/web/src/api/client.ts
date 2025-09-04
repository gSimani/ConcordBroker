import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
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
  signUp: (email: string, password: string, fullName?: string, company?: string) =>
    client.post('/api/v1/auth/signup', { 
      email, 
      password,
      full_name: fullName,
      company
    }),
  
  signIn: (email: string, password: string) =>
    client.post('/api/v1/auth/signin', { email, password }),
  
  signOut: () =>
    client.post('/api/v1/auth/signout'),
  
  refreshToken: (refreshToken: string) =>
    client.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
  
  resetPassword: (email: string) =>
    client.post('/api/v1/auth/reset-password', { email }),
  
  updatePassword: (newPassword: string) =>
    client.post('/api/v1/auth/update-password', { new_password: newPassword }),
  
  getCurrentUser: () =>
    client.get('/api/v1/auth/me'),
  
  // Properties - Address-based API
  searchProperties: (params: URLSearchParams) =>
    client.get(`/api/properties/search?${params.toString()}`),
  
  getProperty: (id: string) =>
    client.get(`/api/properties/${id}`),
    
  getPropertyByAddress: (address: string, city?: string) => {
    const url = city 
      ? `/api/properties/address/${encodeURIComponent(address)}?city=${encodeURIComponent(city)}`
      : `/api/properties/address/${encodeURIComponent(address)}`;
    return client.get(url);
  },
  
  getPropertyByParcel: (parcelId: string) =>
    client.get(`/api/properties/parcel/${parcelId}`),
  
  // Dashboard Statistics
  getOverviewStats: () =>
    client.get('/api/properties/stats/overview'),
    
  getCityStats: () =>
    client.get('/api/properties/stats/by-city'),
    
  getTypeStats: () =>
    client.get('/api/properties/stats/by-type'),
    
  getRecentSales: (days: number = 30, limit: number = 10) =>
    client.get(`/api/properties/recent-sales?days=${days}&limit=${limit}`),
    
  getHighValueProperties: (minValue: number = 1000000) =>
    client.get(`/api/properties/high-value?min_value=${minValue}`),
  
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
    client.get('/health'),
  
  getDetailedHealth: () =>
    client.get('/health/detailed'),
  
  getSystemStatus: () =>
    client.get('/status'),
  
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