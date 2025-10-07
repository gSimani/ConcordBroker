/**
 * Property Intelligence Agent
 * Analyzes property data and provides intelligent reasoning for missing or N/A values
 */

export interface PropertyIntelligence {
  hasBuilding: boolean;
  buildingStatus: string;
  lotStatus: string;
  saleStatus: string;
  investmentPotential: string;
  dataCompleteness: number;
  recommendations: string[];
}

export class PropertyDataAnalyzer {
  /**
   * Analyze why living area might be N/A and provide reasoning
   */
  static analyzeLivingArea(bcpaData: any): { value: string | null; reason: string } {
    // Check multiple field variations
    const livingArea =
      bcpaData?.living_area ||
      bcpaData?.livingArea ||
      bcpaData?.tot_lvg_area ||
      bcpaData?.total_living_area ||
      bcpaData?.buildingSqFt ||
      bcpaData?.building_sqft ||
      0;

    const buildingValue =
      bcpaData?.building_value ||
      bcpaData?.buildingValue ||
      bcpaData?.bldg_val ||
      0;

    const propertyUse =
      bcpaData?.property_use ||
      bcpaData?.property_use_code ||
      bcpaData?.dor_uc ||
      bcpaData?.propertyUse ||
      '0';

    // Parse values
    const sqft = parseFloat(String(livingArea || 0));
    const bldgVal = parseFloat(String(buildingValue || 0));
    const useCode = String(propertyUse);

    // Determine reason for N/A
    if (useCode === '0' || useCode.includes('VACANT')) {
      return {
        value: null,
        reason: "Vacant land - No structures on property"
      };
    }

    if (sqft > 0) {
      return {
        value: `${sqft.toLocaleString()} sqft`,
        reason: ""
      };
    }

    if (bldgVal > 0) {
      return {
        value: null,
        reason: "Building exists but square footage not recorded"
      };
    }

    // Check if it's a special property type
    const useCodeNum = parseInt(useCode);
    if (useCodeNum >= 70 && useCodeNum <= 79) {
      return {
        value: null,
        reason: "Institutional/governmental property"
      };
    }

    if (useCodeNum >= 80 && useCodeNum <= 89) {
      return {
        value: null,
        reason: "Special purpose property - Area may not apply"
      };
    }

    return {
      value: null,
      reason: "Building data not available in records"
    };
  }

  /**
   * Analyze year built and provide reasoning
   */
  static analyzeYearBuilt(bcpaData: any): { value: string | null; reason: string } {
    const yearBuilt =
      bcpaData?.year_built ||
      bcpaData?.yearBuilt ||
      bcpaData?.act_yr_blt ||
      bcpaData?.eff_year_built ||
      null;

    const buildingValue =
      bcpaData?.building_value ||
      bcpaData?.buildingValue ||
      0;

    const propertyUse =
      bcpaData?.property_use ||
      bcpaData?.property_use_code ||
      bcpaData?.propertyUse ||
      '0';

    if (yearBuilt && yearBuilt > 1800 && yearBuilt <= new Date().getFullYear()) {
      return {
        value: String(yearBuilt),
        reason: ""
      };
    }

    if (propertyUse === '0' || String(propertyUse).includes('VACANT')) {
      return {
        value: null,
        reason: "Vacant land - No structures built"
      };
    }

    if (parseFloat(String(buildingValue)) > 0) {
      return {
        value: null,
        reason: "Structure exists but construction year not recorded"
      };
    }

    return {
      value: null,
      reason: "No building on this property"
    };
  }

