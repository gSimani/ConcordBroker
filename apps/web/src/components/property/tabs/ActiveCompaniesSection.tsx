import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Search, Building2, Users, MapPin, Phone, Mail, Filter, Download,
  ExternalLink, ArrowRight, Loader2, Database, TrendingUp, Badge as BadgeIcon,
  ChevronDown, ChevronUp, Star, AlertCircle, CheckCircle, Eye, RefreshCw
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ActiveCompany {
  id: string;
  entity_name: string;
  entity_type: string;
  status: string;
  filing_date?: string;
  business_address: string;
  officer_name?: string;
  officer_email?: string;
  officer_phone?: string;
  doc_number: string;
  source: string;
}

interface ActiveCompaniesStats {
  total_active: number;
  corporations: number;
  active_entities: number;
  property_owners: number;
  with_contacts: number;
}

interface ActiveCompaniesProps {
  propertyData: any;
}

const ActiveCompaniesSection: React.FC<ActiveCompaniesProps> = ({ propertyData }) => {
  const [activeCompanies, setActiveCompanies] = useState<ActiveCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showContacts, setShowContacts] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [totalStats, setTotalStats] = useState<ActiveCompaniesStats>({
    total_active: 8352062,
    corporations: 2030890,
    active_entities: 4289282,
    property_owners: 2031890,
    with_contacts: 1182
  });
  const [hasMore, setHasMore] = useState(false);
  const [currentOffset, setCurrentOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Extract property data for search context
  const ownerName = propertyData?.bcpaData?.owner_name || propertyData?.owner_name || '';
  const propertyAddress = propertyData?.bcpaData?.property_address_street || propertyData?.phy_addr1 || '';

  // Fetch active companies data
  useEffect(() => {
    fetchActiveCompanies();
  }, [propertyData]);

  useEffect(() => {
    if (searchTerm || filterType !== 'all') {
      const timeoutId = setTimeout(() => {
        fetchActiveCompanies(0);
      }, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [searchTerm, filterType]);

  const fetchActiveCompanies = async (offset = 0) => {
    setLoading(true);
    setError(null);

    try {
      const requestBody = {
        search_term: searchTerm || undefined,
        owner_name: ownerName || undefined,
        property_address: propertyAddress || undefined,
        entity_type: filterType === 'all' ? undefined : filterType,
        limit: 20,
        offset: offset
      };

      const response = await fetch('/api/supabase/active-companies', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();

      if (offset === 0) {
        setActiveCompanies(data.companies || []);
      } else {
        setActiveCompanies(prev => [...prev, ...(data.companies || [])]);
      }

      setTotalStats(data.statistics || totalStats);
      setHasMore(data.has_more || false);
      setCurrentOffset(offset);

    } catch (error) {
      console.error('Error fetching active companies:', error);
      setError(error.message);

      // Fallback to enhanced sample data on error
      if (offset === 0) {
        const sampleCompanies: ActiveCompany[] = [
          {
            id: 'sample_1',
            entity_name: 'CONCORDBROKER PROPERTY MANAGEMENT LLC',
            entity_type: 'LLC',
            status: 'ACTIVE',
            filing_date: '2024-01-15',
            business_address: '123 Investment Blvd, Miami, FL 33101',
            officer_name: 'John Smith',
            officer_email: 'john@concordbroker.com',
            officer_phone: '(305) 555-0123',
            doc_number: 'L24000123456',
            source: 'sunbiz_corporate'
          },
          {
            id: 'sample_2',
            entity_name: 'FLORIDA TECH SOLUTIONS INC',
            entity_type: 'CORP',
            status: 'ACTIVE',
            filing_date: '2023-08-22',
            business_address: '456 Business Blvd, Orlando, FL 32801',
            officer_name: 'Sarah Johnson',
            officer_email: 'sarah@floridatech.com',
            officer_phone: '(407) 555-0456',
            doc_number: 'P23000789012',
            source: 'florida_entities'
          },
          {
            id: 'sample_3',
            entity_name: 'COASTAL REAL ESTATE GROUP',
            entity_type: 'CORP',
            status: 'ACTIVE',
            filing_date: '2024-03-10',
            business_address: '789 Ocean Dr, Fort Lauderdale, FL 33301',
            officer_name: 'Michael Davis',
            officer_email: 'mdavis@coastalre.com',
            officer_phone: '(954) 555-0789',
            doc_number: 'P24000345678',
            source: 'officer_matches'
          }
        ];
        setActiveCompanies(sampleCompanies);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      fetchActiveCompanies(currentOffset + 20);
    }
  };

  const filteredCompanies = showContacts
    ? activeCompanies.filter(company => company.officer_email || company.officer_phone)
    : activeCompanies;

  const exportToCSV = () => {
    const csv = [
      ['Entity Name', 'Type', 'Status', 'Doc Number', 'Address', 'Officer', 'Email', 'Phone', 'Source'],
      ...filteredCompanies.map(company => [
        company.entity_name,
        company.entity_type,
        company.status,
        company.doc_number,
        company.business_address,
        company.officer_name || '',
        company.officer_email || '',
        company.officer_phone || '',
        company.source
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `florida-active-companies-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getStatusBadge = (status: string) => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('active')) {
      return <Badge className="bg-green-100 text-green-800 text-xs">Active</Badge>;
    } else if (statusLower.includes('inactive')) {
      return <Badge className="bg-red-100 text-red-800 text-xs">Inactive</Badge>;
    }
    return <Badge variant="outline" className="text-xs">{status}</Badge>;
  };

  const getEntityTypeBadge = (type: string) => {
    const colors = {
      'CORP': 'bg-blue-100 text-blue-800',
      'LLC': 'bg-purple-100 text-purple-800',
      'ENTITY': 'bg-gray-100 text-gray-800',
      'INC': 'bg-indigo-100 text-indigo-800'
    };
    const colorClass = colors[type] || 'bg-gray-100 text-gray-800';
    return <Badge className={`${colorClass} text-xs font-medium`}>{type}</Badge>;
  };

  const getSourceBadge = (source: string) => {
    const colors = {
      'sunbiz_corporate': 'bg-orange-100 text-orange-800',
      'florida_entities': 'bg-green-100 text-green-800',
      'officer_matches': 'bg-blue-100 text-blue-800',
      'sample': 'bg-yellow-100 text-yellow-800'
    };
    const labels = {
      'sunbiz_corporate': 'Sunbiz Corp',
      'florida_entities': 'FL Entities',
      'officer_matches': 'Contact Data',
      'sample': 'Demo'
    };
    const colorClass = colors[source] || 'bg-gray-100 text-gray-800';
    const label = labels[source] || source;
    return <Badge className={`${colorClass} text-xs`}>{label}</Badge>;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card-executive animate-elegant border-l-4 border-gold mb-8"
    >
      {/* Header */}
      <div className="elegant-card-header">
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={() => setExpanded(!expanded)}
        >
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 rounded-lg mr-3" style={{background: '#d4af37'}}>
              <Database className="w-4 h-4 text-white" />
            </div>
            Active Florida Companies Database
            <Badge className="ml-3 bg-gold text-navy text-xs font-semibold">
              {formatNumber(totalStats.total_active)} COMPANIES
            </Badge>
          </h3>
          {expanded ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </div>
        <p className="text-sm mt-4 text-gray-elegant">
          Complete Florida business intelligence with 8.35+ million active companies from Department of State
        </p>
      </div>

      {expanded && (
        <div className="pt-8">
          {/* Statistics Dashboard */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-lg border border-blue-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-600 font-medium">Corporations</p>
                  <p className="text-2xl font-bold text-blue-900">{formatNumber(totalStats.corporations)}</p>
                </div>
                <Building2 className="w-8 h-8 text-blue-500" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-lg border border-green-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-600 font-medium">Active Entities</p>
                  <p className="text-2xl font-bold text-green-900">{formatNumber(totalStats.active_entities)}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-lg border border-purple-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-600 font-medium">Property Owners</p>
                  <p className="text-2xl font-bold text-purple-900">{formatNumber(totalStats.property_owners)}</p>
                </div>
                <MapPin className="w-8 h-8 text-purple-500" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-gradient-to-r from-orange-50 to-orange-100 p-6 rounded-lg border border-orange-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-600 font-medium">With Contacts</p>
                  <p className="text-2xl font-bold text-orange-900">{formatNumber(totalStats.with_contacts)}</p>
                </div>
                <Users className="w-8 h-8 text-orange-500" />
              </div>
            </motion.div>
          </div>

          {/* Search and Filter Controls */}
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search companies by name or document number..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-transparent"
              />
            </div>

            <div className="flex gap-2">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-transparent"
              >
                <option value="all">All Types</option>
                <option value="CORP">Corporations</option>
                <option value="LLC">LLCs</option>
                <option value="ENTITY">Entities</option>
              </select>

              <button
                onClick={() => setShowContacts(!showContacts)}
                className={`px-4 py-2 rounded-lg border transition-colors ${
                  showContacts
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                <Mail className="w-4 h-4 inline mr-2" />
                Contacts Only
              </button>

              <button
                onClick={exportToCSV}
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                <Download className="w-4 h-4 inline mr-2" />
                Export
              </button>

              <button
                onClick={() => fetchActiveCompanies(0)}
                disabled={loading}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <Alert className="mb-6 border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                <strong>API Error:</strong> {error}. Showing sample data for demonstration.
              </AlertDescription>
            </Alert>
          )}

          {/* Companies Grid */}
          {loading && activeCompanies.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-gold mr-3" />
              <span className="text-lg text-gray-600">Loading active companies...</span>
            </div>
          ) : (
            <>
              <div className="grid gap-4 mb-6">
                {filteredCompanies.map((company, index) => (
                  <motion.div
                    key={company.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-all group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <Building2 className="w-5 h-5 text-blue-600" />
                          <h4 className="text-lg font-semibold text-navy group-hover:text-gold transition-colors">
                            {company.entity_name}
                          </h4>
                          {getEntityTypeBadge(company.entity_type)}
                          {getStatusBadge(company.status)}
                          {getSourceBadge(company.source)}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Document Number</p>
                            <p className="text-sm font-mono text-navy">{company.doc_number}</p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Filing Date</p>
                            <p className="text-sm text-navy">
                              {company.filing_date
                                ? new Date(company.filing_date).toLocaleDateString()
                                : 'N/A'}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Address</p>
                            <p className="text-sm text-navy truncate" title={company.business_address}>
                              {company.business_address || 'N/A'}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Source Database</p>
                            <p className="text-sm text-navy">{company.source.replace('_', ' ').toUpperCase()}</p>
                          </div>
                        </div>

                        {/* Contact Information */}
                        {(company.officer_name || company.officer_email || company.officer_phone) && (
                          <div className="border-t border-gray-100 pt-4">
                            <p className="text-xs uppercase tracking-wider text-gray-500 mb-2">Officer Contact</p>
                            <div className="flex flex-wrap gap-4">
                              {company.officer_name && (
                                <div className="flex items-center gap-2">
                                  <Users className="w-4 h-4 text-gray-400" />
                                  <span className="text-sm text-navy">{company.officer_name}</span>
                                </div>
                              )}
                              {company.officer_email && (
                                <div className="flex items-center gap-2">
                                  <Mail className="w-4 h-4 text-gray-400" />
                                  <a
                                    href={`mailto:${company.officer_email}`}
                                    className="text-sm text-blue-600 hover:text-blue-800"
                                  >
                                    {company.officer_email}
                                  </a>
                                </div>
                              )}
                              {company.officer_phone && (
                                <div className="flex items-center gap-2">
                                  <Phone className="w-4 h-4 text-gray-400" />
                                  <a
                                    href={`tel:${company.officer_phone}`}
                                    className="text-sm text-blue-600 hover:text-blue-800"
                                  >
                                    {company.officer_phone}
                                  </a>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col gap-2 ml-4">
                        <a
                          href={`https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResultDetail?inquirytype=EntityName&directionType=Initial&searchNameOrder=${company.doc_number}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                          title="View on Sunbiz"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                        <button
                          className="p-2 bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Load More Button */}
              {hasMore && (
                <div className="text-center">
                  <button
                    onClick={loadMore}
                    disabled={loading}
                    className="px-6 py-3 bg-gold text-navy rounded-lg hover:bg-gold-dark transition-colors disabled:opacity-50 font-medium"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
                        Loading more...
                      </>
                    ) : (
                      <>
                        Load More Companies
                        <ArrowRight className="w-4 h-4 inline ml-2" />
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Results Summary */}
              <div className="mt-6 text-center text-sm text-gray-500">
                Showing {filteredCompanies.length} companies
                {searchTerm && ` matching "${searchTerm}"`}
                {showContacts && ' with contact information'}
                {hasMore && ' (more available)'}
              </div>
            </>
          )}
        </div>
      )}
    </motion.div>
  );
};

export default ActiveCompaniesSection;