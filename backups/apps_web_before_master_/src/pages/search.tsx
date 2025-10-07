import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Filter,
  MapPin,
  DollarSign,
  Home,
  Bed,
  Bath,
  Square,
  Calendar,
  TrendingUp,
  ChevronDown,
  Grid,
  List,
  Map,
  Heart,
  Share2,
  Eye,
  Building2,
  Trees,
  Car,
  Wifi,
  Wind,
  Droplets,
  Sun,
  Package,
  Zap,
  Users,
  Target,
  Shield,
  Mountain,
  FileText,
  BarChart,
  Percent,
  ArrowUp,
  Check,
  X,
  Info
} from 'lucide-react'
import { 
  PROPERTY_USE_CODES, 
  PROPERTY_CATEGORIES, 
  FIELD_DEFINITIONS,
  ZONING_CODES,
  PROPERTY_STATUS
} from '@/lib/property-types'
import { getAllUseCategories, UseIcon } from '@/lib/icons/useIcons'

// Generate diverse sample properties
const generateSampleProperties = () => {
  const properties = []
  const images = [
    'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1497366754035-f200586c6c24?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1500916434205-0c77489c4000?w=800&h=600&fit=crop'
  ]

  // Residential Properties
  properties.push({
    id: 1,
    title: 'Luxury Oceanfront Condo',
    address: '1500 Ocean Drive, Fort Lauderdale, FL 33301',
    price: 2850000,
    useCode: '04',
    type: 'Condominium',
    beds: 3,
    baths: 2,
    sqft: 2200,
    yearBuilt: 2019,
    image: images[0],
    featured: true,
    status: 'ACTIVE',
    pool: true,
    waterfront: true,
    hoa: 850
  })

  // Commercial Properties
  properties.push({
    id: 2,
    title: 'Prime Retail Shopping Center',
    address: '200 Las Olas Blvd, Fort Lauderdale, FL 33301',
    price: 8500000,
    useCode: '16',
    type: 'Community Shopping Center',
    buildingSqft: 45000,
    landSqft: 120000,
    yearBuilt: 2018,
    image: images[6],
    featured: true,
    status: 'ACTIVE',
    parkingSpaces: 180,
    tenants: 12,
    occupancyRate: 95,
    netOperatingIncome: 680000,
    capRate: 8.0,
    zoning: 'C-2'
  })

  // Industrial Properties
  properties.push({
    id: 3,
    title: 'Modern Distribution Center',
    address: '890 Industrial Way, Pompano Beach, FL 33069',
    price: 12000000,
    useCode: '48',
    type: 'Warehouse',
    buildingSqft: 85000,
    landSqft: 200000,
    yearBuilt: 2020,
    image: images[7],
    featured: false,
    status: 'ACTIVE',
    clearHeight: 32,
    dockDoors: 20,
    railAccess: true,
    power: '2000 Amps',
    zoning: 'I-2'
  })

  // Agricultural Properties
  properties.push({
    id: 4,
    title: 'Organic Farm with Citrus Grove',
    address: '5000 Griffin Road, Davie, FL 33314',
    price: 3500000,
    useCode: '54',
    type: 'Orchard/Citrus/Grove',
    acres: 40,
    image: images[9],
    featured: false,
    status: 'ACTIVE',
    irrigated: true,
    cropType: 'Citrus - Orange & Grapefruit',
    soilType: 'Sandy Loam',
    waterRights: true,
    buildings: 3,
    productivity: '1200 tons/year'
  })

  // Institutional Properties
  properties.push({
    id: 5,
    title: 'Medical Office Building',
    address: '1200 Healthcare Blvd, Coral Springs, FL 33071',
    price: 6200000,
    useCode: '73',
    type: 'Hospital/Medical',
    buildingSqft: 35000,
    landSqft: 60000,
    yearBuilt: 2017,
    image: images[8],
    featured: true,
    status: 'ACTIVE',
    parkingSpaces: 120,
    capacity: 200,
    specialUse: 'Medical/Healthcare',
    zoning: 'P'
  })

  // Vacant Land
  properties.push({
    id: 6,
    title: 'Development-Ready Commercial Land',
    address: 'University Drive, Pembroke Pines, FL 33024',
    price: 4500000,
    useCode: '10',
    type: 'Vacant Commercial',
    acres: 5.5,
    image: images[9],
    featured: false,
    status: 'ACTIVE',
    zoning: 'MU',
    utilities: 'All Available',
    roadAccess: 'Paved - 4 Lane Highway',
    topography: 'Level',
    wetlands: false,
    futureUse: 'Mixed Use Development',
    entitlements: 'Approved for 150,000 sqft'
  })

  // Office Building
  properties.push({
    id: 7,
    title: 'Class A Office Tower',
    address: '100 E Las Olas Blvd, Fort Lauderdale, FL 33301',
    price: 25000000,
    useCode: '18',
    type: 'Office Building, Multi-Story',
    buildingSqft: 120000,
    landSqft: 40000,
    yearBuilt: 2019,
    stories: 15,
    image: images[6],
    featured: true,
    status: 'ACTIVE',
    parkingSpaces: 400,
    occupancyRate: 88,
    netOperatingIncome: 2100000,
    capRate: 8.4,
    zoning: 'CBD'
  })

  // Hotel
  properties.push({
    id: 8,
    title: 'Beachfront Resort Hotel',
    address: '3000 N Ocean Blvd, Fort Lauderdale, FL 33308',
    price: 45000000,
    useCode: '39',
    type: 'Hotel/Motel',
    buildingSqft: 180000,
    landSqft: 120000,
    yearBuilt: 2016,
    image: images[1],
    featured: true,
    status: 'ACTIVE',
    capacity: 250,
    parkingSpaces: 300,
    specialUse: 'Resort Hotel - 250 Rooms',
    netOperatingIncome: 4500000,
    capRate: 10.0
  })

  // Restaurant
  properties.push({
    id: 9,
    title: 'Prime Restaurant Location',
    address: '400 Las Olas Blvd, Fort Lauderdale, FL 33301',
    price: 3200000,
    useCode: '21',
    type: 'Restaurant/Cafeteria',
    buildingSqft: 8000,
    landSqft: 15000,
    yearBuilt: 2015,
    image: images[2],
    featured: false,
    status: 'LEASE',
    parkingSpaces: 50,
    specialUse: 'Full Service Restaurant',
    zoning: 'C-2'
  })

  // Mobile Home Park
  properties.push({
    id: 10,
    title: 'Mobile Home Community',
    address: '2500 State Road 7, Margate, FL 33063',
    price: 8900000,
    useCode: '02',
    type: 'Mobile Home',
    acres: 15,
    image: images[3],
    featured: false,
    status: 'ACTIVE',
    capacity: 85,
    specialUse: 'Mobile Home Park - 85 Lots',
    netOperatingIncome: 712000,
    capRate: 8.0
  })

  return properties
}

