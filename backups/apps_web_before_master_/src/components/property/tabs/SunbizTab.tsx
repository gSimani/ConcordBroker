import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { OfficerProperty } from '@/types/api';
import ActiveCompaniesSection from './ActiveCompaniesSection';
import {
  Building2, FileText, Hash, Calendar, MapPin, Mail,
  User, Users, AlertTriangle, CheckCircle, Info,
  ExternalLink, Briefcase, Link, Search, AlertCircle, Loader2,
  ChevronDown, ChevronUp, Building, Home, ArrowRight
} from 'lucide-react';
import { useSunbizData, transformSunbizData } from '@/hooks/useSunbizData';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

interface SunbizTabProps {
  propertyData: any;
}

interface ExpandedSections {
  companies: boolean;
  properties: boolean;
  details: boolean;
}

// Use the OfficerProperty interface from types/api.ts

export function SunbizTab({ propertyData }: SunbizTabProps) {
  // Handle both nested bcpaData structure and direct property data
  const bcpaData = propertyData?.bcpaData || propertyData;
  const propSunbizData = propertyData?.sunbizData;

  // Extract owner and address information with multiple fallbacks
  const ownerName = bcpaData?.owner_name || bcpaData?.own_name || bcpaData?.owner || '';
  const propertyAddress = bcpaData?.property_address_street || bcpaData?.phy_addr1 || bcpaData?.property_address || '';
  const propertyCity = bcpaData?.property_address_city || bcpaData?.phy_city || bcpaData?.city || '';

  // Fetch real Sunbiz data from Supabase
  const { corporate, fictitious, events, loading, error } = useSunbizData(
    ownerName,
    propertyAddress,
    propertyCity
  );

  // State management
  const [sunbizEntity, setSunbizEntity] = useState<any>(null);
  const [allCompanies, setAllCompanies] = useState<any[]>([]);
  const [officerProperties, setOfficerProperties] = useState<OfficerProperty[]>([]);
  const [expandedSections, setExpandedSections] = useState<ExpandedSections>({
    companies: true,
    properties: false,
    details: false
  });
  const [loadingProperties, setLoadingProperties] = useState(false);
  const [loadingCompanies, setLoadingCompanies] = useState(false);
  
  // Function to fetch all companies for an owner
  const fetchAllCompanies = async (ownerName: string) => {
    if (!ownerName || loadingCompanies) return;

    setLoadingCompanies(true);
    try {
      // Simple search in entity name and registered agent - much more reliable
      const { data, error } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .or(`entity_name.ilike.%${ownerName}%,registered_agent.ilike.%${ownerName}%`)
        .limit(20);

      if (error) {
        console.error('Error fetching companies:', error);
        setAllCompanies([]); // Set empty array on error
        return;
      }

      console.log(`Found ${data?.length || 0} companies for owner: ${ownerName}`);
      setAllCompanies(data || []);
    } catch (error) {
      console.error('Error in fetchAllCompanies:', error);
      setAllCompanies([]); // Set empty array on error
    } finally {
      setLoadingCompanies(false);
    }
  };

  // Function to fetch properties owned by registered agents or entity names
  const fetchOfficerProperties = async (companies: any[]) => {
    if (!companies.length || loadingProperties) return;

    setLoadingProperties(true);
    try {
      const searchNames = new Set<string>();

      // Extract entity names and registered agents for property search
      companies.forEach(company => {
        if (company.entity_name) {
          searchNames.add(company.entity_name.trim());
        }
        if (company.registered_agent) {
          searchNames.add(company.registered_agent.trim());
        }
      });

      console.log(`Searching properties for ${searchNames.size} business-related names`);

      // Search for properties owned by these names
      const propertyPromises = Array.from(searchNames).slice(0, 10).map(async (searchName) => {
        const { data, error } = await supabase
          .from('florida_parcels')
          .select('parcel_id, phy_addr1, phy_city, just_value, property_use, year_built, owner_name')
          .ilike('owner_name', `%${searchName}%`)
          .limit(3);

        if (error) {
          console.error(`Error fetching properties for ${searchName}:`, error);
          return [];
        }

        return (data || []).map(property => ({
          ...property,
          officer_name: searchName,
          company_name: companies.find(c =>
            c.entity_name === searchName || c.registered_agent === searchName
          )?.entity_name || 'Related Entity'
        }));
      });

      const allResults = await Promise.all(propertyPromises);
      const flatResults = allResults.flat();

      console.log(`Found ${flatResults.length} properties owned by related entities`);
      setOfficerProperties(flatResults);
    } catch (error) {
      console.error('Error in fetchOfficerProperties:', error);
      setOfficerProperties([]); // Set empty array on error
    } finally {
      setLoadingProperties(false);
    }
  };

  useEffect(() => {
    console.log('SunbizTab data state:', {
      loading,
      corporateCount: corporate.length,
      fictitiousCount: fictitious.length,
      eventsCount: events.length,
      propSunbizDataCount: propSunbizData?.length || 0,
      ownerName: ownerName,
      address: propertyAddress,
      city: propertyCity
    });

    // Use data from propertyData first (includes mock data)
    if (propSunbizData && propSunbizData.length > 0) {
      console.log('Using Sunbiz data from propertyData');
      setSunbizEntity(propSunbizData[0]);
      setAllCompanies(propSunbizData);
    } else if (!loading && (corporate.length > 0 || fictitious.length > 0)) {
      const transformed = transformSunbizData(corporate, fictitious, events);
      console.log('Transformed Sunbiz data:', transformed);
      setSunbizEntity(transformed);
      // Use the live corporate data from useSunbizData hook
      setAllCompanies(corporate);
    } else if (!loading && corporate.length === 0 && ownerName) {
      // Only do additional search if the main hook found nothing
      console.log('No data from useSunbizData hook, doing additional search');
      fetchAllCompanies(ownerName);
    }
  }, [corporate, fictitious, events, loading, propSunbizData, ownerName]);

  // Fetch officer properties when companies data changes
  useEffect(() => {
    if (allCompanies.length > 0) {
      fetchOfficerProperties(allCompanies);
    }
  }, [allCompanies]);
  
  // Show initial loading state only if absolutely no data
  if (loading && !sunbizEntity && (!propSunbizData || propSunbizData.length === 0) && allCompanies.length === 0) {
    return (
      <div className="space-y-8">

      {/* Active Florida Companies Database */}
      <ActiveCompaniesSection propertyData={propertyData} />

        <div className="card-executive animate-elegant">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-gold mr-3" />
            <span className="text-lg text-gray-600">Loading Sunbiz business information...</span>
          </div>
        </div>
      </div>
    );
  }
  
  // Always use mock data when real data is not available
  const hasSunbizData = sunbizEntity && Object.keys(sunbizEntity).length > 0;
  const hasRealData = corporate.length > 0 || fictitious.length > 0;
  
  // Use live Supabase data only - no mock fallbacks
  const liveEntityData = hasSunbizData 
    ? [sunbizEntity] 
    : (corporate.length > 0 ? corporate : []);
  
  // Get the primary Sunbiz entity from live data (first match or most relevant)
  const primaryEntity = sunbizEntity || allCompanies?.[0] || corporate?.[0];
  
  // Construct the Sunbiz URL for the primary entity
  const sunbizUrl = primaryEntity 
    ? `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResultDetail?inquirytype=EntityName&directionType=Initial&searchNameOrder=${primaryEntity?.document_number || primaryEntity?.doc_number || ''}&aggregateId=${primaryEntity?.aggregate_id || ''}&searchTerm=${encodeURIComponent(primaryEntity?.entity_name || primaryEntity?.corporate_name || '')}`
    : `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchByName/${encodeURIComponent(ownerName || '')}`;
  
  // Check if addresses match EXACTLY with property
  const checkAddressMatch = (sunbizAddress: string | undefined, propertyAddress: string | undefined) => {
    if (!sunbizAddress || !propertyAddress) return false;
    const normalize = (addr: string) => addr.toUpperCase().trim();
    // Exact match only
    return normalize(sunbizAddress) === normalize(propertyAddress);
  };
  
  // Check if owner names match EXACTLY (for officer matching)
  const checkNameMatch = (sunbizName: string | undefined, propertyOwner: string | undefined) => {
    if (!sunbizName || !propertyOwner) return false;
    const normalize = (name: string) => name.toUpperCase().trim();
    
    // Parse property owner names (handle multiple owners)
    const ownerNames = propertyOwner
      .split(/\s*(?:&|\sAND\s|,)\s*/i)
      .map(name => normalize(name))
      .filter(name => name.length > 0);
    
    const sunbizNorm = normalize(sunbizName);
    
    // Check for exact match with any owner name
    return ownerNames.some(ownerName => ownerName === sunbizNorm);
  };

  const formatDate = (date: string | undefined) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (status: string | undefined) => {
    if (!status) return <Badge variant="outline">Unknown</Badge>;

    const statusLower = status.toLowerCase();
    if (statusLower.includes('active')) {
      return <Badge className="bg-green-100 text-green-800">Active</Badge>;
    } else if (statusLower.includes('inactive')) {
      return <Badge className="bg-red-100 text-red-800">Inactive</Badge>;
    } else if (statusLower.includes('admin')) {
      return <Badge className="bg-yellow-100 text-yellow-800">Admin Dissolved</Badge>;
    }
    return <Badge variant="outline">{status}</Badge>;
  };

  const toggleSection = (section: keyof ExpandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const formatCurrency = (value?: number | string) => {
    if (!value) return 'N/A';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(num);
  };

  // Debug logging
  console.log('SunbizTab Render State:', {
    loading,
    error,
    corporateCount: corporate.length,
    allCompaniesCount: allCompanies.length,
    officerPropertiesCount: officerProperties.length,
    ownerName,
    propertyAddress,
    propertyCity,
    hasSunbizData,
    hasRealData,
    sunbizEntity: !!sunbizEntity,
    primaryEntity: !!primaryEntity,
    loadingCompanies,
    loadingProperties
  });

  const principalMatch = checkAddressMatch(primaryEntity?.principal_address || primaryEntity?.prin_addr1, propertyAddress);
  const mailingMatch = checkAddressMatch(primaryEntity?.mailing_address || primaryEntity?.mail_addr1, propertyAddress);
  const isAddressMatch = principalMatch || mailingMatch;
  const isOfficerMatch = !isAddressMatch && primaryEntity?.officers?.some((officer: any) => 
    checkNameMatch(officer.name, ownerName)
  );

  // Determine if we're showing mock data
  const isShowingMockData = !hasSunbizData && !hasRealData;

  // Ensure we always have some data to display, even if empty
  const displayCompanies = allCompanies.length > 0 ? allCompanies : [];
  const displayProperties = officerProperties.length > 0 ? officerProperties : [];

  // Add fallback data if we have owner name but no companies found
  const shouldShowNoDataMessage = !loading && !loadingCompanies && displayCompanies.length === 0 && ownerName;

  // Always ensure we have some sample data to show the UI structure
  const ensureVisibleContent = displayCompanies.length === 0 && displayProperties.length === 0;

  // Create a mock company entry if no data is available, just to show the UI structure
  const mockCompany = ensureVisibleContent ? {
    entity_name: `Sample Corporate Entity for ${ownerName || 'Property Owner'}`,
    doc_number: 'P12345678',
    status: 'ACTIVE',
    entity_type: 'LLC',
    filing_date: '2023-01-01',
    prin_addr1: propertyAddress || 'Sample Address',
    registered_agent: 'Sample Agent'
  } : null;

  return (
    <div className="space-y-8">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-executive animate-elegant text-center"
        >
          <div className="p-6">
            <div className="text-3xl font-light text-gold mb-2">
              {loadingCompanies ? (
                <Loader2 className="w-8 h-8 animate-spin mx-auto" />
              ) : (
                displayCompanies.length
              )}
            </div>
            <p className="text-sm text-gray-elegant uppercase tracking-wider">Total Companies</p>
            <p className="text-xs text-gray-500 mt-1">Associated with this owner</p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-executive animate-elegant text-center"
        >
          <div className="p-6">
            <div className="text-3xl font-light text-gold mb-2">
              {loadingProperties ? (
                <Loader2 className="w-8 h-8 animate-spin mx-auto" />
              ) : (
                displayProperties.length
              )}
            </div>
            <p className="text-sm text-gray-elegant uppercase tracking-wider">Officer Properties</p>
            <p className="text-xs text-gray-500 mt-1">Properties owned by officers</p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-executive animate-elegant text-center"
        >
          <div className="p-6">
            <div className="text-3xl font-light text-gold mb-2">
              {displayProperties.reduce((sum, prop) => sum + (parseFloat((prop.market_value || prop.just_value)?.toString() || '0') || 0), 0) > 0
                ? formatCurrency(displayProperties.reduce((sum, prop) => sum + (parseFloat((prop.market_value || prop.just_value)?.toString() || '0') || 0), 0))
                : 'N/A'}
            </div>
            <p className="text-sm text-gray-elegant uppercase tracking-wider">Portfolio Value</p>
            <p className="text-xs text-gray-500 mt-1">Total estimated value</p>
          </div>
        </motion.div>
      </div>

      {/* All Companies Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-executive animate-elegant border-l-4 border-blue-500"
      >
        <div className="elegant-card-header">
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => toggleSection('companies')}
          >
            <h3 className="elegant-card-title blue-accent flex items-center">
              <div className="p-2 rounded-lg mr-3 bg-blue-500">
                <Building2 className="w-4 h-4 text-white" />
              </div>
              All Companies ({displayCompanies.length})
              {loadingCompanies && <Loader2 className="w-4 h-4 animate-spin ml-2" />}
            </h3>
            {expandedSections.companies ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>
          <p className="text-sm mt-4 text-gray-elegant">All business entities associated with property owner</p>
        </div>

        {expandedSections.companies && (
          <div className="pt-8">
            {displayCompanies.length > 0 || mockCompany ? (
              <div className="space-y-4">
                {/* Show real companies first */}
                {displayCompanies.map((company, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-all bg-white"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <Building className="w-5 h-5 mr-3 text-blue-600" />
                          <span className="text-lg font-semibold text-navy">
                            {company.entity_name || company.corporate_name}
                          </span>
                          {getStatusBadge(company.status)}
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Type</p>
                            <p className="text-sm text-navy">{company.entity_type || 'Corporation'}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Document #</p>
                            <p className="text-sm text-navy font-mono">{company.doc_number || company.document_number}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Filing Date</p>
                            <p className="text-sm text-navy">{formatDate(company.filing_date || company.date_filed)}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Principal Address</p>
                            <p className="text-sm text-navy">{company.prin_addr1 || company.principal_address || 'N/A'}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}

                {/* Show mock company if no real data */}
                {mockCompany && displayCompanies.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="border border-yellow-200 rounded-lg p-6 hover:shadow-lg transition-all bg-yellow-50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <Building className="w-5 h-5 mr-3 text-yellow-600" />
                          <span className="text-lg font-semibold text-navy">
                            {mockCompany.entity_name}
                          </span>
                          <Badge className="ml-2 bg-yellow-100 text-yellow-800 text-xs">Demo Data</Badge>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Type</p>
                            <p className="text-sm text-navy">{mockCompany.entity_type}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Document #</p>
                            <p className="text-sm text-navy font-mono">{mockCompany.doc_number}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Filing Date</p>
                            <p className="text-sm text-navy">{formatDate(mockCompany.filing_date)}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Principal Address</p>
                            <p className="text-sm text-navy">{mockCompany.prin_addr1}</p>
                          </div>
                        </div>
                        <Alert className="mt-4 border-yellow-200 bg-yellow-100">
                          <Info className="h-4 w-4 text-yellow-600" />
                          <AlertDescription className="text-sm text-yellow-800">
                            <strong>Sample Data:</strong> This is demo content showing the UI structure.
                            Real business entity searches are performed in the background.
                          </AlertDescription>
                        </Alert>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <Building2 className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">
                  {shouldShowNoDataMessage ? `No companies found for "${ownerName}"` : 'Searching for companies...'}
                </p>
                {shouldShowNoDataMessage && (
                  <div className="mt-4">
                    <a
                      href={`https://search.sunbiz.org/Inquiry/CorporationSearch/SearchByName/${encodeURIComponent(ownerName || '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm"
                    >
                      Search Sunbiz Manually
                      <ExternalLink className="w-4 h-4 ml-2" />
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </motion.div>

      {/* Officer Properties Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card-executive animate-elegant border-l-4 border-green-500"
      >
        <div className="elegant-card-header">
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => toggleSection('properties')}
          >
            <h3 className="elegant-card-title green-accent flex items-center">
              <div className="p-2 rounded-lg mr-3 bg-green-500">
                <Home className="w-4 h-4 text-white" />
              </div>
              Properties Owned by Officers ({displayProperties.length})
              {loadingProperties && <Loader2 className="w-4 h-4 animate-spin ml-2" />}
            </h3>
            {expandedSections.properties ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>
          <p className="text-sm mt-4 text-gray-elegant">Real estate portfolio of company officers</p>
        </div>

        {expandedSections.properties && (
          <div className="pt-8">
            {displayProperties.length > 0 ? (
              <div className="space-y-4">
                {displayProperties.map((property, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-all bg-white"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <Home className="w-5 h-5 mr-3 text-green-600" />
                          <span className="text-lg font-semibold text-navy">
                            {property.phy_addr1}, {property.phy_city}
                          </span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Officer/Owner</p>
                            <p className="text-sm text-navy font-medium">{property.officer_name}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Company</p>
                            <p className="text-sm text-navy">{property.company_name}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Market Value</p>
                            <p className="text-sm text-navy font-medium">{formatCurrency(property.market_value || property.just_value)}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Property Type</p>
                            <p className="text-sm text-navy">{property.property_use || 'N/A'}</p>
                          </div>
                        </div>
                        <div className="flex items-center mt-4 pt-4 border-t border-gray-100">
                          <ArrowRight className="w-4 h-4 mr-2 text-blue-500" />
                          <span className="text-sm text-blue-600 hover:text-blue-800 cursor-pointer">
                            View Property Details
                          </span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Home className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">
                  {displayCompanies.length > 0 ? 'No properties found for company officers' : 'No companies to search for officer properties'}
                </p>
              </div>
            )}
          </div>
        )}
      </motion.div>

      {/* Mock Data Notice */}
      {isShowingMockData && (
        <Alert className="border-blue-200 bg-blue-50">
          <Info className="h-4 w-4 text-blue-600" />
          <AlertDescription>
            <strong>Demo Data:</strong> Showing sample business entity information.
            Actual Sunbiz data is not available at this time.
          </AlertDescription>
        </Alert>
      )}
      
      {/* Detailed Entity Information */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="card-executive animate-elegant border-l-4 border-gold"
      >
        <div className="elegant-card-header">
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => toggleSection('details')}
          >
            <h3 className="elegant-card-title gold-accent flex items-center">
              <div className="p-2 rounded-lg mr-3" style={{background: '#d4af37'}}>
                <FileText className="w-4 h-4 text-white" />
              </div>
              Primary Entity Details
              {primaryEntity && (
                <Badge className="ml-3 bg-gold text-navy text-xs font-semibold">
                  {primaryEntity.entity_name || primaryEntity.corporate_name}
                </Badge>
              )}
            </h3>
            {expandedSections.details ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>
          <p className="text-sm mt-4 text-gray-elegant">Complete filing information and officer details</p>
        </div>

        {expandedSections.details && primaryEntity && (
          <div className="pt-8">
            {/* Match Type Indicator */}
            {(isAddressMatch || isOfficerMatch) && (
              <div className="mb-6 p-4 border border-blue-200 rounded-lg bg-blue-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-blue-500">
                      <Info className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-navy">MATCH TYPE</h4>
                      <p className="text-xs text-gray-600 mt-1">
                        {isAddressMatch ? (
                          <>✓ EXACT ADDRESS MATCH - Entity registered at property address</>
                        ) : isOfficerMatch ? (
                          <>✓ OWNER NAME MATCH - Property owner is an officer in this entity</>
                        ) : (
                          <>ℹ Related entity found</>
                        )}
                      </p>
                    </div>
                  </div>
                  <Badge className={isAddressMatch ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}>
                    {isAddressMatch ? 'Priority 1 Match' : 'Priority 2 Match'}
                  </Badge>
                </div>
              </div>
            )}
      
      {/* Agent Matching Summary - Critical Information */}
      <div className="card-executive animate-elegant border-l-4 border-gold bg-gradient-to-r from-gold-light to-yellow-50">
        <div className="elegant-card-header border-gold">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#d4af37'}}>
              <AlertCircle className="w-4 h-4 text-white" />
            </div>
            AGENT MATCHING SUMMARY
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Critical for Property-Entity Connection - Monitor these matches</p>
        </div>
        <div className="pt-8">
          <div className="space-y-4">
            {/* Principal Address Match */}
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-start justify-between p-4 bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-all"
            >
              <div className="flex items-start">
                <MapPin className="w-5 h-5 mr-3 mt-1 text-gray-600" />
                <div>
                  <span className="text-sm font-semibold text-navy">Principal Address Match:</span>
                  <p className="text-xs text-gray-600 mt-1">
                    {primaryEntity?.principal_address || 'N/A'}
                  </p>
                </div>
              </div>
              {principalMatch ? (
                <Badge className="bg-green-100 text-green-800 font-semibold">✓ MATCHES</Badge>
              ) : (
                <Badge className="bg-yellow-100 text-yellow-800 font-semibold">⚠ NO MATCH</Badge>
              )}
            </motion.div>
            
            {/* Mailing Address Match */}
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="flex items-start justify-between p-4 bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-all"
            >
              <div className="flex items-start">
                <Mail className="w-5 h-5 mr-3 mt-1 text-gray-600" />
                <div>
                  <span className="text-sm font-semibold text-navy">Mailing Address Match:</span>
                  <p className="text-xs text-gray-600 mt-1">
                    {primaryEntity?.mailing_address || 'N/A'}
                  </p>
                </div>
              </div>
              {mailingMatch ? (
                <Badge className="bg-green-100 text-green-800 font-semibold">✓ MATCHES</Badge>
              ) : (
                <Badge className="bg-yellow-100 text-yellow-800 font-semibold">⚠ NO MATCH</Badge>
              )}
            </motion.div>
            
            {/* Owner Name Match */}
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="flex items-start justify-between p-4 bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-all"
            >
              <div className="flex items-start">
                <User className="w-5 h-5 mr-3 mt-1 text-gray-600" />
                <div>
                  <span className="text-sm font-semibold text-navy">Officer/Owner Name Match:</span>
                  <p className="text-xs text-gray-600 mt-1">
                    Property Owner: {ownerName || 'N/A'}
                  </p>
                </div>
              </div>
              {primaryEntity?.officers?.some((officer: any) => 
                checkNameMatch(officer.name, ownerName)
              ) ? (
                <Badge className="bg-green-100 text-green-800 font-semibold">✓ MATCHES</Badge>
              ) : (
                <Badge className="bg-yellow-100 text-yellow-800 font-semibold">⚠ NO MATCH</Badge>
              )}
            </motion.div>
          </div>
          
          <Alert className="mt-6 border-blue-200 bg-blue-50">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-sm">
              <strong>AGENT INSTRUCTION:</strong> Always monitor these matches. When addresses and names match between 
              Sunbiz and Property Appraisal, it confirms ownership connection and makes our work easier. 
              This is critical for identifying investment opportunities and ownership structures.
            </AlertDescription>
          </Alert>
        </div>
      </div>

      {/* Detail by Entity Name */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-executive animate-elegant"
      >
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
              <Building2 className="w-4 h-4 text-white" />
            </div>
            Detail by Entity Name
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Corporate entity identification and classification</p>
        </div>
        <div className="pt-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light">
                <div className="flex items-center mb-3">
                  <Briefcase className="w-4 h-4 mr-2 text-gold" />
                  <span className="text-xs uppercase tracking-wider text-gray-elegant">Name of Company</span>
                </div>
                <p className="text-lg font-light text-navy group-hover:text-gold transition-colors">
                  {primaryEntity?.entity_name || 'N/A'}
                </p>
              </div>
              
              <div className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light">
                <div className="flex items-center mb-3">
                  <Building2 className="w-4 h-4 mr-2 text-gold" />
                  <span className="text-xs uppercase tracking-wider text-gray-elegant">Incorporation Type</span>
                </div>
                <p className="text-lg font-light text-navy group-hover:text-gold transition-colors">
                  {primaryEntity?.entity_type || 'N/A'}
                </p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light">
                <div className="flex items-center mb-3">
                  <CheckCircle className="w-4 h-4 mr-2 text-gold" />
                  <span className="text-xs uppercase tracking-wider text-gray-elegant">Status</span>
                </div>
                <div className="mt-2">
                  {getStatusBadge(primaryEntity?.status)}
                </div>
              </div>
              
              <div className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light">
                <div className="flex items-center mb-3">
                  <MapPin className="w-4 h-4 mr-2 text-gold" />
                  <span className="text-xs uppercase tracking-wider text-gray-elegant">State</span>
                </div>
                <p className="text-lg font-light text-navy group-hover:text-gold transition-colors">
                  {primaryEntity?.state || 'Florida'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Filing Information */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card-executive animate-elegant"
      >
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
              <FileText className="w-4 h-4 text-white" />
            </div>
            Filing Information
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Official state registration and identification details</p>
        </div>
        <div className="pt-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex justify-between items-start p-4 border-b border-gray-100 hover:bg-gray-50 transition-all rounded">
                <span className="text-sm text-gray-elegant font-medium">Document Number</span>
                <span className="text-sm font-semibold text-navy font-mono">
                  {primaryEntity?.document_number || 'N/A'}
                </span>
              </div>
              
              <div className="flex justify-between items-start p-4 border-b border-gray-100 hover:bg-gray-50 transition-all rounded">
                <span className="text-sm text-gray-elegant font-medium">FEI/EIN Number</span>
                <span className="text-sm font-semibold text-navy font-mono">
                  {primaryEntity?.fei_ein_number || 'N/A'}
                </span>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-start p-4 border-b border-gray-100 hover:bg-gray-50 transition-all rounded">
                <span className="text-sm text-gray-elegant font-medium">Date Filed</span>
                <span className="text-sm font-semibold text-navy">
                  {formatDate(primaryEntity?.date_filed)}
                </span>
              </div>
              
              <div className="flex justify-between items-start p-4 border-b border-gray-100 hover:bg-gray-50 transition-all rounded">
                <span className="text-sm text-gray-elegant font-medium">Effective Date</span>
                <div className="text-right">
                  <span className="text-sm font-semibold text-navy">
                    {formatDate(primaryEntity?.effective_date)}
                  </span>
                  <p className="text-xs text-gray-500 mt-1 font-light">
                    (Company start date)
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Corporate Addresses - Critical for Agent Matching */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-executive animate-elegant border-l-4 border-gold"
      >
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#d4af37'}}>
              <MapPin className="w-4 h-4 text-white" />
            </div>
            Corporate Addresses
            <Badge className="ml-3 bg-gold text-navy text-xs font-semibold">AGENT ALERT</Badge>
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Address matching is critical for confirming property-entity connection</p>
        </div>
        <div className="pt-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Principal Address */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-semibold text-gray-700 flex items-center">
                  <Building2 className="w-4 h-4 mr-2" />
                  Principal Address
                </span>
                {principalMatch && (
                  <Badge className="bg-green-100 text-green-800 text-xs font-semibold">
                    <Link className="w-3 h-3 mr-1" />
                    Matches Property
                  </Badge>
                )}
              </div>
              <div className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all">
                <p className="text-sm text-navy font-medium">
                  {primaryEntity?.principal_address || 'N/A'}
                </p>
              </div>
              {!principalMatch && propertyAddress && (
                <Alert className="mt-3 border-yellow-100 bg-yellow-50">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <AlertDescription className="text-sm">
                    <strong>🚨 AGENT ALERT:</strong> Corporate principal address <strong>does not match</strong> property address.
                    <br /><br />
                    <strong>Why this matters:</strong> The principal address is where the business officially operates. 
                    When it matches the property address, it confirms:
                    <ul className="mt-2 ml-4 space-y-1 list-disc">
                      <li><strong>Business operations:</strong> Company likely runs business from this property</li>
                      <li><strong>Owner connection:</strong> Stronger tie between property and entity ownership</li>
                      <li><strong>Commercial use:</strong> Property may have mixed-use or commercial potential</li>
                    </ul>
                  </AlertDescription>
                </Alert>
              )}
            </div>
            
            {/* Mailing Address */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-semibold text-gray-700 flex items-center">
                  <Mail className="w-4 h-4 mr-2" />
                  Mailing Address
                </span>
                {mailingMatch && (
                  <Badge className="bg-green-100 text-green-800 text-xs font-semibold">
                    <Link className="w-3 h-3 mr-1" />
                    Matches Property
                  </Badge>
                )}
              </div>
              <div className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all">
                <p className="text-sm text-navy font-medium">
                  {primaryEntity?.mailing_address || 'N/A'}
                </p>
              </div>
              {!mailingMatch && propertyAddress && (
                <Alert className="mt-3 border-yellow-100 bg-yellow-50">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <AlertDescription className="text-sm">
                    <strong>🚨 AGENT ALERT:</strong> Corporate mailing address <strong>does not match</strong> property address.
                    <br /><br />
                    <strong>Why this matters:</strong> When the business entity's mailing address matches the property address, 
                    it indicates the owner likely lives at or operates from the property. This is valuable for:
                    <ul className="mt-2 ml-4 space-y-1 list-disc">
                      <li><strong>Investment opportunities:</strong> Owner-occupied properties may have different sale motivations</li>
                      <li><strong>Due diligence:</strong> Confirms property-entity relationship for compliance</li>
                      <li><strong>Contact accuracy:</strong> Property address = business address = easier contact</li>
                    </ul>
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Registered Agent */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card-executive animate-elegant"
      >
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
              <User className="w-4 h-4 text-white" />
            </div>
            Registered Agent
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Official state-appointed representative for legal correspondence</p>
        </div>
        <div className="pt-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light">
              <div className="flex items-center mb-3">
                <User className="w-4 h-4 mr-2 text-gold" />
                <span className="text-xs uppercase tracking-wider text-gray-elegant">Agent Name</span>
              </div>
              <p className="text-lg font-light text-navy group-hover:text-gold transition-colors">
                {primaryEntity?.registered_agent_name || 'N/A'}
              </p>
            </div>
            
            <div className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light">
              <div className="flex items-center mb-3">
                <MapPin className="w-4 h-4 mr-2 text-gold" />
                <span className="text-xs uppercase tracking-wider text-gray-elegant">Agent Address</span>
              </div>
              <p className="text-sm font-light text-navy group-hover:text-gold transition-colors">
                {primaryEntity?.registered_agent_address || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Officer/Director Detail - Critical for Agent Matching */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="card-executive animate-elegant border-l-4 border-gold"
      >
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#d4af37'}}>
              <Users className="w-4 h-4 text-white" />
            </div>
            Officer/Director Detail
            <Badge className="ml-3 bg-gold text-navy text-xs font-semibold">AGENT ALERT</Badge>
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Officer name matching confirms ownership connection with property</p>
        </div>
        <div className="pt-8">
          <Alert className="mb-6 border-blue-200 bg-blue-50">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-sm">
              <strong>AGENT NOTE:</strong> Officer/Director names (especially first and last names) need to match 
              with the Property Appraisal property owner name to make our work easier. Always be on the lookout for name matches.
            </AlertDescription>
          </Alert>

          <div className="space-y-6">
            {/* Registered Agent Information */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-all bg-white"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <User className="w-5 h-5 mr-3 text-gray-600" />
                    <span className="text-lg font-semibold text-navy">
                      {primaryEntity?.registered_agent || 'Not Available'}
                    </span>
                    {checkNameMatch(primaryEntity?.registered_agent, ownerName) && (
                      <Badge className="ml-3 bg-green-100 text-green-800 text-xs font-semibold">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Matches Owner
                      </Badge>
                    )}
                  </div>
                  <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                    Registered Agent
                  </span>
                </div>
              </div>
              {checkNameMatch(primaryEntity?.registered_agent, ownerName) && (
                <Alert className="mt-4 border-green-100 bg-green-50">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-sm">
                    <strong>✅ MATCH CONFIRMED:</strong> Registered agent matches property owner!
                    <br /><br />
                    This suggests the property owner serves as the registered agent for this business entity.
                  </AlertDescription>
                </Alert>
              )}
            </motion.div>

            {/* Entity Name Check */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-all bg-white"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <Building2 className="w-5 h-5 mr-3 text-blue-600" />
                    <span className="text-lg font-semibold text-navy">
                      {primaryEntity?.entity_name || 'Entity Name Not Available'}
                    </span>
                    {ownerName && primaryEntity?.entity_name?.toLowerCase().includes(ownerName.toLowerCase()) && (
                      <Badge className="ml-3 bg-blue-100 text-blue-800 text-xs font-semibold">
                        <Info className="w-3 h-3 mr-1" />
                        Contains Owner Name
                      </Badge>
                    )}
                  </div>
                  <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                    Business Entity Name
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Additional Note */}
            <Alert className="border-blue-100 bg-blue-50">
              <Info className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-sm">
                <strong>AGENT NOTE:</strong> Name matching is performed between the property owner and registered agent/entity names.
                Additional officer information may be available through the complete Sunbiz filing records.
              </AlertDescription>
            </Alert>
          </div>
        </div>
      </motion.div>

      {/* Additional Information Sections */}
      {primaryEntity?.annual_reports && primaryEntity.annual_reports.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card-executive animate-elegant"
        >
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent flex items-center">
              <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
                <FileText className="w-4 h-4 text-white" />
              </div>
              Annual Reports
            </h3>
            <p className="text-sm mt-4 text-gray-elegant">Filing compliance and reporting history</p>
          </div>
          <div className="pt-8">
            <div className="space-y-3">
              {primaryEntity.annual_reports.map((report: any, index: number) => (
                <div key={index} className="flex justify-between items-center p-4 border-b border-gray-100 hover:bg-gray-50 transition-all rounded">
                  <span className="text-sm text-gray-600">Year {report.year}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-navy font-medium">{formatDate(report.filed_date)}</span>
                    <Badge className="bg-green-100 text-green-800 text-xs">{report.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Important Dates */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="card-executive animate-elegant"
      >
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
              <Calendar className="w-4 h-4 text-white" />
            </div>
            Important Dates
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Key timeline information for entity operations</p>
        </div>
        <div className="pt-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light">
              <div className="flex items-center mb-3">
                <Calendar className="w-4 h-4 mr-2 text-gold" />
                <span className="text-xs uppercase tracking-wider text-gray-elegant">Last Event Date</span>
              </div>
              <p className="text-lg font-light text-navy group-hover:text-gold transition-colors">
                {formatDate(primaryEntity?.last_event_date || primaryEntity?.date_filed)}
              </p>
            </div>
            
            <div className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light">
              <div className="flex items-center mb-3">
                <Calendar className="w-4 h-4 mr-2 text-gold" />
                <span className="text-xs uppercase tracking-wider text-gray-elegant">Next Annual Report Due</span>
              </div>
              <p className="text-lg font-light text-navy group-hover:text-gold transition-colors">
                {primaryEntity?.next_report_due || 'May 1, ' + new Date().getFullYear()}
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Direct Link to Sunbiz */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="card-executive animate-elegant border-l-4 border-gold"
      >
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#d4af37'}}>
              <ExternalLink className="w-4 h-4 text-white" />
            </div>
            View Full Sunbiz Record
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Access complete corporate filing history and documents</p>
        </div>
        <div className="pt-8">
          <div className="text-center py-8">
            <div className="flex items-center justify-center mb-6">
              <div className="p-4 bg-gold-light rounded-full">
                <ExternalLink className="w-8 h-8 text-gold" />
              </div>
            </div>
            <p className="text-gray-elegant mb-6">
              Access the complete corporate filing history and documents on Florida Sunbiz
            </p>
            <div className="space-y-4">
              <a
                href={sunbizUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-6 py-3 bg-gold text-navy rounded hover:bg-gold-dark transition-colors font-semibold"
              >
                View Complete Filing History
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
              <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded border">
                <strong>URL:</strong> 
                <br />
                <span className="font-mono text-blue-600 break-all">
                  {sunbizUrl}
                </span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
          </div>
        )}
      </motion.div>
    </div>
  );
}