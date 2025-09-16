#!/usr/bin/env node

/**
 * DataValidationAgent - Ensures all displayed data is accurate and from Supabase
 * 
 * Responsibilities:
 * 1. Verify data accuracy against source
 * 2. Detect missing or null fields
 * 3. Validate data types and formats
 * 4. Report discrepancies
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config({ path: join(dirname(__dirname), 'web/.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export class DataValidationAgent {
  constructor() {
    this.validationRules = {
      // Core fields that must always have data
      required: [
        'parcel_id',
        'phy_addr1',
        'phy_city',
        'county'
      ],
      
      // Fields that should be numbers
      numeric: [
        'just_value',
        'assessed_value',
        'taxable_value',
        'land_value',
        'building_value',
        'total_living_area',
        'land_sqft',
        'year_built',
        'bedrooms',
        'bathrooms',
        'sale_price'
      ],
      
      // Fields that should be dates
      dates: [
        'sale_date',
        'import_date'
      ],
      
      // Fields with specific formats
      formats: {
        parcel_id: /^\d{10,15}$/,
        phy_zipcd: /^\d{5}(-\d{4})?$/,
        year_built: /^(19|20)\d{2}$/
      }
    };
    
    this.stats = {
      totalChecked: 0,
      totalErrors: 0,
      missingData: {},
      invalidFormats: {},
      nullCriticalFields: []
    };
  }

  /**
   * Validate a single property record
   */
  async validateProperty(property) {
    const errors = [];
    const warnings = [];
    
    // Check required fields
    for (const field of this.validationRules.required) {
      if (!property[field] || property[field] === null) {
        errors.push({
          field,
          type: 'MISSING_REQUIRED',
          message: `Required field '${field}' is missing`
        });
        this.stats.nullCriticalFields.push(field);
      }
    }
    
    // Check numeric fields
    for (const field of this.validationRules.numeric) {
      if (property[field] !== undefined && property[field] !== null) {
        const value = property[field];
        if (isNaN(value) || typeof value !== 'number') {
          warnings.push({
            field,
            type: 'INVALID_TYPE',
            message: `Field '${field}' should be numeric but is '${typeof value}'`,
            value
          });
        }
        
        // Check for suspicious values
        if (field.includes('value') && value === 0) {
          warnings.push({
            field,
            type: 'SUSPICIOUS_VALUE',
            message: `Field '${field}' has a value of 0, which may indicate missing data`,
            value
          });
        }
      }
    }
    
    // Check date fields
    for (const field of this.validationRules.dates) {
      if (property[field] && property[field] !== null) {
        const date = new Date(property[field]);
        if (isNaN(date.getTime())) {
          errors.push({
            field,
            type: 'INVALID_DATE',
            message: `Field '${field}' contains invalid date: ${property[field]}`,
            value: property[field]
          });
        }
      }
    }
    
    // Check format rules
    for (const [field, regex] of Object.entries(this.validationRules.formats)) {
      if (property[field] && !regex.test(property[field].toString())) {
        warnings.push({
          field,
          type: 'INVALID_FORMAT',
          message: `Field '${field}' doesn't match expected format`,
          value: property[field],
          expectedFormat: regex.toString()
        });
        
        if (!this.stats.invalidFormats[field]) {
          this.stats.invalidFormats[field] = 0;
        }
        this.stats.invalidFormats[field]++;
      }
    }
    
    // Cross-field validation
    if (property.sale_price && property.sale_date) {
      const saleYear = new Date(property.sale_date).getFullYear();
      const currentYear = new Date().getFullYear();
      
      if (saleYear > currentYear) {
        errors.push({
          field: 'sale_date',
          type: 'FUTURE_DATE',
          message: `Sale date is in the future: ${property.sale_date}`
        });
      }
    }
    
    // Check for data completeness score
    const totalFields = Object.keys(property).length;
    const nullFields = Object.values(property).filter(v => v === null || v === undefined).length;
    const completeness = ((totalFields - nullFields) / totalFields) * 100;
    
    return {
      parcel_id: property.parcel_id,
      isValid: errors.length === 0,
      completeness: completeness.toFixed(2),
      errors,
      warnings,
      summary: {
        totalFields,
        nullFields,
        errorCount: errors.length,
        warningCount: warnings.length
      }
    };
  }

  /**
   * Validate multiple properties
   */
  async validateBatch(properties) {
    const results = [];
    
    for (const property of properties) {
      const validation = await this.validateProperty(property);
      results.push(validation);
      
      this.stats.totalChecked++;
      if (!validation.isValid) {
        this.stats.totalErrors++;
      }
      
      // Track missing data patterns
      for (const [key, value] of Object.entries(property)) {
        if (value === null || value === undefined) {
          if (!this.stats.missingData[key]) {
            this.stats.missingData[key] = 0;
          }
          this.stats.missingData[key]++;
        }
      }
    }
    
    return results;
  }

  /**
   * Check if data exists in Supabase for a property
   */
  async verifyDataSource(parcelId) {
    try {
      // Check main parcels table
      const { data: parcel, error: parcelError } = await supabase
        .from('florida_parcels')
        .select('*')
        .eq('parcel_id', parcelId)
        .single();
      
      if (parcelError || !parcel) {
        return {
          exists: false,
          table: 'florida_parcels',
          error: parcelError?.message
        };
      }
      
      // Check related tables
      const checks = await Promise.all([
        // Sales history
        supabase
          .from('property_sales_history')
          .select('count')
          .eq('parcel_id', parcelId)
          .single(),
        
        // NAV assessments
        supabase
          .from('nav_assessments')
          .select('count')
          .eq('parcel_id', parcelId)
          .single(),
        
        // Sunbiz data
        supabase
          .from('sunbiz_corporate')
          .select('count')
          .ilike('officers', `%${parcel.owner_name}%`)
          .limit(1)
      ]);
      
      return {
        exists: true,
        mainRecord: parcel,
        relatedData: {
          salesHistory: checks[0].data?.count || 0,
          navAssessments: checks[1].data?.count || 0,
          sunbizMatches: checks[2].data?.length || 0
        }
      };
      
    } catch (error) {
      return {
        exists: false,
        error: error.message
      };
    }
  }

  /**
   * Generate validation report
   */
  generateReport() {
    const sortedMissing = Object.entries(this.stats.missingData)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
    
    return {
      summary: {
        totalPropertiesChecked: this.stats.totalChecked,
        propertiesWithErrors: this.stats.totalErrors,
        errorRate: ((this.stats.totalErrors / this.stats.totalChecked) * 100).toFixed(2) + '%'
      },
      criticalIssues: {
        missingRequiredFields: [...new Set(this.stats.nullCriticalFields)],
        invalidFormats: this.stats.invalidFormats
      },
      topMissingFields: sortedMissing.map(([field, count]) => ({
        field,
        count,
        percentage: ((count / this.stats.totalChecked) * 100).toFixed(2) + '%'
      })),
      recommendations: this.generateRecommendations()
    };
  }

  /**
   * Generate recommendations based on validation results
   */
  generateRecommendations() {
    const recommendations = [];
    
    // Check for systematic missing data
    const missingThreshold = this.stats.totalChecked * 0.3; // 30% threshold
    
    for (const [field, count] of Object.entries(this.stats.missingData)) {
      if (count > missingThreshold) {
        recommendations.push({
          priority: 'HIGH',
          field,
          issue: `Field '${field}' is missing in ${((count / this.stats.totalChecked) * 100).toFixed(1)}% of records`,
          action: `Consider implementing data enrichment for '${field}' field`
        });
      }
    }
    
    // Check for format issues
    for (const [field, count] of Object.entries(this.stats.invalidFormats)) {
      if (count > 10) {
        recommendations.push({
          priority: 'MEDIUM',
          field,
          issue: `${count} records have invalid format for '${field}'`,
          action: `Implement format standardization for '${field}'`
        });
      }
    }
    
    // Check critical fields
    if (this.stats.nullCriticalFields.length > 0) {
      recommendations.push({
        priority: 'CRITICAL',
        issue: 'Critical fields are missing',
        fields: [...new Set(this.stats.nullCriticalFields)],
        action: 'Immediately populate required fields or filter out incomplete records'
      });
    }
    
    return recommendations;
  }

  /**
   * Real-time validation for UI components
   */
  async validateForUI(parcelId) {
    const start = Date.now();
    
    // Quick validation for UI responsiveness
    const { data, error } = await supabase
      .from('florida_parcels')
      .select('*')
      .eq('parcel_id', parcelId)
      .single();
    
    if (error) {
      return {
        valid: false,
        error: error.message,
        responseTime: Date.now() - start
      };
    }
    
    const validation = await this.validateProperty(data);
    
    return {
      valid: validation.isValid,
      completeness: validation.completeness,
      data,
      issues: [...validation.errors, ...validation.warnings],
      responseTime: Date.now() - start
    };
  }
}

