/**
 * Algorithm Service - Orchestrates all algorithm operations
 * Provides a unified interface for the application
 */

import { 
  addressTrie, 
  cityTrie, 
  ownerTrie,
  PropertyAddressTrie 
} from './property-trie';
import { 
  PropertyHeap, 
  TopKPropertyHeap,
  ScoredProperty 
} from './property-heap';
import { 
  PropertyBST, 
  MultiPropertyBST 
} from './property-bst';
import { 
  propertyCache,
  searchCache,
  apiResponseCache 
} from './property-cache';
import { 
  entityGraph,
  EntityGraph 
} from './entity-graph';

export class AlgorithmService {
  private static instance: AlgorithmService;
  
  // Data structures
  private addressTrie: PropertyAddressTrie;
  private cityTrie: PropertyAddressTrie;
  private ownerTrie: PropertyAddressTrie;
  private scoringHeap: PropertyHeap;
  private priceBST: PropertyBST;
  private multiBST: MultiPropertyBST;
  private entityGraph: EntityGraph;
  
  // Initialization flag
  private initialized = false;

  private constructor() {
    this.addressTrie = addressTrie;
    this.cityTrie = cityTrie;
    this.ownerTrie = ownerTrie;
    this.scoringHeap = new PropertyHeap(true); // Max heap for top scores
    this.priceBST = new PropertyBST('price');
    this.multiBST = new MultiPropertyBST();
    this.entityGraph = entityGraph;

    // Setup multi-dimensional BST indexes
    this.multiBST.addIndex('price');
    this.multiBST.addIndex('sqft');
    this.multiBST.addIndex('year_built');
    this.multiBST.addIndex('lot_size');
  }

  /**
   * Get singleton instance
   */
  static getInstance(): AlgorithmService {
    if (!AlgorithmService.instance) {
      AlgorithmService.instance = new AlgorithmService();
    }
    return AlgorithmService.instance;
  }

  /**
   * Initialize with data from API
   */
  async initialize(apiUrl: string): Promise<void> {
    if (this.initialized) return;

    try {
      // Load initial data for tries
      await this.loadAutocompleteData(apiUrl);
      
      // Load property data for BSTs and heaps
      await this.loadPropertyData(apiUrl);
      
      // Load entity relationships
      await this.loadEntityData(apiUrl);
      
      this.initialized = true;
      console.log('[AlgorithmService] Initialized successfully');
    } catch (error) {
      console.error('[AlgorithmService] Initialization failed:', error);
    }
  }

  /**
   * Load autocomplete data into tries
   */
  private async loadAutocompleteData(apiUrl: string): Promise<void> {
    // Check cache first
    const cacheKey = 'autocomplete_data';
    let data = searchCache.get(cacheKey);

    if (!data) {
      try {
        // Fetch common addresses, cities, and owners
        const [addressRes, cityRes, ownerRes] = await Promise.all([
          fetch(`${apiUrl}/api/autocomplete/common-addresses`),
          fetch(`${apiUrl}/api/autocomplete/common-cities`),
          fetch(`${apiUrl}/api/autocomplete/common-owners`)
        ]);

        if (addressRes.ok) {
          const addresses = await addressRes.json();
          addresses.forEach((item: any) => {
            this.addressTrie.insert(item.address, item.frequency || 1);
          });
        }

        if (cityRes.ok) {
          const cities = await cityRes.json();
          cities.forEach((item: any) => {
            this.cityTrie.insert(item.city, item.frequency || 1);
          });
        }

        if (ownerRes.ok) {
          const owners = await ownerRes.json();
          owners.forEach((item: any) => {
            this.ownerTrie.insert(item.owner, item.frequency || 1);
          });
        }

        // Cache the loaded state
        searchCache.put(cacheKey, { loaded: true });
      } catch (error) {
        console.error('[AlgorithmService] Failed to load autocomplete data:', error);
      }
    }
  }

  /**
   * Load property data for BSTs and scoring
   */
  private async loadPropertyData(apiUrl: string): Promise<void> {
    const cacheKey = 'property_index_data';
    let data = propertyCache.get(cacheKey);

    if (!data) {
      try {
        // Fetch sample property data for indexing
        const response = await fetch(`${apiUrl}/api/properties/featured?limit=1000`);
        
        if (response.ok) {
          const properties = await response.json();
          
          properties.forEach((property: any) => {
            // Add to BSTs for range queries
            this.multiBST.insert(property);
            
            // Add to price BST
            if (property.price || property.just_value) {
              this.priceBST.insert(
                property.id || property.parcel_id,
                property.price || property.just_value,
                property
              );
            }
            
            // Add to scoring heap if has score
            if (property.investment_score) {
              this.scoringHeap.insert({
                id: property.id || property.parcel_id,
                score: property.investment_score,
                data: property
              });
            }
          });
          
          // Cache the loaded state
          propertyCache.put(cacheKey, { loaded: true, count: properties.length });
        }
      } catch (error) {
        console.error('[AlgorithmService] Failed to load property data:', error);
      }
    }
  }

