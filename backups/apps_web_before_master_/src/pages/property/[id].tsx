import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Share2,
  Heart,
  Download,
  Printer,
  MapPin,
  Calendar,
  DollarSign,
  Building2,
  Home,
  Ruler,
  Trees,
  Car,
  Droplets,
  Zap,
  Shield,
  TrendingUp,
  FileText,
  User,
  Phone,
  Mail,
  Globe,
  Camera,
  ChevronRight,
  ChevronLeft,
  Check,
  X,
  AlertCircle,
  Info,
  Calculator,
  Briefcase,
  Clock,
  BarChart3,
  PieChart,
  Activity,
  Eye,
  Edit,
  Trash2,
  Plus,
  Package,
  Truck,
  Factory,
  Wheat,
  Mountain,
  Waves,
  Sun,
  Cloud,
  Wind,
  Compass,
  Map,
  Maximize2,
  Layers,
  Navigation,
  Target,
  Award,
  Key,
  Lock,
  Unlock,
  CreditCard,
  Receipt,
  FileCheck,
  Clipboard,
  Database,
  Server,
  Cpu,
  HardDrive,
  Wifi,
  Radio,
  Satellite,
  Train,
  Bus,
  Plane,
  Anchor,
  BookOpen,
  GraduationCap,
  Stethoscope,
  ShoppingCart,
  Coffee,
  Utensils,
  Bed,
  Bath,
  Sofa,
  Tv,
  Smartphone,
  Monitor,
  Headphones,
  Speaker,
  Mic,
  Video,
  Image,
  Film,
  Music,
  Volume2,
  Bell,
  BellOff,
  MessageSquare,
  Send,
  Inbox,
  Archive,
  Folder,
  FolderOpen,
  File,
  FilePlus,
  FileX,
  Save,
  RefreshCw,
  RotateCw,
  Loader,
  Square,
  Circle,
  Triangle,
  Star,
  Heart as HeartIcon,
  ThumbsUp,
  ThumbsDown,
  Award as AwardIcon,
  Flag,
  Bookmark,
  Tag,
  Tags,
  Hash,
  AtSign,
  Percent,
  Binary,
  Code,
  Terminal,
  Command,
  Cloud as CloudIcon,
  CloudRain,
  CloudSnow,
  CloudOff,
  Sunrise,
  Sunset,
  Moon,
  CloudDrizzle,
  CloudLightning,
  Thermometer,
  Umbrella,
  Snowflake,
  Zap as ZapIcon,
  Battery,
  BatteryCharging,
  Bluetooth,
  Cast,
  Voicemail,
  Inbox as InboxIcon,
  Search,
  Filter,
  Settings,
  Tool,
  Wrench,
  Hammer,
  PaintBucket,
  Palette,
  Brush,
  Pen,
  PenTool,
  Eraser,
  Type,
  Bold,
  Italic,
  Underline
} from 'lucide-react'
import { PropertyMainProfile, FIELD_VISIBILITY_CONFIG } from '@/lib/property-data-fields'
import { PROPERTY_USE_CODES, PROPERTY_CATEGORIES } from '@/lib/property-types'
import {
  propertyApiClient,
  PropertyDetail,
  QuickPropertyData,
  formatCurrency,
  formatDate,
  formatNumber,
  calculatePricePerSqft
} from '@/lib/property-api-client'