  /**
   * Analyze bed/bath data and provide reasoning
   */
  static analyzeBedBath(bcpaData: any): { value: string | null; reason: string } {
    const bedrooms = bcpaData?.bedrooms || bcpaData?.no_of_bedrooms;
    const bathrooms = bcpaData?.bathrooms || bcpaData?.no_of_bathrooms;
    const propertyUse =
      bcpaData?.property_use ||
      bcpaData?.property_use_code ||
      bcpaData?.propertyUse ||
      bcpaData?.dor_uc ||
      '0';

    const livingArea =
      bcpaData?.living_area ||
      bcpaData?.livingArea ||
      bcpaData?.tot_lvg_area ||
      bcpaData?.buildingSqFt ||
      0;

    const useCodeNum = parseInt(String(propertyUse));
    const sqft = parseFloat(String(livingArea || 0));

    // For residential properties (codes 1-4)
    if (useCodeNum >= 1 && useCodeNum <= 4) {
      if (bedrooms && bathrooms) {
        return {
          value: `${bedrooms} bed / ${bathrooms} bath`,
          reason: ""
        };
      }

      if (sqft > 0) {
        // Estimate based on square footage
        const estimatedBeds = Math.max(1, Math.floor(sqft / 500));
        const estimatedBaths = Math.max(1, Math.floor(estimatedBeds / 1.5));
        return {
          value: `Est. ${estimatedBeds} bed / ${estimatedBaths} bath`,
          reason: "Estimated based on living area"
        };
      }

      return {
        value: null,
        reason: "Residential property - Bed/bath count not recorded"
      };
    }

    // For vacant land
    if (useCodeNum === 0) {
      return {
        value: null,
        reason: "Vacant land - No structures"
      };
    }

    // For commercial properties
    if (useCodeNum >= 5 && useCodeNum <= 39) {
      return {
        value: null,
        reason: "Commercial property - Bed/bath not applicable"
      };
    }

    // For industrial properties
    if (useCodeNum >= 40 && useCodeNum <= 49) {
      return {
        value: null,
        reason: "Industrial property - Bed/bath not applicable"
      };
    }

    // For agricultural properties
    if (useCodeNum >= 50 && useCodeNum <= 69) {
      return {
        value: null,
        reason: "Agricultural property"
      };
    }

    return {
      value: null,
      reason: "Property type does not typically have bed/bath counts"
    };
  }

  /**
   * Analyze lot size and provide formatting
   */
  static analyzeLotSize(bcpaData: any): { value: string | null; reason: string } {
    const lotSize =
      bcpaData?.lot_size_sqft ||
      bcpaData?.lnd_sqfoot ||
      bcpaData?.landSqFt ||
      bcpaData?.land_sqft ||
      0;

    const acres =
      bcpaData?.acres ||
      bcpaData?.landAcres ||
      bcpaData?.land_acres ||
      0;

    const sqft = parseFloat(String(lotSize || 0));
    const acreage = parseFloat(String(acres || 0));

    if (sqft > 0) {
      // Format based on size
      if (sqft >= 43560) { // 1 acre or more
        const acresCalc = (sqft / 43560).toFixed(2);
        return {
          value: `${sqft.toLocaleString()} sqft (${acresCalc} acres)`,
          reason: ""
        };
      }
      return {
        value: `${sqft.toLocaleString()} sqft`,
        reason: ""
      };
    }

    if (acreage > 0) {
      const sqftCalc = Math.round(acreage * 43560);
      return {
        value: `${sqftCalc.toLocaleString()} sqft (${acreage} acres)`,
        reason: ""
      };
    }

    // Check if it's a condo/townhouse
    const propertyUse = bcpaData?.property_use || bcpaData?.property_use_code || '0';
    if (propertyUse === '4' || propertyUse === '04') {
      return {
        value: null,
        reason: "Condo/Townhome - Land shared with other units"
      };
    }

    return {
      value: null,
      reason: "Lot size not recorded"
    };
  }