  /**
   * Load entity relationship data
   */
  private async loadEntityData(apiUrl: string): Promise<void> {
    const cacheKey = 'entity_graph_data';
    let data = propertyCache.get(cacheKey);

    if (!data) {
      try {
        // Fetch entity relationships
        const response = await fetch(`${apiUrl}/api/entities/relationships`);
        
        if (response.ok) {
          const relationships = await response.json();
          
          relationships.forEach((rel: any) => {
            // Add nodes
            if (rel.entity) {
              this.entityGraph.addNode(
                rel.entity.id,
                rel.entity.type,
                rel.entity.name,
                rel.entity
              );
            }
            
            if (rel.property) {
              this.entityGraph.addNode(
                rel.property.id,
                'property',
                rel.property.address,
                rel.property
              );
              
              // Add ownership edge
              if (rel.entity && rel.relationship === 'owns') {
                this.entityGraph.addEdge(
                  rel.entity.id,
                  rel.property.id,
                  'owns',
                  1,
                  { date: rel.date }
                );
              }
            }
          });
          
          // Cache the loaded state
          propertyCache.put(cacheKey, { loaded: true });
        }
      } catch (error) {
        console.error('[AlgorithmService] Failed to load entity data:', error);
      }
    }
  }

  /**
   * Search addresses with autocomplete
   */
  searchAddresses(prefix: string, limit = 10): string[] {
    // Check cache
    const cacheKey = `addr_${prefix}`;
    let results = apiResponseCache.get(cacheKey);
    
    if (!results) {
      results = this.addressTrie.search(prefix, limit);
      apiResponseCache.put(cacheKey, results, 30000); // Cache for 30 seconds
    }
    
    return results;
  }

  /**
   * Fuzzy search for addresses (handles typos)
   */
  fuzzySearchAddresses(prefix: string, limit = 10, tolerance = 2): string[] {
    const cacheKey = `fuzzy_addr_${prefix}`;
    let results = apiResponseCache.get(cacheKey);
    
    if (!results) {
      results = this.addressTrie.fuzzySearch(prefix, limit, tolerance);
      apiResponseCache.put(cacheKey, results, 30000);
    }
    
    return results;
  }

  /**
   * Find properties in price range
   */
  findPropertiesInPriceRange(min: number, max: number): any[] {
    const cacheKey = `price_range_${min}_${max}`;
    let results = searchCache.get(cacheKey);
    
    if (!results) {
      results = this.priceBST.findInRange(min, max);
      searchCache.put(cacheKey, results);
    }
    
    return results;
  }

  /**
   * Find properties matching multiple criteria
   */
  findPropertiesMultiCriteria(criteria: Array<{ field: string; min: number; max: number }>): any[] {
    const cacheKey = `multi_${JSON.stringify(criteria)}`;
    let results = searchCache.get(cacheKey);
    
    if (!results) {
      results = this.multiBST.findMultiRange(criteria);
      searchCache.put(cacheKey, results);
    }
    
    return results;
  }

  /**
   * Get top scored properties
   */
  getTopScoredProperties(n = 10): ScoredProperty[] {
    return this.scoringHeap.getTopN(n);
  }

  /**
   * Add property score
   */
  addPropertyScore(id: string, score: number, data: any): void {
    this.scoringHeap.insert({ id, score, data });
  }

  /**
   * Find entity's property portfolio
   */
  findEntityPortfolio(entityId: string): any[] {
    const cacheKey = `portfolio_${entityId}`;
    let results = propertyCache.get(cacheKey);
    
    if (!results) {
      results = this.entityGraph.findOwnedProperties(entityId);
      propertyCache.put(cacheKey, results, 5 * 60 * 1000); // Cache for 5 minutes
    }
    
    return results;
  }

  /**
   * Find related entities
   */
  findRelatedEntities(entityId: string, maxDepth = 2): Map<string, any> {
    return this.entityGraph.findConnectedEntities(entityId, maxDepth);
  }

  /**
   * Calculate entity importance (PageRank)
   */
  calculateEntityImportance(): Map<string, number> {
    const cacheKey = 'entity_pagerank';
    let results = propertyCache.get(cacheKey);
    
    if (!results) {
      results = this.entityGraph.calculatePageRank();
      propertyCache.put(cacheKey, results, 60 * 60 * 1000); // Cache for 1 hour
    }
    
    return results;
  }

  /**
   * Get algorithm statistics
   */
  getStats(): any {
    return {
      trie: {
        addresses: this.addressTrie.getStats(),
        cities: this.cityTrie.getStats(),
        owners: this.ownerTrie.getStats()
      },
      bst: {
        price: this.priceBST.getStats(),
      },
      heap: {
        size: this.scoringHeap.size(),
        top: this.scoringHeap.peek()
      },
      graph: this.entityGraph.getStats(),
      cache: {
        property: propertyCache.getStats(),
        search: searchCache.getStats(),
        api: { size: apiResponseCache.size() }
      }
    };
  }

  /**
   * Clear all data structures
   */
  clear(): void {
    this.addressTrie.clear();
    this.cityTrie.clear();
    this.ownerTrie.clear();
    this.scoringHeap.clear();
    this.priceBST.clear();
    this.multiBST.clear();
    this.entityGraph.clear();
    propertyCache.clear();
    searchCache.clear();
    apiResponseCache.clear();
    this.initialized = false;
  }
}

// Export singleton instance
export const algorithmService = AlgorithmService.getInstance();