const sampleProperties = generateSampleProperties()

export default function SearchPage() {
  const navigate = useNavigate()
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'map'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('ALL')
  const [selectedUseCode, setSelectedUseCode] = useState('')
  const [priceRange, setPriceRange] = useState({ min: 0, max: 50000000 })
  const [sortBy, setSortBy] = useState('Price: Low to High')
  const [showFilters, setShowFilters] = useState(true)
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)

  // Filter properties based on selected category and use code
  const filteredProperties = useMemo(() => {
    let filtered = [...sampleProperties]

    // Filter by category
    if (selectedCategory !== 'ALL') {
      const category = PROPERTY_CATEGORIES[selectedCategory]
      if (category) {
        filtered = filtered.filter(p => category.codes.includes(p.useCode))
      }
    }

    // Filter by specific use code
    if (selectedUseCode) {
      filtered = filtered.filter(p => p.useCode === selectedUseCode)
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(p => 
        p.title.toLowerCase().includes(query) ||
        p.address.toLowerCase().includes(query) ||
        p.type.toLowerCase().includes(query)
      )
    }

    // Filter by price
    filtered = filtered.filter(p => 
      p.price >= priceRange.min && p.price <= priceRange.max
    )

    // Sort
    if (sortBy === 'Price: Low to High') {
      filtered.sort((a, b) => a.price - b.price)
    } else if (sortBy === 'Price: High to Low') {
      filtered.sort((a, b) => b.price - a.price)
    }

    return filtered
  }, [selectedCategory, selectedUseCode, searchQuery, priceRange, sortBy])

  // Get relevant fields for selected category
  const getRelevantFields = (property: any) => {
    const category = Object.values(PROPERTY_CATEGORIES).find(cat => 
      cat.codes.includes(property.useCode)
    )
    return category?.fields || []
  }

  const PropertyCard = ({ property, index }: { property: any, index: number }) => {
    const relevantFields = getRelevantFields(property)
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: index * 0.05 }}
        className="bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all group"
      >
        {/* Image */}
        <div className="relative h-64 overflow-hidden">
          <img
            src={property.image}
            alt={property.title}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          />
          {property.featured && (
            <div className="absolute top-4 left-4 px-3 py-1 bg-yellow-500 text-white text-xs font-semibold rounded-full">
              Featured
            </div>
          )}
          <div className="absolute top-4 right-4 flex gap-2">
            <button className="p-2 bg-white/90 backdrop-blur rounded-full hover:bg-white transition-colors">
              <Heart className="w-4 h-4 text-gray-700" />
            </button>
            <button className="p-2 bg-white/90 backdrop-blur rounded-full hover:bg-white transition-colors">
              <Share2 className="w-4 h-4 text-gray-700" />
            </button>
          </div>
          <div className="absolute bottom-4 left-4 flex gap-2">
            <span className="px-3 py-1 bg-blue-600 text-white text-sm font-semibold rounded-full">
              {PROPERTY_USE_CODES[property.useCode]}
            </span>
            <span className={`px-3 py-1 text-white text-sm font-semibold rounded-full ${
              property.status === 'ACTIVE' ? 'bg-green-600' :
              property.status === 'PENDING' ? 'bg-yellow-600' :
              property.status === 'LEASE' ? 'bg-purple-600' :
              'bg-gray-600'
            }`}>
              {PROPERTY_STATUS[property.status]}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="p-5">
          <div className="mb-3">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">{property.title}</h3>
            <div className="flex items-center gap-1 text-gray-600">
              <MapPin className="w-4 h-4" />
              <span className="text-sm">{property.address}</span>
            </div>
          </div>

          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-2xl font-bold text-gray-900">
                ${property.price.toLocaleString()}
              </p>
              {property.capRate && (
                <p className="text-sm text-gray-500">
                  Cap Rate: {property.capRate}%
                </p>
              )}
            </div>
            {property.netOperatingIncome && (
              <div className="text-right">
                <p className="text-sm text-gray-500">NOI</p>
                <p className="text-lg font-semibold text-green-600">
                  ${property.netOperatingIncome.toLocaleString()}
                </p>
              </div>
            )}
          </div>

          {/* Dynamic Fields Based on Property Type */}
          <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
            {property.beds && (
              <div className="flex items-center gap-1 text-gray-600">
                <Bed className="w-4 h-4" />
                <span>{property.beds} beds</span>
              </div>
            )}
            {property.baths && (
              <div className="flex items-center gap-1 text-gray-600">
                <Bath className="w-4 h-4" />
                <span>{property.baths} baths</span>
              </div>
            )}
            {property.sqft && (
              <div className="flex items-center gap-1 text-gray-600">
                <Square className="w-4 h-4" />
                <span>{property.sqft.toLocaleString()} sqft</span>
              </div>
            )}
            {property.buildingSqft && (
              <div className="flex items-center gap-1 text-gray-600">
                <Building2 className="w-4 h-4" />
                <span>{property.buildingSqft.toLocaleString()} sqft</span>
              </div>
            )}
            {property.acres && (
              <div className="flex items-center gap-1 text-gray-600">
                <Trees className="w-4 h-4" />
                <span>{property.acres} acres</span>
              </div>
            )}
            {property.parkingSpaces && (
              <div className="flex items-center gap-1 text-gray-600">
                <Car className="w-4 h-4" />
                <span>{property.parkingSpaces} parking</span>
              </div>
            )}
            {property.dockDoors && (
              <div className="flex items-center gap-1 text-gray-600">
                <Package className="w-4 h-4" />
                <span>{property.dockDoors} docks</span>
              </div>
            )}
            {property.clearHeight && (
              <div className="flex items-center gap-1 text-gray-600">
                <ArrowUp className="w-4 h-4" />
                <span>{property.clearHeight}' clear</span>
              </div>
            )}
            {property.occupancyRate && (
              <div className="flex items-center gap-1 text-gray-600">
                <Users className="w-4 h-4" />
                <span>{property.occupancyRate}% occupied</span>
              </div>
            )}
            {property.zoning && (
              <div className="flex items-center gap-1 text-gray-600">
                <FileText className="w-4 h-4" />
                <span>{property.zoning}</span>
              </div>
            )}
          </div>

          {/* Special Features */}
          <div className="flex flex-wrap gap-1 mb-4">
            {property.waterfront && (
              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                Waterfront
              </span>
            )}
            {property.pool && (
              <span className="px-2 py-1 bg-cyan-100 text-cyan-700 text-xs rounded-full">
                Pool
              </span>
            )}
            {property.railAccess && (
              <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                Rail Access
              </span>
            )}
            {property.irrigated && (
              <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                Irrigated
              </span>
            )}
          </div>

          <button 
            onClick={() => navigate(`/property/${property.id}`)}
            className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
            <Eye className="w-4 h-4" />
            View Details
          </button>
        </div>
      </motion.div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="sticky top-0 z-40 bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex flex-col gap-4">
            {/* Search Bar */}
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by address, property name, or type..."
                  className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="px-6 py-3 bg-white border border-gray-200 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors flex items-center gap-2"
              >
                <Filter className="w-4 h-4" />
                Filters
                <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
              </button>
            </div>

            {/* Property Category Tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              <button
                onClick={() => setSelectedCategory('ALL')}
                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                  selectedCategory === 'ALL' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All Properties
              </button>
              {Object.entries(PROPERTY_CATEGORIES).map(([key, category]) => {
                // Map PROPERTY_CATEGORIES to centralized icons
                const iconKey = category.name.toLowerCase().replace(' ', '_');
                return (
                  <button
                    key={key}
                    onClick={() => setSelectedCategory(key)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors flex items-center gap-2 ${
                      selectedCategory === key
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <UseIcon category={category.name} size={16} className="inline-block" />
                    {category.name}
                  </button>
                )
              })}
            </div>

            {/* Filter Bar */}
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-4"
              >
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                  {/* Property Use Code */}
                  <select 
                    value={selectedUseCode}
                    onChange={(e) => setSelectedUseCode(e.target.value)}
                    className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Property Types</option>
                    {Object.entries(PROPERTY_USE_CODES)
                      .filter(([code]) => {
                        if (selectedCategory === 'ALL') return true
                        const category = PROPERTY_CATEGORIES[selectedCategory]
                        return category?.codes.includes(code)
                      })
                      .map(([code, name]) => (
                        <option key={code} value={code}>{name}</option>
                      ))
                    }
                  </select>
                  
                  {/* Price Range */}
                  <select className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option>Any Price</option>
                    <option>Under $500K</option>
                    <option>$500K - $1M</option>
                    <option>$1M - $2M</option>
                    <option>$2M - $5M</option>
                    <option>$5M - $10M</option>
                    <option>$10M+</option>
                  </select>

                  {/* Status */}
                  <select className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option>All Status</option>
                    {Object.entries(PROPERTY_STATUS).map(([key, value]) => (
                      <option key={key} value={key}>{value}</option>
                    ))}
                  </select>

                  {/* Zoning */}
                  <select className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option>All Zoning</option>
                    {Object.entries(ZONING_CODES).map(([code, name]) => (
                      <option key={code} value={code}>{code} - {name}</option>
                    ))}
                  </select>

                  {/* Year Built */}
                  <select className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option>Any Year</option>
                    <option>2020+</option>
                    <option>2015-2019</option>
                    <option>2010-2014</option>
                    <option>2000-2009</option>
                    <option>Before 2000</option>
                  </select>
                  
                  <button className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                    Apply Filters
                  </button>
                </div>

                {/* Advanced Filters Toggle */}
                <button
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                >
                  <Info className="w-4 h-4" />
                  {showAdvancedFilters ? 'Hide' : 'Show'} Advanced Filters
                </button>

                {/* Advanced Filters */}
                {showAdvancedFilters && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="p-4 bg-gray-50 rounded-xl space-y-3"
                  >
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {selectedCategory === 'RESIDENTIAL' && (
                        <>
                          <select className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm">
                            <option>Any Beds</option>
                            <option>1+</option>
                            <option>2+</option>
                            <option>3+</option>
                            <option>4+</option>
                            <option>5+</option>
                          </select>
                          <select className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm">
                            <option>Any Baths</option>
                            <option>1+</option>
                            <option>2+</option>
                            <option>3+</option>
                            <option>4+</option>
                          </select>
                          <label className="flex items-center gap-2 px-3 py-2">
                            <input type="checkbox" className="rounded" />
                            <span className="text-sm">Waterfront</span>
                          </label>
                          <label className="flex items-center gap-2 px-3 py-2">
                            <input type="checkbox" className="rounded" />
                            <span className="text-sm">Pool</span>
                          </label>
                        </>
                      )}
                      
                      {(selectedCategory === 'COMMERCIAL' || selectedCategory === 'INDUSTRIAL') && (
                        <>
                          <input type="number" placeholder="Min Sq Ft" className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm" />
                          <input type="number" placeholder="Max Sq Ft" className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm" />
                          <input type="number" placeholder="Min Cap Rate %" className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm" />
                          <input type="number" placeholder="Min Parking" className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm" />
                        </>
                      )}
                      
                      {selectedCategory === 'AGRICULTURAL' && (
                        <>
                          <input type="number" placeholder="Min Acres" className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm" />
                          <label className="flex items-center gap-2 px-3 py-2">
                            <input type="checkbox" className="rounded" />
                            <span className="text-sm">Irrigated</span>
                          </label>
                          <label className="flex items-center gap-2 px-3 py-2">
                            <input type="checkbox" className="rounded" />
                            <span className="text-sm">Water Rights</span>
                          </label>
                        </>
                      )}
                      
                      {selectedCategory === 'VACANT_LAND' && (
                        <>
                          <input type="number" placeholder="Min Acres" className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm" />
                          <label className="flex items-center gap-2 px-3 py-2">
                            <input type="checkbox" className="rounded" />
                            <span className="text-sm">Utilities Available</span>
                          </label>
                          <label className="flex items-center gap-2 px-3 py-2">
                            <input type="checkbox" className="rounded" />
                            <span className="text-sm">No Wetlands</span>
                          </label>
                        </>
                      )}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Results Bar */}
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-gray-500">Showing</span>
                <span className="text-sm font-semibold text-gray-900 ml-1">{filteredProperties.length} properties</span>
                {selectedCategory !== 'ALL' && (
                  <span className="text-sm text-gray-500 ml-1">in {PROPERTY_CATEGORIES[selectedCategory].name}</span>
                )}
              </div>
              
              <div className="flex items-center gap-3">
                <select 
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option>Price: Low to High</option>
                  <option>Price: High to Low</option>
                  <option>Newest First</option>
                  <option>Cap Rate: High to Low</option>
                  <option>NOI: High to Low</option>
                </select>
                
                <div className="flex items-center bg-white border border-gray-200 rounded-lg">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-2 ${viewMode === 'grid' ? 'bg-blue-50 text-blue-600' : 'text-gray-500'} transition-colors`}
                  >
                    <Grid className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 ${viewMode === 'list' ? 'bg-blue-50 text-blue-600' : 'text-gray-500'} transition-colors`}
                  >
                    <List className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('map')}
                    className={`p-2 ${viewMode === 'map' ? 'bg-blue-50 text-blue-600' : 'text-gray-500'} transition-colors`}
                  >
                    <Map className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Properties Display */}
      <div className="p-6">
        {/* Property Type Info Banner */}
        {selectedUseCode && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl"
          >
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-blue-900">
                  {PROPERTY_USE_CODES[selectedUseCode]}
                </h3>
                <p className="text-sm text-blue-700 mt-1">
                  Showing all properties classified as "{PROPERTY_USE_CODES[selectedUseCode]}" (Use Code: {selectedUseCode})
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {viewMode === 'grid' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProperties.map((property, index) => (
              <PropertyCard key={property.id} property={property} index={index} />
            ))}
          </div>
        )}

        {viewMode === 'list' && (
          <div className="space-y-4">
            {filteredProperties.map((property, index) => (
              <motion.div
                key={property.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="bg-white rounded-xl p-5 shadow-sm hover:shadow-lg transition-all flex gap-5"
              >
                <img
                  src={property.image}
                  alt={property.title}
                  className="w-48 h-32 object-cover rounded-lg"
                />
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-lg font-semibold text-gray-900">{property.title}</h3>
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                          {PROPERTY_USE_CODES[property.useCode]}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-gray-600 mt-1">
                        <MapPin className="w-4 h-4" />
                        <span className="text-sm">{property.address}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900">
                        ${property.price.toLocaleString()}
                      </p>
                      {property.capRate && (
                        <p className="text-sm text-gray-500">Cap Rate: {property.capRate}%</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                    {property.buildingSqft && (
                      <span className="flex items-center gap-1">
                        <Building2 className="w-4 h-4" />
                        {property.buildingSqft.toLocaleString()} sqft
                      </span>
                    )}
                    {property.acres && (
                      <span className="flex items-center gap-1">
                        <Trees className="w-4 h-4" />
                        {property.acres} acres
                      </span>
                    )}
                    {property.netOperatingIncome && (
                      <span className="flex items-center gap-1 text-green-600 font-medium">
                        NOI: ${property.netOperatingIncome.toLocaleString()}
                      </span>
                    )}
                    {property.zoning && (
                      <span className="flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        Zoning: {property.zoning}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between mt-4">
                    <div className="flex gap-2">
                      <span className={`px-3 py-1 text-white text-sm font-medium rounded-full ${
                        property.status === 'ACTIVE' ? 'bg-green-600' :
                        property.status === 'PENDING' ? 'bg-yellow-600' :
                        property.status === 'LEASE' ? 'bg-purple-600' :
                        'bg-gray-600'
                      }`}>
                        {PROPERTY_STATUS[property.status]}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <Heart className="w-4 h-4 text-gray-600" />
                      </button>
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <Share2 className="w-4 h-4 text-gray-600" />
                      </button>
                      <button 
                        onClick={() => navigate(`/property/${property.id}`)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                        View Details
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {viewMode === 'map' && (
          <div className="bg-white rounded-2xl p-8 shadow-sm h-[600px] flex items-center justify-center">
            <div className="text-center">
              <Map className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Interactive Map View</h3>
              <p className="text-gray-600">Map integration would show property locations here</p>
              <p className="text-sm text-gray-500 mt-2">Properties would be color-coded by type</p>
            </div>
          </div>
        )}

        {filteredProperties.length === 0 && (
          <div className="text-center py-12">
            <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No properties found</h3>
            <p className="text-gray-600">Try adjusting your filters or search criteria</p>
          </div>
        )}
      </div>
    </div>
  )
}