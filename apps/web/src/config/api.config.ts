/**
 * API Configuration for ConcordBroker
 * Centralizes all API endpoints for localhost development
 */

// Base URLs - all pointing to localhost
const BASE_URLS = {
  FRONTEND: import.meta.env.VITE_APP_URL || 'http://localhost:5173',
  PROPERTY_API: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  VISUALIZATION_API: import.meta.env.VITE_VISUALIZATION_API_URL || 'http://localhost:8002',
  MCP_SERVER: import.meta.env.VITE_MCP_SERVER_URL || 'http://localhost:3005',
  LANGCHAIN_API: import.meta.env.VITE_LANGCHAIN_API_URL || 'http://localhost:8003',
  SUPABASE: import.meta.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co'
};

// API Keys
const API_KEYS = {
  MCP: import.meta.env.VITE_MCP_API_KEY || 'concordbroker-mcp-key-claude',
  SUPABASE_ANON: import.meta.env.VITE_SUPABASE_ANON_KEY,
  GOOGLE_MAPS: import.meta.env.VITE_GOOGLE_MAPS_KEY
};

// API Endpoints
export const API_ENDPOINTS = {
  // Property API Endpoints (Port 8000)
  PROPERTY: {
    BASE: BASE_URLS.PROPERTY_API,
    SEARCH: `${BASE_URLS.PROPERTY_API}/api/properties/search`,
    DETAILS: (folio: string) => `${BASE_URLS.PROPERTY_API}/api/property/${folio}`,
    SALES: (folio: string) => `${BASE_URLS.PROPERTY_API}/api/property/${folio}/sales`,
    COMPARABLES: (folio: string) => `${BASE_URLS.PROPERTY_API}/api/property/${folio}/comparables`,
    OWNER_PROPERTIES: (owner: string) => `${BASE_URLS.PROPERTY_API}/api/owner/${encodeURIComponent(owner)}/properties`,
    ADVANCED_SEARCH: `${BASE_URLS.PROPERTY_API}/api/properties/advanced-search`,
    AUTOCOMPLETE: `${BASE_URLS.PROPERTY_API}/api/properties/autocomplete`,
    STATS: `${BASE_URLS.PROPERTY_API}/api/properties/stats`
  },

  // Visualization API Endpoints (Port 8001)
  VISUALIZATION: {
    BASE: BASE_URLS.VISUALIZATION_API,
    MARKET_OVERVIEW: `${BASE_URLS.VISUALIZATION_API}/api/visualize/market-overview`,
    SALES_TRENDS: `${BASE_URLS.VISUALIZATION_API}/api/visualize/sales-trends`,
    INVESTMENT_METRICS: (folio: string) => `${BASE_URLS.VISUALIZATION_API}/api/visualize/investment-metrics/${folio}`,
    TAX_DEEDS: `${BASE_URLS.VISUALIZATION_API}/api/visualize/tax-deeds`,
    HEAT_MAP: `${BASE_URLS.VISUALIZATION_API}/api/visualize/heat-map`,
    CORRELATION_MATRIX: `${BASE_URLS.VISUALIZATION_API}/api/visualize/correlation`
  },

  // MCP Server Endpoints (Port 3005)
  MCP: {
    BASE: BASE_URLS.MCP_SERVER,
    HEALTH: `${BASE_URLS.MCP_SERVER}/health`,
    SUPABASE: {
      QUERY: `${BASE_URLS.MCP_SERVER}/api/supabase/query`,
      TABLE: (table: string) => `${BASE_URLS.MCP_SERVER}/api/supabase/${table}`,
      INSERT: (table: string) => `${BASE_URLS.MCP_SERVER}/api/supabase/${table}`,
      UPDATE: (table: string, id: string) => `${BASE_URLS.MCP_SERVER}/api/supabase/${table}/${id}`,
      DELETE: (table: string, id: string) => `${BASE_URLS.MCP_SERVER}/api/supabase/${table}/${id}`
    },
    DEPLOYMENT: {
      VERCEL: `${BASE_URLS.MCP_SERVER}/api/vercel/deploy`,
      RAILWAY: `${BASE_URLS.MCP_SERVER}/api/railway/deploy`,
      ALL: `${BASE_URLS.MCP_SERVER}/api/deploy-all`
    },
    AI: {
      HUGGINGFACE: `${BASE_URLS.MCP_SERVER}/api/huggingface/inference`,
      OPENAI: `${BASE_URLS.MCP_SERVER}/api/openai/complete`
    }
  },

  // LangChain API Endpoints (Port 8003)
  LANGCHAIN: {
    BASE: BASE_URLS.LANGCHAIN_API,
    HEALTH: `${BASE_URLS.LANGCHAIN_API}/health`,
    CHAT: `${BASE_URLS.LANGCHAIN_API}/chat`,
    AGENT: `${BASE_URLS.LANGCHAIN_API}/agent`,
    CHAIN: `${BASE_URLS.LANGCHAIN_API}/chain`
  },

  // Supabase Direct Endpoints
  SUPABASE: {
    BASE: BASE_URLS.SUPABASE,
    REST: `${BASE_URLS.SUPABASE}/rest/v1`,
    AUTH: `${BASE_URLS.SUPABASE}/auth/v1`,
    STORAGE: `${BASE_URLS.SUPABASE}/storage/v1`
  }
};

