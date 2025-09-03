import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
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
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const api = {
  // Properties
  searchProperties: (params: URLSearchParams) =>
    client.get(`/api/v1/parcels/search?${params.toString()}`),
  
  getProperty: (folio: string) =>
    client.get(`/api/v1/parcels/${folio}`),
  
  getPropertyScore: (folio: string) =>
    client.post(`/api/v1/parcels/${folio}/score`),
  
  getComparables: (folio: string) =>
    client.get(`/api/v1/parcels/${folio}/comparables`),
  
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
}

export default client