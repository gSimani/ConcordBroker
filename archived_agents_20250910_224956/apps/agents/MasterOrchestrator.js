#!/usr/bin/env node

/**
 * MasterOrchestrator - Coordinates all agents for optimal data management
 * 
 * Responsibilities:
 * 1. Coordinate DataValidationAgent, PerformanceAgent, and DataCompletionAgent
 * 2. Ensure data accuracy, speed, and completeness
 * 3. Manage agent priorities and workflows
 * 4. Provide real-time data quality monitoring
 */

import { DataValidationAgent } from './DataValidationAgent.js';
import { PerformanceAgent } from './PerformanceAgent.js';
import { DataCompletionAgent } from './DataCompletionAgent.js';
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

export class MasterOrchestrator {
  constructor() {
    // Initialize all agents
    this.validationAgent = new DataValidationAgent();
    this.performanceAgent = new PerformanceAgent();
    this.completionAgent = new DataCompletionAgent();
    
    // Orchestration settings
    this.config = {
      autoComplete: true,
      autoValidate: true,
      cacheEnabled: true,
      performanceTargets: {
        propertyLoad: 200,  // ms
        searchResponse: 300, // ms
        dataCompletion: 500  // ms
      },
      validationThresholds: {
        minCompleteness: 70, // %
        maxErrors: 5
      }
    };
    
    // Monitoring state
    this.monitoring = {
      activeRequests: 0,
      totalProcessed: 0,
      avgResponseTime: 0,
      dataQualityScore: 0,
      lastHealthCheck: null
    };
  }

  /**
   * Process a property request with all agents
   */
  async processPropertyRequest(parcelId, options = {}) {
    const startTime = Date.now();
    this.monitoring.activeRequests++;
    
    try {
      // Step 1: Use PerformanceAgent for optimized fetching
      const property = await this.performanceAgent.optimizedQuery(
        `property:${parcelId}`,
        async () => {
          const { data, error } = await supabase
            .from('florida_parcels')
            .select('*')
            .eq('parcel_id', parcelId)
            .single();
          
          if (error) throw error;
          return data;
        }
      );
      
      if (!property) {
        return {
          success: false,
          error: 'Property not found',
          responseTime: Date.now() - startTime
        };
      }
      
      // Step 2: Validate the data
      const validation = await this.validationAgent.validateProperty(property);
      
      // Step 3: Complete missing data if needed
      let finalProperty = property;
      let completionResult = null;
      
      if (this.config.autoComplete && validation.completeness < this.config.validationThresholds.minCompleteness) {
        completionResult = await this.completionAgent.completePropertyData(parcelId);
        if (completionResult.success) {
          finalProperty = completionResult.updatedProperty;
          // Re-validate after completion
          validation.afterCompletion = await this.validationAgent.validateProperty(finalProperty);
        }
      }
      
      // Step 4: Prefetch related data for performance
      if (options.prefetch !== false) {
        this.performanceAgent.prefetchRelatedData(parcelId);
      }
      
      // Update monitoring
      const responseTime = Date.now() - startTime;
      this.updateMonitoring(responseTime, validation);
      
      return {
        success: true,
        property: finalProperty,
        quality: {
          completeness: validation.afterCompletion?.completeness || validation.completeness,
          errors: validation.errors.length,
          warnings: validation.warnings.length,
          dataSource: completionResult ? 'enhanced' : 'original'
        },
        performance: {
          responseTime,
          fromCache: responseTime < 50,
          target: this.config.performanceTargets.propertyLoad,
          status: responseTime <= this.config.performanceTargets.propertyLoad ? 'optimal' : 'slow'
        },
        enhancements: completionResult?.completed || []
      };
      
    } catch (error) {
      console.error('Orchestra error:', error);
      return {
        success: false,
        error: error.message,
        responseTime: Date.now() - startTime
      };
    } finally {
      this.monitoring.activeRequests--;
    }
  }

  /**
   * Process search with optimization
   */
  async processSearch(searchTerm, filters = {}) {
    const startTime = Date.now();
    
    try {
      // Use PerformanceAgent for optimized search
      const searchResult = await this.performanceAgent.optimizedSearch(searchTerm, filters);
      
      if (!searchResult.data || searchResult.data.length === 0) {
        return {
          success: true,
          properties: [],
          count: 0,
          responseTime: searchResult.executionTime
        };
      }
      
      // Validate and enhance results in parallel
      const enhancedResults = await Promise.all(
        searchResult.data.map(async (property) => {
          // Quick validation
          const validation = await this.validationAgent.validateProperty(property);
          
          // Mark incomplete properties
          if (validation.completeness < this.config.validationThresholds.minCompleteness) {
            property._needsCompletion = true;
            property._completeness = validation.completeness;
          }
          
          return property;
        })
      );
      
      return {
        success: true,
        properties: enhancedResults,
        count: enhancedResults.length,
        performance: {
          responseTime: searchResult.executionTime,
          target: this.config.performanceTargets.searchResponse,
          status: searchResult.executionTime <= this.config.performanceTargets.searchResponse ? 'optimal' : 'slow'
        },
        quality: {
          avgCompleteness: enhancedResults.reduce((sum, p) => sum + (p._completeness || 100), 0) / enhancedResults.length,
          needingCompletion: enhancedResults.filter(p => p._needsCompletion).length
        }
      };
      
    } catch (error) {
      console.error('Search orchestra error:', error);
      return {
        success: false,
        error: error.message,
        responseTime: Date.now() - startTime
      };
    }
  }