// Request Headers
export const API_HEADERS = {
  DEFAULT: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  MCP: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'x-api-key': API_KEYS.MCP
  },
  SUPABASE: {
    'Content-Type': 'application/json',
    'apikey': API_KEYS.SUPABASE_ANON,
    'Authorization': `Bearer ${API_KEYS.SUPABASE_ANON}`
  }
};

// API Client Factory
export class APIClient {
  private baseUrl: string;
  private headers: HeadersInit;

  constructor(baseUrl: string, headers: HeadersInit = API_HEADERS.DEFAULT) {
    this.baseUrl = baseUrl;
    this.headers = headers;
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'GET',
      headers: this.headers
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} - ${response.statusText}`);
    }

    return response.json();
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: this.headers,
      body: data ? JSON.stringify(data) : undefined
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} - ${response.statusText}`);
    }

    return response.json();
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      headers: this.headers,
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} - ${response.statusText}`);
    }

    return response.json();
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'DELETE',
      headers: this.headers
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} - ${response.statusText}`);
    }

    return response.json();
  }
}

// Pre-configured API Clients
export const apiClients = {
  property: new APIClient(BASE_URLS.PROPERTY_API, API_HEADERS.DEFAULT),
  visualization: new APIClient(BASE_URLS.VISUALIZATION_API, API_HEADERS.DEFAULT),
  mcp: new APIClient(BASE_URLS.MCP_SERVER, API_HEADERS.MCP),
  langchain: new APIClient(BASE_URLS.LANGCHAIN_API, API_HEADERS.DEFAULT),
  supabase: new APIClient(BASE_URLS.SUPABASE + '/rest/v1', API_HEADERS.SUPABASE)
};

// Health Check Function
export async function checkAllServices(): Promise<{[key: string]: boolean}> {
  const services = {
    property_api: false,
    visualization_api: false,
    mcp_server: false,
    langchain_api: false,
    supabase: false
  };

  // Check Property API
  try {
    const response = await fetch(`${BASE_URLS.PROPERTY_API}/health`);
    services.property_api = response.ok;
  } catch (error) {
    console.error('Property API not available:', error);
  }

  // Check Visualization API
  try {
    const response = await fetch(`${BASE_URLS.VISUALIZATION_API}/health`);
    services.visualization_api = response.ok;
  } catch (error) {
    console.error('Visualization API not available:', error);
  }

  // Check MCP Server
  try {
    const response = await fetch(API_ENDPOINTS.MCP.HEALTH, {
      headers: { 'x-api-key': API_KEYS.MCP }
    });
    services.mcp_server = response.ok;
  } catch (error) {
    console.error('MCP Server not available:', error);
  }

  // Check LangChain API
  try {
    const response = await fetch(API_ENDPOINTS.LANGCHAIN.HEALTH);
    services.langchain_api = response.ok;
  } catch (error) {
    console.error('LangChain API not available:', error);
  }

  // Check Supabase
  try {
    const response = await fetch(`${BASE_URLS.SUPABASE}/rest/v1/`, {
      headers: API_HEADERS.SUPABASE
    });
    services.supabase = response.ok;
  } catch (error) {
    console.error('Supabase not available:', error);
  }

  return services;
}

// WebSocket Configuration
export const WEBSOCKET_URLS = {
  MCP: `ws://localhost:3005`,
  LANGCHAIN: `ws://localhost:8003`,
  PROPERTY_UPDATES: `ws://localhost:8080/ws`
};

// Environment Check
export const isLocalhost = () => {
  return window.location.hostname === 'localhost' ||
         window.location.hostname === '127.0.0.1' ||
         window.location.hostname.startsWith('192.168');
};

// CORS Configuration
export const CORS_CONFIG = {
  credentials: 'include' as RequestCredentials,
  mode: 'cors' as RequestMode
};

// Export everything as default
export default {
  BASE_URLS,
  API_KEYS,
  API_ENDPOINTS,
  API_HEADERS,
  APIClient,
  apiClients,
  checkAllServices,
  WEBSOCKET_URLS,
  isLocalhost,
  CORS_CONFIG
};