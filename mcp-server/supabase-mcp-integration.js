/**
 * Supabase MCP Integration for ConcordBroker
 *
 * Integrates the Supabase MCP server (https://github.com/gSimani/supabase-mcp)
 * to enable AI-powered database operations with security controls.
 *
 * Features:
 * - Read-only mode for safe database access
 * - Scoped to specific project
 * - Tools for database queries, table management, and edge functions
 * - Integration with existing MCP server
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: '../.env.mcp' });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const SUPABASE_PROJECT_ID = process.env.SUPABASE_PROJECT_ID;

/**
 * Supabase MCP Tools Configuration
 */
const SUPABASE_MCP_CONFIG = {
  // Security settings
  readOnly: process.env.SUPABASE_MCP_READ_ONLY === 'true' || true, // Default to read-only
  projectId: SUPABASE_PROJECT_ID,

  // Feature groups to enable
  features: [
    'docs',      // Documentation search
    'database',  // Database operations (SELECT queries only in read-only mode)
    'debugging', // Query debugging tools
  ],

  // Optional features (disabled by default for security)
  // Uncomment to enable:
  // 'account',    // Account management
  // 'development', // Development tools
  // 'functions',  // Edge functions
  // 'branching',  // Database branching
  // 'storage',    // Storage operations
};

/**
 * Initialize Supabase client for MCP operations
 */
export function createSupabaseMcpClient() {
  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
    console.warn('⚠️  Supabase MCP: Missing credentials in .env.mcp');
    return null;
  }

  const client = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  });

  console.log('✅ Supabase MCP client initialized');
  console.log(`   - URL: ${SUPABASE_URL}`);
  console.log(`   - Project ID: ${SUPABASE_PROJECT_ID || 'All projects'}`);
  console.log(`   - Read-only: ${SUPABASE_MCP_CONFIG.readOnly}`);
  console.log(`   - Features: ${SUPABASE_MCP_CONFIG.features.join(', ')}`);

  return client;
}

/**
 * Supabase MCP Tools
 *
 * These tools allow AI assistants to interact with Supabase in a controlled manner.
 */
export const supabaseMcpTools = {
  /**
   * Query database tables with AI assistance
   */
  async queryDatabase(params) {
    const { table, select = '*', filters = {}, limit = 100 } = params;

    const client = createSupabaseMcpClient();
    if (!client) throw new Error('Supabase client not initialized');

    let query = client.from(table).select(select);

    // Apply filters
    for (const [key, value] of Object.entries(filters)) {
      if (value !== null && value !== undefined) {
        query = query.eq(key, value);
      }
    }

    // Apply limit
    query = query.limit(limit);

    const { data, error } = await query;

    if (error) {
      throw new Error(`Database query error: ${error.message}`);
    }

    return {
      table,
      count: data?.length || 0,
      data: data || [],
      query: {
        table,
        select,
        filters,
        limit
      }
    };
  },

  /**
   * Get table schema information
   */
  async getTableSchema(params) {
    const { table } = params;

    const client = createSupabaseMcpClient();
    if (!client) throw new Error('Supabase client not initialized');

    // Use RPC or direct query to get column details
    try {
      // Try using a simple query to get column info from the table itself
      const { data: sampleData, error: sampleError } = await client
        .from(table)
        .select('*')
        .limit(1);

      if (sampleError) {
        throw new Error(`Schema query error: ${sampleError.message}`);
      }

      // Extract column information from the sample row
      const columns = sampleData && sampleData[0]
        ? Object.keys(sampleData[0]).map(key => ({
            column_name: key,
            data_type: typeof sampleData[0][key],
            sample_value: sampleData[0][key]
          }))
        : [];

      return {
        table,
        columns,
        columnCount: columns.length
      };
    } catch (error) {
      throw new Error(`Schema query error: ${error.message}`);
    }
  },

  /**
   * List available tables
   */
  async listTables() {
    const client = createSupabaseMcpClient();
    if (!client) throw new Error('Supabase client not initialized');

    // For ConcordBroker, return known tables
    // Note: In production, use RPC function or proper information_schema access
    const knownTables = [
      'florida_parcels',
      'property_sales_history',
      'florida_entities',
      'sunbiz_corporate',
      'tax_certificates'
    ];

    const tables = knownTables.map(name => ({
      table_name: name,
      table_type: 'BASE TABLE'
    }));

    return {
      tables,
      tableCount: tables.length
    };
  },

  /**
   * Execute a safe read-only query
   */
  async executeSafeQuery(params) {
    const { query } = params;

    // Security check: only allow SELECT queries
    const queryLower = query.trim().toLowerCase();
    if (!queryLower.startsWith('select')) {
      throw new Error('Only SELECT queries are allowed in safe mode');
    }

    // Block dangerous keywords
    const dangerousKeywords = ['drop', 'delete', 'update', 'insert', 'alter', 'truncate'];
    if (dangerousKeywords.some(keyword => queryLower.includes(keyword))) {
      throw new Error('Query contains potentially dangerous keywords');
    }

    const client = createSupabaseMcpClient();
    if (!client) throw new Error('Supabase client not initialized');

    const { data, error } = await client.rpc('execute_sql', { query });

    if (error) {
      throw new Error(`Query execution error: ${error.message}`);
    }

    return {
      query,
      rowCount: data?.length || 0,
      data: data || []
    };
  },

  /**
   * Get database statistics for ConcordBroker tables
   */
  async getDatabaseStats() {
    const client = createSupabaseMcpClient();
    if (!client) throw new Error('Supabase client not initialized');

    const tables = [
      'florida_parcels',
      'property_sales_history',
      'florida_entities',
      'sunbiz_corporate',
      'tax_certificates'
    ];

    const stats = {};

    for (const table of tables) {
      try {
        const { count, error } = await client
          .from(table)
          .select('*', { count: 'exact', head: true });

        stats[table] = {
          count: count || 0,
          error: error?.message || null
        };
      } catch (err) {
        stats[table] = {
          count: 0,
          error: err.message
        };
      }
    }

    return {
      timestamp: new Date().toISOString(),
      stats
    };
  },

  /**
   * Search properties using AI-friendly interface
   */
  async searchProperties(params) {
    const {
      county,
      city,
      minValue,
      maxValue,
      propertyUse,
      limit = 100
    } = params;

    const client = createSupabaseMcpClient();
    if (!client) throw new Error('Supabase client not initialized');

    let query = client.from('florida_parcels').select('*');

    if (county) query = query.eq('county', county.toUpperCase());
    if (city) query = query.ilike('phy_city', `%${city}%`);
    if (minValue) query = query.gte('just_value', minValue);
    if (maxValue) query = query.lte('just_value', maxValue);
    if (propertyUse) query = query.eq('property_use_code', propertyUse);

    query = query.limit(limit);

    const { data, error } = await query;

    if (error) {
      throw new Error(`Property search error: ${error.message}`);
    }

    return {
      count: data?.length || 0,
      properties: data || [],
      filters: { county, city, minValue, maxValue, propertyUse }
    };
  }
};