// Export for use in other modules
export default DataValidationAgent;

// CLI interface for testing
if (import.meta.url === `file://${process.argv[1]}`) {
  const agent = new DataValidationAgent();
  
  console.log('🔍 Data Validation Agent Started');
  console.log('================================\n');
  
  // Test with sample properties
  const testValidation = async () => {
    try {
      // Get sample properties
      const { data: properties } = await supabase
        .from('florida_parcels')
        .select('*')
        .limit(100);
      
      if (!properties || properties.length === 0) {
        console.log('No properties found to validate');
        return;
      }
      
      console.log(`Validating ${properties.length} properties...\n`);
      
      // Validate batch
      const results = await agent.validateBatch(properties);
      
      // Show sample results
      const invalid = results.filter(r => !r.isValid);
      console.log(`❌ Found ${invalid.length} properties with validation errors\n`);
      
      if (invalid.length > 0) {
        console.log('Sample validation errors:');
        invalid.slice(0, 3).forEach(result => {
          console.log(`\nParcel ID: ${result.parcel_id}`);
          console.log(`Completeness: ${result.completeness}%`);
          console.log('Errors:', result.errors.slice(0, 2));
        });
      }
      
      // Generate report
      const report = agent.generateReport();
      console.log('\n📊 Validation Report:');
      console.log('====================');
      console.log(JSON.stringify(report, null, 2));
      
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };
  
  testValidation();
}