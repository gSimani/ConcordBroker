#!/usr/bin/env node

/**
 * Enhanced Supabase MCP Server
 * Advanced database operations with vector support and AI capabilities
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const { createClient } = require('@supabase/supabase-js');

class EnhancedSupabaseServer {
  constructor() {
    this.server = new Server(
      {
        name: 'supabase-enhanced-server',
        version: '2.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      },
    );

    this.supabase = null;
    this.initializeSupabase();
    this.setupToolHandlers();

    // Error handling
    this.server.onerror = error => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  initializeSupabase() {
    const url = process.env.SUPABASE_URL;
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY;

    if (!url || !key) {
      console.error('Supabase credentials not configured');
      return;
    }

    this.supabase = createClient(url, key);
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        // Database Operations
        {
          name: 'supabase_query',
          description: 'Execute a SELECT query on Supabase database',
          inputSchema: {
            type: 'object',
            properties: {
              table: { type: 'string', description: 'Table name' },
              columns: { type: 'string', description: 'Columns to select (default: *)' },
              filters: { type: 'object', description: 'Filter conditions' },
              limit: { type: 'number', description: 'Result limit' },
              orderBy: { type: 'string', description: 'Order by column' },
            },
            required: ['table'],
          },
        },
        {
          name: 'supabase_insert',
          description: 'Insert data into Supabase table',
          inputSchema: {
            type: 'object',
            properties: {
              table: { type: 'string', description: 'Table name' },
              data: { type: 'object', description: 'Data to insert' },
              returning: { type: 'boolean', description: 'Return inserted data' },
            },
            required: ['table', 'data'],
          },
        },
        {
          name: 'supabase_update',
          description: 'Update data in Supabase table',
          inputSchema: {
            type: 'object',
            properties: {
              table: { type: 'string', description: 'Table name' },
              data: { type: 'object', description: 'Data to update' },
              filters: { type: 'object', description: 'Filter conditions' },
              returning: { type: 'boolean', description: 'Return updated data' },
            },
            required: ['table', 'data', 'filters'],
          },
        },
        {
          name: 'supabase_delete',
          description: 'Delete data from Supabase table',
          inputSchema: {
            type: 'object',
            properties: {
              table: { type: 'string', description: 'Table name' },
              filters: { type: 'object', description: 'Filter conditions' },
              returning: { type: 'boolean', description: 'Return deleted data' },
            },
            required: ['table', 'filters'],
          },
        },
        // Vector Operations
        {
          name: 'supabase_vector_search',
          description: 'Perform vector similarity search',
          inputSchema: {
            type: 'object',
            properties: {
              table: { type: 'string', description: 'Table name with vector column' },
              embedding: { type: 'array', description: 'Query embedding vector' },
              vectorColumn: { type: 'string', description: 'Name of vector column' },
              matchCount: { type: 'number', description: 'Number of matches' },
              threshold: { type: 'number', description: 'Similarity threshold' },
            },
            required: ['table', 'embedding'],
          },
        },
        {
          name: 'supabase_generate_embedding',
          description: 'Generate embeddings using OpenAI',
          inputSchema: {
            type: 'object',
            properties: {
              text: { type: 'string', description: 'Text to embed' },
              model: { type: 'string', description: 'Embedding model (default: text-embedding-3-small)' },
            },
            required: ['text'],
          },
        },
        // Storage Operations
        {
          name: 'supabase_upload_file',
          description: 'Upload file to Supabase Storage',
          inputSchema: {
            type: 'object',
            properties: {
              bucket: { type: 'string', description: 'Storage bucket name' },
              path: { type: 'string', description: 'File path in bucket' },
              data: { type: 'string', description: 'Base64 encoded file data' },
              contentType: { type: 'string', description: 'File content type' },
            },
            required: ['bucket', 'path', 'data'],
          },
        },
        {
          name: 'supabase_download_file',
          description: 'Download file from Supabase Storage',
          inputSchema: {
            type: 'object',
            properties: {
              bucket: { type: 'string', description: 'Storage bucket name' },
              path: { type: 'string', description: 'File path in bucket' },
            },
            required: ['bucket', 'path'],
          },
        },
        // RPC Functions
        {
          name: 'supabase_rpc',
          description: 'Call a Supabase RPC function',
          inputSchema: {
            type: 'object',
            properties: {
              functionName: { type: 'string', description: 'RPC function name' },
              params: { type: 'object', description: 'Function parameters' },
            },
            required: ['functionName'],
          },
        },
        // Schema Information
        {
          name: 'supabase_get_schema',
          description: 'Get database schema information',
          inputSchema: {
            type: 'object',
            properties: {
              table: { type: 'string', description: 'Table name (optional)' },
            },
          },
        },
        // Real-time Operations
        {
          name: 'supabase_realtime_info',
          description: 'Get real-time subscription information',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        // Edge Functions
        {
          name: 'supabase_invoke_edge_function',
          description: 'Invoke a Supabase Edge Function',
          inputSchema: {
            type: 'object',
            properties: {
              functionName: { type: 'string', description: 'Edge Function name' },
              body: { type: 'object', description: 'Request body' },
              headers: { type: 'object', description: 'Request headers' },
            },
            required: ['functionName'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async request => {
      const { name, arguments: args } = request.params;

      try {
        if (!this.supabase) {
          throw new Error('Supabase client not initialized');
        }

        switch (name) {
          case 'supabase_query':
            return await this.handleQuery(args);
          case 'supabase_insert':
            return await this.handleInsert(args);
          case 'supabase_update':
            return await this.handleUpdate(args);
          case 'supabase_delete':
            return await this.handleDelete(args);
          case 'supabase_vector_search':
            return await this.handleVectorSearch(args);
          case 'supabase_generate_embedding':
            return await this.handleGenerateEmbedding(args);
          case 'supabase_upload_file':
            return await this.handleUploadFile(args);
          case 'supabase_download_file':
            return await this.handleDownloadFile(args);
          case 'supabase_rpc':
            return await this.handleRpc(args);
          case 'supabase_get_schema':
            return await this.handleGetSchema(args);
          case 'supabase_realtime_info':
            return await this.handleRealtimeInfo(args);
          case 'supabase_invoke_edge_function':
            return await this.handleInvokeEdgeFunction(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}\n\nStack: ${error.stack}`,
            },
          ],
        };
      }
    });
  }

  async handleQuery(args) {
    const { table, columns = '*', filters = {}, limit, orderBy } = args;

    let query = this.supabase.from(table).select(columns);

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      if (typeof value === 'object' && value.op) {
        // Advanced filter with operator
        switch (value.op) {
          case 'eq':
            query = query.eq(key, value.value);
            break;
          case 'neq':
            query = query.neq(key, value.value);
            break;
          case 'gt':
            query = query.gt(key, value.value);
            break;
          case 'gte':
            query = query.gte(key, value.value);
            break;
          case 'lt':
            query = query.lt(key, value.value);
            break;
          case 'lte':
            query = query.lte(key, value.value);
            break;
          case 'like':
            query = query.like(key, value.value);
            break;
          case 'ilike':
            query = query.ilike(key, value.value);
            break;
          case 'in':
            query = query.in(key, value.value);
            break;
          case 'is':
            query = query.is(key, value.value);
            break;
        }
      } else {
        // Simple equality filter
        query = query.eq(key, value);
      }
    });

    if (limit) {
      query = query.limit(limit);
    }

    if (orderBy) {
      const [column, direction = 'asc'] = orderBy.split(':');
      query = query.order(column, { ascending: direction === 'asc' });
    }

    const { data, error, count } = await query;

    if (error) throw error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            count: data.length,
            total: count,
            data: data,
          }, null, 2),
        },
      ],
    };
  }

  async handleInsert(args) {
    const { table, data, returning = true } = args;

    let query = this.supabase.from(table).insert(data);

    if (returning) {
      query = query.select();
    }

    const result = await query;

    if (result.error) throw result.error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            inserted: Array.isArray(data) ? data.length : 1,
            data: result.data,
          }, null, 2),
        },
      ],
    };
  }

  async handleUpdate(args) {
    const { table, data, filters, returning = true } = args;

    let query = this.supabase.from(table).update(data);

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      query = query.eq(key, value);
    });

    if (returning) {
      query = query.select();
    }

    const result = await query;

    if (result.error) throw result.error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            updated: result.data ? result.data.length : 'unknown',
            data: result.data,
          }, null, 2),
        },
      ],
    };
  }

  async handleDelete(args) {
    const { table, filters, returning = true } = args;

    let query = this.supabase.from(table).delete();

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      query = query.eq(key, value);
    });

    if (returning) {
      query = query.select();
    }

    const result = await query;

    if (result.error) throw result.error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            deleted: result.data ? result.data.length : 'unknown',
            data: result.data,
          }, null, 2),
        },
      ],
    };
  }

  async handleVectorSearch(args) {
    const { 
      table, 
      embedding, 
      vectorColumn = 'embedding', 
      matchCount = 5,
      threshold = 0.7 
    } = args;

    // Use RPC function for vector search
    const { data, error } = await this.supabase.rpc('match_embeddings', {
      query_embedding: embedding,
      match_count: matchCount,
      match_threshold: threshold,
      table_name: table,
      embedding_column: vectorColumn,
    });

    if (error) throw error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            matches: data.length,
            data: data,
          }, null, 2),
        },
      ],
    };
  }

  async handleGenerateEmbedding(args) {
    const { text, model = 'text-embedding-3-small' } = args;

    // Call Edge Function to generate embedding
    const { data, error } = await this.supabase.functions.invoke('generate-embedding', {
      body: { text, model },
    });

    if (error) throw error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            model: model,
            dimensions: data.embedding ? data.embedding.length : 0,
            embedding: data.embedding,
          }, null, 2),
        },
      ],
    };
  }

  async handleUploadFile(args) {
    const { bucket, path, data, contentType = 'application/octet-stream' } = args;

    // Convert base64 to buffer
    const buffer = Buffer.from(data, 'base64');

    const { data: uploadData, error } = await this.supabase.storage
      .from(bucket)
      .upload(path, buffer, {
        contentType,
        upsert: true,
      });

    if (error) throw error;

    // Get public URL
    const { data: { publicUrl } } = this.supabase.storage
      .from(bucket)
      .getPublicUrl(path);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            path: uploadData.path,
            publicUrl: publicUrl,
          }, null, 2),
        },
      ],
    };
  }

  async handleDownloadFile(args) {
    const { bucket, path } = args;

    const { data, error } = await this.supabase.storage
      .from(bucket)
      .download(path);

    if (error) throw error;

    // Convert blob to base64
    const buffer = await data.arrayBuffer();
    const base64 = Buffer.from(buffer).toString('base64');

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            path: path,
            size: buffer.byteLength,
            data: base64,
          }, null, 2),
        },
      ],
    };
  }

  async handleRpc(args) {
    const { functionName, params = {} } = args;

    const { data, error } = await this.supabase.rpc(functionName, params);

    if (error) throw error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            function: functionName,
            result: data,
          }, null, 2),
        },
      ],
    };
  }

  async handleGetSchema(args) {
    const { table } = args;

    // Get table information
    const query = table
      ? `SELECT * FROM information_schema.columns WHERE table_name = '${table}'`
      : `SELECT table_name, column_name, data_type, is_nullable 
         FROM information_schema.columns 
         WHERE table_schema = 'public' 
         ORDER BY table_name, ordinal_position`;

    const { data, error } = await this.supabase.rpc('execute_sql', {
      query: query,
    });

    if (error) {
      // Fallback: get basic table list
      const { data: tables, error: tablesError } = await this.supabase
        .from('information_schema.tables')
        .select('table_name')
        .eq('table_schema', 'public');

      if (tablesError) throw tablesError;

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              tables: tables.map(t => t.table_name),
            }, null, 2),
          },
        ],
      };
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            schema: data,
          }, null, 2),
        },
      ],
    };
  }

  async handleRealtimeInfo(args) {
    // Provide information about real-time capabilities
    const info = {
      enabled: true,
      features: [
        'Database changes (INSERT, UPDATE, DELETE)',
        'Presence (user online status)',
        'Broadcast (custom events)',
      ],
      usage: {
        subscribe: `
const channel = supabase
  .channel('room:1')
  .on('postgres_changes', 
    { event: '*', schema: 'public', table: 'messages' }, 
    payload => console.log(payload)
  )
  .subscribe()`,
        broadcast: `
channel.send({
  type: 'broadcast',
  event: 'cursor',
  payload: { x: 10, y: 20 }
})`,
        presence: `
channel.track({ user_id: 123, username: 'user' })`,
      },
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(info, null, 2),
        },
      ],
    };
  }

  async handleInvokeEdgeFunction(args) {
    const { functionName, body = {}, headers = {} } = args;

    const { data, error } = await this.supabase.functions.invoke(functionName, {
      body,
      headers,
    });

    if (error) throw error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            function: functionName,
            response: data,
          }, null, 2),
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Enhanced Supabase MCP server running on stdio');
  }
}

const server = new EnhancedSupabaseServer();
server.run().catch(console.error);