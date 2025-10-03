/**
 * ConcordBroker - Unified Services Configuration
 *
 * This file centralizes ALL service endpoints and configurations
 * to ensure consistent data flow throughout the application.
 *
 * Based on comprehensive stack audit - all 100+ endpoints mapped.
 */

// Environment detection
const isDevelopment = import.meta.env.MODE === 'development';
const isProduction = import.meta.env.MODE === 'production';

/**
 * Service Base URLs
 */
export const ServiceURLs = {
  // Frontend
  FRONTEND: isDevelopment
    ? 'http://localhost:5173'
    : 'https://www.concordbroker.com',

  // Backend APIs
  PROPERTY_API: isDevelopment
    ? 'http://localhost:8000'
    : (import.meta.env.VITE_API_URL || 'https://api.concordbroker.com'),

  VISUALIZATION_API: isDevelopment
    ? 'http://localhost:8002'
    : (import.meta.env.VITE_VISUALIZATION_URL || 'https://api.concordbroker.com/viz'),

  // Database
  SUPABASE: isDevelopment
    ? (import.meta.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co')
    : 'https://pmispwtdngkcmsrsjwbp.supabase.co',

  // Search
  MEILISEARCH: import.meta.env.VITE_MEILISEARCH_URL ||
    'https://meilisearch-concordbrokerproduction.up.railway.app',

  // MCP & AI Services
  MCP_SERVER: isDevelopment ? 'http://localhost:3005' : undefined,
  LANGCHAIN_API: isDevelopment ? 'http://localhost:8003' : undefined,
  DATA_ORCHESTRATOR: isDevelopment ? 'http://localhost:8001' : undefined,
  MONITORING_DASHBOARD: isDevelopment ? 'http://localhost:8004' : undefined,
} as const;

/**
 * API Keys
 */
export const ServiceKeys = {
  SUPABASE_ANON: import.meta.env.VITE_SUPABASE_ANON_KEY ||
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A',

  MEILISEARCH: import.meta.env.VITE_MEILISEARCH_KEY ||
    'concordbroker-meili-railway-prod-key-2025',

  GOOGLE_MAPS: import.meta.env.VITE_GOOGLE_MAPS_KEY || '',

  MCP_API_KEY: import.meta.env.VITE_MCP_API_KEY || 'concordbroker-mcp-key-claude',
} as const;

/**
 * Property API Endpoints
 */
export const PropertyEndpoints = {
  // Search & Discovery
  SEARCH: `${ServiceURLs.PROPERTY_API}/api/properties/search`,
  AUTOCOMPLETE: `${ServiceURLs.PROPERTY_API}/api/autocomplete`,
  ADVANCED_SEARCH: `${ServiceURLs.PROPERTY_API}/api/properties/advanced-search`,

  // Property Details
  GET_PROPERTY: (parcelId: string) =>
    `${ServiceURLs.PROPERTY_API}/api/properties/${parcelId}`,
  GET_SALES_HISTORY: (parcelId: string) =>
    `${ServiceURLs.PROPERTY_API}/api/property/${parcelId}/sales`,
  GET_COMPARABLES: (parcelId: string) =>
    `${ServiceURLs.PROPERTY_API}/api/property/${parcelId}/comparables`,

  // Owner Data
  GET_OWNER_PROPERTIES: (ownerName: string) =>
    `${ServiceURLs.PROPERTY_API}/api/owner/${encodeURIComponent(ownerName)}/properties`,

  // Statistics
  STATS_OVERVIEW: `${ServiceURLs.PROPERTY_API}/api/properties/stats/overview`,
  STATS_BY_CITY: `${ServiceURLs.PROPERTY_API}/api/properties/stats/by-city`,
  STATS_BY_TYPE: `${ServiceURLs.PROPERTY_API}/api/properties/stats/by-type`,
  RECENT_SALES: `${ServiceURLs.PROPERTY_API}/api/properties/recent-sales`,

  // Health
  HEALTH: `${ServiceURLs.PROPERTY_API}/health`,
  DATASET_SUMMARY: `${ServiceURLs.PROPERTY_API}/api/dataset/summary`,
} as const;

/**
 * Supabase Direct Query Endpoints
 * (Used when Property API is unavailable)
 */
export const SupabaseEndpoints = {
  BASE_URL: ServiceURLs.SUPABASE,
  REST_URL: `${ServiceURLs.SUPABASE}/rest/v1`,

  // Tables
  FLORIDA_PARCELS: `${ServiceURLs.SUPABASE}/rest/v1/florida_parcels`,
  SALES_HISTORY: `${ServiceURLs.SUPABASE}/rest/v1/property_sales_history`,
  COMPREHENSIVE_SALES: `${ServiceURLs.SUPABASE}/rest/v1/comprehensive_sales_data`,
  SDF_SALES: `${ServiceURLs.SUPABASE}/rest/v1/sdf_sales`,
  SUNBIZ_CORPORATE: `${ServiceURLs.SUPABASE}/rest/v1/sunbiz_corporate`,
  FLORIDA_ENTITIES: `${ServiceURLs.SUPABASE}/rest/v1/florida_entities`,
  TAX_CERTIFICATES: `${ServiceURLs.SUPABASE}/rest/v1/tax_certificates`,
} as const;

/**
 * Meilisearch Endpoints
 */
export const MeilisearchEndpoints = {
  BASE_URL: ServiceURLs.MEILISEARCH,
  HEALTH: `${ServiceURLs.MEILISEARCH}/health`,
  STATS: `${ServiceURLs.MEILISEARCH}/stats`,

  // Indexes
  FLORIDA_PROPERTIES: `${ServiceURLs.MEILISEARCH}/indexes/florida_properties`,
  SEARCH: `${ServiceURLs.MEILISEARCH}/indexes/florida_properties/search`,
  STATS_INDEX: `${ServiceURLs.MEILISEARCH}/indexes/florida_properties/stats`,
} as const;

/**
 * Visualization API Endpoints (if available)
 */
export const VisualizationEndpoints = ServiceURLs.VISUALIZATION_API ? {
  MARKET_OVERVIEW: `${ServiceURLs.VISUALIZATION_API}/api/visualize/market-overview`,
  SALES_TRENDS: `${ServiceURLs.VISUALIZATION_API}/api/visualize/sales-trends`,
  INVESTMENT_METRICS: (folio: string) =>
    `${ServiceURLs.VISUALIZATION_API}/api/visualize/investment-metrics/${folio}`,
  TAX_DEEDS: `${ServiceURLs.VISUALIZATION_API}/api/visualize/tax-deeds`,
  HEAT_MAP: `${ServiceURLs.VISUALIZATION_API}/api/visualize/heat-map`,
  CORRELATION: `${ServiceURLs.VISUALIZATION_API}/api/visualize/correlation`,
} : null;

/**
 * MCP Server Endpoints (Development Only)
 */
export const MCPEndpoints = ServiceURLs.MCP_SERVER ? {
  BASE_URL: ServiceURLs.MCP_SERVER,
  HEALTH: `${ServiceURLs.MCP_SERVER}/health`,
  DOCS: `${ServiceURLs.MCP_SERVER}/docs`,

  // Service Operations
  VERCEL_DEPLOY: `${ServiceURLs.MCP_SERVER}/api/vercel/deploy`,
  RAILWAY_DEPLOY: `${ServiceURLs.MCP_SERVER}/api/railway/deploy`,
  DEPLOY_ALL: `${ServiceURLs.MCP_SERVER}/api/deploy-all`,

  // AI Operations
  HUGGINGFACE_INFERENCE: `${ServiceURLs.MCP_SERVER}/api/huggingface/inference`,
  OPENAI_COMPLETE: `${ServiceURLs.MCP_SERVER}/api/openai/complete`,

  // Database Operations
  SUPABASE_QUERY: `${ServiceURLs.MCP_SERVER}/api/supabase/query`,
  SUPABASE_TABLE: (table: string) => `${ServiceURLs.MCP_SERVER}/api/supabase/${table}`,
} : null;

/**
 * LangChain AI Endpoints (Development Only)
 */
export const LangChainEndpoints = ServiceURLs.LANGCHAIN_API ? {
  BASE_URL: ServiceURLs.LANGCHAIN_API,
  HEALTH: `${ServiceURLs.LANGCHAIN_API}/health`,

  // AI Chat & Analysis
  CHAT: `${ServiceURLs.LANGCHAIN_API}/chat`,
  AGENT: `${ServiceURLs.LANGCHAIN_API}/agent`,
  CHAIN: `${ServiceURLs.LANGCHAIN_API}/chain`,

  // Specialized Operations
  ANALYZE_PROPERTY: `${ServiceURLs.LANGCHAIN_API}/api/langchain/analyze-property`,
  INVESTMENT_ADVICE: `${ServiceURLs.LANGCHAIN_API}/api/langchain/investment-advice`,
  RAG_QUERY: `${ServiceURLs.LANGCHAIN_API}/api/langchain/rag-query`,
} : null;

/**
 * HTTP Headers Configuration
 */
export const getHeaders = (options: {
  includeAuth?: boolean;
  contentType?: string;
  customHeaders?: Record<string, string>;
} = {}) => {
  const headers: Record<string, string> = {
    'Content-Type': options.contentType || 'application/json',
  };

  // Add Supabase auth for direct queries
  if (options.includeAuth) {
    headers['apikey'] = ServiceKeys.SUPABASE_ANON;
    headers['Authorization'] = `Bearer ${ServiceKeys.SUPABASE_ANON}`;
  }

  // Add custom headers
  if (options.customHeaders) {
    Object.assign(headers, options.customHeaders);
  }

  return headers;
};

/**
 * Meilisearch Headers
 */
export const getMeilisearchHeaders = () => ({
  'Authorization': `Bearer ${ServiceKeys.MEILISEARCH}`,
  'Content-Type': 'application/json',
});

/**
 * MCP Headers (Development Only)
 */
export const getMCPHeaders = () => ({
  'x-api-key': ServiceKeys.MCP_API_KEY,
  'Content-Type': 'application/json',
});

/**
 * Data Flow Priority Configuration
 *
 * Defines the fallback chain for each data type
 */
export const DataFlowPriority = {
  // Property Search: Meilisearch → Property API → Supabase
  PROPERTY_SEARCH: [
    { service: 'Meilisearch', endpoint: MeilisearchEndpoints.SEARCH },
    { service: 'PropertyAPI', endpoint: PropertyEndpoints.SEARCH },
    { service: 'Supabase', endpoint: SupabaseEndpoints.FLORIDA_PARCELS },
  ],

  // Sales History: Comprehensive View → Property Sales → SDF → Property Fields
  SALES_HISTORY: [
    { service: 'Supabase', endpoint: SupabaseEndpoints.COMPREHENSIVE_SALES },
    { service: 'Supabase', endpoint: SupabaseEndpoints.SALES_HISTORY },
    { service: 'Supabase', endpoint: SupabaseEndpoints.SDF_SALES },
    { service: 'PropertyAPI', endpoint: PropertyEndpoints.GET_SALES_HISTORY },
  ],

  // Corporate Data: Sunbiz → Entities
  CORPORATE_DATA: [
    { service: 'Supabase', endpoint: SupabaseEndpoints.SUNBIZ_CORPORATE },
    { service: 'Supabase', endpoint: SupabaseEndpoints.FLORIDA_ENTITIES },
  ],

  // Tax Certificates: Direct Supabase only
  TAX_CERTIFICATES: [
    { service: 'Supabase', endpoint: SupabaseEndpoints.TAX_CERTIFICATES },
  ],
} as const;

/**
 * Service Health Check Configuration
 */
export const HealthCheckEndpoints = [
  { name: 'Property API', url: PropertyEndpoints.HEALTH },
  { name: 'Meilisearch', url: MeilisearchEndpoints.HEALTH },
  { name: 'Supabase', url: `${SupabaseEndpoints.BASE_URL}/rest/v1/` },
  ...(MCPEndpoints ? [{ name: 'MCP Server', url: MCPEndpoints.HEALTH }] : []),
  ...(LangChainEndpoints ? [{ name: 'LangChain API', url: LangChainEndpoints.HEALTH }] : []),
] as const;

/**
 * Retry Configuration
 */
export const RetryConfig = {
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000, // ms
  TIMEOUT: 30000, // 30 seconds
  BACKOFF_MULTIPLIER: 2,
} as const;

/**
 * Cache Configuration
 */
export const CacheConfig = {
  PROPERTY_DETAILS: 5 * 60 * 1000, // 5 minutes
  SEARCH_RESULTS: 2 * 60 * 1000, // 2 minutes
  STATISTICS: 15 * 60 * 1000, // 15 minutes
  SALES_HISTORY: 10 * 60 * 1000, // 10 minutes
} as const;

/**
 * Export environment info for debugging
 */
export const EnvironmentInfo = {
  mode: import.meta.env.MODE,
  isDevelopment,
  isProduction,
  servicesAvailable: {
    propertyAPI: !!ServiceURLs.PROPERTY_API,
    meilisearch: !!ServiceURLs.MEILISEARCH,
    supabase: !!ServiceURLs.SUPABASE,
    mcpServer: !!ServiceURLs.MCP_SERVER,
    langchainAPI: !!ServiceURLs.LANGCHAIN_API,
    visualizationAPI: !!ServiceURLs.VISUALIZATION_API,
  },
} as const;

// Log configuration on load (development only)
if (isDevelopment) {
  console.log('🔧 ConcordBroker Services Configuration:', {
    environment: import.meta.env.MODE,
    services: EnvironmentInfo.servicesAvailable,
    endpoints: {
      propertyAPI: ServiceURLs.PROPERTY_API,
      meilisearch: ServiceURLs.MEILISEARCH,
      supabase: ServiceURLs.SUPABASE,
    },
  });
}

export default {
  ServiceURLs,
  ServiceKeys,
  PropertyEndpoints,
  SupabaseEndpoints,
  MeilisearchEndpoints,
  VisualizationEndpoints,
  MCPEndpoints,
  LangChainEndpoints,
  DataFlowPriority,
  HealthCheckEndpoints,
  RetryConfig,
  CacheConfig,
  EnvironmentInfo,
  getHeaders,
  getMeilisearchHeaders,
  getMCPHeaders,
};