  /**
   * Batch process properties for data quality
   */
  async batchProcessProperties(parcelIds, options = {}) {
    const results = {
      processed: [],
      failed: [],
      summary: {
        total: parcelIds.length,
        completed: 0,
        enhanced: 0,
        errors: 0
      }
    };
    
    const batchSize = options.batchSize || 10;
    
    for (let i = 0; i < parcelIds.length; i += batchSize) {
      const batch = parcelIds.slice(i, i + batchSize);
      
      const batchResults = await Promise.all(
        batch.map(async (parcelId) => {
          try {
            const result = await this.processPropertyRequest(parcelId, {
              prefetch: false // Don't prefetch in batch mode
            });
            
            if (result.success) {
              results.processed.push({
                parcelId,
                completeness: result.quality.completeness,
                enhanced: result.enhancements.length > 0
              });
              
              results.summary.completed++;
              if (result.enhancements.length > 0) {
                results.summary.enhanced++;
              }
            } else {
              results.failed.push({ parcelId, error: result.error });
              results.summary.errors++;
            }
            
            return result;
          } catch (error) {
            results.failed.push({ parcelId, error: error.message });
            results.summary.errors++;
            return null;
          }
        })
      );
      
      // Progress callback
      if (options.onProgress) {
        options.onProgress({
          current: Math.min(i + batchSize, parcelIds.length),
          total: parcelIds.length,
          percentage: ((Math.min(i + batchSize, parcelIds.length) / parcelIds.length) * 100).toFixed(1)
        });
      }
    }
    
    return results;
  }

  /**
   * Real-time monitoring for UI components
   */
  async monitorDataCell(parcelId, field, component) {
    // Check if data exists
    const { data, error } = await supabase
      .from('florida_parcels')
      .select(field)
      .eq('parcel_id', parcelId)
      .single();
    
    if (error || !data || data[field] === null) {
      // Attempt to complete the missing field
      const property = await this.processPropertyRequest(parcelId);
      
      if (property.success && property.property[field]) {
        // Update the component with new data
        if (component && component.update) {
          component.update({
            field,
            value: property.property[field],
            source: property.enhancements.includes(field) ? 'completed' : 'original',
            quality: property.quality
          });
        }
        
        return {
          success: true,
          value: property.property[field],
          enhanced: property.enhancements.includes(field)
        };
      }
      
      return {
        success: false,
        field,
        message: 'Unable to complete missing data'
      };
    }
    
    return {
      success: true,
      value: data[field],
      enhanced: false
    };
  }

  /**
   * Health check for all agents
   */
  async performHealthCheck() {
    const health = {
      timestamp: new Date().toISOString(),
      agents: {},
      database: {},
      overall: 'healthy'
    };
    
    // Test ValidationAgent
    try {
      const testProperty = { parcel_id: 'test', phy_addr1: '123 Test St' };
      await this.validationAgent.validateProperty(testProperty);
      health.agents.validation = 'healthy';
    } catch (error) {
      health.agents.validation = 'error';
      health.overall = 'degraded';
    }
    
    // Test PerformanceAgent
    const perfReport = this.performanceAgent.generatePerformanceReport();
    health.agents.performance = {
      status: 'healthy',
      cacheHitRate: perfReport.summary.cacheHitRate,
      slowQueries: perfReport.summary.slowQueries.length
    };
    
    if (perfReport.summary.slowQueries.length > 5) {
      health.agents.performance.status = 'degraded';
      health.overall = 'degraded';
    }
    
    // Test CompletionAgent
    health.agents.completion = {
      status: 'healthy',
      stats: this.completionAgent.generateReport().summary
    };
    
    // Test database connection
    try {
      const { count } = await supabase
        .from('florida_parcels')
        .select('*', { count: 'exact', head: true });
      
      health.database = {
        status: 'connected',
        totalRecords: count
      };
    } catch (error) {
      health.database = {
        status: 'error',
        error: error.message
      };
      health.overall = 'critical';
    }
    
    // Calculate data quality score
    health.dataQuality = await this.calculateDataQualityScore();
    
    this.monitoring.lastHealthCheck = health;
    return health;
  }

