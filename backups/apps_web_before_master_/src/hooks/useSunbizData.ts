import { useState, useEffect } from 'react';
import { sunbizService, type SunbizCorporate, type SunbizFictitious, type SunbizEvent } from '@/services/sunbizService';

interface SunbizData {
  corporate: SunbizCorporate[];
  fictitious: SunbizFictitious[];
  events: SunbizEvent[];
  loading: boolean;
  error: string | null;
}

export function useSunbizData(ownerName?: string, address?: string, city?: string) {
  const [data, setData] = useState<SunbizData>({
    corporate: [],
    fictitious: [],
    events: [],
    loading: true,
    error: null
  });

  useEffect(() => {
    const fetchSunbizData = async () => {
      // Skip if no owner name or address
      if (!ownerName && !address) {
        setData(prev => ({
          ...prev,
          loading: false,
          error: 'No owner name or address provided'
        }));
        return;
      }

      setData(prev => ({ ...prev, loading: true, error: null }));

      try {
        // Clean the inputs
        const cleanOwner = ownerName?.trim() || '';
        const cleanAddress = address?.trim() || '';
        const cleanCity = city?.trim();

        console.log('Sunbiz search starting with priority rules:', {
          '1_address_exact_match': cleanAddress,
          '2_owner_names': cleanOwner,
          'city': cleanCity
        });

        // Search for Sunbiz data with priority matching
        const results = await sunbizService.searchForProperty(
          cleanOwner,
          cleanAddress,
          cleanCity
        );

        setData({
          corporate: results.corporate,
          fictitious: results.fictitious,
          events: results.events,
          loading: false,
          error: null
        });

        // Log match type for debugging
        if (results.corporate.length > 0) {
          const hasAddressMatch = results.corporate.some(corp => 
            corp.prin_addr1?.includes(cleanAddress.toUpperCase()) || 
            corp.mail_addr1?.includes(cleanAddress.toUpperCase())
          );
          
          console.log('Sunbiz matches found:', {
            total: results.corporate.length,
            matchType: hasAddressMatch ? 'EXACT ADDRESS MATCH' : 'OWNER NAME IN OFFICERS',
            entities: results.corporate.map(c => ({
              name: c.entity_name,
              address: c.prin_addr1
            }))
          });
        } else {
          console.log('No Sunbiz matches found for property');
        }
      } catch (error) {
        console.error('Error fetching Sunbiz data:', error);
        setData(prev => ({
          ...prev,
          loading: false,
          error: 'Failed to fetch Sunbiz data'
        }));
      }
    };

    fetchSunbizData();
  }, [ownerName, address, city]);

  return data;
}

/**
 * Transform Sunbiz data to match the component's expected format
 */
export function transformSunbizData(
  corporate: SunbizCorporate[],
  fictitious: SunbizFictitious[],
  events: SunbizEvent[]
) {
  // Take the most relevant corporate entity (first active one or first overall)
  const primaryEntity = corporate.find(e => sunbizService.isActive(e)) || corporate[0];

  if (!primaryEntity) {
    return null;
  }

  // Group events by document number
  const entityEvents = events.filter(e => e.doc_number === primaryEntity.doc_number);

  // Format annual reports from events
  const annualReports = entityEvents
    .filter(e => e.event_type?.toLowerCase().includes('annual'))
    .map(e => ({
      year: new Date(e.event_date).getFullYear(),
      filed_date: e.event_date,
      status: 'Filed'
    }));

  // Format filing history
  const filingHistory = entityEvents.map(e => ({
    date: e.event_date,
    type: e.event_type,
    document_number: e.doc_number,
    detail: e.detail
  }));

  // Format fictitious names (DBAs)
  const dbas = fictitious.map(f => ({
    name: f.name,
    filed_date: f.filed_date,
    expires_date: f.expires_date,
    county: f.county
  }));

  return {
    entity_name: primaryEntity.entity_name,
    entity_type: sunbizService.getEntityType(primaryEntity),
    status: primaryEntity.status,
    state: primaryEntity.state_country || 'FL',
    document_number: primaryEntity.doc_number,
    fei_ein_number: primaryEntity.ein,
    date_filed: primaryEntity.filing_date,
    effective_date: primaryEntity.filing_date,
    principal_address: sunbizService.formatAddress(primaryEntity, 'principal'),
    mailing_address: sunbizService.formatAddress(primaryEntity, 'mailing'),
    registered_agent_name: primaryEntity.registered_agent,
    registered_agent_address: null, // Would need separate query for agent details
    officers: [], // Would need separate table/query for officers
    aggregate_id: primaryEntity.id.toString(),
    annual_reports: annualReports,
    filing_history: filingHistory,
    fictitious_names: dbas,
    
    // Additional fields
    prin_addr1: primaryEntity.prin_addr1,
    prin_city: primaryEntity.prin_city,
    prin_state: primaryEntity.prin_state,
    prin_zip: primaryEntity.prin_zip,
    mail_addr1: primaryEntity.mail_addr1,
    mail_city: primaryEntity.mail_city,
    mail_state: primaryEntity.mail_state,
    mail_zip: primaryEntity.mail_zip,
    
    // Related entities
    related_entities: corporate.slice(1).map(e => ({
      entity_name: e.entity_name,
      doc_number: e.doc_number,
      status: e.status,
      filing_date: e.filing_date,
      type: sunbizService.getEntityType(e)
    }))
  };
}