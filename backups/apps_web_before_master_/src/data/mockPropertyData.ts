// Mock property data with appraised values for testing
export const mockProperties = [
  {
    parcel_id: "123456789",
    phy_addr1: "123 Main Street",
    phy_addr2: "Unit 101",
    phy_city: "Miami",
    phy_zipcd: "33101",
    owner_name: "John Smith",
    just_value: 450000,  // Appraised value
    jv: 450000,         // Alternative field name
    market_value: 450000,
    taxable_value: 425000,
    tv_sd: 425000,
    land_value: 150000,
    lnd_val: 150000,
    building_sqft: 2500,
    tot_lvg_area: 2500,
    land_sqft: 7500,
    lnd_sqfoot: 7500,
    year_built: 2015,
    act_yr_blt: 2015,
    property_use: "01",
    propertyUseDesc: "Single Family Residential",
    sale_price: 425000,
    sale_yr1: 2023,
    sale_date: "2023-06-15",
    unit_number: "101",
    is_condo: true
  },
  {
    parcel_id: "987654321",
    phy_addr1: "456 Oak Avenue",
    phy_addr2: null,
    phy_city: "Fort Lauderdale",
    phy_zipcd: "33301",
    owner_name: "Jane Doe",
    just_value: 325000,  // Appraised value
    jv: 325000,
    market_value: 325000,
    taxable_value: 300000,
    tv_sd: 300000,
    land_value: 100000,
    lnd_val: 100000,
    building_sqft: 1800,
    tot_lvg_area: 1800,
    land_sqft: 6000,
    lnd_sqfoot: 6000,
    year_built: 2010,
    act_yr_blt: 2010,
    property_use: "01",
    propertyUseDesc: "Single Family Residential",
    sale_price: 310000,
    sale_yr1: 2022,
    sale_date: "2022-03-20",
    unit_number: "",
    is_condo: false
  },
  {
    parcel_id: "555666777",
    phy_addr1: "789 Beach Boulevard",
    phy_addr2: "APT 2405",
    phy_city: "Miami Beach",
    phy_zipcd: "33139",
    owner_name: "Beach Properties LLC",
    just_value: 1250000,  // Appraised value
    jv: 1250000,
    market_value: 1250000,
    taxable_value: 1100000,
    tv_sd: 1100000,
    land_value: 400000,
    lnd_val: 400000,
    building_sqft: 3200,
    tot_lvg_area: 3200,
    land_sqft: 0, // Condo - no individual land
    lnd_sqfoot: 0,
    year_built: 2020,
    act_yr_blt: 2020,
    property_use: "03",
    propertyUseDesc: "Condominium",
    sale_price: 1150000,
    sale_yr1: 2024,
    sale_date: "2024-01-10",
    unit_number: "2405",
    is_condo: true
  }
];

// Function to get mock autocomplete suggestions
export function getMockAutocompleteSuggestions(query: string) {
  const lowerQuery = query.toLowerCase();

  return mockProperties
    .filter(prop =>
      prop.phy_addr1.toLowerCase().includes(lowerQuery) ||
      prop.phy_city.toLowerCase().includes(lowerQuery) ||
      prop.owner_name.toLowerCase().includes(lowerQuery)
    )
    .map(prop => ({
      // Autocomplete fields
      address: prop.unit_number ? `${prop.phy_addr1} Unit ${prop.unit_number}` : prop.phy_addr1,
      city: prop.phy_city,
      zip_code: prop.phy_zipcd,
      full_address: prop.unit_number
        ? `${prop.phy_addr1} Unit ${prop.unit_number}, ${prop.phy_city} ${prop.phy_zipcd}`
        : `${prop.phy_addr1}, ${prop.phy_city} ${prop.phy_zipcd}`,
      type: "property",

      // Unit information
      unit_number: prop.unit_number,
      is_condo: prop.is_condo,

      // Complete property data for mini cards
      parcel_id: prop.parcel_id,

      // Owner fields (both formats)
      owner_name: prop.owner_name,
      own_name: prop.owner_name,

      // Value fields (all formats for compatibility)
      just_value: prop.just_value,
      jv: prop.jv,
      market_value: prop.market_value,

      // Property type
      property_type: prop.is_condo ? "Condo" : "Property",
      property_use_desc: prop.propertyUseDesc,

      // Address fields
      phy_addr1: prop.phy_addr1,
      phy_addr2: prop.phy_addr2,
      phy_city: prop.phy_city,
      phy_zipcd: prop.phy_zipcd,

      // Additional fields
      tot_lvg_area: prop.tot_lvg_area,
      lnd_sqfoot: prop.lnd_sqfoot,
      act_yr_blt: prop.act_yr_blt,
      sale_price: prop.sale_price,
      sale_yr1: prop.sale_yr1,
      sale_date: prop.sale_date
    }));
}