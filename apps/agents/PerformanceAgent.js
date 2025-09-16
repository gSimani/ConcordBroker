#!/usr/bin/env node

/**
 * PerformanceAgent - Optimizes data fetching speed and caching
 * 
 * Responsibilities:
 * 1. Monitor query performance
 * 2. Implement intelligent caching
 * 3. Optimize slow queries
 * 4. Predict and prefetch data
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(dirname(__dirname), 'web/.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export class PerformanceAgent {
  constructor() {
    this.cache = new Map();
    this.queryMetrics = new Map();
    this.prefetchQueue = [];
    this.cacheConfig = {
      maxSize: 1000,
      ttl: 5 * 60 * 1000, // 5 minutes
      prefetchThreshold: 100 // ms
    };
    
    this.performanceTargets = {
      singlePropertyLoad: 200,    // ms
      listLoad: 500,              // ms
      searchResponse: 300,        // ms
      autocomplete: 150          // ms
    };
  }

  /**
   * Measure and optimize a query
   */
  async optimizedQuery(queryName, queryFn, options = {}) {
    const startTime = Date.now();
    const cacheKey = `${queryName}:${JSON.stringify(options)}`;
    
    // Check cache first
    const cached = this.getFromCache(cacheKey);
    if (cached) {
      this.recordMetric(queryName, Date.now() - startTime, true);
      return cached;
    }
    
    try {
      // Execute query
      const result = await queryFn();
      const executionTime = Date.now() - startTime;
      
      // Record metrics
      this.recordMetric(queryName, executionTime, false);
      
      // Cache if successful
      if (result) {
        this.setCache(cacheKey, result);
      }
      
      // Check if optimization needed
      if (executionTime > this.cacheConfig.prefetchThreshold) {
        this.scheduleOptimization(queryName, options);
      }
      
      return result;
    } catch (error) {
      console.error(`Query failed: ${queryName}`, error);
      throw error;
    }
  }

  /**
   * Batch fetch multiple properties efficiently
   */
  async batchFetchProperties(parcelIds) {
    const startTime = Date.now();
    const results = [];
    const uncached = [];
    
    // Check cache for each ID
    for (const id of parcelIds) {
      const cached = this.getFromCache(`property:${id}`);
      if (cached) {
        results.push(cached);
      } else {
        uncached.push(id);
      }
    }
    
    // Batch fetch uncached properties
    if (uncached.length > 0) {
      const { data, error } = await supabase
        .from('florida_parcels')
        .select('*')
        .in('parcel_id', uncached);
      
      if (data) {
        // Cache each property
        data.forEach(property => {
          this.setCache(`property:${property.parcel_id}`, property);
          results.push(property);
        });
      }
    }
    
    const executionTime = Date.now() - startTime;
    console.log(`Batch fetch: ${parcelIds.length} properties in ${executionTime}ms (${uncached.length} from DB)`);
    
    return results;
  }

  /**
   * Intelligent prefetching based on user patterns
   */
  async prefetchRelatedData(parcelId) {
    // Prefetch commonly accessed related data
    const prefetchTasks = [
      // Sales history
      this.optimizedQuery(
        'sales_history',
        () => supabase
          .from('property_sales_history')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false })
          .limit(10),
        { parcelId }
      ),
      
      // NAV assessments
      this.optimizedQuery(
        'nav_assessments',
        () => supabase
          .from('nav_assessments')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('year', { ascending: false })
          .limit(5),
        { parcelId }
      ),
      
      // Nearby properties (for comparison)
      this.prefetchNearbyProperties(parcelId)
    ];
    
    // Execute prefetch in background
    Promise.all(prefetchTasks).catch(error => {
      console.error('Prefetch error:', error);
    });
  }

  /**
   * Prefetch nearby properties for comparison
   */
  async prefetchNearbyProperties(parcelId) {
    const cacheKey = `nearby:${parcelId}`;
    
    if (this.getFromCache(cacheKey)) {
      return;
    }
    
    // Get base property
    const { data: baseProperty } = await supabase
      .from('florida_parcels')
      .select('phy_addr1, phy_city, phy_zipcd')
      .eq('parcel_id', parcelId)
      .single();
    
    if (!baseProperty) return;
    
    // Find nearby properties
    const { data: nearby } = await supabase
      .from('florida_parcels')
      .select('parcel_id, phy_addr1, taxable_value, total_living_area, year_built')
      .eq('phy_zipcd', baseProperty.phy_zipcd)
      .neq('parcel_id', parcelId)
      .limit(20);
    
    if (nearby) {
      this.setCache(cacheKey, nearby);
    }
  }

  /**
   * Optimize search queries with intelligent indexing
   */
  async optimizedSearch(searchTerm, filters = {}) {
    const startTime = Date.now();
    
    // Build optimized query
    let query = supabase
      .from('florida_parcels')
      .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, taxable_value');
    
    // Use most selective filter first
    if (filters.parcel_id) {
      query = query.eq('parcel_id', filters.parcel_id);
    } else if (searchTerm) {
      // Optimize search based on pattern
      if (/^\d+/.test(searchTerm)) {
        // Starts with number - likely address
        query = query.ilike('phy_addr1', `${searchTerm}%`);
      } else if (searchTerm.length <= 3) {
        // Short search - use exact prefix
        query = query.or(
          `phy_addr1.ilike.${searchTerm}%,` +
          `owner_name.ilike.${searchTerm}%`
        );
      } else {
        // Longer search - use contains
        query = query.or(
          `phy_addr1.ilike.%${searchTerm}%,` +
          `owner_name.ilike.%${searchTerm}%,` +
          `phy_city.ilike.%${searchTerm}%`
        );
      }
    }
    
    // Apply additional filters efficiently
    if (filters.city) {
      query = query.eq('phy_city', filters.city.toUpperCase());
    }
    if (filters.minValue) {
      query = query.gte('taxable_value', filters.minValue);
    }
    if (filters.maxValue) {
      query = query.lte('taxable_value', filters.maxValue);
    }
    
    // Limit for performance
    query = query.limit(50);
    
    const { data, error } = await query;
    const executionTime = Date.now() - startTime;
    
    // Log slow queries
    if (executionTime > this.performanceTargets.searchResponse) {
      console.warn(`Slow search query: ${executionTime}ms for "${searchTerm}"`);
      this.suggestOptimization('search', { searchTerm, filters, executionTime });
    }
    
    return { data, executionTime, error };
  }

  /**
   * Cache management
   */
  getFromCache(key) {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    // Check TTL
    if (Date.now() - entry.timestamp > this.cacheConfig.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    entry.hits++;
    return entry.data;
  }

  setCache(key, data) {
    // Implement LRU if cache is full
    if (this.cache.size >= this.cacheConfig.maxSize) {
      this.evictLRU();
    }
    
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      hits: 0
    });
  }

  evictLRU() {
    let oldestKey = null;
    let oldestTime = Date.now();
    
    for (const [key, entry] of this.cache.entries()) {
      if (entry.timestamp < oldestTime && entry.hits === 0) {
        oldestTime = entry.timestamp;
        oldestKey = key;
      }
    }
    
    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  /**
   * Performance monitoring
   */
  recordMetric(queryName, executionTime, fromCache) {
    if (!this.queryMetrics.has(queryName)) {
      this.queryMetrics.set(queryName, {
        count: 0,
        totalTime: 0,
        avgTime: 0,
        maxTime: 0,
        minTime: Infinity,
        cacheHits: 0
      });
    }
    
    const metrics = this.queryMetrics.get(queryName);
    metrics.count++;
    metrics.totalTime += executionTime;
    metrics.avgTime = metrics.totalTime / metrics.count;
    metrics.maxTime = Math.max(metrics.maxTime, executionTime);
    metrics.minTime = Math.min(metrics.minTime, executionTime);
    
    if (fromCache) {
      metrics.cacheHits++;
    }
  }

  /**
   * Suggest query optimizations
   */
  suggestOptimization(queryType, details) {
    const suggestions = [];
    
    if (queryType === 'search') {
      if (details.executionTime > 500) {
        suggestions.push({
          type: 'INDEX',
          message: 'Consider adding index on frequently searched columns',
          columns: ['phy_addr1', 'owner_name', 'phy_city']
        });
      }
      
      if (details.searchTerm && details.searchTerm.length < 3) {
        suggestions.push({
          type: 'QUERY',
          message: 'Short search terms are slow. Consider minimum length of 3 characters'
        });
      }
    }
    
    return suggestions;
  }

  /**
   * Schedule background optimization
   */
  scheduleOptimization(queryName, options) {
    // Add to optimization queue
    this.prefetchQueue.push({ queryName, options, timestamp: Date.now() });
    
    // Process queue in background
    if (this.prefetchQueue.length === 1) {
      setTimeout(() => this.processOptimizationQueue(), 1000);
    }
  }

  async processOptimizationQueue() {
    while (this.prefetchQueue.length > 0) {
      const task = this.prefetchQueue.shift();
      // Implement specific optimizations based on query type
      console.log(`Background optimization for: ${task.queryName}`);
    }
  }

  /**
   * Generate performance report
   */
  generatePerformanceReport() {
    const report = {
      summary: {
        totalQueries: 0,
        avgResponseTime: 0,
        cacheHitRate: 0,
        slowQueries: []
      },
      metrics: {},
      recommendations: []
    };
    
    for (const [name, metrics] of this.queryMetrics.entries()) {
      report.summary.totalQueries += metrics.count;
      
      const cacheHitRate = (metrics.cacheHits / metrics.count) * 100;
      
      report.metrics[name] = {
        count: metrics.count,
        avgTime: metrics.avgTime.toFixed(2),
        maxTime: metrics.maxTime,
        minTime: metrics.minTime === Infinity ? 0 : metrics.minTime,
        cacheHitRate: cacheHitRate.toFixed(2) + '%'
      };
      
      // Flag slow queries
      const target = this.performanceTargets[name] || 300;
      if (metrics.avgTime > target) {
        report.summary.slowQueries.push({
          name,
          avgTime: metrics.avgTime.toFixed(2),
          target,
          recommendation: `Optimize ${name} query - currently ${((metrics.avgTime / target) * 100 - 100).toFixed(0)}% over target`
        });
      }
    }
    
    // Calculate overall cache hit rate
    let totalHits = 0;
    let totalCount = 0;
    for (const metrics of this.queryMetrics.values()) {
      totalHits += metrics.cacheHits;
      totalCount += metrics.count;
    }
    report.summary.cacheHitRate = totalCount > 0 ? 
      ((totalHits / totalCount) * 100).toFixed(2) + '%' : '0%';
    
    // Add recommendations
    if (report.summary.cacheHitRate < 30) {
      report.recommendations.push('Increase cache TTL or size for better hit rate');
    }
    
    if (report.summary.slowQueries.length > 0) {
      report.recommendations.push('Consider implementing query result pagination');
      report.recommendations.push('Add database indexes on frequently queried columns');
    }
    
    return report;
  }
}

