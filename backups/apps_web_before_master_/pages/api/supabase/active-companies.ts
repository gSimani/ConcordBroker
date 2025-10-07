import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  (process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || ''),
  (process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '')
);

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const {
      property_address,
      owner_name,
      search_term,
      entity_type = 'all',
      limit = 50,
      offset = 0
    } = req.body;

    // Query 1: Get active corporations from sunbiz_corporate
    let corporationQuery = supabase
      .from('sunbiz_corporate')
      .select(`
        id,
        doc_number,
        entity_name,
        status,
        filing_date,
        prin_addr1,
        prin_addr2,
        prin_city,
        prin_state,
        prin_zip
      `);

    // Add search filters
    if (search_term) {
      corporationQuery = corporationQuery.or(`entity_name.ilike.%${search_term}%,doc_number.ilike.%${search_term}%`);
    } else if (owner_name) {
      corporationQuery = corporationQuery.ilike('entity_name', `%${owner_name}%`);
    }

    const { data: corporations, error: corpError } = await corporationQuery
      .limit(limit)
      .range(offset, offset + limit - 1);

    if (corpError) {
      console.error('Corporation query error:', corpError);
    }

    // Query 2: Get companies with contact information
    const { data: companiesWithContacts, error: contactError } = await supabase
      .from('sunbiz_officer_corporation_matches')
      .select(`
        doc_number,
        officer_name,
        officer_email,
        officer_phone,
        corp_name,
        corp_address
      `)
      .not('officer_email', 'is', null)
      .limit(25);

    if (contactError) {
      console.error('Contact query error:', contactError);
    }

    // Query 3: Get active entities from florida_entities
    let entitiesQuery = supabase
      .from('florida_entities')
      .select(`
        id,
        entity_id,
        entity_type,
        business_name,
        entity_status,
        business_address_line1,
        business_city,
        business_state,
        business_zip
      `)
      .eq('entity_status', 'ACTIVE');

    if (search_term) {
      entitiesQuery = entitiesQuery.ilike('business_name', `%${search_term}%`);
    }

    const { data: activeEntities, error: entitiesError } = await entitiesQuery
      .limit(25);

    if (entitiesError) {
      console.error('Entities query error:', entitiesError);
    }

    // Query 4: Get total counts for statistics
    const { count: totalCorpCount } = await supabase
      .from('sunbiz_corporate')
      .select('*', { count: 'exact', head: true });

    const { count: totalActiveEntitiesCount } = await supabase
      .from('florida_entities')
      .select('*', { count: 'exact', head: true })
      .eq('entity_status', 'ACTIVE');

    const { count: totalParcelCount } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('owner_state', 'FL');

    // Combine and format results
    const companies = [];

    // Add corporations
    if (corporations) {
      corporations.forEach(corp => {
        const address = [corp.prin_addr1, corp.prin_addr2, corp.prin_city, corp.prin_state, corp.prin_zip]
          .filter(Boolean)
          .join(', ');

        // Check if this corporation has contact info
        const contactInfo = companiesWithContacts?.find(contact =>
          contact.doc_number === corp.doc_number
        );

        companies.push({
          id: corp.id,
          entity_name: corp.entity_name,
          entity_type: 'CORP',
          status: corp.status || 'ACTIVE',
          filing_date: corp.filing_date,
          business_address: address,
          doc_number: corp.doc_number,
          officer_name: contactInfo?.officer_name,
          officer_email: contactInfo?.officer_email,
          officer_phone: contactInfo?.officer_phone,
          source: 'sunbiz_corporate'
        });
      });
    }

    // Add active entities
    if (activeEntities) {
      activeEntities.forEach(entity => {
        const address = [entity.business_address_line1, entity.business_city, entity.business_state, entity.business_zip]
          .filter(Boolean)
          .join(', ');

        companies.push({
          id: entity.id,
          entity_name: entity.business_name,
          entity_type: entity.entity_type || 'ENTITY',
          status: entity.entity_status,
          filing_date: null,
          business_address: address,
          doc_number: entity.entity_id,
          officer_name: null,
          officer_email: null,
          officer_phone: null,
          source: 'florida_entities'
        });
      });
    }

    // Add companies with contact info that weren't already included
    if (companiesWithContacts) {
      companiesWithContacts.forEach(contact => {
        const alreadyAdded = companies.find(comp => comp.doc_number === contact.doc_number);
        if (!alreadyAdded) {
          companies.push({
            id: `contact_${contact.doc_number}`,
            entity_name: contact.corp_name,
            entity_type: 'ENTITY',
            status: 'ACTIVE',
            filing_date: null,
            business_address: contact.corp_address,
            doc_number: contact.doc_number,
            officer_name: contact.officer_name,
            officer_email: contact.officer_email,
            officer_phone: contact.officer_phone,
            source: 'officer_matches'
          });
        }
      });
    }

    // Calculate statistics
    const stats = {
      total_active: (totalCorpCount || 0) + (totalActiveEntitiesCount || 0) + (totalParcelCount || 0),
      corporations: totalCorpCount || 0,
      active_entities: totalActiveEntitiesCount || 0,
      property_owners: totalParcelCount || 0,
      with_contacts: companiesWithContacts?.length || 0
    };

    // Return results
    res.status(200).json({
      companies: companies.slice(0, limit),
      total_count: stats.total_active,
      has_more: companies.length === limit,
      statistics: stats,
      query_info: {
        searched_term: search_term,
        entity_type_filter: entity_type,
        results_from: ['sunbiz_corporate', 'florida_entities', 'officer_matches']
      }
    });

  } catch (error) {
    console.error('API error:', error);
    res.status(500).json({
      error: 'Failed to fetch active companies',
      details: error.message
    });
  }
}
