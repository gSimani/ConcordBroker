import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Building2, FileText, Hash, Calendar, MapPin, Mail, 
  User, Users, AlertTriangle, CheckCircle, Info,
  ExternalLink, Briefcase, Link, Search, AlertCircle, Loader2
} from 'lucide-react';
import { useSunbizData, transformSunbizData } from '@/hooks/useSunbizData';

interface SunbizTabProps {
  propertyData: any;
}

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
  
  // Transform the real data to match component format
  const [sunbizEntity, setSunbizEntity] = useState<any>(null);
  
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
    } else if (!loading && (corporate.length > 0 || fictitious.length > 0)) {
      const transformed = transformSunbizData(corporate, fictitious, events);
      console.log('Transformed Sunbiz data:', transformed);
      setSunbizEntity(transformed);
    }
  }, [corporate, fictitious, events, loading, propSunbizData]);
  
  // Show loading state only if we don't have any data
  if (loading && !sunbizEntity && (!propSunbizData || propSunbizData.length === 0)) {
    return (
      <div className="space-y-8">
        <div className="card-executive animate-elegant">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-gold mr-3" />
            <span className="text-lg text-gray-600">Loading Sunbiz business information...</span>
          </div>
        </div>
      </div>
    );
  }
  
  // Show error state only if we don't have fallback data
  if (error && !sunbizEntity && (!propSunbizData || propSunbizData.length === 0)) {
    return (
      <div className="space-y-8">
        <div className="card-executive animate-elegant border-l-4 border-red-400">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center text-red-700">
              <div className="p-2 rounded-lg mr-3 bg-red-400">
                <AlertTriangle className="w-4 h-4 text-white" />
              </div>
              Error Loading Sunbiz Data
            </h3>
            <p className="text-sm mt-4 text-red-600">{error}</p>
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
  const primaryEntity = liveEntityData?.[0] || corporate?.[0];
  
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

  if (!liveEntityData || liveEntityData.length === 0) {
    return (
      <div className="space-y-8">
        <div className="card-executive animate-elegant border-l-4 border-yellow-400">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center text-yellow-700">
              <div className="p-2 rounded-lg mr-3 bg-yellow-400">
                <AlertTriangle className="w-4 h-4 text-white" />
              </div>
              No Sunbiz Information Found
            </h3>
            <p className="text-sm mt-4 text-yellow-600">
              No corporate filing information found for this property owner
            </p>
          </div>
          <div className="pt-8">
            <Alert className="border-yellow-200 bg-yellow-50 mb-6">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <AlertDescription>
                No Sunbiz corporate filing information found for this property.
                The owner may be an individual or the entity may not be registered in Florida.
              </AlertDescription>
            </Alert>
            
            {/* Search Suggestion */}
            <div className="text-center py-8">
              <div className="flex items-center justify-center mb-4">
                <div className="p-4 bg-gold-light rounded-full">
                  <Search className="w-8 h-8 text-gold" />
                </div>
              </div>
              <h3 className="text-xl elegant-heading text-navy mb-4">Search Sunbiz Manually</h3>
              <p className="text-gray-elegant mb-6">
                You can search for the entity directly on Florida Sunbiz
              </p>
              <a
                href={`https://search.sunbiz.org/Inquiry/CorporationSearch/SearchByName/${encodeURIComponent(ownerName || '')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-6 py-3 bg-gold text-navy rounded hover:bg-gold-dark transition-colors font-semibold"
              >
                Search for "{ownerName || 'Owner'}"
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const principalMatch = checkAddressMatch(primaryEntity?.principal_address || primaryEntity?.prin_addr1, propertyAddress);
  const mailingMatch = checkAddressMatch(primaryEntity?.mailing_address || primaryEntity?.mail_addr1, propertyAddress);
  const isAddressMatch = principalMatch || mailingMatch;
  const isOfficerMatch = !isAddressMatch && primaryEntity?.officers?.some((officer: any) => 
    checkNameMatch(officer.name, ownerName)
  );

  // Determine if we're showing mock data
  const isShowingMockData = !hasSunbizData && !hasRealData;
  
  return (
    <div className="space-y-8">
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
      
      {/* Match Type Indicator */}
      {(isAddressMatch || isOfficerMatch) && (
        <div className="card-executive animate-elegant border-l-4 border-blue-500">
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

          {primaryEntity?.officers && primaryEntity.officers.length > 0 ? (
            <div className="space-y-6">
              {primaryEntity.officers.map((officer: any, index: number) => {
                const nameMatches = checkNameMatch(officer.name, ownerName);
                
                return (
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
                          <User className="w-5 h-5 mr-3 text-gray-600" />
                          <span className="text-lg font-semibold text-navy">
                            {officer.name}
                          </span>
                          {nameMatches && (
                            <Badge className="ml-3 bg-green-100 text-green-800 text-xs font-semibold">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Matches Owner
                            </Badge>
                          )}
                        </div>
                        <span className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                          {officer.title || 'Officer'}
                        </span>
                        {officer.address && (
                          <p className="text-sm text-gray-500 mt-3 pl-8">
                            <MapPin className="w-4 h-4 inline mr-2" />
                            {officer.address}
                          </p>
                        )}
                      </div>
                    </div>
                    {nameMatches && (
                      <Alert className="mt-4 border-green-100 bg-green-50">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <AlertDescription className="text-sm">
                          <strong>✅ MATCH CONFIRMED:</strong> Officer name matches property owner!
                          <br /><br />
                          This confirms a direct ownership connection between the business entity and the property. 
                          This match is valuable for due diligence and ownership verification.
                        </AlertDescription>
                      </Alert>
                    )}
                  </motion.div>
                );
              })}
              
              {!primaryEntity.officers.some((officer: any) => 
                checkNameMatch(officer.name, ownerName)
              ) && (
                <Alert className="border-yellow-100 bg-yellow-50">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <AlertDescription className="text-sm">
                    <strong>🔍 AGENT ALERT:</strong> No officer names match the property owner.
                    <br /><br />
                    <strong>This may indicate:</strong>
                    <ul className="mt-2 ml-4 space-y-1 list-disc">
                      <li><strong>Indirect ownership:</strong> Property owned through management companies or trusts</li>
                      <li><strong>Recent changes:</strong> Business sold, officers changed, or ownership restructured</li>
                      <li><strong>Name variations:</strong> Officer uses different name format (full vs. nickname)</li>
                    </ul>
                    <strong>Next steps:</strong> Continue monitoring for name matches to establish ownership connections.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <Users className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500">No officer/director information available</p>
            </div>
          )}
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
  );
}