export default PerformanceAgent;

// CLI testing
if (import.meta.url === `file://${process.argv[1]}`) {
  const agent = new PerformanceAgent();
  
  console.log('⚡ Performance Agent Started');
  console.log('============================\n');
  
  const runPerformanceTest = async () => {
    try {
      // Test single property fetch
      console.log('Testing single property fetch...');
      const start1 = Date.now();
      await agent.optimizedQuery(
        'single_property',
        () => supabase
          .from('florida_parcels')
          .select('*')
          .eq('parcel_id', '484330110110')
          .single()
      );
      console.log(`First fetch: ${Date.now() - start1}ms\n`);
      
      // Test cache hit
      const start2 = Date.now();
      await agent.optimizedQuery(
        'single_property',
        () => supabase
          .from('florida_parcels')
          .select('*')
          .eq('parcel_id', '484330110110')
          .single()
      );
      console.log(`Cached fetch: ${Date.now() - start2}ms\n`);
      
      // Test batch fetch
      console.log('Testing batch fetch...');
      const parcelIds = ['484330110110', '484330110120', '484330110130'];
      await agent.batchFetchProperties(parcelIds);
      
      // Test search
      console.log('\nTesting search performance...');
      const searchResult = await agent.optimizedSearch('2630 NE');
      console.log(`Search returned ${searchResult.data?.length || 0} results in ${searchResult.executionTime}ms\n`);
      
      // Generate report
      const report = agent.generatePerformanceReport();
      console.log('📊 Performance Report:');
      console.log('=====================');
      console.log(JSON.stringify(report, null, 2));
      
    } catch (error) {
      console.error('Performance test failed:', error);
    }
  };
  
  runPerformanceTest();
}