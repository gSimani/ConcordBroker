/**
 * Property Ranking System based on USE codes
 * Implements the priority order for property display
 */

export interface PropertyRank {
  priority: number;
  category: string;
  hasSales: boolean;
}

/**
 * Get the display priority for a property based on its DOR use code
 * Lower numbers = higher priority (shown first)
 *
 * Priority Order:
 * 1. Multifamily (10+ units) - DOR code '003'
 * 2. Commercial (all commercial codes) - DOR codes 010-039
 * 3. Industrial - DOR codes 040-049
 * 4. Hotels/Motels - DOR code '039'
 * 5. Residential - DOR codes 000-009 (except 003, 008)
 * 6. Multifamily (<10 units) - DOR code '008'
 * 7. Land/Vacant - DOR codes with 'Vacant' in description
 * 8. Agricultural - DOR codes 050-069
 * 9. Institutional - DOR codes 070-079
 * 10. Governmental - DOR codes 080-089
 * 11. Everything else
 *
 * Within each category, properties WITH sales data rank higher
 */
export function getPropertyRank(dorCode?: string, hasSales?: boolean): PropertyRank {
  if (!dorCode) {
    return { priority: 1000, category: 'Unknown', hasSales: !!hasSales };
  }

  const code = dorCode.padStart(3, '0');
  const salesBoost = hasSales ? 0 : 100; // Properties WITH sales get 0, WITHOUT get +100

  // 1. Multifamily 10+ units (highest priority)
  if (code === '003') {
    return { priority: 1 + salesBoost, category: 'Multifamily 10+', hasSales: !!hasSales };
  }

  // 2. Commercial (excluding hotels for now)
  if ((code >= '010' && code <= '038') || code === '011' || code === '012' || code === '013' ||
      code === '014' || code === '015' || code === '016' || code === '017' || code === '018' ||
      code === '019' || code === '020' || code === '021' || code === '022' || code === '023' ||
      code === '024' || code === '025' || code === '026' || code === '027' || code === '028' ||
      code === '029' || code === '030' || code === '031' || code === '032' || code === '033' ||
      code === '034' || code === '035' || code === '036' || code === '037' || code === '038') {
    return { priority: 2 + salesBoost, category: 'Commercial', hasSales: !!hasSales };
  }

  // 3. Industrial
  if (code >= '040' && code <= '049') {
    return { priority: 3 + salesBoost, category: 'Industrial', hasSales: !!hasSales };
  }

  // 4. Hotels/Motels (special commercial category)
  if (code === '039') {
    return { priority: 4 + salesBoost, category: 'Hotel/Motel', hasSales: !!hasSales };
  }

  // 5. Residential (excluding multifamily)
  if ((code >= '000' && code <= '009') && code !== '003' && code !== '008') {
    return { priority: 5 + salesBoost, category: 'Residential', hasSales: !!hasSales };
  }

  // 6. Multifamily <10 units
  if (code === '008') {
    return { priority: 6 + salesBoost, category: 'Multifamily <10', hasSales: !!hasSales };
  }

  // 7. Vacant/Land (any code with '0' at end indicating vacant)
  if (code === '000' || code === '010' || code === '040' || code === '050' || code === '070' || code === '080' || code === '090') {
    return { priority: 7 + salesBoost, category: 'Vacant/Land', hasSales: !!hasSales };
  }

  // 8. Agricultural
  if (code >= '050' && code <= '069') {
    return { priority: 8 + salesBoost, category: 'Agricultural', hasSales: !!hasSales };
  }

  // 9. Institutional
  if (code >= '070' && code <= '079') {
    return { priority: 9 + salesBoost, category: 'Institutional', hasSales: !!hasSales };
  }

  // 10. Governmental
  if (code >= '080' && code <= '089') {
    return { priority: 10 + salesBoost, category: 'Governmental', hasSales: !!hasSales };
  }

  // 11. Everything else
  return { priority: 11 + salesBoost, category: 'Other', hasSales: !!hasSales };
}

/**
 * Sort properties by ranking priority
 */
export function sortByPropertyRank(properties: any[]): any[] {
  return [...properties].sort((a, b) => {
    const rankA = getPropertyRank(a.property_use || a.dor_uc, a.has_sales || a.sales_count > 0);
    const rankB = getPropertyRank(b.property_use || b.dor_uc, b.has_sales || b.sales_count > 0);

    // Sort by priority (lower number = higher priority = shown first)
    if (rankA.priority !== rankB.priority) {
      return rankA.priority - rankB.priority;
    }

    // If same priority, sort by property value (higher value first)
    const valueA = a.just_value || a.value || 0;
    const valueB = b.just_value || b.value || 0;
    return valueB - valueA;
  });
}

/**
 * Get SQL ORDER BY clause for ranked sorting
 * This creates a CASE statement that can be used in Supabase queries
 */
export function getSQLOrderByRank(): string {
  return `
    CASE
      WHEN dor_uc = '003' THEN 1  -- Multifamily 10+
      WHEN dor_uc BETWEEN '010' AND '038' THEN 2  -- Commercial
      WHEN dor_uc BETWEEN '040' AND '049' THEN 3  -- Industrial
      WHEN dor_uc = '039' THEN 4  -- Hotels
      WHEN dor_uc IN ('001', '002', '004', '005', '006', '007', '009') THEN 5  -- Residential
      WHEN dor_uc = '008' THEN 6  -- Multifamily <10
      WHEN dor_uc IN ('000', '010', '040', '050', '070', '080', '090') THEN 7  -- Vacant/Land
      WHEN dor_uc BETWEEN '050' AND '069' THEN 8  -- Agricultural
      WHEN dor_uc BETWEEN '070' AND '079' THEN 9  -- Institutional
      WHEN dor_uc BETWEEN '080' AND '089' THEN 10  -- Governmental
      ELSE 11  -- Other
    END ASC,
    just_value DESC
  `.trim();
}
