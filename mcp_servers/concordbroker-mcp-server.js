/**
 * ConcordBroker MCP Server
 * Custom Model Context Protocol server for Concord Broker
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { createClient } from '@supabase/supabase-js';

class ConcordBrokerMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'concordbroker-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      },
    );

    // Initialize Supabase client
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY;

    console.error(`Initializing Supabase: ${supabaseUrl ? 'URL found' : 'URL missing'}, ${supabaseKey ? 'Key found' : 'Key missing'}`);

    this.supabase = createClient(supabaseUrl, supabaseKey);

    this.setupHandlers();
  }

  setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'search_properties',
          description: 'Search for properties in the ConcordBroker database',
          inputSchema: {
            type: 'object',
            properties: {
              location: { type: 'string', description: 'Property location' },
              minPrice: { type: 'number', description: 'Minimum price' },
              maxPrice: { type: 'number', description: 'Maximum price' },
              propertyType: { type: 'string', description: 'Type of property' },
            },
          },
        },
        {
          name: 'get_property_details',
          description: 'Get detailed information about a specific property',
          inputSchema: {
            type: 'object',
            properties: {
              propertyId: { type: 'string', description: 'Property ID' },
            },
            required: ['propertyId'],
          },
        },
        {
          name: 'query_database',
          description: 'Execute a custom query on ConcordBroker database',
          inputSchema: {
            type: 'object',
            properties: {
              table: { type: 'string', description: 'Table name to query' },
              filters: { type: 'object', description: 'Filter conditions' },
              limit: { type: 'number', description: 'Maximum number of results', default: 100 },
            },
            required: ['table'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'search_properties':
            return await this.searchProperties(args);

          case 'get_property_details':
            return await this.getPropertyDetails(args);

          case 'query_database':
            return await this.queryDatabase(args);

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async searchProperties(args) {
    const { location, minPrice, maxPrice, propertyType } = args;

    let query = this.supabase.from('properties').select('*');

    if (location) query = query.ilike('location', `%${location}%`);
    if (minPrice) query = query.gte('price', minPrice);
    if (maxPrice) query = query.lte('price', maxPrice);
    if (propertyType) query = query.eq('property_type', propertyType);

    const { data, error } = await query.limit(50);

    if (error) throw error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }

  async getPropertyDetails(args) {
    const { propertyId } = args;

    const { data, error } = await this.supabase
      .from('properties')
      .select('*')
      .eq('id', propertyId)
      .single();

    if (error) throw error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }

  async queryDatabase(args) {
    const { table, filters = {}, limit = 100 } = args;

    let query = this.supabase.from(table).select('*');

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      query = query.eq(key, value);
    });

    const { data, error } = await query.limit(limit);

    if (error) throw error;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('ConcordBroker MCP server running on stdio');
  }
}

const server = new ConcordBrokerMCPServer();
server.run().catch(console.error);