  /**
   * Analyze sales data and generate record link
   */
  static analyzeSaleData(bcpaData: any, lastSale: any): {
    saleInfo: string | null;
    recordLink: string | null;
    reason: string;
  } {
    // Check for sale data in multiple locations
    const salePrice =
      lastSale?.sale_price ||
      bcpaData?.sale_price ||
      bcpaData?.salePrice ||
      bcpaData?.sale_prc1 ||
      null;

    const saleDate =
      lastSale?.sale_date ||
      bcpaData?.sale_date ||
      bcpaData?.saleDate ||
      bcpaData?.lastSaleDate ||
      null;

    const book =
      lastSale?.book ||
      bcpaData?.or_book ||
      bcpaData?.book ||
      null;

    const page =
      lastSale?.page ||
      bcpaData?.or_page ||
      bcpaData?.page ||
      null;

    const cin =
      lastSale?.cin ||
      lastSale?.instrument_number ||
      bcpaData?.cin ||
      bcpaData?.clerk_instrument_number ||
      null;

    // Generate record link based on available data
    let recordLink = null;
    if (cin) {
      // CIN-based link (most modern)
      recordLink = `https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx?cin=${cin}`;
    } else if (book && page) {
      // Book/Page link (traditional)
      recordLink = `https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx?book=${book}&page=${page}`;
    }

    // Format sale info
    if (salePrice && parseFloat(String(salePrice)) > 0) {
      const price = parseFloat(String(salePrice));
      const formattedPrice = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(price);

      const dateStr = saleDate ? new Date(saleDate).toLocaleDateString() : 'Date unknown';

      return {
        saleInfo: `${formattedPrice} on ${dateStr}`,
        recordLink,
        reason: ""
      };
    }

    // Check if there's an owner but no sale data
    if (bcpaData?.owner_name && bcpaData?.owner_name !== 'UNKNOWN') {
      return {
        saleInfo: null,
        recordLink,
        reason: "Owner on record but sale details not available - May be inherited or pre-digital record"
      };
    }

    return {
      saleInfo: null,
      recordLink: null,
      reason: "No sales history found in public records"
    };
  }

  /**
   * Generate overall property intelligence
   */
  static analyzeProperty(bcpaData: any, lastSale: any): PropertyIntelligence {
    const livingAreaAnalysis = this.analyzeLivingArea(bcpaData);
    const yearBuiltAnalysis = this.analyzeYearBuilt(bcpaData);
    const bedBathAnalysis = this.analyzeBedBath(bcpaData);
    const saleAnalysis = this.analyzeSaleData(bcpaData, lastSale);

    const hasBuilding = !!(
      livingAreaAnalysis.value ||
      yearBuiltAnalysis.value ||
      (bcpaData?.building_value && parseFloat(bcpaData.building_value) > 0)
    );

    const propertyUse = bcpaData?.property_use || bcpaData?.property_use_code || '0';
    const useCodeNum = parseInt(String(propertyUse));

    // Determine building status
    let buildingStatus = "Unknown";
    if (hasBuilding) {
      buildingStatus = "Structure present on property";
    } else if (useCodeNum === 0) {
      buildingStatus = "Vacant land - No structures";
    } else if (useCodeNum >= 1 && useCodeNum <= 4) {
      buildingStatus = "Residential property type but no building data";
    } else {
      buildingStatus = "Non-residential property";
    }

    // Calculate data completeness
    let dataPoints = 0;
    let totalPoints = 0;

    // Check key data points
    const checkPoints = [
      bcpaData?.owner_name,
      bcpaData?.market_value || bcpaData?.marketValue,
      bcpaData?.assessed_value || bcpaData?.assessedValue,
      livingAreaAnalysis.value,
      yearBuiltAnalysis.value,
      saleAnalysis.saleInfo,
      bcpaData?.property_address_full || bcpaData?.address,
      bcpaData?.parcel_id
    ];

    checkPoints.forEach(point => {
      totalPoints++;
      if (point) dataPoints++;
    });

    const dataCompleteness = Math.round((dataPoints / totalPoints) * 100);

    // Generate recommendations
    const recommendations = [];

    if (!livingAreaAnalysis.value && hasBuilding) {
      recommendations.push("Request building measurements from property appraiser");
    }

    if (!yearBuiltAnalysis.value && hasBuilding) {
      recommendations.push("Check building permits for construction year");
    }

    if (!saleAnalysis.recordLink && saleAnalysis.saleInfo) {
      recommendations.push("Obtain official record documents for sale verification");
    }

    if (dataCompleteness < 50) {
      recommendations.push("Limited data available - Consider ordering property report");
    }

    return {
      hasBuilding,
      buildingStatus,
      lotStatus: useCodeNum === 0 ? "Vacant land" : "Improved property",
      saleStatus: saleAnalysis.saleInfo ? "Sale recorded" : "No recent sales",
      investmentPotential: dataCompleteness > 70 ? "High data confidence" : "Additional research recommended",
      dataCompleteness,
      recommendations
    };
  }
}

export default PropertyDataAnalyzer;