/**
 * Register Supabase MCP tools with the main MCP server
 */
export function registerSupabaseMcpTools(mcpServer) {
  if (!mcpServer) {
    console.error('❌ Cannot register Supabase MCP tools: MCP server not provided');
    return;
  }

  console.log('📦 Registering Supabase MCP tools...');

  // Register each tool
  const tools = [
    {
      name: 'supabase_query_database',
      description: 'Query a Supabase database table with filters',
      handler: supabaseMcpTools.queryDatabase,
      schema: {
        type: 'object',
        properties: {
          table: { type: 'string', description: 'Table name to query' },
          select: { type: 'string', description: 'Columns to select (default: *)' },
          filters: { type: 'object', description: 'Filter criteria as key-value pairs' },
          limit: { type: 'number', description: 'Max rows to return (default: 100)' }
        },
        required: ['table']
      }
    },
    {
      name: 'supabase_get_table_schema',
      description: 'Get schema information for a database table',
      handler: supabaseMcpTools.getTableSchema,
      schema: {
        type: 'object',
        properties: {
          table: { type: 'string', description: 'Table name' }
        },
        required: ['table']
      }
    },
    {
      name: 'supabase_list_tables',
      description: 'List all available tables in the database',
      handler: supabaseMcpTools.listTables,
      schema: {
        type: 'object',
        properties: {}
      }
    },
    {
      name: 'supabase_execute_safe_query',
      description: 'Execute a safe read-only SQL query (SELECT only)',
      handler: supabaseMcpTools.executeSafeQuery,
      schema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'SQL SELECT query to execute' }
        },
        required: ['query']
      }
    },
    {
      name: 'supabase_get_database_stats',
      description: 'Get statistics for ConcordBroker database tables',
      handler: supabaseMcpTools.getDatabaseStats,
      schema: {
        type: 'object',
        properties: {}
      }
    },
    {
      name: 'supabase_search_properties',
      description: 'Search Florida properties with filters',
      handler: supabaseMcpTools.searchProperties,
      schema: {
        type: 'object',
        properties: {
          county: { type: 'string', description: 'County name (e.g., BROWARD, MIAMI-DADE)' },
          city: { type: 'string', description: 'City name' },
          minValue: { type: 'number', description: 'Minimum property value' },
          maxValue: { type: 'number', description: 'Maximum property value' },
          propertyUse: { type: 'string', description: 'Property use code' },
          limit: { type: 'number', description: 'Max results (default: 100)' }
        }
      }
    }
  ];

  let registeredCount = 0;
  for (const tool of tools) {
    try {
      if (typeof mcpServer.registerTool === 'function') {
        mcpServer.registerTool(tool);
        registeredCount++;
      } else if (typeof mcpServer.tool === 'function') {
        mcpServer.tool(tool.name, tool.description, tool.schema, tool.handler);
        registeredCount++;
      }
    } catch (error) {
      console.error(`⚠️  Failed to register tool ${tool.name}:`, error.message);
    }
  }

  console.log(`✅ Registered ${registeredCount}/${tools.length} Supabase MCP tools`);

  return registeredCount;
}

/**
 * Health check for Supabase MCP integration
 */
export async function checkSupabaseMcpHealth() {
  const client = createSupabaseMcpClient();

  if (!client) {
    return {
      healthy: false,
      error: 'Supabase client not initialized'
    };
  }

  try {
    // Test connection by querying a known table
    const { error } = await client
      .from('florida_parcels')
      .select('parcel_id')
      .limit(1);

    if (error) {
      return {
        healthy: false,
        error: error.message
      };
    }

    return {
      healthy: true,
      config: SUPABASE_MCP_CONFIG,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      healthy: false,
      error: error.message
    };
  }
}

export default {
  createSupabaseMcpClient,
  supabaseMcpTools,
  registerSupabaseMcpTools,
  checkSupabaseMcpHealth,
  config: SUPABASE_MCP_CONFIG
};
