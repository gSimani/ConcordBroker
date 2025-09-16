import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MiniPropertyCard, getPropertyCategory } from '@/components/property/MiniPropertyCard';
import { PropertyMap } from '@/components/property/PropertyMap';
import { PropertyAutocomplete } from '@/components/PropertyAutocomplete';
import { AIPropertyCard } from '@/components/ai/AIPropertyCard';
import { AISearchBar } from '@/components/ai/AISearchBar';
import { parcelService, type FloridaParcel } from '@/lib/supabase';
// Mock data removed - using only real database data
import '@/styles/elegant-property.css';
import { 
  Search, 
  Filter, 
  MapPin, 
  Grid3X3, 
  List,
  SlidersHorizontal,
  TrendingUp,
  Building,
  Home,
  RefreshCw,
  Download,
  Map,
  CheckSquare,
  Square,
  Database,
  AlertCircle
} from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export function PropertySearchSupabase() {
  const navigate = useNavigate();
  const [properties, setProperties] = useState<FloridaParcel[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'map'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedProperties, setSelectedProperties] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [showUsageCodeDropdown, setShowUsageCodeDropdown] = useState(false);
  const [showSubUsageCodeDropdown, setShowSubUsageCodeDropdown] = useState(false);
  
  // Search filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    county: 'BROWARD',
    city: '',
    zipCode: '',
    ownerName: '',
    minPrice: '',
    maxPrice: '',
    propertyType: '',
    minYear: '',
    maxYear: '',
    minSqFt: '',
    maxSqFt: '',
    minBeds: '',
    minBaths: '',
    minLotSize: '',
    maxLotSize: '',
    minSalePrice: '',
    maxSalePrice: '',
    minSaleDate: '',
    maxSaleDate: '',
    usageCode: '',
    subUsageCode: '',
    hasForeclosure: false,
    hasTaxDeed: false,
    hasTaxLien: false
  });

  // Statistics
  const [stats, setStats] = useState({
    avgValue: 0,
    totalValue: 0,
    recentSales: 0
  });

  // Handle database errors and empty results
  const handleNoResults = useCallback((reason: string) => {
    console.log('No results:', reason);
    setProperties([]);
    setTotalResults(0);
    setError(`No properties found: ${reason}`);
  }, []);

  // Fetch properties from Supabase - NO RESTRICTIONS
  const fetchProperties = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Build query with NO restrictions - allow searching everything
      let query = supabase
        .from('florida_parcels')
        .select('*', { count: 'exact' });
      
      // Apply filters ONLY if user explicitly sets them
      if (searchQuery) {
        query = query.or(`phy_addr1.ilike.%${searchQuery}%,owner_name.ilike.%${searchQuery}%,parcel_id.eq.${searchQuery}`);
      }
      
      if (filters.city && filters.city !== '') {
        query = query.ilike('phy_city', `%${filters.city}%`);
      }
      
      if (filters.zipCode && filters.zipCode !== '') {
        query = query.eq('phy_zipcd', filters.zipCode);
      }
      
      if (filters.ownerName && filters.ownerName !== '') {
        query = query.ilike('owner_name', `%${filters.ownerName}%`);
      }
      
      // Value filters - no restrictions
      if (filters.minPrice && filters.minPrice !== '') {
        query = query.gte('taxable_value', parseInt(filters.minPrice));
      }
      
      if (filters.maxPrice && filters.maxPrice !== '') {
        query = query.lte('taxable_value', parseInt(filters.maxPrice));
      }
      
      // Year filters - no restrictions
      if (filters.minYear && filters.minYear !== '') {
        query = query.gte('year_built', parseInt(filters.minYear));
      }
      
      if (filters.maxYear && filters.maxYear !== '') {
        query = query.lte('year_built', parseInt(filters.maxYear));
      }
      
      // Size filters - no restrictions
      if (filters.minSqFt && filters.minSqFt !== '') {
        query = query.gte('total_living_area', parseInt(filters.minSqFt));
      }
      
      if (filters.maxSqFt && filters.maxSqFt !== '') {
        query = query.lte('total_living_area', parseInt(filters.maxSqFt));
      }
      
      // Bed/Bath filters - no restrictions
      if (filters.minBeds && filters.minBeds !== '') {
        query = query.gte('bedrooms', parseInt(filters.minBeds));
      }
      
      if (filters.minBaths && filters.minBaths !== '') {
        query = query.gte('bathrooms', parseFloat(filters.minBaths));
      }
      
      // Lot size filters - no restrictions
      if (filters.minLotSize && filters.minLotSize !== '') {
        query = query.gte('land_sqft', parseInt(filters.minLotSize));
      }
      
      if (filters.maxLotSize && filters.maxLotSize !== '') {
        query = query.lte('land_sqft', parseInt(filters.maxLotSize));
      }
      
      // Sale filters - no restrictions
      if (filters.minSalePrice && filters.minSalePrice !== '') {
        query = query.gte('sale_price', parseInt(filters.minSalePrice));
      }
      
      if (filters.maxSalePrice && filters.maxSalePrice !== '') {
        query = query.lte('sale_price', parseInt(filters.maxSalePrice));
      }
      
      if (filters.minSaleDate && filters.minSaleDate !== '') {
        query = query.gte('sale_date', filters.minSaleDate);
      }
      
      if (filters.maxSaleDate && filters.maxSaleDate !== '') {
        query = query.lte('sale_date', filters.maxSaleDate);
      }
      
      // Usage code filters - no restrictions
      if (filters.usageCode && filters.usageCode !== '') {
        const code = filters.usageCode.split(' - ')[0];
        query = query.eq('property_use', code);
      }
      
      // Property type filter based on DOR use codes
      if (filters.propertyType && filters.propertyType !== '') {
        if (filters.propertyType === 'Residential') {
          // Residential: 000-099
          query = query.like('property_use', '0*');
        } else if (filters.propertyType === 'Commercial') {
          // Commercial: 100-399
          query = query.or('property_use.like.1*,property_use.like.2*,property_use.like.3*');
        } else if (filters.propertyType === 'Industrial') {
          // Industrial: 400-499
          query = query.like('property_use', '4*');
        } else if (filters.propertyType === 'Agricultural') {
          // Agricultural: 500-699
          query = query.or('property_use.like.5*,property_use.like.6*');
        } else if (filters.propertyType === 'Vacant Land') {
          // Vacant/Land: typically x00 codes (000, 100, 400, 500, etc.)
          query = query.or('property_use.eq.000,property_use.eq.100,property_use.eq.400,property_use.eq.500,property_use.eq.082,property_use.eq.096');
        } else if (filters.propertyType === 'Tax Deed Sales') {
          // Properties with tax certificates or upcoming auctions
          query = query.eq('has_tax_certificates', true);
        }
      }
      
      // NO COUNTY RESTRICTION - search all Florida
      // Remove the automatic BROWARD filter
      
      // Pagination
      const startRange = (currentPage - 1) * pageSize;
      const endRange = startRange + pageSize - 1;
      query = query.range(startRange, endRange);
      
      // Order by parcel_id for consistency
      query = query.order('parcel_id', { ascending: true });
      
      // Execute query
      const { data, error, count } = await query;
      
      if (error) {
        console.error('Query error:', error);
        setError(`Database error: ${error.message}`);
        setProperties([]);
        setTotalResults(0);
        return;
      }
      
      // Set results
      setProperties(data || []);
      setTotalResults(count || 0);
      setError(null);

      // Calculate statistics if data exists
      if (data && data.length > 0) {
        const values = data.map(p => p.just_value || p.taxable_value || 0);
        const avgValue = values.reduce((a, b) => a + b, 0) / values.length;
        const totalValue = values.reduce((a, b) => a + b, 0);
        
        setStats({
          avgValue,
          totalValue,
          recentSales: data.filter(p => p.sale_date).length
        });
      }

    } catch (err) {
      console.error('Error fetching properties:', err);
      setError('Failed to load properties. Please check your Supabase configuration.');
      setProperties([]);
    } finally {
      setLoading(false);
    }
  }, [filters, searchQuery, currentPage, pageSize]);

  // Initial load
  useEffect(() => {
    fetchProperties();
  }, []);

  // Refetch when filters change
  useEffect(() => {
    fetchProperties();
  }, [filters.propertyType, filters.city, filters.minPrice, filters.maxPrice, filters.hasForeclosure, filters.hasTaxDeed, filters.hasTaxLien, currentPage, pageSize, searchQuery]);

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchProperties();
  };

  // Handle filter change
  const handleFilterChange = (key: string, value: string) => {
    // Convert 'all' back to empty string for filter logic
    const filterValue = value === 'all' ? '' : value;
    setFilters(prev => ({ ...prev, [key]: filterValue }));
    setCurrentPage(1);
  };

  // Toggle property selection
  const togglePropertySelection = (parcelId: string) => {
    setSelectedProperties(prev => {
      const newSet = new Set(prev);
      if (newSet.has(parcelId)) {
        newSet.delete(parcelId);
      } else {
        newSet.add(parcelId);
      }
      return newSet;
    });
  };

  // Select all on current page
  const selectAllOnPage = () => {
    const pageIds = properties.map(p => p.parcel_id);
    setSelectedProperties(prev => {
      const newSet = new Set(prev);
      pageIds.forEach(id => newSet.add(id));
      return newSet;
    });
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedProperties(new Set());
  };

  // Select all properties from all pages
  const selectAllProperties = () => {
    if (selectedProperties.size === totalResults && totalResults > 0) {
      // If all are selected, unselect all
      clearSelection();
    } else {
      // Select all current properties
      const allIds = new Set<string>();
      
      // Add all fetched properties
      properties.forEach(prop => {
        allIds.add(prop.parcel_id);
      });
      
      setSelectedProperties(allIds);
    }
  };

  // Check if all properties are selected
  const isAllPropertiesSelected = selectedProperties.size > 0 && selectedProperties.size === totalResults;

  // Check if all current page properties are selected
  const isCurrentPageSelected = properties.length > 0 && 
    properties.every(p => selectedProperties.has(p.parcel_id));

  // Export selected properties
  const exportSelected = () => {
    const selected = properties.filter(p => selectedProperties.has(p.parcel_id));
    const csv = convertToCSV(selected);
    downloadCSV(csv, `broward_properties_${Date.now()}.csv`);
  };

  // Convert to CSV
  const convertToCSV = (data: FloridaParcel[]) => {
    const headers = ['Parcel ID', 'Address', 'City', 'Owner', 'Value', 'Year Built', 'Sq Ft'];
    const rows = data.map(p => [
      p.parcel_id,
      p.phy_addr1 || '',
      p.phy_city || '',
      p.owner_name || '',
      p.taxable_value || '',
      p.year_built || '',
      p.total_living_area || ''
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  };

  // Download CSV
  const downloadCSV = (csv: string, filename: string) => {
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  };

  // Popular Broward cities
  const browardCities = [
    'Fort Lauderdale', 'Hollywood', 'Pompano Beach', 'Coral Springs',
    'Davie', 'Plantation', 'Sunrise', 'Weston', 'Deerfield Beach',
    'Coconut Creek', 'Pembroke Pines', 'Miramar'
  ];

  // Usage Code Options (Florida DOR Codes)
  const usageCodeOptions = {
    residential: [
      { code: '001', description: 'Single Family' },
      { code: '002', description: 'Mobile Homes' },
      { code: '003', description: 'Multi-Family (10+ units)' },
      { code: '004', description: 'Condominiums' },
      { code: '005', description: 'Cooperatives' },
      { code: '006', description: 'Retirement Homes' },
      { code: '007', description: 'Misc Residential' },
      { code: '008', description: 'Multi-Family (2-9 units)' },
      { code: '009', description: 'Undefined Residential' }
    ],
    commercial: [
      { code: '100', description: 'Vacant Commercial' },
      { code: '101', description: 'Stores' },
      { code: '102', description: 'Mixed Use' },
      { code: '103', description: 'Department Stores' },
      { code: '104', description: 'Supermarkets' },
      { code: '105', description: 'Regional Shopping' },
      { code: '106', description: 'Community Shopping' },
      { code: '107', description: 'Office Buildings' },
      { code: '108', description: 'Professional Buildings' },
      { code: '109', description: 'Airports' },
      { code: '110', description: 'Hotels/Motels' },
      { code: '111', description: 'Banks' },
      { code: '112', description: 'Parking Lots' },
      { code: '113', description: 'Automobile Sales' },
      { code: '114', description: 'Service Stations' },
      { code: '115', description: 'Auto Repair' },
      { code: '116', description: 'Restaurants' },
      { code: '117', description: 'Nightclubs/Bars' },
      { code: '118', description: 'Bowling Alleys' },
      { code: '119', description: 'Theaters' },
      { code: '120', description: 'Medical Buildings' },
      { code: '121', description: 'Veterinary Clinics' },
      { code: '122', description: 'Hospitals' },
      { code: '123', description: 'Nursing Homes' },
      { code: '124', description: 'Clinics' }
    ],
    industrial: [
      { code: '400', description: 'Vacant Industrial' },
      { code: '401', description: 'Light Manufacturing' },
      { code: '402', description: 'Heavy Manufacturing' },
      { code: '403', description: 'Lumber Yards' },
      { code: '404', description: 'Packing Plants' },
      { code: '405', description: 'Canneries' },
      { code: '410', description: 'Warehouses' },
      { code: '411', description: 'Distribution' },
      { code: '412', description: 'Terminals' },
      { code: '413', description: 'Mini-Warehouses' },
      { code: '420', description: 'Industrial Park' },
      { code: '421', description: 'Industrial Condos' }
    ]
  };

  // Get sub-usage codes based on main usage code
  const getSubUsageCodes = (mainCode: string) => {
    const subCodes = [];
    // Extract just the code part if it includes description
    const code = mainCode.split(' - ')[0];
    
    if (code.startsWith('00')) {
      // Residential sub-codes
      subCodes.push(
        { code: '00', description: 'Standard/Regular' },
        { code: '01', description: 'Waterfront' },
        { code: '02', description: 'Golf Course' },
        { code: '03', description: 'High-Rise' },
        { code: '04', description: 'Gated Community' },
        { code: '05', description: 'Historic' }
      );
    } else if (code.startsWith('1')) {
      // Commercial sub-codes
      subCodes.push(
        { code: '00', description: 'Standard' },
        { code: '01', description: 'Prime Location' },
        { code: '02', description: 'Secondary Location' },
        { code: '03', description: 'Mall/Shopping Center' },
        { code: '04', description: 'Stand-alone' },
        { code: '05', description: 'Mixed Use' }
      );
    } else if (code.startsWith('4')) {
      // Industrial sub-codes
      subCodes.push(
        { code: '00', description: 'General Purpose' },
        { code: '01', description: 'Flex Space' },
        { code: '02', description: 'Research & Development' },
        { code: '03', description: 'Cold Storage' },
        { code: '04', description: 'Distribution Center' }
      );
    }
    
    return subCodes;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Executive Header */}
      <div className="executive-header text-white">
        <div className="px-8 py-12">
          <div className="max-w-7xl mx-auto">
            <div className="animate-elegant">
              <h1 className="text-3xl elegant-heading text-white mb-2 gold-accent">
                Broward County Properties
              </h1>
              <p className="text-lg font-light opacity-90">
                Search {totalResults.toLocaleString()} properties from Florida Revenue data
              </p>
            </div>
            
            <div className="flex items-center justify-between mt-8">
              <div className="flex items-center space-x-4">
                <span className="badge-elegant badge-gold">
                  Advanced Search
                </span>
                <span className="text-sm font-light opacity-75">
                  {totalResults > 0 && `${totalResults.toLocaleString()} properties available`}
                </span>
              </div>
              
              <div className="flex space-x-3">
                <button 
                  className="btn-outline-executive text-white border-white hover:bg-white hover:text-navy"
                  onClick={() => setViewMode('map')}
                >
                  <Map className="w-4 h-4 inline mr-2" />
                  <span>Map View</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Container */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Elegant Tabs for Property Types */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex rounded-lg p-1" style={{background: 'linear-gradient(135deg, #f8f9fa 0%, #fff 100%)', boxShadow: '0 2px 10px rgba(0,0,0,0.1)'}}>
            <button
              onClick={() => {
                setFilters(prev => ({ ...prev, propertyType: 'Residential' }));
                setShowAdvancedFilters(false);
                setCurrentPage(1);
              }}
              className={`px-6 py-3 rounded-lg transition-all duration-300 flex items-center space-x-2 ${
                filters.propertyType === 'Residential' 
                  ? 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white shadow-lg' 
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
              style={filters.propertyType === 'Residential' ? {background: 'linear-gradient(135deg, #d4af37 0%, #b8941f 100%)'} : {}}
            >
              <Home className="w-4 h-4" />
              <span>Residential</span>
            </button>
            <button
              onClick={() => {
                setFilters(prev => ({ ...prev, propertyType: 'Commercial' }));
                setShowAdvancedFilters(false);
                setCurrentPage(1);
              }}
              className={`px-6 py-3 rounded-lg transition-all duration-300 flex items-center space-x-2 ${
                filters.propertyType === 'Commercial' 
                  ? 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white shadow-lg' 
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
              style={filters.propertyType === 'Commercial' ? {background: 'linear-gradient(135deg, #d4af37 0%, #b8941f 100%)'} : {}}
            >
              <Building className="w-4 h-4" />
              <span>Commercial</span>
            </button>
            <button
              onClick={() => {
                setFilters(prev => ({ ...prev, propertyType: 'Industrial' }));
                setShowAdvancedFilters(false);
                setCurrentPage(1);
              }}
              className={`px-6 py-3 rounded-lg transition-all duration-300 flex items-center space-x-2 ${
                filters.propertyType === 'Industrial' 
                  ? 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white shadow-lg' 
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
              style={filters.propertyType === 'Industrial' ? {background: 'linear-gradient(135deg, #d4af37 0%, #b8941f 100%)'} : {}}
            >
              <Building className="w-4 h-4" />
              <span>Industrial</span>
            </button>
            <button
              onClick={() => {
                setFilters(prev => ({ ...prev, propertyType: '' }));
                setShowAdvancedFilters(false);
                setCurrentPage(1);
              }}
              className={`px-6 py-3 rounded-lg transition-all duration-300 flex items-center space-x-2 ${
                !filters.propertyType && !showAdvancedFilters
                  ? 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white shadow-lg' 
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
              style={!filters.propertyType && !showAdvancedFilters ? {background: 'linear-gradient(135deg, #d4af37 0%, #b8941f 100%)'} : {}}
            >
              <Grid3X3 className="w-4 h-4" />
              <span>All Properties</span>
            </button>
            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className={`px-6 py-3 rounded-lg transition-all duration-300 flex items-center space-x-2 ${
                showAdvancedFilters 
                  ? 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white shadow-lg' 
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
              style={showAdvancedFilters ? {background: 'linear-gradient(135deg, #d4af37 0%, #b8941f 100%)'} : {}}
            >
              <SlidersHorizontal className="w-4 h-4" />
              <span>Advanced</span>
            </button>
          </div>
        </div>

        {/* Search Bar - Elegant Design */}
        <div className="elegant-card hover-lift animate-in mb-6">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent flex items-center">
              <Search className="w-5 h-5 mr-2" style={{color: '#2c3e50'}} />
              {showAdvancedFilters ? 'Advanced Property Search' : `Search ${filters.propertyType === '001' ? 'Residential' : filters.propertyType === '200' ? 'Commercial' : filters.propertyType === '400' ? 'Industrial' : 'All'} Properties`}
            </h3>
            <p className="text-sm mt-3" style={{ color: '#7f8c8d' }}>
              {showAdvancedFilters 
                ? 'Find properties using comprehensive search criteria' 
                : `Quick search for ${filters.propertyType === '001' ? 'residential' : filters.propertyType === '200' ? 'commercial' : filters.propertyType === '400' ? 'industrial' : 'all'} properties in Broward County`}
            </p>
          </div>
          <div className="p-8">
            {/* Property Autocomplete for instant results */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Quick Property Search</h3>
              <PropertyAutocomplete
                placeholder="Start typing an address, city, owner name, or parcel ID..."
                showFullResults={true}
                onSelect={(property) => {
                  // Navigate to property detail
                  window.location.href = `/property/${property.parcel_id}`;
                }}
                className="w-full"
              />
            </div>
            
            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">or use AI search</span>
              </div>
            </div>
            
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="flex space-x-4">
                <div className="flex-1">
                  <AISearchBar 
                    onSearch={(query, aiResults) => {
                      setSearchQuery(query);
                      if (aiResults) {
                        console.log('AI Search Results:', aiResults);
                      }
                    }}
                  />
                </div>
                <Button 
                  type="submit" 
                  className="h-14 px-8 hover-lift"
                  disabled={loading}
                  style={{background: '#d4af37', borderColor: '#d4af37'}}
                >
                  {loading ? <RefreshCw className="w-5 h-5 animate-spin mr-2" /> : <Search className="w-5 h-5 mr-2" />}
                  Search
                </Button>
              </div>
            </form>

            {/* Quick Filters - Elegant Design */}
            <div className="mt-6 flex flex-wrap gap-4 items-center p-4 rounded-lg" style={{background: 'linear-gradient(135deg, #f8f9fa 0%, #fff 100%)'}}>
              <Select value={filters.city || 'all'} onValueChange={(v) => handleFilterChange('city', v)}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select City" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Cities</SelectItem>
                  {browardCities.map(city => (
                    <SelectItem key={city} value={city.toUpperCase()}>
                      {city}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={filters.propertyType || 'all'} onValueChange={(v) => handleFilterChange('propertyType', v)}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Property Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="001">Residential</SelectItem>
                  <SelectItem value="200">Commercial</SelectItem>
                  <SelectItem value="400">Industrial</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              >
                <SlidersHorizontal className="mr-2 h-4 w-4" />
                Advanced Filters
              </Button>
            </div>

            {/* Advanced Filters - Comprehensive Options */}
            {showAdvancedFilters && (
              <div className="border-t-2 pt-6 mt-6" style={{borderColor: '#d4af37'}}>
                {/* Property Value & Year Filters */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Value</label>
                    <Input
                      placeholder="$100,000"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.minPrice}
                      onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Value</label>
                    <Input
                      placeholder="$1,000,000"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.maxPrice}
                      onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Year Built</label>
                    <Input
                      placeholder="1990"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.minYear}
                      onChange={(e) => handleFilterChange('minYear', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Year Built</label>
                    <Input
                      placeholder="2024"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.maxYear}
                      onChange={(e) => handleFilterChange('maxYear', e.target.value)}
                    />
                  </div>
                </div>
                
                {/* Square Footage & Bed/Bath Filters */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Living Area (SqFt)</label>
                    <Input
                      placeholder="1000"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.minSqFt}
                      onChange={(e) => handleFilterChange('minSqFt', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Living Area (SqFt)</label>
                    <Input
                      placeholder="5000"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.maxSqFt}
                      onChange={(e) => handleFilterChange('maxSqFt', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Bedrooms</label>
                    <Input
                      placeholder="2"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.minBeds}
                      onChange={(e) => handleFilterChange('minBeds', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Bathrooms</label>
                    <Input
                      placeholder="1"
                      type="number"
                      step="0.5"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.minBaths}
                      onChange={(e) => handleFilterChange('minBaths', e.target.value)}
                    />
                  </div>
                </div>

                {/* Lot Size and Building Size Filters */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Lot Size (SqFt)</label>
                    <Input
                      placeholder="5000"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.minLotSize}
                      onChange={(e) => handleFilterChange('minLotSize', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Lot Size (SqFt)</label>
                    <Input
                      placeholder="20000"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.maxLotSize}
                      onChange={(e) => handleFilterChange('maxLotSize', e.target.value)}
                    />
                  </div>
                </div>

                {/* Sales History Filters */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Sale Price</label>
                    <Input
                      placeholder="$100,000"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.minSalePrice}
                      onChange={(e) => handleFilterChange('minSalePrice', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Sale Price</label>
                    <Input
                      placeholder="$500,000"
                      type="number"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.maxSalePrice}
                      onChange={(e) => handleFilterChange('maxSalePrice', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Sale Date From</label>
                    <Input
                      type="date"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.minSaleDate}
                      onChange={(e) => handleFilterChange('minSaleDate', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Sale Date To</label>
                    <Input
                      type="date"
                      className="h-12 rounded-lg"
                      style={{borderColor: '#ecf0f1'}}
                      value={filters.maxSaleDate}
                      onChange={(e) => handleFilterChange('maxSaleDate', e.target.value)}
                    />
                  </div>
                </div>

                {/* Usage Code Filters with Autocomplete */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                  <div className="relative space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Usage Code (DOR Code)</label>
                    <div className="relative">
                      <Input
                        placeholder="e.g., 001 for Single Family, 002 for Condo"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1', fontFamily: 'Georgia, serif'}}
                        value={filters.usageCode}
                        onChange={(e) => handleFilterChange('usageCode', e.target.value)}
                        onFocus={() => setShowUsageCodeDropdown(true)}
                        onBlur={() => setTimeout(() => setShowUsageCodeDropdown(false), 200)}
                      />
                      {showUsageCodeDropdown && (
                        <div className="absolute z-50 w-full mt-1 bg-white border rounded-lg shadow-xl max-h-64 overflow-auto" 
                             style={{borderColor: '#ecf0f1', top: '100%'}}>
                          {/* Common Residential Codes */}
                          <div className="p-2 bg-gray-50 border-b" style={{borderColor: '#ecf0f1'}}>
                            <p className="text-xs font-semibold uppercase tracking-wider" style={{color: '#95a5a6'}}>Residential (000-099)</p>
                          </div>
                          {usageCodeOptions.residential.map(code => (
                            <div
                              key={code.code}
                              className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 transition-all"
                              style={{borderColor: '#ecf0f1'}}
                              onMouseDown={(e) => e.preventDefault()}
                              onClick={() => {
                                handleFilterChange('usageCode', `${code.code} - ${code.description}`);
                                handleFilterChange('subUsageCode', ''); // Reset sub-usage when main changes
                                setShowUsageCodeDropdown(false);
                                fetchProperties();
                              }}
                            >
                              <div className="flex justify-between items-center">
                                <span className="font-medium" style={{color: '#2c3e50', fontFamily: 'Georgia, serif'}}>
                                  {code.code}
                                </span>
                                <span className="text-sm" style={{color: '#7f8c8d'}}>
                                  {code.description}
                                </span>
                              </div>
                            </div>
                          ))}
                          
                          {/* Commercial Codes */}
                          <div className="p-2 bg-gray-50 border-b border-t" style={{borderColor: '#ecf0f1'}}>
                            <p className="text-xs font-semibold uppercase tracking-wider" style={{color: '#95a5a6'}}>Commercial (100-399)</p>
                          </div>
                          {usageCodeOptions.commercial.map(code => (
                            <div
                              key={code.code}
                              className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 transition-all"
                              style={{borderColor: '#ecf0f1'}}
                              onMouseDown={(e) => e.preventDefault()}
                              onClick={() => {
                                handleFilterChange('usageCode', `${code.code} - ${code.description}`);
                                handleFilterChange('subUsageCode', '');
                                setShowUsageCodeDropdown(false);
                                fetchProperties();
                              }}
                            >
                              <div className="flex justify-between items-center">
                                <span className="font-medium" style={{color: '#2c3e50', fontFamily: 'Georgia, serif'}}>
                                  {code.code}
                                </span>
                                <span className="text-sm" style={{color: '#7f8c8d'}}>
                                  {code.description}
                                </span>
                              </div>
                            </div>
                          ))}
                          
                          {/* Industrial Codes */}
                          <div className="p-2 bg-gray-50 border-b border-t" style={{borderColor: '#ecf0f1'}}>
                            <p className="text-xs font-semibold uppercase tracking-wider" style={{color: '#95a5a6'}}>Industrial (400-499)</p>
                          </div>
                          {usageCodeOptions.industrial.map(code => (
                            <div
                              key={code.code}
                              className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 transition-all"
                              style={{borderColor: '#ecf0f1'}}
                              onMouseDown={(e) => e.preventDefault()}
                              onClick={() => {
                                handleFilterChange('usageCode', `${code.code} - ${code.description}`);
                                handleFilterChange('subUsageCode', '');
                                setShowUsageCodeDropdown(false);
                                fetchProperties();
                              }}
                            >
                              <div className="flex justify-between items-center">
                                <span className="font-medium" style={{color: '#2c3e50', fontFamily: 'Georgia, serif'}}>
                                  {code.code}
                                </span>
                                <span className="text-sm" style={{color: '#7f8c8d'}}>
                                  {code.description}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <p className="text-xs" style={{color: '#95a5a6'}}>Click to see all available codes or type to filter</p>
                  </div>
                  
                  <div className="relative space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Sub-Usage Code</label>
                    <div className="relative">
                      <Input
                        placeholder={filters.usageCode ? "Click to see available sub-codes" : "Select usage code first"}
                        className="h-12 rounded-lg"
                        style={{
                          borderColor: '#ecf0f1', 
                          fontFamily: 'Georgia, serif',
                          opacity: filters.usageCode ? 1 : 0.5
                        }}
                        value={filters.subUsageCode}
                        onChange={(e) => handleFilterChange('subUsageCode', e.target.value)}
                        onFocus={() => filters.usageCode && setShowSubUsageCodeDropdown(true)}
                        onBlur={() => setTimeout(() => setShowSubUsageCodeDropdown(false), 200)}
                        disabled={!filters.usageCode}
                      />
                      {showSubUsageCodeDropdown && filters.usageCode && (
                        <div className="absolute z-50 w-full mt-1 bg-white border rounded-lg shadow-xl max-h-64 overflow-auto" 
                             style={{borderColor: '#ecf0f1', top: '100%'}}>
                          <div className="p-2 bg-gray-50 border-b" style={{borderColor: '#ecf0f1'}}>
                            <p className="text-xs font-semibold uppercase tracking-wider" style={{color: '#95a5a6'}}>
                              Sub-codes for {filters.usageCode.split(' - ')[0]}
                            </p>
                          </div>
                          
                          {/* Option to select ALL sub-codes */}
                          <div
                            className="px-4 py-3 hover:bg-yellow-50 cursor-pointer border-b transition-all"
                            style={{borderColor: '#ecf0f1', background: 'rgba(212, 175, 55, 0.05)'}}
                            onMouseDown={(e) => e.preventDefault()}
                            onClick={() => {
                              handleFilterChange('subUsageCode', 'ALL - All Sub-categories');
                              setShowSubUsageCodeDropdown(false);
                              fetchProperties();
                            }}
                          >
                            <div className="flex justify-between items-center">
                              <span className="font-medium" style={{color: '#d4af37', fontFamily: 'Georgia, serif'}}>
                                ALL
                              </span>
                              <span className="text-sm" style={{color: '#d4af37'}}>
                                All sub-categories for {filters.usageCode.split(' - ')[0]}
                              </span>
                            </div>
                          </div>
                          
                          {getSubUsageCodes(filters.usageCode).map(subCode => (
                            <div
                              key={subCode.code}
                              className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 transition-all"
                              style={{borderColor: '#ecf0f1'}}
                              onMouseDown={(e) => e.preventDefault()}
                              onClick={() => {
                                handleFilterChange('subUsageCode', `${subCode.code} - ${subCode.description}`);
                                setShowSubUsageCodeDropdown(false);
                                fetchProperties();
                              }}
                            >
                              <div className="flex justify-between items-center">
                                <span className="font-medium" style={{color: '#2c3e50', fontFamily: 'Georgia, serif'}}>
                                  {subCode.code}
                                </span>
                                <span className="text-sm" style={{color: '#7f8c8d'}}>
                                  {subCode.description}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <p className="text-xs" style={{color: '#95a5a6'}}>
                      {filters.usageCode ? 'Leave empty to include all sub-categories' : 'Select a usage code first'}
                    </p>
                  </div>
                </div>

                {/* Quick Date Range Buttons */}
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <p className="text-xs uppercase tracking-wider font-medium mb-3" style={{color: '#95a5a6'}}>Quick Date Ranges</p>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="hover-lift"
                      style={{borderColor: '#ecf0f1'}}
                      onClick={() => {
                        const today = new Date();
                        const lastMonth = new Date(today);
                        lastMonth.setMonth(today.getMonth() - 1);
                        handleFilterChange('minSaleDate', lastMonth.toISOString().split('T')[0]);
                        handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                      }}
                    >
                      Last 30 Days
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="hover-lift"
                      style={{borderColor: '#ecf0f1'}}
                      onClick={() => {
                        const today = new Date();
                        const lastQuarter = new Date(today);
                        lastQuarter.setMonth(today.getMonth() - 3);
                        handleFilterChange('minSaleDate', lastQuarter.toISOString().split('T')[0]);
                        handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                      }}
                    >
                      Last 90 Days
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="hover-lift"
                      style={{borderColor: '#ecf0f1'}}
                      onClick={() => {
                        const today = new Date();
                        const lastSix = new Date(today);
                        lastSix.setMonth(today.getMonth() - 6);
                        handleFilterChange('minSaleDate', lastSix.toISOString().split('T')[0]);
                        handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                      }}
                    >
                      Last 6 Months
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="hover-lift"
                      style={{borderColor: '#ecf0f1'}}
                      onClick={() => {
                        const today = new Date();
                        const lastYear = new Date(today);
                        lastYear.setFullYear(today.getFullYear() - 1);
                        handleFilterChange('minSaleDate', lastYear.toISOString().split('T')[0]);
                        handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                      }}
                    >
                      Last Year
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="hover-lift"
                      style={{borderColor: '#ecf0f1'}}
                      onClick={() => {
                        const today = new Date();
                        const yearStart = new Date(today.getFullYear(), 0, 1);
                        handleFilterChange('minSaleDate', yearStart.toISOString().split('T')[0]);
                        handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                      }}
                    >
                      Year to Date
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="hover-lift"
                      style={{borderColor: '#ecf0f1'}}
                      onClick={() => {
                        const today = new Date();
                        const fiveYears = new Date(today);
                        fiveYears.setFullYear(today.getFullYear() - 5);
                        handleFilterChange('minSaleDate', fiveYears.toISOString().split('T')[0]);
                        handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                      }}
                    >
                      Last 5 Years
                    </Button>
                  </div>
                </div>

                {/* Special Property Status Filters */}
                <div className="mt-6 p-4 rounded-lg" style={{background: 'linear-gradient(135deg, #f8f9fa 0%, #fff 100%)'}}>
                  <p className="text-xs uppercase tracking-wider font-medium mb-4" style={{color: '#95a5a6'}}>Property Status</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-gray-50 transition-all cursor-pointer" 
                         style={{borderColor: filters.hasForeclosure ? '#d4af37' : '#ecf0f1', 
                                background: filters.hasForeclosure ? 'rgba(212, 175, 55, 0.1)' : 'white'}}
                         onClick={() => setFilters(prev => ({ ...prev, hasForeclosure: !prev.hasForeclosure }))}>
                      <input
                        type="checkbox"
                        checked={filters.hasForeclosure}
                        onChange={(e) => setFilters(prev => ({ ...prev, hasForeclosure: e.target.checked }))}
                        className="w-4 h-4 rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                      />
                      <div>
                        <span className="text-sm font-medium" style={{color: '#2c3e50'}}>
                          Foreclosure Properties
                        </span>
                        <p className="text-xs" style={{color: '#7f8c8d'}}>
                          Properties with active or past foreclosure proceedings
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-gray-50 transition-all cursor-pointer" 
                         style={{borderColor: filters.hasTaxDeed ? '#d4af37' : '#ecf0f1', 
                                background: filters.hasTaxDeed ? 'rgba(212, 175, 55, 0.1)' : 'white'}}
                         onClick={() => setFilters(prev => ({ ...prev, hasTaxDeed: !prev.hasTaxDeed }))}>
                      <input
                        type="checkbox"
                        checked={filters.hasTaxDeed}
                        onChange={(e) => setFilters(prev => ({ ...prev, hasTaxDeed: e.target.checked }))}
                        className="w-4 h-4 rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                      />
                      <div>
                        <span className="text-sm font-medium" style={{color: '#2c3e50'}}>
                          Tax Deed Auction Items
                        </span>
                        <p className="text-xs" style={{color: '#7f8c8d'}}>
                          Properties available at upcoming or past tax deed auctions
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3 p-3 rounded-lg border hover:bg-gray-50 transition-all cursor-pointer" 
                         style={{borderColor: filters.hasTaxLien ? '#d4af37' : '#ecf0f1', 
                                background: filters.hasTaxLien ? 'rgba(212, 175, 55, 0.1)' : 'white'}}
                         onClick={() => setFilters(prev => ({ ...prev, hasTaxLien: !prev.hasTaxLien }))}>
                      <input
                        type="checkbox"
                        checked={filters.hasTaxLien}
                        onChange={(e) => setFilters(prev => ({ ...prev, hasTaxLien: e.target.checked }))}
                        className="w-4 h-4 rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                      />
                      <div>
                        <span className="text-sm font-medium" style={{color: '#2c3e50'}}>
                          Tax Lien Properties
                        </span>
                        <p className="text-xs" style={{color: '#7f8c8d'}}>
                          Properties with outstanding tax liens or certificates
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Clear and Apply Buttons */}
                <div className="flex justify-end mt-8 space-x-4">
                  <Button 
                    variant="outline" 
                    className="hover-lift h-12 px-6"
                    style={{borderColor: '#ecf0f1'}}
                    onClick={() => {
                      setFilters({
                        county: 'BROWARD',
                        city: '',
                        zipCode: '',
                        ownerName: '',
                        minPrice: '',
                        maxPrice: '',
                        propertyType: '',
                        minYear: '',
                        maxYear: '',
                        minSqFt: '',
                        maxSqFt: '',
                        minBeds: '',
                        minBaths: '',
                        minLotSize: '',
                        maxLotSize: '',
                        minSalePrice: '',
                        maxSalePrice: '',
                        minSaleDate: '',
                        maxSaleDate: '',
                        usageCode: '',
                        subUsageCode: '',
                        hasForeclosure: false,
                        hasTaxDeed: false,
                        hasTaxLien: false
                      });
                      setSearchQuery('');
                      setCurrentPage(1);
                    }}
                  >
                    <span style={{color: '#2c3e50'}}>Clear All Filters</span>
                  </Button>
                  <Button 
                    className="h-12 px-6 hover-lift"
                    style={{background: '#d4af37', borderColor: '#d4af37'}}
                    onClick={() => fetchProperties()}
                  >
                    Apply Filters
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Statistics Cards - Elegant Design */}
      <div className="max-w-7xl mx-auto px-4 mt-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="elegant-card hover-lift animate-in">
            <div className="p-4">
              <p className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Total Properties</p>
              <p className="text-2xl font-bold mt-2" style={{color: '#2c3e50'}}>{totalResults.toLocaleString()}</p>
            </div>
          </div>
          
          <div className="elegant-card hover-lift animate-in">
            <div className="p-4">
              <p className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Avg. Value</p>
              <p className="text-2xl font-bold mt-2" style={{color: '#2c3e50'}}>
                {stats.avgValue >= 1000000000 ? `$${(stats.avgValue / 1000000000).toFixed(1)}B` :
                 stats.avgValue >= 1000000 ? `$${(stats.avgValue / 1000000).toFixed(1)}M` :
                 stats.avgValue >= 1000 ? `$${(stats.avgValue / 1000).toFixed(0)}K` :
                 `$${stats.avgValue.toFixed(0)}`}
              </p>
            </div>
          </div>
          
          <div className="elegant-card hover-lift animate-in">
            <div className="p-4">
              <p className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Total Value</p>
              <p className="text-2xl font-bold mt-2" style={{color: '#2c3e50'}}>
                {stats.totalValue >= 1000000000 ? `$${(stats.totalValue / 1000000000).toFixed(1)}B` :
                 stats.totalValue >= 1000000 ? `$${(stats.totalValue / 1000000).toFixed(1)}M` :
                 stats.totalValue >= 1000 ? `$${(stats.totalValue / 1000).toFixed(0)}K` :
                 `$${stats.totalValue.toFixed(0)}`}
              </p>
            </div>
          </div>
          
          <div className="elegant-card hover-lift animate-in">
            <div className="p-4">
              <p className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Recent Sales</p>
              <p className="text-2xl font-bold mt-2" style={{color: '#2c3e50'}}>{stats.recentSales}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Results Section - Elegant Design */}
      <div className="max-w-7xl mx-auto px-4 mt-6">
        {/* Results Header - Elegant Design */}
        <div className="elegant-card hover-lift animate-in mb-6">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <h3 className="text-xl font-semibold" style={{color: '#2c3e50'}}>
                  {totalResults.toLocaleString()} Properties Found
                </h3>
                {filters.city && (
                  <div className="badge-elegant" style={{borderColor: '#3498db', color: '#3498db', background: 'rgba(52, 152, 219, 0.1)'}}>
                    <MapPin className="w-3 h-3 mr-1" />
                    {filters.city}
                  </div>
                )}
                {filters.propertyType && (
                  <div className="badge-elegant" style={{borderColor: '#9b59b6', color: '#9b59b6', background: 'rgba(155, 89, 182, 0.1)'}}>
                    <Building className="w-3 h-3 mr-1" />
                    {filters.propertyType === '001' ? 'Residential' : filters.propertyType === '200' ? 'Commercial' : filters.propertyType === '400' ? 'Industrial' : filters.propertyType}
                  </div>
                )}
                {filters.hasForeclosure && (
                  <div className="badge-elegant" style={{borderColor: '#e74c3c', color: '#e74c3c', background: 'rgba(231, 76, 60, 0.1)'}}>
                    <AlertCircle className="w-3 h-3 mr-1" />
                    Foreclosures
                  </div>
                )}
                {filters.hasTaxDeed && (
                  <div className="badge-elegant" style={{borderColor: '#f39c12', color: '#f39c12', background: 'rgba(243, 156, 18, 0.1)'}}>
                    <TrendingUp className="w-3 h-3 mr-1" />
                    Tax Deed Auctions
                  </div>
                )}
                {filters.hasTaxLien && (
                  <div className="badge-elegant" style={{borderColor: '#e67e22', color: '#e67e22', background: 'rgba(230, 126, 34, 0.1)'}}>
                    <Database className="w-3 h-3 mr-1" />
                    Tax Liens
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-3">
                <div className="flex border rounded-lg" style={{borderColor: '#ecf0f1'}}>
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'ghost'}
                    size="sm"
                    className="hover-lift"
                    style={viewMode === 'grid' ? {background: '#d4af37', borderColor: '#d4af37'} : {}}
                    onClick={() => setViewMode('grid')}
                  >
                    <Grid3X3 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'ghost'}
                    size="sm"
                    className="hover-lift"
                    style={viewMode === 'list' ? {background: '#d4af37', borderColor: '#d4af37'} : {}}
                    onClick={() => setViewMode('list')}
                  >
                    <List className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'map' ? 'default' : 'ghost'}
                    size="sm"
                    className="hover-lift"
                    style={viewMode === 'map' ? {background: '#d4af37', borderColor: '#d4af37'} : {}}
                    onClick={() => setViewMode('map')}
                  >
                    <Map className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Selection Controls - Consistent Design */}
            <div className="flex items-center space-x-3">
              {/* Select All Properties Button */}
              <Button
                variant="outline"
                size="sm"
                className="hover-lift flex items-center"
                style={{
                  borderColor: isAllPropertiesSelected ? '#d4af37' : '#ecf0f1',
                  background: isAllPropertiesSelected ? 'rgba(212, 175, 55, 0.1)' : 'white',
                  transition: 'all 0.3s ease'
                }}
                onClick={selectAllProperties}
              >
                {isAllPropertiesSelected ? (
                  <CheckSquare className="w-4 h-4 mr-2" style={{color: '#d4af37'}} />
                ) : (
                  <Square className="w-4 h-4 mr-2" style={{color: '#2c3e50'}} />
                )}
                <span style={{color: '#2c3e50', fontWeight: isAllPropertiesSelected ? '500' : '400'}}>
                  {isAllPropertiesSelected ? 'Unselect All Properties' : 'Select All Properties'}
                  {totalResults > 0 && ` (${totalResults})`}
                </span>
              </Button>
              
              {/* Select Current Page Button */}
              <Button
                variant="outline"
                size="sm"
                className="hover-lift flex items-center"
                style={{
                  borderColor: isCurrentPageSelected ? '#d4af37' : '#ecf0f1',
                  background: isCurrentPageSelected ? 'rgba(212, 175, 55, 0.1)' : 'white',
                  transition: 'all 0.3s ease'
                }}
                onClick={() => {
                  if (isCurrentPageSelected) {
                    // Unselect all from current page
                    setSelectedProperties(prev => {
                      const newSet = new Set(prev);
                      properties.forEach(p => newSet.delete(p.parcel_id));
                      return newSet;
                    });
                  } else {
                    // Select all from current page
                    setSelectedProperties(prev => {
                      const newSet = new Set(prev);
                      properties.forEach(p => newSet.add(p.parcel_id));
                      return newSet;
                    });
                  }
                }}
              >
                {isCurrentPageSelected ? (
                  <CheckSquare className="w-4 h-4 mr-2" style={{color: '#d4af37'}} />
                ) : (
                  <Square className="w-4 h-4 mr-2" style={{color: '#2c3e50'}} />
                )}
                <span style={{color: '#2c3e50', fontWeight: isCurrentPageSelected ? '500' : '400'}}>
                  {isCurrentPageSelected ? 'Unselect Page' : 'Select Page'}
                  {properties.length > 0 && ` (${properties.length})`}
                </span>
              </Button>
              
              {selectedProperties.size > 0 && (
                <>
                  <div className="badge-elegant" style={{background: '#d4af37', color: 'white'}}>
                    {selectedProperties.size} selected
                  </div>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="hover-lift"
                    style={{borderColor: '#ecf0f1'}}
                    onClick={clearSelection}
                  >
                    <span style={{color: '#2c3e50'}}>Clear</span>
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <Card className="mb-4 border-red-200 bg-red-50">
            <CardContent className="flex items-center p-4">
              <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
              <p className="text-red-800">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Properties Grid/List/Map */}
        {viewMode === 'map' ? (
          <Card className="h-[600px]">
            <PropertyMap 
              properties={properties.filter(p => selectedProperties.size === 0 || selectedProperties.has(p.parcel_id))}
            />
          </Card>
        ) : (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-4'}>
            {properties.map((property) => (
              <MiniPropertyCard
                key={property.parcel_id}
                parcelId={property.parcel_id}
                data={{
                  phy_addr1: property.phy_addr1 || property.address || 'Address Not Available',
                  phy_city: property.phy_city || property.city || 'City Not Available',
                  phy_zipcd: property.phy_zipcd || property.zipcode || '',
                  own_name: property.owner_name || 'Owner Not Available',
                  jv: property.assessed_value || property.taxable_value || 0, // Just (appraised) value
                  tv_sd: property.taxable_value || 0, // Taxable value
                  lnd_val: property.land_value || 0, // Land value
                  tot_lvg_area: property.total_living_area || 0, // Building square feet
                  lnd_sqfoot: property.lot_size || 0, // Land square feet
                  act_yr_blt: property.year_built || 0, // Year built
                  dor_uc: property.property_use || property.usage_code || '', // Department of Revenue Use Code
                  sale_prc1: property.sale_price || 0, // Last sale price
                  sale_yr1: property.sale_date ? new Date(property.sale_date).getFullYear() : 0, // Last sale year
                  property_type: property.property_use_desc || property.property_type || '', // Property type description
                }}
                onClick={() => {
                  // Navigate to property profile page
                  window.location.href = `/property/${property.parcel_id}`;
                }}
                variant={viewMode === 'list' ? 'list' : 'grid'}
                showQuickActions={true}
                isWatched={false}
                hasNotes={false}
                priority={undefined}
                isSelected={selectedProperties.has(property.parcel_id)}
                onToggleSelection={() => togglePropertySelection(property.parcel_id)}
              />
            ))}
          </div>
        )}

        {/* Elegant Pagination Footer */}
        {totalResults > pageSize && (
          <div className="elegant-card hover-lift animate-in mt-8">
            <div className="p-6">
              <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
                {/* Page Size Selector */}
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium" style={{color: '#2c3e50'}}>Show per page:</span>
                  <Select 
                    value={pageSize.toString()} 
                    onValueChange={(v) => setPageSize(parseInt(v))}
                  >
                    <SelectTrigger className="w-20 h-9 rounded-lg" style={{borderColor: '#ecf0f1'}}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10</SelectItem>
                      <SelectItem value="20">20</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                    </SelectContent>
                  </Select>
                  <span className="text-sm" style={{color: '#7f8c8d'}}>
                    Showing {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalResults)} of {totalResults.toLocaleString()} properties
                  </span>
                </div>

                {/* Page Navigation */}
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    disabled={currentPage === 1}
                    className="hover-lift h-9 px-4"
                    style={{borderColor: '#ecf0f1'}}
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  >
                    <span style={{color: '#2c3e50'}}>Previous</span>
                  </Button>
                  
                  <div className="flex items-center space-x-1">
                    {Array.from({ length: Math.min(5, Math.ceil(totalResults / pageSize)) }, (_, i) => {
                      const page = i + 1;
                      return (
                        <Button
                          key={page}
                          variant={currentPage === page ? 'default' : 'outline'}
                          size="sm"
                          className="hover-lift h-9 w-9"
                          style={currentPage === page ? 
                            {background: '#d4af37', borderColor: '#d4af37', color: 'white'} : 
                            {borderColor: '#ecf0f1', color: '#2c3e50'}
                          }
                          onClick={() => setCurrentPage(page)}
                        >
                          {page}
                        </Button>
                      );
                    })}
                  </div>

                  <Button
                    variant="outline"
                    disabled={currentPage >= Math.ceil(totalResults / pageSize)}
                    className="hover-lift h-9 px-4"
                    style={{borderColor: '#ecf0f1'}}
                    onClick={() => setCurrentPage(prev => Math.min(Math.ceil(totalResults / pageSize), prev + 1))}
                  >
                    <span style={{color: '#2c3e50'}}>Next</span>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Data Source Notice */}
      <div className="container mx-auto px-4 mt-8 mb-4">
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="flex items-center p-4">
            <Database className="h-5 w-5 text-blue-600 mr-2" />
            <p className="text-sm text-blue-800">
              Data sourced from Florida Revenue Property Tax Oversight (PTO) - Updated {new Date().toLocaleDateString()}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}