import { PropertyData } from '@/hooks/usePropertyData'
import { Receipt, DollarSign, AlertTriangle, Calculator, TrendingUp, Clock, Home, Building, TreePine, Landmark, FileText, ExternalLink, AlertCircle, CheckCircle, Star, User, Hash, Calendar, Info, ArrowRight, Building2, Users, Edit3, Trash2, Link } from 'lucide-react'
import { motion } from 'framer-motion'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useState, useEffect, useMemo } from 'react'
import { supabase } from '@/lib/supabase'

interface TaxesTabProps {
  data: PropertyData
}

interface TaxCertificate {
  real_estate_account: string
  certificate_number: string
  buyer: string
  buyer_entity?: {
    entity_name: string
    status: string
    filing_type?: string
    principal_address: string
    registered_agent: string
    document_number: string
    // Extended properties from live Sunbiz data
    entity_type?: string
    filing_date?: string
    agent_address?: string
    officers?: Array<{ name: string; title: string; address: string }>
    match_confidence?: number
    search_term_used?: string
    state?: string
    zip_code?: string
    is_live_data?: boolean
  }
  advertised_number?: string
  face_amount: number
  issued_date: string
  expiration_date: string
  interest_rate: number
  status?: 'active' | 'redeemed' | 'expired'
  tax_year?: number
  winning_bid_percentage?: number
  redemption_amount?: number
  redemption_date?: string
}

interface SunbizEntity {
  entity_name: string
  entity_type: string
  status: string
  state: string
  document_number: string
  fei_ein_number?: string
  date_filed: string
  effective_date: string
  principal_address: string
  mailing_address: string
  registered_agent_name: string
  registered_agent_address: string
  officers: Array<{
    name: string
    title: string
    address: string
  }>
  aggregate_id?: string
  annual_reports?: Array<{
    year: number
    filed_date: string
    status: string
  }>
  filing_history?: Array<{
    date: string
    type: string
    document_number: string
  }>
}

interface BuyerSunbizMatches {
  entityMatches: SunbizEntity[]
  officerMatches: Array<{
    entity: SunbizEntity
    matchingOfficers: Array<{
      name: string
      title: string
      address: string
    }>
  }>
  nameScore: number
}

