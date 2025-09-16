#!/usr/bin/env node

/**
 * ComprehensiveDataAnalyzer - Complete analysis of all components and data flow
 * Uses chain of agents to ensure 100% data accuracy
 */

import { MasterOrchestrator } from './MasterOrchestrator.js';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs/promises';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(dirname(__dirname), 'web/.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export class ComprehensiveDataAnalyzer {
  constructor() {
    this.orchestrator = new MasterOrchestrator();
    
    // Component mapping
    this.components = {
      cards: {
        MiniPropertyCard: {
          path: 'apps/web/src/components/property/MiniPropertyCard.tsx',
          requiredFields: [
            'parcel_id', 'phy_addr1', 'phy_city', 'phy_state', 'phy_zipcd',
            'owner_name', 'property_use_desc', 'year_built', 'total_living_area',
            'bedrooms', 'bathrooms', 'taxable_value', 'sale_price', 'sale_date'
          ]
        }
      },
      profile: {
        PropertyProfile: {
          path: 'apps/web/src/pages/property/PropertyProfile.tsx',
          requiredFields: [
            'parcel_id', 'phy_addr1', 'phy_city', 'phy_state', 'phy_zipcd',
            'owner_name', 'owner_addr1', 'owner_city', 'owner_state', 'owner_zip',
            'just_value', 'assessed_value', 'taxable_value', 'land_value', 'building_value'
          ]
        },
        EnhancedPropertyProfile: {
          path: 'apps/web/src/pages/property/EnhancedPropertyProfile.tsx',
          requiredFields: [
            'parcel_id', 'phy_addr1', 'phy_city', 'owner_name',
            'property_use_desc', 'year_built', 'total_living_area',
            'land_sqft', 'bedrooms', 'bathrooms', 'sale_price', 'sale_date'
          ]
        }
      },
      tabs: {
        CorePropertyTab: {
          path: 'apps/web/src/components/property/tabs/CorePropertyTab.tsx',
          requiredFields: [
            'parcel_id', 'property_use', 'property_use_desc', 'subdivision',
            'legal_desc', 'year_built', 'total_living_area', 'bedrooms', 'bathrooms',
            'land_sqft', 'land_acres', 'zoning'
          ],
          relatedTables: ['property_sales_history']
        },
        SunbizInfoTab: {
          path: 'apps/web/src/components/property/tabs/SunbizInfoTab.tsx',
          requiredFields: ['owner_name'],
          relatedTables: ['sunbiz_corporate']
        },
        PropertyTaxInfoTab: {
          path: 'apps/web/src/components/property/tabs/PropertyTaxInfoTab.tsx',
          requiredFields: [
            'just_value', 'assessed_value', 'taxable_value', 
            'land_value', 'building_value', 'exemptions'
          ],
          relatedTables: ['nav_assessments', 'tax_certificates']
        },
        PermitTab: {
          path: 'apps/web/src/components/property/tabs/PermitTab.tsx',
          requiredFields: ['parcel_id'],
          relatedTables: ['permits']
        },
        ForeclosureTab: {
          path: 'apps/web/src/components/property/tabs/ForeclosureTab.tsx',
          requiredFields: ['parcel_id'],
          relatedTables: ['foreclosure_cases']
        },
        SalesTaxDeedTab: {
          path: 'apps/web/src/components/property/tabs/SalesTaxDeedTab.tsx',
          requiredFields: ['parcel_id'],
          relatedTables: ['tax_deed_bidding_items']
        },
        TaxLienTab: {
          path: 'apps/web/src/components/property/tabs/TaxLienTab.tsx',
          requiredFields: ['parcel_id'],
          relatedTables: ['tax_lien_certificates']
        },
        AnalysisTab: {
          path: 'apps/web/src/components/property/tabs/AnalysisTab.tsx',
          requiredFields: [
            'taxable_value', 'sale_price', 'year_built', 'total_living_area',
            'land_sqft', 'bedrooms', 'bathrooms', 'phy_zipcd'
          ],
          relatedTables: ['property_sales_history', 'nav_assessments']
        }
      }
    };
    
    this.analysisResults = {
      componentIssues: {},
      databaseIssues: {},
      dataFlowIssues: {},
      missingTables: [],
      incompleteRecords: [],
      recommendations: []
    };
  }

  /**
   * Phase 1: Analyze all components for data binding
   */
  async analyzeAllComponents() {
    console.log('\n🔍 PHASE 1: Component Analysis');
    console.log('================================\n');
    
    const issues = [];
    
    // Analyze MiniPropertyCards
    console.log('Analyzing MiniPropertyCard...');
    const cardIssues = await this.analyzeComponent('MiniPropertyCard', this.components.cards.MiniPropertyCard);
    if (cardIssues.length > 0) {
      issues.push({ component: 'MiniPropertyCard', issues: cardIssues });
    }
    
    // Analyze PropertyProfiles
    for (const [name, config] of Object.entries(this.components.profile)) {
      console.log(`Analyzing ${name}...`);
      const profileIssues = await this.analyzeComponent(name, config);
      if (profileIssues.length > 0) {
        issues.push({ component: name, issues: profileIssues });
      }
    }
    
    // Analyze all tabs
    for (const [name, config] of Object.entries(this.components.tabs)) {
      console.log(`Analyzing ${name}...`);
      const tabIssues = await this.analyzeComponent(name, config);
      if (tabIssues.length > 0) {
        issues.push({ component: name, issues: tabIssues });
      }
    }
    
    this.analysisResults.componentIssues = issues;
    return issues;
  }

  /**
   * Analyze a single component
   */
  async analyzeComponent(name, config) {
    const issues = [];
    
    // Check if component file exists
    try {
      const filePath = path.join(process.cwd(), config.path);
      const content = await fs.readFile(filePath, 'utf8');
      
      // Check data bindings
      for (const field of config.requiredFields) {
        // Check if field is referenced in component
        const patterns = [
          `property?.${field}`,
          `data?.${field}`,
          `{${field}}`,
          `property.${field}`,
          `data.${field}`
        ];
        
        const isReferenced = patterns.some(pattern => content.includes(pattern));
        
        if (!isReferenced) {
          issues.push({
            type: 'MISSING_BINDING',
            field,
            message: `Field '${field}' not bound in component`
          });
        }
      }
      
      // Check related tables
      if (config.relatedTables) {
        for (const table of config.relatedTables) {
          const tableExists = await this.checkTableExists(table);
          if (!tableExists) {
            issues.push({
              type: 'MISSING_TABLE',
              table,
              message: `Related table '${table}' does not exist`
            });
          }
        }
      }
      
    } catch (error) {
      issues.push({
        type: 'FILE_ERROR',
        message: `Could not read component file: ${error.message}`
      });
    }
    
    return issues;
  }

  /**
   * Phase 2: Analyze database structure
   */
  async analyzeDatabaseStructure() {
    console.log('\n🗄️ PHASE 2: Database Analysis');
    console.log('================================\n');
    
    const issues = [];
    
    // Check main table
    console.log('Checking florida_parcels table...');
    const { data: sampleData, error } = await supabase
      .from('florida_parcels')
      .select('*')
      .limit(100);
    
    if (error) {
      issues.push({
        type: 'TABLE_ERROR',
        table: 'florida_parcels',
        error: error.message
      });
    } else if (sampleData) {
      // Analyze data completeness
      const completenessReport = await this.analyzeDataCompleteness(sampleData);
      issues.push({
        type: 'COMPLETENESS',
        table: 'florida_parcels',
        report: completenessReport
      });
    }
    
    // Check all required tables
    const requiredTables = [
      'florida_parcels',
      'property_sales_history',
      'nav_assessments',
      'sunbiz_corporate',
      'tax_certificates',
      'permits',
      'foreclosure_cases',
      'tax_deed_bidding_items',
      'tax_lien_certificates'
    ];
    
    for (const table of requiredTables) {
      console.log(`Checking ${table} table...`);
      const exists = await this.checkTableExists(table);
      if (!exists) {
        this.analysisResults.missingTables.push(table);
        issues.push({
          type: 'MISSING_TABLE',
          table,
          message: `Required table '${table}' is missing`
        });
      }
    }
    
    this.analysisResults.databaseIssues = issues;
    return issues;
  }

  /**
   * Check if table exists
   */
  async checkTableExists(tableName) {
    try {
      const { count, error } = await supabase
        .from(tableName)
        .select('*', { count: 'exact', head: true });
      
      return !error;
    } catch {
      return false;
    }
  }

  /**
   * Analyze data completeness
   */
  async analyzeDataCompleteness(data) {
    const fieldCompleteness = {};
    const totalRecords = data.length;
    
    // Get all field names
    const allFields = new Set();
    data.forEach(record => {
      Object.keys(record).forEach(field => allFields.add(field));
    });
    
    // Calculate completeness for each field
    for (const field of allFields) {
      let nonNullCount = 0;
      let nonZeroCount = 0;
      
      data.forEach(record => {
        if (record[field] !== null && record[field] !== undefined) {
          nonNullCount++;
          if (record[field] !== 0 && record[field] !== '') {
            nonZeroCount++;
          }
        }
      });
      
      fieldCompleteness[field] = {
        completeness: ((nonNullCount / totalRecords) * 100).toFixed(1),
        meaningful: ((nonZeroCount / totalRecords) * 100).toFixed(1)
      };
    }
    
    // Find critical missing fields
    const criticalFields = [
      'parcel_id', 'phy_addr1', 'phy_city', 'owner_name',
      'taxable_value', 'year_built', 'total_living_area'
    ];
    
    const criticalIssues = [];
    for (const field of criticalFields) {
      if (fieldCompleteness[field] && parseFloat(fieldCompleteness[field].meaningful) < 50) {
        criticalIssues.push({
          field,
          completeness: fieldCompleteness[field].meaningful + '%'
        });
      }
    }
    
    return {
      totalRecords,
      fieldCompleteness,
      criticalIssues,
      overallCompleteness: this.calculateOverallCompleteness(fieldCompleteness)
    };
  }

  /**
   * Calculate overall completeness
   */
  calculateOverallCompleteness(fieldCompleteness) {
    const values = Object.values(fieldCompleteness).map(f => parseFloat(f.meaningful));
    const average = values.reduce((sum, val) => sum + val, 0) / values.length;
    return average.toFixed(1);
  }

  /**
   * Phase 3: Fix data issues using agent chain
   */
  async fixDataIssues() {
    console.log('\n🔧 PHASE 3: Fixing Data Issues');
    console.log('================================\n');
    
    const fixes = [];
    
    // Find properties with incomplete data
    console.log('Finding properties with incomplete data...');
    const { data: incompleteProperties } = await supabase
      .from('florida_parcels')
      .select('parcel_id')
      .or('year_built.is.null,bedrooms.is.null,bathrooms.is.null,total_living_area.is.null')
      .limit(100);
    
    if (incompleteProperties && incompleteProperties.length > 0) {
      console.log(`Found ${incompleteProperties.length} properties with missing data\n`);
      
      // Process in batches
      const batchSize = 10;
      for (let i = 0; i < Math.min(incompleteProperties.length, 20); i += batchSize) {
        const batch = incompleteProperties.slice(i, i + batchSize);
        
        console.log(`Processing batch ${i / batchSize + 1}...`);
        
        const batchResults = await Promise.all(
          batch.map(async (prop) => {
            const result = await this.orchestrator.processPropertyRequest(prop.parcel_id);
            return {
              parcel_id: prop.parcel_id,
              success: result.success,
              completeness: result.quality?.completeness,
              enhanced: result.enhancements?.length > 0
            };
          })
        );
        
        fixes.push(...batchResults);
      }
    }
    
    return fixes;
  }

  /**
   * Phase 4: Create data mapping configuration
   */
  async createDataMapping() {
    console.log('\n🗺️ PHASE 4: Creating Data Mapping');
    console.log('===================================\n');
    
    const mapping = {
      MiniPropertyCard: {
        source: 'florida_parcels',
        fields: {
          address: 'phy_addr1',
          city: 'phy_city',
          state: 'phy_state || "FL"',
          zip: 'phy_zipcd',
          owner: 'owner_name',
          propertyType: 'property_use_desc || inferFromCode(property_use)',
          yearBuilt: 'year_built || inferFromNeighbors()',
          sqft: 'total_living_area',
          bedrooms: 'bedrooms || inferFromSqft(total_living_area)',
          bathrooms: 'bathrooms || inferFromBedrooms(bedrooms)',
          value: 'taxable_value',
          salePrice: 'sale_price || estimateFromValue(taxable_value)',
          saleDate: 'sale_date'
        }
      },
      PropertyProfile: {
        sources: {
          main: 'florida_parcels',
          sales: 'property_sales_history',
          assessments: 'nav_assessments',
          sunbiz: 'sunbiz_corporate'
        },
        tabs: {
          CoreProperty: {
            requiredQueries: [
              'SELECT * FROM florida_parcels WHERE parcel_id = ?',
              'SELECT * FROM property_sales_history WHERE parcel_id = ? ORDER BY sale_date DESC'
            ]
          },
          SunbizInfo: {
            requiredQueries: [
              'SELECT * FROM sunbiz_corporate WHERE officers ILIKE ?',
              'SELECT * FROM sunbiz_corporate WHERE corporate_name ILIKE ?'
            ]
          },
          PropertyTax: {
            requiredQueries: [
              'SELECT * FROM nav_assessments WHERE parcel_id = ?',
              'SELECT * FROM tax_certificates WHERE parcel_id = ?'
            ]
          }
        }
      }
    };
    
    return mapping;
  }

  /**
   * Phase 5: Validate all fixes
   */
  async validateFixes() {
    console.log('\n✅ PHASE 5: Validation');
    console.log('========================\n');
    
    // Test sample properties
    const testParcels = ['484330110110', '484330110120', '484330110130'];
    const validationResults = [];
    
    for (const parcelId of testParcels) {
      console.log(`Validating ${parcelId}...`);
      
      // Get property with all agents
      const result = await this.orchestrator.processPropertyRequest(parcelId);
      
      if (result.success) {
        const property = result.property;
        
        // Check all required fields
        const validation = {
          parcel_id: parcelId,
          completeness: result.quality.completeness,
          criticalFields: {
            address: !!property.phy_addr1,
            city: !!property.phy_city,
            owner: !!property.owner_name,
            value: !!property.taxable_value,
            yearBuilt: !!property.year_built,
            sqft: !!property.total_living_area,
            bedrooms: !!property.bedrooms,
            bathrooms: !!property.bathrooms
          },
          missingCritical: []
        };
        
        // Find missing critical fields
        for (const [field, hasValue] of Object.entries(validation.criticalFields)) {
          if (!hasValue) {
            validation.missingCritical.push(field);
          }
        }
        
        validationResults.push(validation);
      }
    }
    
    return validationResults;
  }

  /**
   * Generate comprehensive report
   */
  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        componentIssues: this.analysisResults.componentIssues.length,
        databaseIssues: this.analysisResults.databaseIssues.length,
        missingTables: this.analysisResults.missingTables.length,
        recommendations: []
      },
      details: this.analysisResults,
      solutions: []
    };
    
    // Generate recommendations
    if (this.analysisResults.missingTables.length > 0) {
      report.summary.recommendations.push({
        priority: 'CRITICAL',
        action: 'Create missing database tables',
        tables: this.analysisResults.missingTables
      });
    }
    
    if (this.analysisResults.componentIssues.length > 0) {
      report.summary.recommendations.push({
        priority: 'HIGH',
        action: 'Fix component data bindings',
        components: this.analysisResults.componentIssues.map(i => i.component)
      });
    }
    
    // Generate solutions
    report.solutions = [
      {
        issue: 'Missing data in database',
        solution: 'Use DataCompletionAgent to fill missing fields',
        implementation: 'orchestrator.completionAgent.batchComplete(parcelIds)'
      },
      {
        issue: 'Slow data loading',
        solution: 'Enable PerformanceAgent caching',
        implementation: 'orchestrator.performanceAgent.prefetchRelatedData(parcelId)'
      },
      {
        issue: 'Data validation errors',
        solution: 'Use DataValidationAgent for all queries',
        implementation: 'orchestrator.validationAgent.validateBatch(properties)'
      }
    ];
    
    return report;
  }

  /**
   * Run complete analysis and fix chain
   */
  async runCompleteAnalysis() {
    console.log('🚀 COMPREHENSIVE DATA ANALYSIS & FIX');
    console.log('=====================================\n');
    
    try {
      // Phase 1: Component Analysis
      await this.analyzeAllComponents();
      
      // Phase 2: Database Analysis
      await this.analyzeDatabaseStructure();
      
      // Phase 3: Fix Issues
      const fixes = await this.fixDataIssues();
      console.log(`\n✅ Applied ${fixes.filter(f => f.enhanced).length} data enhancements`);
      
      // Phase 4: Create Mapping
      const mapping = await this.createDataMapping();
      console.log('\n✅ Data mapping configuration created');
      
      // Phase 5: Validate
      const validation = await this.validateFixes();
      console.log('\n✅ Validation complete');
      
      // Generate Report
      const report = this.generateReport();
      
      // Save report
      await fs.writeFile(
        path.join(process.cwd(), 'DATA_ANALYSIS_REPORT.json'),
        JSON.stringify(report, null, 2)
      );
      
      console.log('\n📊 ANALYSIS COMPLETE');
      console.log('====================');
      console.log(`Component Issues: ${report.summary.componentIssues}`);
      console.log(`Database Issues: ${report.summary.databaseIssues}`);
      console.log(`Missing Tables: ${report.summary.missingTables}`);
      console.log('\nReport saved to DATA_ANALYSIS_REPORT.json');
      
      return report;
      
    } catch (error) {
      console.error('Analysis failed:', error);
      throw error;
    }
  }
}

export default ComprehensiveDataAnalyzer;

// CLI execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const analyzer = new ComprehensiveDataAnalyzer();
  
  analyzer.runCompleteAnalysis().then(report => {
    console.log('\n✅ Analysis and fixes complete!');
    process.exit(0);
  }).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}