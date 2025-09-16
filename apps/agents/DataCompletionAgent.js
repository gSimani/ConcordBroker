#!/usr/bin/env node

/**
 * DataCompletionAgent - Automatically fills missing data from various sources
 * 
 * Responsibilities:
 * 1. Identify missing data fields
 * 2. Find alternative data sources
 * 3. Intelligently fill missing values
 * 4. Cross-reference and validate filled data
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

export class DataCompletionAgent {
  constructor() {
    this.dataSources = {
      primary: 'florida_parcels',
      secondary: [
        'property_sales_history',
        'nav_assessments',
        'sunbiz_corporate',
        'tax_certificates'
      ]
    };
    
    this.completionStrategies = {
      // Strategies for filling missing data
      year_built: this.inferYearBuilt.bind(this),
      bedrooms: this.inferBedrooms.bind(this),
      bathrooms: this.inferBathrooms.bind(this),
      owner_zip: this.inferOwnerZip.bind(this),
      property_use_desc: this.inferPropertyUseDesc.bind(this),
      subdivision: this.inferSubdivision.bind(this),
      sale_price: this.inferSalePrice.bind(this),
      total_living_area: this.inferLivingArea.bind(this)
    };
    
    this.stats = {
      totalProcessed: 0,
      fieldsCompleted: {},
      strategiesUsed: {},
      errors: []
    };
  }

  /**
   * Complete missing data for a single property
   */
  async completePropertyData(parcelId) {
    try {
      // Fetch main property data
      const { data: property, error } = await supabase
        .from('florida_parcels')
        .select('*')
        .eq('parcel_id', parcelId)
        .single();
      
      if (error || !property) {
        return {
          success: false,
          error: `Property not found: ${parcelId}`
        };
      }
      
      // Identify missing fields
      const missingFields = this.identifyMissingFields(property);
      
      if (missingFields.length === 0) {
        return {
          success: true,
          message: 'No missing fields',
          property
        };
      }
      
      // Attempt to complete each missing field
      const completions = {};
      const sources = {};
      
      for (const field of missingFields) {
        const completion = await this.completeField(property, field);
        if (completion.success) {
          completions[field] = completion.value;
          sources[field] = completion.source;
          
          // Track statistics
          if (!this.stats.fieldsCompleted[field]) {
            this.stats.fieldsCompleted[field] = 0;
          }
          this.stats.fieldsCompleted[field]++;
        }
      }
      
      // Update property with completed data
      if (Object.keys(completions).length > 0) {
        const { error: updateError } = await supabase
          .from('florida_parcels')
          .update(completions)
          .eq('parcel_id', parcelId);
        
        if (updateError) {
          console.error('Update error:', updateError);
          return {
            success: false,
            error: updateError.message
          };
        }
      }
      
      this.stats.totalProcessed++;
      
      return {
        success: true,
        originalMissing: missingFields,
        completed: Object.keys(completions),
        sources,
        updatedProperty: { ...property, ...completions }
      };
      
    } catch (error) {
      this.stats.errors.push({ parcelId, error: error.message });
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Identify missing or null fields in a property
   */
  identifyMissingFields(property) {
    const missingFields = [];
    const importantFields = [
      'year_built', 'bedrooms', 'bathrooms', 'total_living_area',
      'owner_zip', 'property_use_desc', 'subdivision',
      'sale_price', 'sale_date', 'land_acres'
    ];
    
    for (const field of importantFields) {
      if (property[field] === null || property[field] === undefined || 
          property[field] === '' || property[field] === 0) {
        missingFields.push(field);
      }
    }
    
    return missingFields;
  }

  /**
   * Complete a specific missing field
   */
  async completeField(property, field) {
    // Check if we have a strategy for this field
    if (this.completionStrategies[field]) {
      return await this.completionStrategies[field](property);
    }
    
    // Try generic completion strategies
    return await this.genericCompletion(property, field);
  }

  /**
   * Generic completion strategy using related tables
   */
  async genericCompletion(property, field) {
    // Check sales history
    const { data: salesHistory } = await supabase
      .from('property_sales_history')
      .select(field)
      .eq('parcel_id', property.parcel_id)
      .not(field, 'is', null)
      .order('sale_date', { ascending: false })
      .limit(1);
    
    if (salesHistory && salesHistory.length > 0 && salesHistory[0][field]) {
      return {
        success: true,
        value: salesHistory[0][field],
        source: 'property_sales_history'
      };
    }
    
    // Check NAV assessments
    const { data: navData } = await supabase
      .from('nav_assessments')
      .select(field)
      .eq('parcel_id', property.parcel_id)
      .not(field, 'is', null)
      .order('year', { ascending: false })
      .limit(1);
    
    if (navData && navData.length > 0 && navData[0][field]) {
      return {
        success: true,
        value: navData[0][field],
        source: 'nav_assessments'
      };
    }
    
    return { success: false };
  }

  /**
   * Infer year built from similar properties
   */
  async inferYearBuilt(property) {
    // Strategy 1: Check sales history
    const { data: salesData } = await supabase
      .from('property_sales_history')
      .select('year_built')
      .eq('parcel_id', property.parcel_id)
      .not('year_built', 'is', null)
      .limit(1);
    
    if (salesData && salesData.length > 0) {
      return {
        success: true,
        value: salesData[0].year_built,
        source: 'property_sales_history'
      };
    }
    
    // Strategy 2: Use median year from same subdivision
    if (property.subdivision) {
      const { data: neighbors } = await supabase
        .from('florida_parcels')
        .select('year_built')
        .eq('subdivision', property.subdivision)
        .not('year_built', 'is', null)
        .limit(20);
      
      if (neighbors && neighbors.length >= 5) {
        const years = neighbors.map(n => n.year_built).sort();
        const median = years[Math.floor(years.length / 2)];
        
        return {
          success: true,
          value: median,
          source: 'subdivision_median',
          confidence: 0.7
        };
      }
    }
    
    // Strategy 3: Use area average
    const { data: areaProperties } = await supabase
      .from('florida_parcels')
      .select('year_built')
      .eq('phy_zipcd', property.phy_zipcd)
      .not('year_built', 'is', null)
      .gte('total_living_area', (property.total_living_area || 1000) * 0.8)
      .lte('total_living_area', (property.total_living_area || 3000) * 1.2)
      .limit(30);
    
    if (areaProperties && areaProperties.length >= 10) {
      const years = areaProperties.map(p => p.year_built).sort();
      const median = years[Math.floor(years.length / 2)];
      
      return {
        success: true,
        value: median,
        source: 'area_median',
        confidence: 0.6
      };
    }
    
    return { success: false };
  }

  /**
   * Infer number of bedrooms from living area
   */
  async inferBedrooms(property) {
    if (!property.total_living_area) {
      return { success: false };
    }
    
    // Use statistical model based on living area
    const sqft = property.total_living_area;
    let estimatedBedrooms;
    
    if (sqft < 800) {
      estimatedBedrooms = 1;
    } else if (sqft < 1200) {
      estimatedBedrooms = 2;
    } else if (sqft < 1800) {
      estimatedBedrooms = 3;
    } else if (sqft < 2500) {
      estimatedBedrooms = 4;
    } else {
      estimatedBedrooms = Math.floor(sqft / 600);
    }
    
    // Validate against similar properties
    const { data: similar } = await supabase
      .from('florida_parcels')
      .select('bedrooms, total_living_area')
      .eq('phy_zipcd', property.phy_zipcd)
      .gte('total_living_area', sqft * 0.9)
      .lte('total_living_area', sqft * 1.1)
      .not('bedrooms', 'is', null)
      .limit(10);
    
    if (similar && similar.length >= 3) {
      const avgBedrooms = similar.reduce((sum, p) => sum + p.bedrooms, 0) / similar.length;
      estimatedBedrooms = Math.round(avgBedrooms);
    }
    
    return {
      success: true,
      value: estimatedBedrooms,
      source: 'statistical_inference',
      confidence: 0.75
    };
  }

  /**
   * Infer number of bathrooms
   */
  async inferBathrooms(property) {
    // Usually correlates with bedrooms
    if (property.bedrooms) {
      const estimatedBathrooms = Math.max(1, Math.floor(property.bedrooms * 0.75));
      
      return {
        success: true,
        value: estimatedBathrooms,
        source: 'bedroom_correlation',
        confidence: 0.7
      };
    }
    
    if (property.total_living_area) {
      const sqft = property.total_living_area;
      const estimatedBathrooms = Math.max(1, Math.floor(sqft / 750));
      
      return {
        success: true,
        value: estimatedBathrooms,
        source: 'sqft_correlation',
        confidence: 0.6
      };
    }
    
    return { success: false };
  }

  /**
   * Infer owner ZIP code
   */
  async inferOwnerZip(property) {
    // Strategy 1: Use property ZIP if owner city matches
    if (property.owner_city === property.phy_city && property.phy_zipcd) {
      return {
        success: true,
        value: property.phy_zipcd,
        source: 'property_location',
        confidence: 0.9
      };
    }
    
    // Strategy 2: Find other properties with same owner
    if (property.owner_name) {
      const { data: otherProperties } = await supabase
        .from('florida_parcels')
        .select('owner_zip')
        .eq('owner_name', property.owner_name)
        .not('owner_zip', 'is', null)
        .limit(1);
      
      if (otherProperties && otherProperties.length > 0) {
        return {
          success: true,
          value: otherProperties[0].owner_zip,
          source: 'other_properties',
          confidence: 0.95
        };
      }
    }
    
    return { success: false };
  }

  /**
   * Infer property use description
   */
  async inferPropertyUseDesc(property) {
    if (!property.property_use) {
      return { success: false };
    }
    
    const useCodeMap = {
      '001': 'Single Family',
      '002': 'Mobile Home',
      '003': 'Multi-Family',
      '004': 'Condominium',
      '005': 'Cooperative',
      '100': 'Vacant Commercial',
      '101': 'Retail Store',
      '102': 'Office Building'
    };
    
    const description = useCodeMap[property.property_use];
    
    if (description) {
      return {
        success: true,
        value: description,
        source: 'use_code_mapping',
        confidence: 1.0
      };
    }
    
    return { success: false };
  }

  /**
   * Infer subdivision from nearby properties
   */
  async inferSubdivision(property) {
    if (!property.phy_addr1 || !property.phy_city) {
      return { success: false };
    }
    
    // Extract street name
    const streetMatch = property.phy_addr1.match(/\d+\s+(.+)/);
    if (!streetMatch) {
      return { success: false };
    }
    
    const streetName = streetMatch[1];
    
    // Find properties on same street
    const { data: neighbors } = await supabase
      .from('florida_parcels')
      .select('subdivision')
      .ilike('phy_addr1', `%${streetName}%`)
      .eq('phy_city', property.phy_city)
      .not('subdivision', 'is', null)
      .limit(10);
    
    if (neighbors && neighbors.length > 0) {
      // Find most common subdivision
      const subdivisionCounts = {};
      neighbors.forEach(n => {
        subdivisionCounts[n.subdivision] = (subdivisionCounts[n.subdivision] || 0) + 1;
      });
      
      const mostCommon = Object.entries(subdivisionCounts)
        .sort((a, b) => b[1] - a[1])[0];
      
      if (mostCommon && mostCommon[1] >= 3) {
        return {
          success: true,
          value: mostCommon[0],
          source: 'neighbor_inference',
          confidence: mostCommon[1] / neighbors.length
        };
      }
    }
    
    return { success: false };
  }

  /**
   * Infer sale price from assessments
   */
  async inferSalePrice(property) {
    // Check if we have recent assessment value
    if (property.just_value && property.just_value > 0) {
      // Sale prices typically range from 85% to 115% of just value
      const estimatedPrice = Math.round(property.just_value * 0.95);
      
      return {
        success: true,
        value: estimatedPrice,
        source: 'just_value_estimate',
        confidence: 0.6,
        note: 'Estimated from assessed value'
      };
    }
    
    return { success: false };
  }

  /**
   * Infer living area from bedrooms and bathrooms
   */
  async inferLivingArea(property) {
    if (property.bedrooms && property.bathrooms) {
      // Statistical model
      const baseArea = 600; // Base area
      const perBedroom = 350; // Additional area per bedroom
      const perBathroom = 100; // Additional area per bathroom
      
      const estimatedArea = baseArea + 
        (property.bedrooms * perBedroom) + 
        (property.bathrooms * perBathroom);
      
      return {
        success: true,
        value: estimatedArea,
        source: 'room_count_estimate',
        confidence: 0.5
      };
    }
    
    return { success: false };
  }

  /**
   * Batch process multiple properties
   */
  async batchComplete(parcelIds, options = {}) {
    const results = [];
    const batchSize = options.batchSize || 10;
    
    for (let i = 0; i < parcelIds.length; i += batchSize) {
      const batch = parcelIds.slice(i, i + batchSize);
      
      const batchResults = await Promise.all(
        batch.map(id => this.completePropertyData(id))
      );
      
      results.push(...batchResults);
      
      // Progress update
      if (options.onProgress) {
        options.onProgress({
          processed: Math.min(i + batchSize, parcelIds.length),
          total: parcelIds.length,
          percentage: ((Math.min(i + batchSize, parcelIds.length) / parcelIds.length) * 100).toFixed(1)
        });
      }
    }
    
    return results;
  }

  /**
   * Generate completion report
   */
  generateReport() {
    const totalCompleted = Object.values(this.stats.fieldsCompleted)
      .reduce((sum, count) => sum + count, 0);
    
    return {
      summary: {
        propertiesProcessed: this.stats.totalProcessed,
        totalFieldsCompleted: totalCompleted,
        averageCompletionsPerProperty: this.stats.totalProcessed > 0 ? 
          (totalCompleted / this.stats.totalProcessed).toFixed(2) : 0,
        errorCount: this.stats.errors.length
      },
      fieldCompletions: this.stats.fieldsCompleted,
      topCompletedFields: Object.entries(this.stats.fieldsCompleted)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([field, count]) => ({ field, count })),
      errors: this.stats.errors.slice(0, 10)
    };
  }
}