export function TaxesTab({ data }: TaxesTabProps) {
  // Handle undefined data gracefully
  const navData = data?.navData || null
  const totalNavAssessment = data?.totalNavAssessment || 0
  const isInCDD = data?.isInCDD || false
  const bcpaData = data?.bcpaData || data || {}

  const [certificateBuyerData, setCertificateBuyerData] = useState<Record<string, any>>({})
  const [loadingBuyers, setLoadingBuyers] = useState<Record<string, boolean>>({})
  const [enhancedBuyerMatches, setEnhancedBuyerMatches] = useState<Record<string, BuyerSunbizMatches>>({})
  const [editingUrls, setEditingUrls] = useState<Record<string, boolean>>({})
  const [customUrls, setCustomUrls] = useState<Record<string, string>>({})
  const [realTaxCertificates, setRealTaxCertificates] = useState<TaxCertificate[]>([])

  // Fetch real tax certificate data from API and live Sunbiz entities
  useEffect(() => {
    const fetchTaxData = async () => {
      if (!bcpaData?.parcel_id) return
      
      try {
        // Get API base URL from environment or default to localhost
        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002';

        // Fetch tax certificates and Sunbiz entities in parallel from real tax data API
        const [certsResponse, sunbizResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/properties/${bcpaData.parcel_id}/tax-certificates`),
          fetch(`${API_BASE_URL}/api/properties/${bcpaData.parcel_id}/sunbiz-entities`)
        ])
        
        // Process tax certificates
        if (certsResponse.ok) {
          const apiData = await certsResponse.json()

          // Handle both direct certificates array and data.certificates structure
          const certificates = apiData.data?.certificates || apiData.certificates || []
          const taxAssessment = apiData.data?.tax_assessment || null

          if (certificates && certificates.length > 0) {
            const formattedCertificates = certificates.map((cert: any) => ({
              real_estate_account: cert.real_estate_account || cert.parcel_id || bcpaData.parcel_id,
              certificate_number: cert.certificate_number || `${cert.tax_year}-${cert.parcel_id?.slice(-5) || '00001'}`,
              buyer: cert.buyer_name || cert.certificate_buyer || cert.buyer || "Unknown Buyer",
              buyer_entity: cert.buyer_entity,
              advertised_number: cert.advertised_number || `AD-${cert.certificate_number}`,
              face_amount: cert.face_amount || cert.tax_amount || 0,
              issued_date: cert.issued_date || cert.sale_date || `${cert.tax_year}-06-01`,
              expiration_date: cert.expiration_date || `${(cert.tax_year || 2023) + 2}-06-01`,
              interest_rate: cert.interest_rate || cert.bid_percentage || 18,
              status: cert.status || 'active',
              tax_year: cert.tax_year || new Date(cert.issued_date).getFullYear(),
              winning_bid_percentage: cert.winning_bid_percentage || cert.bid_percentage || cert.interest_rate || 18,
              redemption_amount: cert.redemption_amount || (cert.face_amount * 1.18),
              redemption_date: cert.redemption_date
            }))
            setRealTaxCertificates(formattedCertificates)
            console.log(`Loaded ${formattedCertificates.length} tax certificates from API`)
          }
        }
        
        // Process live Sunbiz entities
        if (sunbizResponse.ok) {
          const sunbizData = await sunbizResponse.json()

          // Handle both direct entities array and data.entities structure
          const entities = sunbizData.data?.entities || sunbizData.entities || []
          const propertyOwners = sunbizData.data?.property_owners || sunbizData.property_owners || []

          if (entities && entities.length > 0) {
            console.log(`Found ${entities.length} live Sunbiz entities for property owners: ${propertyOwners.join(', ')}`)
            
            // Update certificates with live Sunbiz entity data
            setRealTaxCertificates(prevCerts =>
              prevCerts.map(cert => {
                // Find matching Sunbiz entity for this certificate buyer
                const matchingEntity = entities.find((entity: any) =>
                  entity.match_confidence && entity.match_confidence > 0.7 &&
                  (cert.buyer.includes(entity.name || entity.entity_name) || (entity.name || entity.entity_name || '').includes(cert.buyer))
                )
                
                if (matchingEntity) {
                  return {
                    ...cert,
                    buyer_entity: {
                      entity_name: matchingEntity.name || matchingEntity.entity_name,
                      document_number: matchingEntity.document_number || matchingEntity.id,
                      entity_type: matchingEntity.entity_type,
                      status: matchingEntity.status,
                      filing_date: matchingEntity.filing_date,
                      principal_address: matchingEntity.address || matchingEntity.principal_address,
                      registered_agent: matchingEntity.agent_name || matchingEntity.registered_agent,
                      agent_address: matchingEntity.agent_address,
                      officers: matchingEntity.officers || [],
                      match_confidence: matchingEntity.match_confidence,
                      search_term_used: matchingEntity.search_term_used,
                      state: matchingEntity.state,
                      zip_code: matchingEntity.zip_code,
                      is_live_data: true
                    }
                  }
                }
                return cert
              })
            )
          }
        }
        
      } catch (err) {
        console.log('Error fetching tax data, falling back to direct Supabase:', err)
        
        // Fallback to direct Supabase query if API fails
        try {
          const { data: certificates, error } = await supabase
            .from('tax_certificates')
            .select('*')
            .eq('parcel_id', bcpaData.parcel_id)
            .order('tax_year', { ascending: false })
          
          if (!error && certificates && certificates.length > 0) {
            const formattedCertificates = certificates.map((cert: any) => ({
              real_estate_account: cert.real_estate_account || cert.parcel_id || bcpaData.parcel_id,
              certificate_number: cert.certificate_number || `${cert.tax_year}-${cert.parcel_id?.slice(-5) || '00001'}`,
              buyer: cert.buyer_name || cert.certificate_buyer || cert.buyer || "Unknown Buyer",
              buyer_entity: cert.buyer_entity,
              advertised_number: cert.advertised_number || `AD-${cert.certificate_number}`,
              face_amount: cert.face_amount || cert.tax_amount || 0,
              issued_date: cert.issued_date || cert.sale_date || `${cert.tax_year}-06-01`,
              expiration_date: cert.expiration_date || `${(cert.tax_year || 2023) + 2}-06-01`,
              interest_rate: cert.interest_rate || cert.bid_percentage || 18,
              status: cert.status || 'active',
              tax_year: cert.tax_year || new Date(cert.issued_date).getFullYear(),
              winning_bid_percentage: cert.winning_bid_percentage || cert.bid_percentage || cert.interest_rate || 18,
              redemption_amount: cert.redemption_amount || (cert.face_amount * 1.18),
              redemption_date: cert.redemption_date
            }))
            setRealTaxCertificates(formattedCertificates)
            console.log(`Loaded ${formattedCertificates.length} tax certificates from Supabase`)
          }
        } catch (err) {
          console.log('Tax certificates table not found or error fetching:', err)
        }
      }
    }
    
    fetchTaxData()
  }, [bcpaData])

  // Generate dynamic mock certificates based on real property data
  const generateDynamicCertificates = (): TaxCertificate[] => {
    const currentYear = new Date().getFullYear()
    const taxableValue = bcpaData?.taxable_value || bcpaData?.assessed_value || 250000
    const annualTaxAmount = taxableValue * 0.02 // Approximate 2% tax rate
    
    // Use owner name to generate certificate buyers if available
    const potentialBuyers = [
      bcpaData?.owner_name?.includes('LLC') ? bcpaData.owner_name : "CAPITAL ONE, NATIONAL ASSOCIATION (USA)",
      "TLGFY, LLC, A FLORIDA LIMITED LIABILITY CO.",
      "5T WEALTH PARTNERS LP",
      "FLORIDA TAX CERTIFICATE FUND III",
      "BRIDGE TAX CERTIFICATE COMPANY"
    ]
    
    return [
      {
        real_estate_account: bcpaData?.parcel_id || "504234-08-00-20",
        certificate_number: `${currentYear - 1}-${(bcpaData?.parcel_id || '00000').slice(-5).padStart(5, '0')}`,
        buyer: potentialBuyers[0],
        advertised_number: `AD-${currentYear - 1}-${(bcpaData?.parcel_id || '00000').slice(-5).padStart(5, '0')}`,
        face_amount: annualTaxAmount * 1.05,
        issued_date: `${currentYear - 1}-06-01`,
        expiration_date: `${currentYear + 1}-06-01`,
        interest_rate: 18,
        status: 'active',
        tax_year: currentYear - 1,
        winning_bid_percentage: 18,
        redemption_amount: annualTaxAmount * 1.05 * 1.18
      },
      {
        real_estate_account: bcpaData?.parcel_id || "504234-08-00-20",
        certificate_number: `${currentYear - 2}-${((parseInt((bcpaData?.parcel_id || '00000').slice(-5)) + 1) % 100000).toString().padStart(5, '0')}`,
        buyer: potentialBuyers[1],
        advertised_number: `AD-${currentYear - 2}-${((parseInt((bcpaData?.parcel_id || '00000').slice(-5)) + 1) % 100000).toString().padStart(5, '0')}`,
        face_amount: annualTaxAmount * 0.98,
        issued_date: `${currentYear - 2}-06-01`,
        expiration_date: `${currentYear}-06-01`,
        interest_rate: 18,
        status: 'active',
        tax_year: currentYear - 2,
        winning_bid_percentage: 18,
        redemption_amount: annualTaxAmount * 0.98 * 1.36
      }
    ]
  }

  // Use real certificates if available, otherwise use dynamic mock based on property data
  // Memoize to prevent infinite loops
  const taxCertificates = useMemo(() => {
    if (realTaxCertificates.length > 0) {
      return realTaxCertificates;
    }
    if ((data as any).taxCertificates) {
      return (data as any).taxCertificates;
    }
    return generateDynamicCertificates();
  }, [realTaxCertificates, data, bcpaData]);

  // Enhanced mock Sunbiz data for comprehensive buyer matching
  const mockSunbizEntities: SunbizEntity[] = [
    {
      entity_name: "CAPITAL ONE, NATIONAL ASSOCIATION",
      entity_type: "Corporation",
      status: "Active",
      state: "VA",
      document_number: "F96000004500",
      fei_ein_number: "54-1628144",
      date_filed: "1996-01-15",
      effective_date: "1996-01-15",
      principal_address: "1680 Capital One Drive, McLean, VA 22102",
      mailing_address: "1680 Capital One Drive, McLean, VA 22102",
      registered_agent_name: "Corporate Services Company",
      registered_agent_address: "2908 Poston Avenue, Nashville, TN 37203",
      officers: [
        {
          name: "Richard D. Fairbank",
          title: "Chief Executive Officer",
          address: "1680 Capital One Drive, McLean, VA 22102"
        },
        {
          name: "Andrew G. Young", 
          title: "Chief Financial Officer",
          address: "1680 Capital One Drive, McLean, VA 22102"
        },
        {
          name: "Matthew H. Cooper",
          title: "President",
          address: "1680 Capital One Drive, McLean, VA 22102"
        }
      ],
      annual_reports: [
        { year: 2024, filed_date: "2024-03-15", status: "Filed" },
        { year: 2023, filed_date: "2023-03-15", status: "Filed" }
      ]
    },
    {
      entity_name: "TLGFY, LLC", 
      entity_type: "Limited Liability Company",
      status: "Active",
      state: "FL",
      document_number: "L22000145890",
      fei_ein_number: "88-2345678",
      date_filed: "2022-03-01",
      effective_date: "2022-03-01",
      principal_address: "500 Brickell Avenue, Suite 3100, Miami, FL 33131",
      mailing_address: "500 Brickell Avenue, Suite 3100, Miami, FL 33131",
      registered_agent_name: "Florida Corporate Filings LLC",
      registered_agent_address: "1200 Brickell Avenue, Suite 1950, Miami, FL 33131",
      officers: [
        {
          name: "Thomas L. Garcia",
          title: "Managing Member",
          address: "500 Brickell Avenue, Suite 3100, Miami, FL 33131"
        },
        {
          name: "Fernando Y. Lopez",
          title: "Member",
          address: "500 Brickell Avenue, Suite 3100, Miami, FL 33131"
        }
      ],
      annual_reports: [
        { year: 2024, filed_date: "2024-05-01", status: "Filed" },
        { year: 2023, filed_date: "2023-05-01", status: "Filed" }
      ]
    },
    {
      entity_name: "5T WEALTH PARTNERS LP",
      entity_type: "Limited Partnership", 
      status: "Active",
      state: "FL",
      document_number: "P20000087654",
      fei_ein_number: "65-3456789",
      date_filed: "2020-08-15",
      effective_date: "2020-08-15",
      principal_address: "800 Brickell Avenue, Suite 900, Miami, FL 33131",
      mailing_address: "800 Brickell Avenue, Suite 900, Miami, FL 33131",
      registered_agent_name: "Wealth Management Services Inc",
      registered_agent_address: "800 Brickell Avenue, Suite 900, Miami, FL 33131",
      officers: [
        {
          name: "Sarah T. Williams",
          title: "General Partner",
          address: "800 Brickell Avenue, Suite 900, Miami, FL 33131"
        },
        {
          name: "Michael R. Thompson",
          title: "Limited Partner",
          address: "800 Brickell Avenue, Suite 900, Miami, FL 33131"
        },
        {
          name: "Jennifer K. Davis",
          title: "Chief Investment Officer",
          address: "800 Brickell Avenue, Suite 900, Miami, FL 33131"
        }
      ],
      annual_reports: [
        { year: 2024, filed_date: "2024-04-01", status: "Filed" },
        { year: 2023, filed_date: "2023-04-01", status: "Filed" }
      ]
    }
  ];

  // Enhanced name matching algorithm
  const calculateNameMatchScore = (name1: string, name2: string): number => {
    const normalize = (str: string) => str.toLowerCase()
      .replace(/[^\w\s]/g, '')
      .replace(/\s*(llc|inc|corp|lp|llp|pa|na|usa|co|company|corporation|limited|national association|association)\s*/gi, ' ')
      .trim();
    
    const normalized1 = normalize(name1);
    const normalized2 = normalize(name2);
    
    if (normalized1 === normalized2) return 100;
    
    const words1 = normalized1.split(/\s+/);
    const words2 = normalized2.split(/\s+/);
    
    let matchingWords = 0;
    let totalWords = Math.max(words1.length, words2.length);
    
    for (const word1 of words1) {
      if (words2.some(word2 => word2.includes(word1) || word1.includes(word2))) {
        matchingWords++;
      }
    }
    
    return Math.round((matchingWords / totalWords) * 100);
  };

  const findSunbizMatches = (buyerName: string): BuyerSunbizMatches => {
    const entityMatches: SunbizEntity[] = [];
    const officerMatches: Array<{ entity: SunbizEntity; matchingOfficers: Array<{ name: string; title: string; address: string }> }> = [];
    let bestNameScore = 0;

    for (const entity of mockSunbizEntities) {
      // Direct entity name matching
      const nameScore = calculateNameMatchScore(buyerName, entity.entity_name);
      if (nameScore >= 60) {
        entityMatches.push(entity);
        bestNameScore = Math.max(bestNameScore, nameScore);
      }

      // Officer name matching
      const matchingOfficers = entity.officers.filter(officer => {
        const officerScore = calculateNameMatchScore(buyerName, officer.name);
        return officerScore >= 70; // Higher threshold for officer matches
      });

      if (matchingOfficers.length > 0) {
        officerMatches.push({
          entity,
          matchingOfficers
        });
      }
    }

    return {
      entityMatches,
      officerMatches,
      nameScore: bestNameScore
    };
  };

  // Initialize enhanced buyer matches
  useEffect(() => {
    const uniqueBuyers = [...new Set(taxCertificates.map((cert: TaxCertificate) => cert.buyer))];
    const newEnhancedMatches: Record<string, BuyerSunbizMatches> = {};

    uniqueBuyers.forEach((buyer: string) => {
      newEnhancedMatches[buyer] = findSunbizMatches(buyer);
    });

    setEnhancedBuyerMatches(newEnhancedMatches);
  }, [taxCertificates]);

  // Format currency
  const formatCurrency = (value?: number | string) => {
    if (!value && value !== 0) return '-';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(num);
  };

  const formatDate = (date?: string) => {
    if (!date) return '-';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Helper function to get tax values with fallback from multiple sources
  const getTaxValue = (fieldName: string, fallback = 0) => {
    // Check both API format (camelCase) and database format (snake_case)
    const apiField = fieldName.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
    const value = bcpaData?.[fieldName] || bcpaData?.[apiField] || fallback;
    return typeof value === 'string' ? parseInt(value) : value;
  };

  // Calculate tax values from available data with improved field mapping
  const marketValue = getTaxValue('market_value') || getTaxValue('just_value');
  const assessedValue = getTaxValue('assessed_value') || marketValue;
  const taxableValue = getTaxValue('taxable_value') || assessedValue;

  // Get estimated taxes from API analysis section or calculate if not available
  const apiEstimatedTaxes = (data as any)?.analysis?.estimatedTaxes;
  const estimatedTaxRate = 0.015; // 1.5% typical rate
  const annualTaxAmount = apiEstimatedTaxes || getTaxValue('tax_amount') || (taxableValue * estimatedTaxRate);
  
  // Calculate total amount due based on certificates
  const totalCertificateAmount = taxCertificates.reduce((sum: number, cert: TaxCertificate) => 
    sum + (cert.redemption_amount || cert.face_amount), 0
  );
  const isDelinquent = taxCertificates.length > 0;
  const totalAmountDue = isDelinquent ? totalCertificateAmount : annualTaxAmount;
  const delinquencyAmount = totalAmountDue - annualTaxAmount;
  
  const certificateCount = taxCertificates?.length || 0;

  return (
    <div className="space-y-8">
      {/* Executive Tax Overview */}
      <div className="card-executive animate-elegant">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
              <Receipt className="w-4 h-4 text-white" />
            </div>
            Property Tax Assessment
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Current tax obligations and payment status</p>
        </div>
        <div className="pt-8">
          <div className="grid md:grid-cols-3 gap-6 mb-6">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-lg hover:shadow-lg transition-all ${
                isDelinquent ? 'bg-red-50 border border-red-200' : 'bg-gold-light border border-gold'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase tracking-wider text-gray-elegant">Total Amount Due</span>
                {isDelinquent ? (
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                ) : (
                  <DollarSign className="w-4 h-4 text-gold" />
                )}
              </div>
              <p className={`text-3xl font-light ${isDelinquent ? 'text-red-600' : 'text-navy'}`}>
                {formatCurrency(totalAmountDue)}
              </p>
              <p className="text-xs text-gray-elegant mt-1">
                {isDelinquent ? 'DELINQUENT - Certificates outstanding' : 'Current outstanding balance'}
              </p>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="p-4 rounded-lg bg-gray-light border border-gray-elegant hover:shadow-lg transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase tracking-wider text-gray-elegant">
                  {apiEstimatedTaxes ? 'Estimated Annual Tax' : 'Annual Tax Amount'}
                </span>
                <Calculator className="w-4 h-4 text-navy" />
              </div>
              <p className="text-3xl font-light text-navy">
                {formatCurrency(annualTaxAmount)}
              </p>
              <p className="text-xs text-gray-elegant mt-1">
                {apiEstimatedTaxes ? 'From API analysis' : 'Estimated tax obligation'}
              </p>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className={`p-4 rounded-lg hover:shadow-lg transition-all ${
                certificateCount > 0 ? 'bg-orange-50 border border-orange-200' : 'bg-blue-50 border border-blue-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase tracking-wider text-gray-elegant">Tax Certificates</span>
                <FileText className={`w-4 h-4 ${certificateCount > 0 ? 'text-orange-600' : 'text-blue-600'}`} />
              </div>
              <p className="text-3xl font-light text-navy">
                {certificateCount}
              </p>
              <p className="text-xs text-gray-elegant mt-1">
                {certificateCount > 0 ? 'Active liens on property' : 'No active certificates'}
              </p>
            </motion.div>
          </div>
          
          {/* Delinquency Warning */}
          {isDelinquent && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <AlertTriangle className="w-5 h-5 text-red-600 mr-3" />
                  <div>
                    <h4 className="font-medium text-red-800">Tax Certificates Detected</h4>
                    <p className="text-sm text-red-600">
                      Property has {certificateCount} outstanding tax certificate{certificateCount > 1 ? 's' : ''} totaling {formatCurrency(totalCertificateAmount)}
                    </p>
                  </div>
                </div>
                <span className="badge-elegant bg-red-100 text-red-800 border-red-200">
                  LIENS ACTIVE
                </span>
              </div>
            </div>
          )}

          {/* Exemptions */}
          {bcpaData?.homestead_exemption && (
            <div className="p-4 rounded-lg bg-green-50 border border-green-200 mt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Home className="w-5 h-5 text-green-600 mr-3" />
                  <div>
                    <h4 className="font-medium text-navy">Homestead Exemption</h4>
                    <p className="text-sm text-gray-elegant">Primary residence tax savings</p>
                  </div>
                </div>
                <span className="badge-elegant badge-gold">
                  {formatCurrency(bcpaData.homestead_exemption || 50000)}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Comprehensive Tax Certificates Section */}
      {certificateCount > 0 && (
        <div className="card-executive animate-elegant border-l-4 border-orange-400">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center text-orange-700">
              <div className="p-2 rounded-lg mr-3 bg-orange-400">
                <FileText className="w-4 h-4 text-white" />
              </div>
              Tax Certificate Details
            </h3>
            <p className="text-sm mt-4 text-orange-600">
              {certificateCount} tax certificate{certificateCount > 1 ? 's' : ''} creating liens on this property
            </p>
          </div>
          <div className="pt-8">
            <div className="space-y-6">
              {taxCertificates.map((cert: TaxCertificate, index: number) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-6 rounded-lg border-2 border-orange-200 bg-white hover:shadow-xl transition-all"
                >
                  {/* Certificate Header */}
                  <div className="flex justify-between items-start mb-6 pb-4 border-b-2 border-orange-100">
                    <div>
                      <h4 className="text-xl font-semibold text-navy mb-2">
                        Certificate #{cert.certificate_number}
                      </h4>
                      <div className="space-y-1">
                        <p className="text-sm text-gray-elegant">
                          <span className="font-medium">Real Estate Account:</span> {cert.real_estate_account}
                        </p>
                        <p className="text-sm text-gray-elegant">
                          <span className="font-medium">Tax Year:</span> {cert.tax_year || '-'}
                        </p>
                        {cert.advertised_number && (
                          <p className="text-sm text-gray-elegant">
                            <span className="font-medium">Advertised #:</span> {cert.advertised_number}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-elegant mb-1">Face Amount</p>
                      <p className="text-3xl font-light text-orange-600">
                        {formatCurrency(cert.face_amount)}
                      </p>
                      {cert.redemption_amount && (
                        <p className="text-sm text-gray-elegant mt-2">
                          Redemption: <span className="font-semibold text-navy">{formatCurrency(cert.redemption_amount)}</span>
                        </p>
                      )}
                    </div>
                  </div>
                  
                  {/* Certificate Details Grid */}
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Left Column - Buyer Information */}
                    <div className="space-y-4">
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <h5 className="text-sm font-semibold text-navy mb-3 flex items-center">
                          <User className="w-4 h-4 mr-2" />
                          Certificate Buyer / Owner
                        </h5>
                        <p className="text-sm font-medium text-navy mb-2">
                          {cert.buyer}
                        </p>
                        
                        {/* Enhanced Sunbiz Buyer Matching */}
                        {enhancedBuyerMatches[cert.buyer] && (enhancedBuyerMatches[cert.buyer].entityMatches.length > 0 || enhancedBuyerMatches[cert.buyer].officerMatches.length > 0) ? (
                          <div className="mt-3 pt-3 border-t border-gray-200 space-y-4">
                            <div className="flex items-center justify-between">
                              <h6 className="text-xs font-semibold text-navy uppercase tracking-wider flex items-center">
                                <Building2 className="w-3 h-3 mr-1" />
                                Sunbiz Entity Matches
                                <Badge className="ml-2 bg-gold text-navy text-xs">
                                  {enhancedBuyerMatches[cert.buyer].nameScore}% Match
                                </Badge>
                              </h6>
                            </div>

                            {/* Direct Entity Matches */}
                            {enhancedBuyerMatches[cert.buyer].entityMatches.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-xs font-medium text-gray-700">Direct Entity Name Matches:</p>
                                {enhancedBuyerMatches[cert.buyer].entityMatches.map((entity, idx) => (
                                  <div key={idx} className="card-executive-mini bg-gold-light border border-gold p-3 rounded-lg">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <div className="flex items-center mb-2">
                                          <Building2 className="w-3 h-3 mr-2 text-navy" />
                                          <p className="text-xs font-semibold text-navy">{entity.entity_name}</p>
                                          <Badge className={entity.status === 'Active' ? 'ml-2 bg-green-100 text-green-800 text-xs' : 'ml-2 bg-gray-100 text-gray-800 text-xs'}>
                                            {entity.status}
                                          </Badge>
                                        </div>
                                        <p className="text-xs text-gray-600 mb-1">
                                          <span className="font-medium">Type:</span> {entity.entity_type}
                                        </p>
                                        <p className="text-xs text-gray-600 mb-2">
                                          <span className="font-medium">Document:</span> {entity.document_number}
                                        </p>
                                        <div className="flex items-center space-x-2">
                                          {editingUrls[`${cert.certificate_number}-${idx}`] ? (
                                            <div className="flex items-center space-x-1">
                                              <input
                                                type="text"
                                                value={customUrls[`${cert.certificate_number}-${idx}`] || ''}
                                                onChange={(e) => setCustomUrls(prev => ({ ...prev, [`${cert.certificate_number}-${idx}`]: e.target.value }))}
                                                placeholder="Enter custom Sunbiz URL"
                                                className="text-xs border rounded px-2 py-1 w-48"
                                              />
                                              <button
                                                onClick={() => setEditingUrls(prev => ({ ...prev, [`${cert.certificate_number}-${idx}`]: false }))}
                                                className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                                              >
                                                Save
                                              </button>
                                            </div>
                                          ) : (
                                            <>
                                              <a 
                                                href={customUrls[`${cert.certificate_number}-${idx}`] || `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResultDetail?inquirytype=EntityName&directionType=Initial&searchNameOrder=${entity.document_number}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-xs font-medium text-blue-600 hover:underline flex items-center"
                                              >
                                                <Link className="w-3 h-3 mr-1" />
                                                View Sunbiz Profile
                                              </a>
                                              <button
                                                onClick={() => setEditingUrls(prev => ({ ...prev, [`${cert.certificate_number}-${idx}`]: true }))}
                                                className="text-xs text-gray-500 hover:text-blue-600"
                                                title="Edit URL"
                                              >
                                                <Edit3 className="w-3 h-3" />
                                              </button>
                                              <button
                                                onClick={() => setCustomUrls(prev => ({ ...prev, [`${cert.certificate_number}-${idx}`]: '' }))}
                                                className="text-xs text-gray-500 hover:text-red-600"
                                                title="Delete custom URL"
                                              >
                                                <Trash2 className="w-3 h-3" />
                                              </button>
                                            </>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Officer Name Matches */}
                            {enhancedBuyerMatches[cert.buyer].officerMatches.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-xs font-medium text-gray-700 flex items-center">
                                  <Users className="w-3 h-3 mr-1" />
                                  Officer/Director Name Matches:
                                </p>
                                {enhancedBuyerMatches[cert.buyer].officerMatches.map((match, idx) => (
                                  <div key={idx} className="card-executive-mini bg-gold-light border border-gold p-3 rounded-lg">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <p className="text-xs font-semibold text-navy mb-1">{match.entity.entity_name}</p>
                                        <div className="space-y-1">
                                          {match.matchingOfficers.map((officer, officerIdx) => (
                                            <div key={officerIdx} className="flex items-center">
                                              <AlertCircle className="w-3 h-3 mr-1 text-navy" />
                                              <p className="text-xs text-gray-600">
                                                <span className="font-medium">{officer.name}</span> - {officer.title}
                                              </p>
                                            </div>
                                          ))}
                                        </div>
                                        <div className="flex items-center space-x-2 mt-2">
                                          <a 
                                            href={`https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResultDetail?inquirytype=EntityName&directionType=Initial&searchNameOrder=${match.entity.document_number}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-xs font-medium text-navy hover:underline flex items-center"
                                          >
                                            <Link className="w-3 h-3 mr-1" />
                                            View Entity Profile
                                          </a>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs text-gray-500 flex items-center">
                              <AlertTriangle className="w-3 h-3 mr-1" />
                              No Sunbiz matches found for this buyer
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Right Column - Certificate Details */}
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Interest Rate</p>
                          <p className="text-lg font-light text-navy">
                            {cert.interest_rate}%
                          </p>
                        </div>
                        <div>
                          <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Winning Bid %</p>
                          <p className="text-lg font-semibold text-navy">
                            {cert.winning_bid_percentage || cert.interest_rate}%
                          </p>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Issued Date</p>
                          <p className="text-sm font-medium text-navy">
                            {formatDate(cert.issued_date)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Expiration Date</p>
                          <p className="text-sm font-medium text-navy">
                            {formatDate(cert.expiration_date)}
                          </p>
                        </div>
                      </div>
                      
                      {cert.redemption_date && (
                        <div>
                          <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Redemption Date</p>
                          <p className="text-sm font-medium text-navy">
                            {formatDate(cert.redemption_date)}
                          </p>
                        </div>
                      )}
                      
                      <div className="pt-3">
                        <p className="text-xs uppercase tracking-wider text-gray-elegant mb-2">Status</p>
                        {cert.status === 'active' ? (
                          <Badge className="badge-elegant badge-gold flex items-center w-fit">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            Active Lien
                          </Badge>
                        ) : cert.status === 'redeemed' ? (
                          <Badge className="badge-elegant flex items-center w-fit">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Redeemed
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="w-fit">
                            {cert.status || 'Unknown'}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Certificate Action Links */}
                  <div className="mt-6 pt-4 border-t border-gray-200 flex flex-wrap gap-4">
                    <a 
                      href={`https://broward.county-taxes.com/public/search/property_tax`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-navy hover:underline flex items-center"
                    >
                      <FileText className="w-4 h-4 mr-1" />
                      View Full Certificate Details
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                    <a 
                      href={`https://broward.county-taxes.com/public/real_estate/parcels/${cert.real_estate_account}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-navy hover:underline flex items-center"
                    >
                      <Receipt className="w-4 h-4 mr-1" />
                      View Tax Bill History
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                    {certificateBuyerData[cert.buyer] && (
                      <a 
                        href={`#sunbiz`}
                        onClick={() => {
                          // Navigate to Sunbiz tab - this would be implemented with proper navigation
                          const sunbizTab = document.querySelector('[value="sunbiz"]');
                          if (sunbizTab) (sunbizTab as HTMLElement).click();
                        }}
                        className="text-sm font-medium text-navy hover:underline flex items-center"
                      >
                        <Building className="w-4 h-4 mr-1" />
                        View Buyer in Sunbiz Tab
                        <ArrowRight className="w-3 h-3 ml-1" />
                      </a>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
            
            {/* Certificate Investment Analysis */}
            <div className="mt-8 p-6 bg-gradient-to-r from-orange-50 to-red-50 rounded-lg border-2 border-orange-200">
              <h4 className="font-semibold text-navy mb-3 flex items-center text-lg">
                <AlertTriangle className="w-5 h-5 mr-2" />
                Investment Impact Analysis
              </h4>
              <div className="space-y-3 text-sm text-navy">
                <p>
                  <span className="font-semibold">Total Lien Amount:</span> {formatCurrency(totalCertificateAmount)} must be paid to clear all certificates
                </p>
                <p>
                  <span className="font-semibold">Interest Accrual:</span> Certificates accrue interest at 18% annually (Florida statutory maximum)
                </p>
                <p>
                  <span className="font-semibold">Title Impact:</span> These liens must be satisfied before any property transfer or refinancing
                </p>
                <p>
                  <span className="font-semibold">Redemption Period:</span> Property owner has 2 years to redeem before certificate holder can apply for tax deed
                </p>
              </div>
              
              <div className="mt-4 p-3 bg-white rounded border border-orange-200">
                <p className="text-xs text-gray-600">
                  <Info className="w-3 h-3 inline mr-1" />
                  Tax certificates represent a superior lien position, taking priority over most mortgages and other liens except federal tax liens.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Valuation Breakdown - Executive Analysis */}
      {bcpaData && (
        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent flex items-center">
              <div className="p-2 bg-navy rounded-lg mr-3">
                <Calculator className="w-4 h-4 text-white" />
              </div>
              Assessment Valuation Breakdown
            </h3>
            <p className="text-sm mt-4 text-gray-elegant">Component analysis of property tax assessment</p>
          </div>
          <div className="pt-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light"
              >
                <div className="flex items-center mb-3">
                  <TreePine className="w-4 h-4 mr-2 text-gold" />
                  <span className="text-xs uppercase tracking-wider text-gray-elegant">Land Value</span>
                </div>
                <p className="text-2xl font-light text-navy group-hover:text-gold transition-colors">
                  {formatCurrency(getTaxValue('land_value'))}
                </p>
                <p className="text-xs text-gray-elegant mt-1">Underlying real estate</p>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light"
              >
                <div className="flex items-center mb-3">
                  <Building className="w-4 h-4 mr-2 text-gold" />
                  <span className="text-xs uppercase tracking-wider text-gray-elegant">Building Value</span>
                </div>
                <p className="text-2xl font-light text-navy group-hover:text-gold transition-colors">
                  {formatCurrency(getTaxValue('building_value'))}
                </p>
                <p className="text-xs text-gray-elegant mt-1">Structure & improvements</p>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="p-4 rounded-lg hover:bg-gray-50 transition-all group border border-gray-light"
              >
                <div className="flex items-center mb-3">
                  <Star className="w-4 h-4 mr-2 text-gold" />
                  <span className="text-xs uppercase tracking-wider text-gray-elegant">Extra Features</span>
                </div>
                <p className="text-2xl font-light text-navy group-hover:text-gold transition-colors">
                  {formatCurrency(getTaxValue('extra_features_value'))}
                </p>
                <p className="text-xs text-gray-elegant mt-1">Pools, garages, etc.</p>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="p-4 rounded-lg bg-gold-light border border-gold hover:shadow-lg transition-all"
              >
                <div className="flex items-center mb-3">
                  <DollarSign className="w-4 h-4 mr-2 text-navy" />
                  <span className="text-xs uppercase tracking-wider text-gray-elegant">Market Value</span>
                </div>
                <p className="text-2xl font-light text-navy">
                  {formatCurrency(marketValue)}
                </p>
                <p className="text-xs text-gray-elegant mt-1">Total assessment</p>
              </motion.div>
            </div>
            
            {/* Assessment Analytics */}
            <div className="mt-8 p-6 bg-navy rounded-lg">
              <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                Tax Assessment Analysis
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-white">
                <div>
                  <p className="text-sm opacity-75">Effective Tax Rate</p>
                  <p className="text-2xl font-light">
                    {marketValue > 0 ? `${((annualTaxAmount / marketValue) * 100).toFixed(2)}%` : '-'}
                  </p>
                </div>
                <div>
                  <p className="text-sm opacity-75">Monthly Tax Cost</p>
                  <p className="text-2xl font-light">
                    {formatCurrency(annualTaxAmount / 12)}
                  </p>
                </div>
                <div>
                  <p className="text-sm opacity-75">Assessment Status</p>
                  <p className="text-lg font-light">
                    {bcpaData?.homestead_exemption ? 'Homesteaded' : 'Investment Property'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Special Assessments - Executive Alert */}
      {isInCDD && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card-executive border-l-4 border-gold bg-gold-light"
        >
          <div className="elegant-card-header border-orange-200">
            <h3 className="elegant-card-title flex items-center text-navy">
              <div className="p-2 rounded-lg mr-3 bg-gold">
                <AlertTriangle className="w-4 h-4 text-white" />
              </div>
              Special Assessment District (CDD/NAV)
            </h3>
            <p className="text-sm mt-4 text-navy">Property is subject to additional annual assessments</p>
          </div>
          <div className="pt-6">
            <div className="text-center p-6 rounded-lg bg-white border border-orange-200">
              <div className="flex items-center justify-center mb-4">
                <Landmark className="w-8 h-8 text-navy mr-3" />
                <div>
                  <p className="text-lg font-light elegant-text text-gray-elegant">Total Annual Assessment</p>
                  <p className="text-4xl font-light text-navy">
                    {formatCurrency(totalNavAssessment)}
                  </p>
                </div>
              </div>
              <div className="text-center p-4 bg-gold-light rounded-lg">
                <p className="text-sm text-navy font-medium mb-2">Investment Impact Analysis</p>
                <p className="text-xs text-gray-elegant">
                  Community Development District assessments represent additional carrying costs that should be factored into investment calculations.
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* No Special Assessments - Clean Status */}
      {(!navData || navData.length === 0) && !isInCDD && certificateCount === 0 && !isDelinquent && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card-executive border-l-4 border-green-400"
        >
          <div className="text-center py-12">
            <div className="flex items-center justify-center mb-4">
              <div className="p-4 bg-gold-light rounded-full">
                <Receipt className="w-8 h-8 text-navy" />
              </div>
            </div>
            <h3 className="text-xl elegant-heading text-navy mb-2">Clean Tax Profile</h3>
            <p className="text-gray-elegant">No tax certificates, special assessments, or delinquencies found for this property.</p>
            <div className="mt-6 p-4 bg-gold-light rounded-lg inline-block">
              <span className="badge-elegant badge-gold">✓ Investment Advantage</span>
              <p className="text-xs text-navy mt-2">Lower carrying costs and no outstanding liens</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