  /**
   * Calculate overall data quality score
   */
  async calculateDataQualityScore() {
    // Sample random properties
    const { data: sample } = await supabase
      .from('florida_parcels')
      .select('*')
      .limit(100);
    
    if (!sample || sample.length === 0) {
      return { score: 0, message: 'No data to analyze' };
    }
    
    const validationResults = await this.validationAgent.validateBatch(sample);
    
    const avgCompleteness = validationResults.reduce((sum, r) => sum + parseFloat(r.completeness), 0) / validationResults.length;
    const errorRate = validationResults.filter(r => !r.isValid).length / validationResults.length * 100;
    
    // Calculate weighted score
    const score = Math.max(0, Math.min(100, 
      (avgCompleteness * 0.6) + // 60% weight on completeness
      ((100 - errorRate) * 0.4)  // 40% weight on validity
    ));
    
    return {
      score: score.toFixed(1),
      avgCompleteness: avgCompleteness.toFixed(1),
      errorRate: errorRate.toFixed(1),
      grade: score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F'
    };
  }

  /**
   * Update monitoring metrics
   */
  updateMonitoring(responseTime, validation) {
    this.monitoring.totalProcessed++;
    
    // Update average response time
    this.monitoring.avgResponseTime = 
      (this.monitoring.avgResponseTime * (this.monitoring.totalProcessed - 1) + responseTime) / 
      this.monitoring.totalProcessed;
    
    // Update data quality score (rolling average)
    const currentQuality = parseFloat(validation.completeness);
    this.monitoring.dataQualityScore = 
      (this.monitoring.dataQualityScore * (this.monitoring.totalProcessed - 1) + currentQuality) / 
      this.monitoring.totalProcessed;
  }

  /**
   * Get current monitoring status
   */
  getMonitoringStatus() {
    return {
      ...this.monitoring,
      performance: this.performanceAgent.generatePerformanceReport(),
      validation: this.validationAgent.generateReport(),
      completion: this.completionAgent.generateReport(),
      health: this.monitoring.lastHealthCheck
    };
  }

  /**
   * Configure orchestrator settings
   */
  configure(settings) {
    this.config = { ...this.config, ...settings };
    
    // Update agent configurations
    if (settings.cacheConfig) {
      this.performanceAgent.cacheConfig = { 
        ...this.performanceAgent.cacheConfig, 
        ...settings.cacheConfig 
      };
    }
    
    if (settings.validationRules) {
      this.validationAgent.validationRules = {
        ...this.validationAgent.validationRules,
        ...settings.validationRules
      };
    }
  }
}

export default MasterOrchestrator;

// CLI testing interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const orchestrator = new MasterOrchestrator();
  
  console.log('🎭 Master Orchestrator Started');
  console.log('==============================\n');
  
  const runOrchestratorTest = async () => {
    try {
      // Test 1: Process a single property
      console.log('[1] Testing single property processing...');
      const propertyResult = await orchestrator.processPropertyRequest('484330110110');
      
      if (propertyResult.success) {
        console.log('✅ Property processed successfully');
        console.log(`   Completeness: ${propertyResult.quality.completeness}%`);
        console.log(`   Response time: ${propertyResult.performance.responseTime}ms`);
        console.log(`   Enhancements: ${propertyResult.enhancements.join(', ') || 'None'}\n`);
      }
      
      // Test 2: Search with optimization
      console.log('[2] Testing optimized search...');
      const searchResult = await orchestrator.processSearch('2630 NE', { city: 'POMPANO BEACH' });
      
      if (searchResult.success) {
        console.log(`✅ Found ${searchResult.count} properties`);
        console.log(`   Response time: ${searchResult.performance.responseTime}ms`);
        console.log(`   Average completeness: ${searchResult.quality.avgCompleteness.toFixed(1)}%\n`);
      }
      
      // Test 3: Batch processing
      console.log('[3] Testing batch processing...');
      const testParcels = ['484330110110', '484330110120', '484330110130'];
      const batchResult = await orchestrator.batchProcessProperties(testParcels, {
        onProgress: (progress) => {
          console.log(`   Progress: ${progress.percentage}%`);
        }
      });
      
      console.log(`✅ Batch processing complete`);
      console.log(`   Processed: ${batchResult.summary.completed}/${batchResult.summary.total}`);
      console.log(`   Enhanced: ${batchResult.summary.enhanced}`);
      console.log(`   Errors: ${batchResult.summary.errors}\n`);
      
      // Test 4: Health check
      console.log('[4] Performing health check...');
      const health = await orchestrator.performHealthCheck();
      console.log(`✅ Health check complete`);
      console.log(`   Overall status: ${health.overall}`);
      console.log(`   Data quality score: ${health.dataQuality.score} (Grade: ${health.dataQuality.grade})`);
      console.log(`   Database: ${health.database.status}\n`);
      
      // Test 5: Get monitoring status
      console.log('[5] Monitoring Status');
      console.log('====================');
      const status = orchestrator.getMonitoringStatus();
      console.log(`Active requests: ${status.activeRequests}`);
      console.log(`Total processed: ${status.totalProcessed}`);
      console.log(`Avg response time: ${status.avgResponseTime.toFixed(2)}ms`);
      console.log(`Data quality score: ${status.dataQualityScore.toFixed(1)}%`);
      
    } catch (error) {
      console.error('Orchestrator test failed:', error);
    }
  };
  
  runOrchestratorTest();
}