export default DataCompletionAgent;

// CLI testing
if (import.meta.url === `file://${process.argv[1]}`) {
  const agent = new DataCompletionAgent();
  
  console.log('🔧 Data Completion Agent Started');
  console.log('=================================\n');
  
  const runCompletionTest = async () => {
    try {
      // Find properties with missing data
      console.log('Finding properties with missing data...');
      const { data: incompleteProperties } = await supabase
        .from('florida_parcels')
        .select('parcel_id')
        .or('year_built.is.null,bedrooms.is.null,bathrooms.is.null')
        .limit(5);
      
      if (!incompleteProperties || incompleteProperties.length === 0) {
        console.log('No properties with missing data found');
        return;
      }
      
      console.log(`Found ${incompleteProperties.length} properties with missing data\n`);
      
      // Process each property
      for (const prop of incompleteProperties) {
        console.log(`Processing ${prop.parcel_id}...`);
        const result = await agent.completePropertyData(prop.parcel_id);
        
        if (result.success) {
          console.log(`  ✅ Completed ${result.completed.length} fields:`);
          result.completed.forEach(field => {
            console.log(`     - ${field}: ${result.sources[field]}`);
          });
        } else {
          console.log(`  ❌ Error: ${result.error}`);
        }
        console.log('');
      }
      
      // Generate report
      const report = agent.generateReport();
      console.log('📊 Completion Report:');
      console.log('====================');
      console.log(JSON.stringify(report, null, 2));
      
    } catch (error) {
      console.error('Completion test failed:', error);
    }
  };
  
  runCompletionTest();
}