// Mock data generator for demonstration
const generateMockPropertyData = (id: string): PropertyMainProfile => {
  // This would normally fetch from your database
  return {
    parcelId: id || '494223-01-01-0010',
    countyNo: '06',
    
    // Owner Information
    ownerName1: 'SUNSHINE INVESTMENT GROUP LLC',
    ownerName2: '',
    ownerMailingAddress1: '1234 CORPORATE BLVD STE 500',
    ownerMailingAddress2: '',
    ownerMailingAddress3: '',
    ownerCity: 'FORT LAUDERDALE',
    ownerState: 'FL',
    ownerZip: '33301',
    
    // Property Location
    situsAddress1: '2500 E LAS OLAS BLVD',
    situsAddress2: '',
    situsCity: 'FORT LAUDERDALE',
    situsState: 'FL',
    situsZip: '33301',
    
    // Legal Description
    legalDescription1: 'VICTORIA PARK 155-23 B',
    legalDescription2: 'LOT 10 BLK 23',
    subdivision: 'VICTORIA PARK',
    block: '23',
    lot: '10',
    section: '15',
    township: '50S',
    range: '42E',
    
    // Classification
    dorCode: '18',
    dorCodeDescription: 'Office Building, Multi-Story',
    propertyUseCode: '18',
    propertyUseDescription: 'Office Building, Multi-Story',
    neighborhoodCode: '0010',
    neighborhoodName: 'DOWNTOWN FORT LAUDERDALE',
    zoningCode: 'CBD',
    zoningDescription: 'Central Business District',
    futureUseCode: 'COM',
    futureUseDescription: 'Commercial',
    
    // Valuations
    justValue: 15750000,
    assessedValue: 15750000,
    taxableValue: 14500000,
    landValue: 4500000,
    buildingValue: 11250000,
    extraFeatureValue: 0,
    totalJustValue: 15750000,
    totalAssessedValue: 15750000,
    totalTaxableValue: 14500000,
    previousYearJustValue: 14800000,
    previousYearAssessedValue: 14800000,
    previousYearTaxableValue: 13600000,
    
    // Exemptions
    homesteadExemption: false,
    homesteadExemptionValue: 0,
    seniorExemption: false,
    veteranExemption: false,
    widowExemption: false,
    disabilityExemption: false,
    agriculturalClassification: false,
    otherExemptions: [],
    totalExemptionValue: 0,
    
    // Building Information
    numberOfBuildings: 1,
    totalBuildingArea: 85000,
    totalLivingArea: 82000,
    adjustedSquareFeet: 82000,
    grossSquareFeet: 85000,
    effectiveYearBuilt: 2010,
    actualYearBuilt: 1998,
    numberOfStories: 8,
    structureType: 'Office Building',
    constructionType: 'Reinforced Concrete',
    foundation: 'Slab',
    roofStructure: 'Built-up',
    roofCover: 'Modified Bitumen',
    exteriorWall: 'Glass Curtain Wall',
    interiorWall: 'Drywall',
    heatingType: 'Central',
    coolingType: 'Central AC',
    fireplaces: 0,
    
    // Commercial Specific
    numberOfCommercialUnits: 42,
    rentableArea: 75000,
    commonArea: 7000,
    grossLeasableArea: 75000,
    netRentableArea: 75000,
    parkingSpaces: 250,
    parkingType: 'Garage',
    loadingDocks: 2,
    officeSpace: 75000,
    
    // Land Characteristics
    totalLandArea: 45000,
    totalAcreage: 1.03,
    frontage: 150,
    depth: 300,
    landSquareFeet: 45000,
    landUseCode: 'COM',
    utilityWater: true,
    utilitySewer: true,
    utilityElectric: true,
    utilityGas: true,
    utilityStreetLights: true,
    streetPaved: true,
    sidewalk: true,
    
    // Sales Information
    lastSaleDate: new Date('2021-03-15'),
    lastSalePrice: 14250000,
    lastSaleQualificationCode: 'Q',
    deedType: 'WD',
    grantor: 'PREVIOUS OWNER LLC',
    grantee: 'SUNSHINE INVESTMENT GROUP LLC',
    instrumentNumber: '115842369',
    priorSaleDate: new Date('2015-06-20'),
    priorSalePrice: 9500000,
    
    // Tax Information
    taxingDistrictCode: '010',
    taxingDistrictName: 'CITY OF FORT LAUDERDALE',
    millageRate: 18.9541,
    nonAdValoremAssessments: 2500,
    totalTaxes: 277234,
    taxBillYear: 2024,
    
    // GIS/Mapping
    latitude: 26.119722,
    longitude: -80.137778,
    gisPin: '494223010010010',
    censusBlock: '1204',
    censusTract: '0010.00',
    floodZone: 'X',
    floodZoneDate: new Date('2021-09-24'),
    
    // Corporate Owner
    corporateOwner: {
      entityName: 'SUNSHINE INVESTMENT GROUP LLC',
      entityType: 'Limited Liability Company',
      sunbizNumber: 'L21000234567',
      filingDate: new Date('2021-01-15'),
      status: 'Active',
      principalAddress: '1234 CORPORATE BLVD STE 500, FORT LAUDERDALE, FL 33301',
      registeredAgent: 'REGISTERED AGENT SERVICES INC',
      registeredAgentAddress: '100 S ANDREWS AVE, FORT LAUDERDALE, FL 33301',
      officers: [
        { name: 'JOHN SMITH', title: 'Manager', address: '1234 CORPORATE BLVD, FORT LAUDERDALE, FL' },
        { name: 'JANE DOE', title: 'Manager', address: '1234 CORPORATE BLVD, FORT LAUDERDALE, FL' }
      ]
    },
    
    // Flags
    isHomestead: false,
    isCommercial: true,
    isVacant: false,
    isAgricultural: false,
    isWaterfront: false,
    isCornerLot: true,
    isHistoric: false,
    isPendingSale: false,
    isForeclosure: false,
    isREO: false,
    
    // Dates
    certifiedDate: new Date('2024-10-01'),
    lastUpdated: new Date('2024-11-15'),
    dataYear: '2024F',
    dataSource: 'NAL',
    dataVersion: 'Final',
    
    // Computed fields
    pricePerSqFt: 185.29,
    taxRate: 1.91,
    monthlyTaxes: 23102,
    appreciationRate: 6.4,
    
    // Images
    images: [
      { url: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1600&h=900&fit=crop', type: 'exterior', caption: 'Building Exterior' },
      { url: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=1600&h=900&fit=crop', type: 'interior', caption: 'Lobby' },
      { url: 'https://images.unsplash.com/photo-1497366754035-f200586c6c24?w=1600&h=900&fit=crop', type: 'interior', caption: 'Office Space' },
      { url: 'https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=1600&h=900&fit=crop', type: 'interior', caption: 'Conference Room' }
    ]
  }
}

export default function PropertyProfilePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [property, setProperty] = useState<PropertyMainProfile | null>(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [activeImageIndex, setActiveImageIndex] = useState(0)
  const [isGalleryOpen, setIsGalleryOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading data
    const loadProperty = async () => {
      setLoading(true)
      // In production, this would be an API call
      setTimeout(() => {
        setProperty(generateMockPropertyData(id || ''))
        setLoading(false)
      }, 1000)
    }
    loadProperty()
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <Loader className="w-8 h-8 text-blue-600" />
        </motion.div>
      </div>
    )
  }

  if (!property) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">Property not found</h2>
          <button
            onClick={() => navigate('/search')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Search
          </button>
        </div>
      </div>
    )
  }

  // Determine property category based on use code
  const getPropertyCategory = () => {
    const code = property.dorCode
    for (const [category, config] of Object.entries(PROPERTY_CATEGORIES)) {
      if (config.codes.includes(code)) {
        return category
      }
    }
    return 'COMMERCIAL' // Default
  }

  const category = getPropertyCategory()
  const visibilityConfig = FIELD_VISIBILITY_CONFIG[category as keyof typeof FIELD_VISIBILITY_CONFIG] || FIELD_VISIBILITY_CONFIG.COMMERCIAL

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatDate = (date: Date | undefined) => {
    if (!date) return 'N/A'
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  // Tab configurations based on property type
  const getTabs = () => {
    const baseTabs = [
      { id: 'overview', label: 'Overview', icon: Eye },
      { id: 'details', label: 'Property Details', icon: Building2 },
      { id: 'valuation', label: 'Valuation & Tax', icon: DollarSign },
      { id: 'ownership', label: 'Ownership', icon: User },
      { id: 'sales', label: 'Sales History', icon: TrendingUp },
      { id: 'land', label: 'Land & Location', icon: MapPin },
      { id: 'documents', label: 'Documents', icon: FileText }
    ]

    if (category === 'COMMERCIAL' || category === 'INDUSTRIAL') {
      baseTabs.splice(2, 0, { id: 'income', label: 'Income Analysis', icon: BarChart3 })
    }

    if (category === 'AGRICULTURAL') {
      baseTabs.splice(2, 0, { id: 'production', label: 'Agricultural Data', icon: Wheat })
    }

    return baseTabs
  }

  const tabs = getTabs()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/search')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold text-gray-900">{property.situsAddress1}</h1>
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full">
                    {PROPERTY_USE_CODES[property.dorCode] || property.dorCode}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {property.situsCity}, {property.situsState} {property.situsZip} • Parcel ID: {property.parcelId}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button className="p-2 bg-white hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors">
                <Share2 className="w-5 h-5 text-gray-700" />
              </button>
              <button className="p-2 bg-white hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors">
                <HeartIcon className="w-5 h-5 text-gray-700" />
              </button>
              <button className="p-2 bg-white hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors">
                <Download className="w-5 h-5 text-gray-700" />
              </button>
              <button className="p-2 bg-white hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors">
                <Printer className="w-5 h-5 text-gray-700" />
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
                <Phone className="w-4 h-4" />
                Contact Agent
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-6">
          <div className="flex items-center gap-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-blue-600'
                    : 'text-gray-600 border-transparent hover:text-gray-900'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Content - 2 columns */}
            <div className="lg:col-span-2 space-y-6">
              {/* Image Gallery */}
              {property.images && property.images.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white rounded-xl shadow-sm overflow-hidden"
                >
                  <div className="relative h-96">
                    <img
                      src={property.images[activeImageIndex].url}
                      alt={property.images[activeImageIndex].caption}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                    
                    {/* Image Navigation */}
                    {property.images.length > 1 && (
                      <>
                        <button
                          onClick={() => setActiveImageIndex(prev => 
                            prev === 0 ? property.images!.length - 1 : prev - 1
                          )}
                          className="absolute left-4 top-1/2 -translate-y-1/2 p-2 bg-white/90 backdrop-blur rounded-full hover:bg-white transition-colors"
                        >
                          <ChevronLeft className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => setActiveImageIndex(prev => 
                            prev === property.images!.length - 1 ? 0 : prev + 1
                          )}
                          className="absolute right-4 top-1/2 -translate-y-1/2 p-2 bg-white/90 backdrop-blur rounded-full hover:bg-white transition-colors"
                        >
                          <ChevronRight className="w-5 h-5" />
                        </button>
                      </>
                    )}
                    
                    {/* Image Counter */}
                    <div className="absolute bottom-4 left-4 px-3 py-1 bg-black/50 backdrop-blur rounded-full text-white text-sm">
                      {activeImageIndex + 1} / {property.images.length}
                    </div>
                    
                    {/* Expand Button */}
                    <button
                      onClick={() => setIsGalleryOpen(true)}
                      className="absolute bottom-4 right-4 p-2 bg-white/90 backdrop-blur rounded-full hover:bg-white transition-colors"
                    >
                      <Maximize2 className="w-5 h-5" />
                    </button>
                  </div>
                  
                  {/* Thumbnails */}
                  {property.images.length > 1 && (
                    <div className="p-4 flex gap-2 overflow-x-auto">
                      {property.images.map((image, index) => (
                        <button
                          key={index}
                          onClick={() => setActiveImageIndex(index)}
                          className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
                            activeImageIndex === index 
                              ? 'border-blue-600 shadow-lg' 
                              : 'border-transparent hover:border-gray-300'
                          }`}
                        >
                          <img
                            src={image.url}
                            alt={image.caption}
                            className="w-full h-full object-cover"
                          />
                        </button>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}

              {/* Tab Content */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-6"
                >
                  {activeTab === 'overview' && (
                    <>
                      {/* Key Metrics */}
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Information</h2>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Market Value</p>
                            <p className="text-2xl font-bold text-gray-900">
                              {formatCurrency(property.justValue)}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Taxable Value</p>
                            <p className="text-2xl font-bold text-gray-900">
                              {formatCurrency(property.taxableValue)}
                            </p>
                          </div>
                          {property.lastSalePrice && (
                            <div>
                              <p className="text-sm text-gray-500 mb-1">Last Sale Price</p>
                              <p className="text-2xl font-bold text-gray-900">
                                {formatCurrency(property.lastSalePrice)}
                              </p>
                            </div>
                          )}
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Building Area</p>
                            <p className="text-xl font-semibold text-gray-900">
                              {property.totalBuildingArea?.toLocaleString()} sqft
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Land Area</p>
                            <p className="text-xl font-semibold text-gray-900">
                              {property.totalAcreage?.toFixed(2)} acres
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Year Built</p>
                            <p className="text-xl font-semibold text-gray-900">
                              {property.actualYearBuilt}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Property Description */}
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Description</h2>
                        <div className="prose max-w-none text-gray-600">
                          <p>
                            This {property.dorCodeDescription} property is located in {property.neighborhoodName}, 
                            {property.situsCity}. Built in {property.actualYearBuilt} and renovated to an effective 
                            year of {property.effectiveYearBuilt}, the property comprises {property.numberOfBuildings} building(s) 
                            with a total of {property.totalBuildingArea?.toLocaleString()} square feet on {property.totalAcreage?.toFixed(2)} acres.
                          </p>
                          <p className="mt-3">
                            The property is zoned {property.zoningCode} ({property.zoningDescription}) and is classified as 
                            {property.futureUseDescription} for future land use. Current market value is assessed 
                            at {formatCurrency(property.justValue)} with a taxable value of {formatCurrency(property.taxableValue)}.
                          </p>
                        </div>
                      </div>

                      {/* Features Grid */}
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Features</h2>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                          {property.utilityWater && (
                            <div className="flex items-center gap-2">
                              <Droplets className="w-5 h-5 text-blue-500" />
                              <span className="text-sm text-gray-700">Water Available</span>
                            </div>
                          )}
                          {property.utilitySewer && (
                            <div className="flex items-center gap-2">
                              <Package className="w-5 h-5 text-gray-500" />
                              <span className="text-sm text-gray-700">Sewer Connected</span>
                            </div>
                          )}
                          {property.utilityElectric && (
                            <div className="flex items-center gap-2">
                              <Zap className="w-5 h-5 text-yellow-500" />
                              <span className="text-sm text-gray-700">Electric Available</span>
                            </div>
                          )}
                          {property.utilityGas && (
                            <div className="flex items-center gap-2">
                              <ZapIcon className="w-5 h-5 text-orange-500" />
                              <span className="text-sm text-gray-700">Gas Available</span>
                            </div>
                          )}
                          {property.streetPaved && (
                            <div className="flex items-center gap-2">
                              <Car className="w-5 h-5 text-gray-600" />
                              <span className="text-sm text-gray-700">Paved Street</span>
                            </div>
                          )}
                          {property.sidewalk && (
                            <div className="flex items-center gap-2">
                              <User className="w-5 h-5 text-gray-600" />
                              <span className="text-sm text-gray-700">Sidewalk</span>
                            </div>
                          )}
                          {property.parkingSpaces && (
                            <div className="flex items-center gap-2">
                              <Car className="w-5 h-5 text-gray-600" />
                              <span className="text-sm text-gray-700">{property.parkingSpaces} Parking Spaces</span>
                            </div>
                          )}
                          {property.isWaterfront && (
                            <div className="flex items-center gap-2">
                              <Waves className="w-5 h-5 text-cyan-500" />
                              <span className="text-sm text-gray-700">Waterfront</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </>
                  )}

                  {activeTab === 'details' && (
                    <div className="bg-white rounded-xl p-6 shadow-sm">
                      <h2 className="text-lg font-semibold text-gray-900 mb-4">Detailed Property Information</h2>
                      <div className="space-y-6">
                        {/* Building Details */}
                        <div>
                          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">Building Specifications</h3>
                          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Structure Type</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.structureType}</dd>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Construction Type</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.constructionType}</dd>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Foundation</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.foundation}</dd>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Number of Stories</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.numberOfStories}</dd>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Roof Structure</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.roofStructure}</dd>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Roof Cover</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.roofCover}</dd>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Exterior Wall</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.exteriorWall}</dd>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Interior Wall</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.interiorWall}</dd>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Heating Type</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.heatingType}</dd>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-100">
                              <dt className="text-sm text-gray-500">Cooling Type</dt>
                              <dd className="text-sm font-medium text-gray-900">{property.coolingType}</dd>
                            </div>
                          </dl>
                        </div>

                        {/* Commercial Details */}
                        {property.numberOfCommercialUnits && (
                          <div>
                            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">Commercial Information</h3>
                            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="flex justify-between py-2 border-b border-gray-100">
                                <dt className="text-sm text-gray-500">Commercial Units</dt>
                                <dd className="text-sm font-medium text-gray-900">{property.numberOfCommercialUnits}</dd>
                              </div>
                              <div className="flex justify-between py-2 border-b border-gray-100">
                                <dt className="text-sm text-gray-500">Rentable Area</dt>
                                <dd className="text-sm font-medium text-gray-900">{property.rentableArea?.toLocaleString()} sqft</dd>
                              </div>
                              <div className="flex justify-between py-2 border-b border-gray-100">
                                <dt className="text-sm text-gray-500">Common Area</dt>
                                <dd className="text-sm font-medium text-gray-900">{property.commonArea?.toLocaleString()} sqft</dd>
                              </div>
                              <div className="flex justify-between py-2 border-b border-gray-100">
                                <dt className="text-sm text-gray-500">Parking Type</dt>
                                <dd className="text-sm font-medium text-gray-900">{property.parkingType}</dd>
                              </div>
                              {property.loadingDocks && (
                                <div className="flex justify-between py-2 border-b border-gray-100">
                                  <dt className="text-sm text-gray-500">Loading Docks</dt>
                                  <dd className="text-sm font-medium text-gray-900">{property.loadingDocks}</dd>
                                </div>
                              )}
                            </dl>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {activeTab === 'valuation' && (
                    <div className="space-y-6">
                      {/* Valuation Breakdown */}
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Valuation</h2>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center py-3 border-b">
                            <div>
                              <p className="text-sm font-medium text-gray-900">Land Value</p>
                              <p className="text-xs text-gray-500">Value of land only</p>
                            </div>
                            <p className="text-lg font-semibold text-gray-900">{formatCurrency(property.landValue)}</p>
                          </div>
                          <div className="flex justify-between items-center py-3 border-b">
                            <div>
                              <p className="text-sm font-medium text-gray-900">Building Value</p>
                              <p className="text-xs text-gray-500">Value of structures</p>
                            </div>
                            <p className="text-lg font-semibold text-gray-900">{formatCurrency(property.buildingValue)}</p>
                          </div>
                          <div className="flex justify-between items-center py-3 border-b">
                            <div>
                              <p className="text-sm font-medium text-gray-900">Extra Features</p>
                              <p className="text-xs text-gray-500">Pools, fencing, etc.</p>
                            </div>
                            <p className="text-lg font-semibold text-gray-900">{formatCurrency(property.extraFeatureValue)}</p>
                          </div>
                          <div className="flex justify-between items-center py-3 bg-gray-50 -mx-6 px-6">
                            <div>
                              <p className="text-base font-semibold text-gray-900">Just (Market) Value</p>
                              <p className="text-xs text-gray-500">Total estimated market value</p>
                            </div>
                            <p className="text-xl font-bold text-blue-600">{formatCurrency(property.justValue)}</p>
                          </div>
                        </div>
                      </div>

                      {/* Tax Information */}
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Tax Assessment</h2>
                        <div className="space-y-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                              <p className="text-sm text-gray-500 mb-1">Assessed Value</p>
                              <p className="text-2xl font-bold text-gray-900">{formatCurrency(property.assessedValue)}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-500 mb-1">Taxable Value</p>
                              <p className="text-2xl font-bold text-gray-900">{formatCurrency(property.taxableValue)}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-500 mb-1">Millage Rate</p>
                              <p className="text-xl font-semibold text-gray-900">{property.millageRate?.toFixed(4)}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-500 mb-1">Annual Taxes</p>
                              <p className="text-2xl font-bold text-red-600">{formatCurrency(property.totalTaxes)}</p>
                            </div>
                          </div>
                          
                          {/* Exemptions */}
                          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                            <h3 className="text-sm font-semibold text-blue-900 mb-2">Exemptions</h3>
                            <div className="grid grid-cols-2 gap-3">
                              <div className="flex items-center gap-2">
                                {property.homesteadExemption ? (
                                  <Check className="w-4 h-4 text-green-600" />
                                ) : (
                                  <X className="w-4 h-4 text-gray-400" />
                                )}
                                <span className="text-sm text-gray-700">Homestead</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {property.seniorExemption ? (
                                  <Check className="w-4 h-4 text-green-600" />
                                ) : (
                                  <X className="w-4 h-4 text-gray-400" />
                                )}
                                <span className="text-sm text-gray-700">Senior</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {property.veteranExemption ? (
                                  <Check className="w-4 h-4 text-green-600" />
                                ) : (
                                  <X className="w-4 h-4 text-gray-400" />
                                )}
                                <span className="text-sm text-gray-700">Veteran</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {property.agriculturalClassification ? (
                                  <Check className="w-4 h-4 text-green-600" />
                                ) : (
                                  <X className="w-4 h-4 text-gray-400" />
                                )}
                                <span className="text-sm text-gray-700">Agricultural</span>
                              </div>
                            </div>
                            {property.totalExemptionValue > 0 && (
                              <p className="mt-3 text-sm font-medium text-blue-900">
                                Total Exemption Value: {formatCurrency(property.totalExemptionValue)}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'ownership' && (
                    <div className="space-y-6">
                      {/* Current Owner */}
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Owner</h2>
                        <div className="space-y-4">
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Owner Name</p>
                            <p className="text-lg font-semibold text-gray-900">{property.ownerName1}</p>
                            {property.ownerName2 && (
                              <p className="text-lg font-semibold text-gray-900">{property.ownerName2}</p>
                            )}
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Mailing Address</p>
                            <p className="text-sm text-gray-700">{property.ownerMailingAddress1}</p>
                            {property.ownerMailingAddress2 && (
                              <p className="text-sm text-gray-700">{property.ownerMailingAddress2}</p>
                            )}
                            <p className="text-sm text-gray-700">
                              {property.ownerCity}, {property.ownerState} {property.ownerZip}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Corporate Owner Details */}
                      {property.corporateOwner && (
                        <div className="bg-white rounded-xl p-6 shadow-sm">
                          <h2 className="text-lg font-semibold text-gray-900 mb-4">Corporate Information</h2>
                          <div className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <p className="text-sm text-gray-500 mb-1">Entity Type</p>
                                <p className="text-sm font-medium text-gray-900">{property.corporateOwner.entityType}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-500 mb-1">Sunbiz Number</p>
                                <p className="text-sm font-medium text-gray-900">{property.corporateOwner.sunbizNumber}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-500 mb-1">Filing Date</p>
                                <p className="text-sm font-medium text-gray-900">
                                  {formatDate(property.corporateOwner.filingDate)}
                                </p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-500 mb-1">Status</p>
                                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                                  {property.corporateOwner.status}
                                </span>
                              </div>
                            </div>

                            {property.corporateOwner.officers && property.corporateOwner.officers.length > 0 && (
                              <div>
                                <h3 className="text-sm font-semibold text-gray-700 mb-2">Officers/Managers</h3>
                                <div className="space-y-2">
                                  {property.corporateOwner.officers.map((officer, index) => (
                                    <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100">
                                      <div>
                                        <p className="text-sm font-medium text-gray-900">{officer.name}</p>
                                        <p className="text-xs text-gray-500">{officer.title}</p>
                                      </div>
                                      <p className="text-xs text-gray-500">{officer.address}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'sales' && (
                    <div className="bg-white rounded-xl p-6 shadow-sm">
                      <h2 className="text-lg font-semibold text-gray-900 mb-4">Sales History</h2>
                      <div className="space-y-4">
                        {property.lastSaleDate && (
                          <div className="p-4 bg-blue-50 rounded-lg">
                            <div className="flex justify-between items-start">
                              <div>
                                <p className="text-sm font-semibold text-blue-900">Most Recent Sale</p>
                                <p className="text-sm text-blue-700 mt-1">{formatDate(property.lastSaleDate)}</p>
                                <p className="text-xs text-blue-600 mt-2">
                                  Deed Type: {property.deedType} | Instrument #: {property.instrumentNumber}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-2xl font-bold text-blue-900">
                                  {formatCurrency(property.lastSalePrice || 0)}
                                </p>
                                <p className="text-xs text-blue-600 mt-1">
                                  {property.lastSaleQualificationCode === 'Q' ? 'Qualified Sale' : 'Non-Qualified'}
                                </p>
                              </div>
                            </div>
                            <div className="mt-3 pt-3 border-t border-blue-200">
                              <div className="flex justify-between text-sm">
                                <span className="text-blue-700">From: {property.grantor}</span>
                                <span className="text-blue-700">To: {property.grantee}</span>
                              </div>
                            </div>
                          </div>
                        )}

                        {property.priorSaleDate && (
                          <div className="p-4 bg-gray-50 rounded-lg">
                            <div className="flex justify-between items-start">
                              <div>
                                <p className="text-sm font-semibold text-gray-900">Prior Sale</p>
                                <p className="text-sm text-gray-700 mt-1">{formatDate(property.priorSaleDate)}</p>
                              </div>
                              <div className="text-right">
                                <p className="text-xl font-bold text-gray-900">
                                  {formatCurrency(property.priorSalePrice || 0)}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Appreciation Analysis */}
                        {property.lastSalePrice && property.priorSalePrice && (
                          <div className="mt-6 p-4 bg-green-50 rounded-lg">
                            <h3 className="text-sm font-semibold text-green-900 mb-2">Value Appreciation</h3>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-xs text-green-700">Total Appreciation</p>
                                <p className="text-lg font-bold text-green-900">
                                  {formatCurrency(property.lastSalePrice - property.priorSalePrice)}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs text-green-700">Percentage Gain</p>
                                <p className="text-lg font-bold text-green-900">
                                  {((property.lastSalePrice - property.priorSalePrice) / property.priorSalePrice * 100).toFixed(1)}%
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {activeTab === 'land' && (
                    <div className="space-y-6">
                      {/* Land Details */}
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Land Information</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="flex justify-between py-2 border-b border-gray-100">
                            <dt className="text-sm text-gray-500">Total Acres</dt>
                            <dd className="text-sm font-medium text-gray-900">{property.totalAcreage?.toFixed(2)}</dd>
                          </div>
                          <div className="flex justify-between py-2 border-b border-gray-100">
                            <dt className="text-sm text-gray-500">Square Feet</dt>
                            <dd className="text-sm font-medium text-gray-900">{property.landSquareFeet?.toLocaleString()}</dd>
                          </div>
                          <div className="flex justify-between py-2 border-b border-gray-100">
                            <dt className="text-sm text-gray-500">Frontage</dt>
                            <dd className="text-sm font-medium text-gray-900">{property.frontage} ft</dd>
                          </div>
                          <div className="flex justify-between py-2 border-b border-gray-100">
                            <dt className="text-sm text-gray-500">Depth</dt>
                            <dd className="text-sm font-medium text-gray-900">{property.depth} ft</dd>
                          </div>
                          <div className="flex justify-between py-2 border-b border-gray-100">
                            <dt className="text-sm text-gray-500">Zoning</dt>
                            <dd className="text-sm font-medium text-gray-900">{property.zoningCode} - {property.zoningDescription}</dd>
                          </div>
                          <div className="flex justify-between py-2 border-b border-gray-100">
                            <dt className="text-sm text-gray-500">Future Land Use</dt>
                            <dd className="text-sm font-medium text-gray-900">{property.futureUseDescription}</dd>
                          </div>
                        </div>
                      </div>

                      {/* Legal Description */}
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Legal Description</h2>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-sm text-gray-700 font-mono">
                            {property.legalDescription1}
                            {property.legalDescription2 && <><br />{property.legalDescription2}</>}
                            {property.legalDescription3 && <><br />{property.legalDescription3}</>}
                          </p>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t border-gray-200">
                            <div>
                              <p className="text-xs text-gray-500">Section</p>
                              <p className="text-sm font-medium text-gray-900">{property.section}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">Township</p>
                              <p className="text-sm font-medium text-gray-900">{property.township}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">Range</p>
                              <p className="text-sm font-medium text-gray-900">{property.range}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">Subdivision</p>
                              <p className="text-sm font-medium text-gray-900">{property.subdivision}</p>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Location Details */}
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Location Details</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Neighborhood</p>
                            <p className="text-sm font-medium text-gray-900">{property.neighborhoodName}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Census Tract</p>
                            <p className="text-sm font-medium text-gray-900">{property.censusTract}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Flood Zone</p>
                            <p className="text-sm font-medium text-gray-900">Zone {property.floodZone}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Coordinates</p>
                            <p className="text-sm font-medium text-gray-900">
                              {property.latitude?.toFixed(6)}, {property.longitude?.toFixed(6)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'documents' && (
                    <div className="bg-white rounded-xl p-6 shadow-sm">
                      <h2 className="text-lg font-semibold text-gray-900 mb-4">Documents & Records</h2>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                          <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-blue-600" />
                            <div>
                              <p className="text-sm font-medium text-gray-900">Property Deed</p>
                              <p className="text-xs text-gray-500">Recorded {formatDate(property.lastSaleDate)}</p>
                            </div>
                          </div>
                          <Download className="w-4 h-4 text-gray-500" />
                        </div>
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                          <div className="flex items-center gap-3">
                            <Receipt className="w-5 h-5 text-green-600" />
                            <div>
                              <p className="text-sm font-medium text-gray-900">Tax Bill {property.taxBillYear}</p>
                              <p className="text-xs text-gray-500">Annual taxes: {formatCurrency(property.totalTaxes)}</p>
                            </div>
                          </div>
                          <Download className="w-4 h-4 text-gray-500" />
                        </div>
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                          <div className="flex items-center gap-3">
                            <Map className="w-5 h-5 text-purple-600" />
                            <div>
                              <p className="text-sm font-medium text-gray-900">Survey Map</p>
                              <p className="text-xs text-gray-500">GIS PIN: {property.gisPin}</p>
                            </div>
                          </div>
                          <Download className="w-4 h-4 text-gray-500" />
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'income' && (property.netOperatingIncome || property.capRate) && (
                    <div className="space-y-6">
                      <div className="bg-white rounded-xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Income Analysis</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Net Operating Income (NOI)</p>
                            <p className="text-3xl font-bold text-green-600">
                              {formatCurrency(property.netOperatingIncome || 0)}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">Annual</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Capitalization Rate</p>
                            <p className="text-3xl font-bold text-blue-600">
                              {property.capRate || 0}%
                            </p>
                            <p className="text-xs text-gray-500 mt-1">Based on current value</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Price per Sq Ft</p>
                            <p className="text-2xl font-semibold text-gray-900">
                              {formatCurrency(property.pricePerSqFt || 0)}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-500 mb-1">Monthly Income</p>
                            <p className="text-2xl font-semibold text-gray-900">
                              {formatCurrency((property.netOperatingIncome || 0) / 12)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Sidebar - 1 column */}
            <div className="space-y-6">
              {/* Quick Actions */}
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
                <div className="space-y-3">
                  <button className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
                    <Calculator className="w-4 h-4" />
                    Calculate Mortgage
                  </button>
                  <button className="w-full px-4 py-3 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Schedule Viewing
                  </button>
                  <button className="w-full px-4 py-3 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-2">
                    <FileText className="w-4 h-4" />
                    Request Documents
                  </button>
                  <button className="w-full px-4 py-3 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-2">
                    <BarChart3 className="w-4 h-4" />
                    View Comparables
                  </button>
                </div>
              </div>

              {/* Key Metrics Summary */}
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Metrics</h2>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-500">Market Value</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {formatCurrency(property.justValue)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full" style={{ width: '100%' }} />
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-500">Taxable Value</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {formatCurrency(property.taxableValue)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full" 
                        style={{ width: `${(property.taxableValue / property.justValue * 100)}%` }} 
                      />
                    </div>
                  </div>

                  {property.lastSalePrice && (
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-gray-500">Last Sale Price</span>
                        <span className="text-sm font-semibold text-gray-900">
                          {formatCurrency(property.lastSalePrice)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-purple-600 h-2 rounded-full" 
                          style={{ width: `${(property.lastSalePrice / property.justValue * 100)}%` }} 
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Property Flags */}
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Status</h2>
                <div className="space-y-2">
                  {property.isHomestead && (
                    <div className="flex items-center gap-2">
                      <Home className="w-4 h-4 text-green-600" />
                      <span className="text-sm text-gray-700">Homestead Property</span>
                    </div>
                  )}
                  {property.isCommercial && (
                    <div className="flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-blue-600" />
                      <span className="text-sm text-gray-700">Commercial Property</span>
                    </div>
                  )}
                  {property.isWaterfront && (
                    <div className="flex items-center gap-2">
                      <Waves className="w-4 h-4 text-cyan-600" />
                      <span className="text-sm text-gray-700">Waterfront Location</span>
                    </div>
                  )}
                  {property.isCornerLot && (
                    <div className="flex items-center gap-2">
                      <Compass className="w-4 h-4 text-purple-600" />
                      <span className="text-sm text-gray-700">Corner Lot</span>
                    </div>
                  )}
                  {property.isHistoric && (
                    <div className="flex items-center gap-2">
                      <AwardIcon className="w-4 h-4 text-amber-600" />
                      <span className="text-sm text-gray-700">Historic Property</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Data Source Info */}
              <div className="bg-blue-50 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-blue-900">Data Source</p>
                    <p className="text-xs text-blue-700 mt-1">
                      Florida DOR {property.dataSource} {property.dataYear} • 
                      Last Updated: {formatDate(property.lastUpdated)}
                    </p>
                    <p className="text-xs text-blue-700 mt-1">
                      County Certified: {formatDate(property.certifiedDate)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fullscreen Gallery Modal */}
      <AnimatePresence>
        {isGalleryOpen && property.images && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black flex items-center justify-center"
            onClick={() => setIsGalleryOpen(false)}
          >
            <button
              onClick={() => setIsGalleryOpen(false)}
              className="absolute top-4 right-4 p-2 bg-white/10 backdrop-blur rounded-full text-white hover:bg-white/20 transition-colors z-10"
            >
              <X className="w-6 h-6" />
            </button>
            
            <img
              src={property.images[activeImageIndex].url}
              alt={property.images[activeImageIndex].caption}
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            
            {property.images.length > 1 && (
              <>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setActiveImageIndex(prev => 
                      prev === 0 ? property.images!.length - 1 : prev - 1
                    )
                  }}
                  className="absolute left-4 p-3 bg-white/10 backdrop-blur rounded-full text-white hover:bg-white/20 transition-colors"
                >
                  <ChevronLeft className="w-6 h-6" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setActiveImageIndex(prev => 
                      prev === property.images!.length - 1 ? 0 : prev + 1
                    )
                  }}
                  className="absolute right-4 p-3 bg-white/10 backdrop-blur rounded-full text-white hover:bg-white/20 transition-colors"
                >
                  <ChevronRight className="w-6 h-6" />
                </button>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}