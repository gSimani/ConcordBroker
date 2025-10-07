import React, { useState, useEffect } from 'react';
import { Search, Building2, Users, MapPin, Phone, Mail, Filter, Download } from 'lucide-react';

interface ActiveCompany {
  id: string;
  entity_name: string;
  entity_type: string;
  status: string;
  filing_date: string;
  business_address: string;
  officer_name?: string;
  officer_email?: string;
  officer_phone?: string;
  doc_number: string;
}

interface SunbizTabProps {
  propertyData: any;
}

const SunbizTab: React.FC<SunbizTabProps> = ({ propertyData }) => {
  const [activeCompanies, setActiveCompanies] = useState<ActiveCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showContacts, setShowContacts] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  // Fetch active companies data
  useEffect(() => {
    fetchActiveCompanies();
  }, [propertyData]);

  const fetchActiveCompanies = async () => {
    setLoading(true);
    try {
      // Query multiple tables for comprehensive company data
      const response = await fetch('/api/supabase/active-companies', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_address: propertyData?.address,
          owner_name: propertyData?.owner_name,
          limit: 100
        }),
      });

      const data = await response.json();
      setActiveCompanies(data.companies || []);
      setTotalCount(data.total_count || 0);
    } catch (error) {
      console.error('Error fetching active companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredCompanies = activeCompanies.filter(company => {
    const matchesSearch = company.entity_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         company.doc_number.includes(searchTerm);
    const matchesFilter = filterType === 'all' || company.entity_type === filterType;
    return matchesSearch && matchesFilter;
  });

  const exportToCSV = () => {
    const csv = [
      ['Entity Name', 'Type', 'Status', 'Doc Number', 'Address', 'Officer', 'Email', 'Phone'],
      ...filteredCompanies.map(company => [
        company.entity_name,
        company.entity_type,
        company.status,
        company.doc_number,
        company.business_address,
        company.officer_name || '',
        company.officer_email || '',
        company.officer_phone || ''
      ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'active_florida_companies.csv';
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Header with Statistics */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
          <Building2 className="mr-3 text-blue-600" />
          Active Florida Companies
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-3xl font-bold text-blue-600">8.35M+</div>
            <div className="text-sm text-gray-600">Total Active Companies</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-3xl font-bold text-green-600">2.03M</div>
            <div className="text-sm text-gray-600">Registered Corporations</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-3xl font-bold text-purple-600">6.3M</div>
            <div className="text-sm text-gray-600">Property Owners</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-3xl font-bold text-orange-600">1,182</div>
            <div className="text-sm text-gray-600">With Contact Info</div>
          </div>
        </div>
      </div>

      {/* Search and Filter Controls */}
      <div className="bg-white rounded-lg p-4 shadow-sm">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex-1 min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search companies by name or document number..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="all">All Types</option>
            <option value="CORP">Corporations</option>
            <option value="LLC">Limited Liability Companies</option>
            <option value="PART">Partnerships</option>
            <option value="NON">Non-Profit</option>
          </select>

          <button
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
            onClick={() => setShowContacts(!showContacts)}
          >
            <Users className="mr-2 h-4 w-4" />
            {showContacts ? 'Hide' : 'Show'} Contacts
          </button>

          <button
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center"
            onClick={exportToCSV}
          >
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Companies List */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Active Companies ({filteredCompanies.length.toLocaleString()} of {totalCount.toLocaleString()})
          </h3>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading active companies...</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredCompanies.map((company) => (
              <div key={company.id} className="p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">
                      {company.entity_name}
                    </h4>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">
                          <strong>Type:</strong> {company.entity_type}
                        </p>
                        <p className="text-gray-600">
                          <strong>Status:</strong>
                          <span className={`ml-1 px-2 py-1 rounded-full text-xs ${
                            company.status === 'ACTIVE'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {company.status || 'Active'}
                          </span>
                        </p>
                        <p className="text-gray-600">
                          <strong>Doc Number:</strong> {company.doc_number}
                        </p>
                        <p className="text-gray-600">
                          <strong>Filing Date:</strong> {company.filing_date}
                        </p>
                      </div>

                      <div>
                        {company.business_address && (
                          <p className="text-gray-600 flex items-start">
                            <MapPin className="mr-1 h-4 w-4 mt-0.5 text-gray-400" />
                            {company.business_address}
                          </p>
                        )}

                        {showContacts && (company.officer_email || company.officer_phone) && (
                          <div className="mt-2 p-2 bg-blue-50 rounded">
                            <p className="text-sm font-medium text-blue-900 mb-1">Contact Information:</p>
                            {company.officer_name && (
                              <p className="text-sm text-blue-800">
                                <strong>Officer:</strong> {company.officer_name}
                              </p>
                            )}
                            {company.officer_email && (
                              <p className="text-sm text-blue-800 flex items-center">
                                <Mail className="mr-1 h-3 w-3" />
                                {company.officer_email}
                              </p>
                            )}
                            {company.officer_phone && (
                              <p className="text-sm text-blue-800 flex items-center">
                                <Phone className="mr-1 h-3 w-3" />
                                {company.officer_phone}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Load More Button */}
      {filteredCompanies.length < totalCount && (
        <div className="text-center">
          <button
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            onClick={() => {
              // Implement pagination/load more functionality
              console.log('Load more companies');
            }}
          >
            Load More Companies
          </button>
        </div>
      )}
    </div>
  );
};

export default SunbizTab;