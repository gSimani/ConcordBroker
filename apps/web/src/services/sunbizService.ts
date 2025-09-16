import { supabase } from '@/lib/supabase';

export interface SunbizCorporate {
  id: number;
  doc_number: string;
  entity_name: string;
  status: string;
  filing_date: string;
  state_country: string;
  prin_addr1?: string;
  prin_addr2?: string;
  prin_city?: string;
  prin_state?: string;
  prin_zip?: string;
  mail_addr1?: string;
  mail_addr2?: string;
  mail_city?: string;
  mail_state?: string;
  mail_zip?: string;
  ein?: string;
  registered_agent?: string;
  file_type?: string;
  subtype?: string;
  import_date?: string;
  update_date?: string;
}

export interface SunbizEvent {
  id: number;
  doc_number: string;
  event_date: string;
  event_type: string;
  detail?: string;
}

export interface SunbizFictitious {
  id: number;
  doc_number: string;
  name: string;
  owner_name: string;
  owner_addr1?: string;
  owner_city?: string;
  owner_state?: string;
  owner_zip?: string;
  filed_date?: string;
  expires_date?: string;
  county?: string;
}

class SunbizService {
  /**
   * Search for Sunbiz entities by owner name
   */
  async searchByOwnerName(ownerName: string): Promise<SunbizCorporate[]> {
    try {
      // Clean the owner name for better matching
      const cleanName = ownerName.trim().toUpperCase();
      
      // Search in corporate entities
      const { data, error } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .or(`entity_name.ilike.%${cleanName}%,registered_agent.ilike.%${cleanName}%`)
        .eq('status', 'ACTIVE')
        .order('filing_date', { ascending: false })
        .limit(10);

      if (error) {
        console.error('Error searching Sunbiz corporate:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in searchByOwnerName:', error);
      return [];
    }
  }

  /**
   * Search for fictitious names (DBAs) by owner
   */
  async searchFictitiousByOwner(ownerName: string): Promise<SunbizFictitious[]> {
    try {
      const cleanName = ownerName.trim().toUpperCase();
      
      const { data, error } = await supabase
        .from('sunbiz_fictitious')
        .select('*')
        .or(`owner_name.ilike.%${cleanName}%,name.ilike.%${cleanName}%`)
        .order('filed_date', { ascending: false })
        .limit(10);

      if (error) {
        console.error('Error searching Sunbiz fictitious:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in searchFictitiousByOwner:', error);
      return [];
    }
  }

  /**
   * Search by address to find businesses at a property
   */
  async searchByAddress(address: string, city?: string): Promise<SunbizCorporate[]> {
    try {
      const cleanAddress = address.trim().toUpperCase();
      const cleanCity = city?.trim().toUpperCase();
      
      let query = supabase
        .from('sunbiz_corporate')
        .select('*')
        .or(`prin_addr1.ilike.%${cleanAddress}%,mail_addr1.ilike.%${cleanAddress}%`);

      if (cleanCity) {
        query = query.or(`prin_city.eq.${cleanCity},mail_city.eq.${cleanCity}`);
      }

      const { data, error } = await query
        .eq('status', 'ACTIVE')
        .order('filing_date', { ascending: false })
        .limit(10);

      if (error) {
        console.error('Error searching by address:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in searchByAddress:', error);
      return [];
    }
  }

  /**
   * Get corporate events for an entity
   */
  async getCorporateEvents(docNumber: string): Promise<SunbizEvent[]> {
    try {
      const { data, error } = await supabase
        .from('sunbiz_corporate_events')
        .select('*')
        .eq('doc_number', docNumber)
        .order('event_date', { ascending: false });

      if (error) {
        console.error('Error fetching corporate events:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in getCorporateEvents:', error);
      return [];
    }
  }

  /**
   * Get entity by document number
   */
  async getEntityByDocNumber(docNumber: string): Promise<SunbizCorporate | null> {
    try {
      const { data, error } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .eq('doc_number', docNumber)
        .single();

      if (error) {
        console.error('Error fetching entity:', error);
        return null;
      }

      return data;
    } catch (error) {
      console.error('Error in getEntityByDocNumber:', error);
      return null;
    }
  }

  /**
   * Search for all business entities related to a property
   * Priority: 1) Exact address match, 2) Owner name match in officers
   */
  async searchForProperty(ownerName: string, address: string, city?: string): Promise<{
    corporate: SunbizCorporate[];
    fictitious: SunbizFictitious[];
    events: SunbizEvent[];
  }> {
    try {
      const corporate: SunbizCorporate[] = [];
      const fictitious: SunbizFictitious[] = [];
      
      // STEP 1: Search for EXACT address match (Priority 1)
      if (address) {
        console.log(`[Sunbiz Priority 1] Searching for EXACT address match: "${address}"`);
        const exactAddressResults = await this.searchByExactAddress(address, city);
        if (exactAddressResults.length > 0) {
          corporate.push(...exactAddressResults);
          console.log(`[Sunbiz Priority 1] ✓ Found ${exactAddressResults.length} exact address match(es)`);
        } else {
          console.log('[Sunbiz Priority 1] ✗ No exact address matches found');
        }
      }
      
      // STEP 2: If no exact address match, search for owner names in officers
      if (corporate.length === 0 && ownerName) {
        console.log(`[Sunbiz Priority 2] No address match found, searching for property owner(s) in officer records`);
        
        // Parse owner names (handle multiple owners separated by &, AND, or comma)
        const ownerNames = this.parseOwnerNames(ownerName);
        console.log(`[Sunbiz Priority 2] Parsed owner names:`, ownerNames);
        
        // Search for each owner name in officer records (exact match only)
        for (const name of ownerNames) {
          console.log(`[Sunbiz Priority 2] Searching for exact officer match: "${name}"`);
          const officerMatches = await this.searchByOfficerName(name);
          if (officerMatches.length > 0) {
            console.log(`[Sunbiz Priority 2] ✓ Found ${officerMatches.length} match(es) for "${name}"`);
            corporate.push(...officerMatches);
          }
        }
        
        // Deduplicate results based on doc_number
        if (corporate.length > 0) {
          const uniqueCorporate = new Map<string, SunbizCorporate>();
          corporate.forEach(entity => {
            if (!uniqueCorporate.has(entity.doc_number)) {
              uniqueCorporate.set(entity.doc_number, entity);
            }
          });
          corporate.length = 0;
          corporate.push(...Array.from(uniqueCorporate.values()));
          console.log(`[Sunbiz Priority 2] Total unique entities found: ${corporate.length}`);
        } else {
          console.log('[Sunbiz Priority 2] ✗ No officer matches found');
        }
      }
      
      // Get fictitious names for owner
      if (ownerName) {
        const fictitiousResults = await this.searchFictitiousByOwner(ownerName);
        fictitious.push(...fictitiousResults);
      }

      // Get events for all corporate entities
      const events: SunbizEvent[] = [];
      if (corporate.length > 0) {
        const eventPromises = corporate.map(entity => 
          this.getCorporateEvents(entity.doc_number)
        );
        const eventsArrays = await Promise.all(eventPromises);
        events.push(...eventsArrays.flat());
      }

      return {
        corporate,
        fictitious,
        events
      };
    } catch (error) {
      console.error('Error in searchForProperty:', error);
      return {
        corporate: [],
        fictitious: [],
        events: []
      };
    }
  }

  /**
   * Search for EXACT address match in corporate entities
   */
  async searchByExactAddress(address: string, city?: string): Promise<SunbizCorporate[]> {
    try {
      const cleanAddress = address.trim().toUpperCase();
      
      // Build exact match filter for addresses
      // Using exact equality (eq) instead of ilike for exact matching
      const { data, error } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .or(`prin_addr1.eq.${cleanAddress},mail_addr1.eq.${cleanAddress}`)
        .eq('status', 'ACTIVE')
        .order('filing_date', { ascending: false })
        .limit(10);
      
      if (error) {
        console.error('Error searching by exact address:', error);
        return [];
      }
      
      // Double-check for exact matches only (case-insensitive)
      const exactMatches = (data || []).filter(entity => {
        const prinAddr = entity.prin_addr1?.toUpperCase().trim();
        const mailAddr = entity.mail_addr1?.toUpperCase().trim();
        return prinAddr === cleanAddress || mailAddr === cleanAddress;
      });
      
      return exactMatches;
    } catch (error) {
      console.error('Error in searchByExactAddress:', error);
      return [];
    }
  }
  
  /**
   * Parse owner names from property records
   * Handles multiple owners separated by &, AND, or comma
   */
  parseOwnerNames(ownerName: string): string[] {
    if (!ownerName) return [];
    
    const cleanName = ownerName.trim();
    const names: string[] = [];
    
    // Check for common patterns in property ownership
    // Pattern 1: "LASTNAME, FIRSTNAME & LASTNAME, FIRSTNAME"
    // Pattern 2: "FIRSTNAME LASTNAME AND FIRSTNAME LASTNAME"
    // Pattern 3: "LASTNAME FIRSTNAME & LASTNAME FIRSTNAME"
    // Pattern 4: "BUSINESS NAME LLC"
    
    // Split by & or AND (with word boundaries)
    const splitPattern = /\s+(?:&|\bAND\b)\s+/i;
    const parts = cleanName.split(splitPattern);
    
    // Process each part
    parts.forEach(part => {
      const trimmedPart = part.trim();
      if (trimmedPart.length > 0) {
        names.push(trimmedPart);
        
        // If the part contains a comma, also try the reversed format
        // "LASTNAME, FIRSTNAME" -> "FIRSTNAME LASTNAME"
        if (trimmedPart.includes(',')) {
          const [last, first] = trimmedPart.split(',').map(s => s.trim());
          if (first && last) {
            names.push(`${first} ${last}`);
          }
        }
      }
    });
    
    // If we found multiple owners, also include the full original name
    // (in case it's a business entity that contains & or AND)
    if (parts.length > 1 && !names.includes(cleanName)) {
      names.push(cleanName);
    }
    
    // Remove duplicates while preserving order
    return Array.from(new Set(names));
  }
  
  /**
   * Search for entities where a person is listed as an officer (EXACT MATCH ONLY)
   */
  async searchByOfficerName(officerName: string): Promise<SunbizCorporate[]> {
    try {
      const cleanName = officerName.trim().toUpperCase();
      
      // Search for EXACT matches in registered_agent field
      // NOTE: When officers table is available, this should query that table
      const { data, error } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .eq('registered_agent', cleanName)
        .eq('status', 'ACTIVE')
        .order('filing_date', { ascending: false })
        .limit(10);
      
      if (error) {
        console.error('Error searching by officer name:', error);
        return [];
      }
      
      // Also check if there's a sunbiz_officers table we can query
      // Try to query the officers table if it exists
      const { data: officerData, error: officerError } = await supabase
        .from('sunbiz_officers')
        .select('doc_number')
        .eq('officer_name', cleanName);
      
      if (!officerError && officerData && officerData.length > 0) {
        // Get the corporate entities for these doc_numbers
        const docNumbers = officerData.map(o => o.doc_number);
        const { data: corpData, error: corpError } = await supabase
          .from('sunbiz_corporate')
          .select('*')
          .in('doc_number', docNumbers)
          .eq('status', 'ACTIVE')
          .order('filing_date', { ascending: false });
        
        if (!corpError && corpData) {
          // Combine both results
          const combinedResults = [...(data || []), ...(corpData || [])];
          // Remove duplicates based on doc_number
          const uniqueResults = Array.from(
            new Map(combinedResults.map(item => [item.doc_number, item])).values()
          );
          return uniqueResults;
        }
      }
      
      return data || [];
    } catch (error) {
      console.error('Error in searchByOfficerName:', error);
      return [];
    }
  }

  /**
   * Format address for display
   */
  formatAddress(entity: SunbizCorporate, type: 'principal' | 'mailing' = 'principal'): string {
    if (type === 'principal') {
      const parts = [
        entity.prin_addr1,
        entity.prin_addr2,
        entity.prin_city,
        entity.prin_state,
        entity.prin_zip
      ].filter(Boolean);
      return parts.join(', ');
    } else {
      const parts = [
        entity.mail_addr1,
        entity.mail_addr2,
        entity.mail_city,
        entity.mail_state,
        entity.mail_zip
      ].filter(Boolean);
      return parts.join(', ');
    }
  }

  /**
   * Check if entity is active
   */
  isActive(entity: SunbizCorporate): boolean {
    return entity.status?.toUpperCase() === 'ACTIVE';
  }

  /**
   * Get entity type description
   */
  getEntityType(entity: SunbizCorporate): string {
    const subtype = entity.subtype?.toUpperCase();
    if (subtype?.includes('LLC')) return 'Limited Liability Company';
    if (subtype?.includes('CORP')) return 'Corporation';
    if (subtype?.includes('LP')) return 'Limited Partnership';
    if (subtype?.includes('NONPROFIT')) return 'Non-Profit Organization';
    return entity.subtype || 'Business Entity';
  }
}

export const sunbizService = new SunbizService();