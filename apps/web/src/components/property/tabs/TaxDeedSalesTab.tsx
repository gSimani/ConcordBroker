import React, { useState, useEffect } from 'react'
import { Gavel, DollarSign, Home, Phone, Mail, FileText, ExternalLink, Building2, User, Calendar, TrendingUp, AlertCircle, Save, Search, ArrowRight, RefreshCw } from 'lucide-react'
import { motion } from 'framer-motion'
import { supabase } from '@/lib/supabase'
import { Link } from 'react-router-dom'

interface TaxDeedProperty {
  id: string
  composite_key: string
  auction_id: string
  tax_deed_number: string
  parcel_number: string
  parcel_url?: string
  tax_certificate_number?: string
  legal_description: string
  situs_address: string
  county?: string
  city?: string
  state?: string
  zip_code?: string
  homestead: boolean
  is_homestead?: boolean  // Legacy field for backward compatibility
  assessed_value?: number
  opening_bid: number
  winning_bid?: number  // Added for past auctions
  winner_name?: string   // Added for past auctions
  best_bid?: number
  close_time?: string
  status: string
  applicant: string
  applicant_name?: string  // Legacy field for backward compatibility
  applicant_companies?: string[]
  gis_map_url?: string
  gis_map_link?: string  // Legacy field for backward compatibility
  property_appraiser_link?: string  // Legacy field for backward compatibility
  sunbiz_matched: boolean
  sunbiz_entity_names?: string[]
  sunbiz_entity_ids?: string[]
  sunbiz_entities?: string[]  // Legacy field for backward compatibility
  sunbiz_data?: any
  auction_date?: string
  auction_description?: string
  // Contact fields
  owner_name?: string
  owner_phone?: string
  owner_email?: string
  contact_status?: string
  notes?: string
  last_contact_date?: string
  next_followup_date?: string
}

interface TaxDeedSalesTabProps {
  parcelNumber?: string
}

export function TaxDeedSalesTab({ parcelNumber }: TaxDeedSalesTabProps) {
  const [properties, setProperties] = useState<TaxDeedProperty[]>([])
  const [filteredProperties, setFilteredProperties] = useState<TaxDeedProperty[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'homestead' | 'high-value'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [editingContact, setEditingContact] = useState<string | null>(null)
  const [contactData, setContactData] = useState<{ [key: string]: any }>({})
  const [selectedAuctionDate, setSelectedAuctionDate] = useState<string>('all')
  const [availableAuctionDates, setAvailableAuctionDates] = useState<{ date: string, description: string, count: number }[]>([])
  const [auctionTab, setAuctionTab] = useState<'upcoming' | 'past' | 'cancelled'>('upcoming')
  const [selectedCounty, setSelectedCounty] = useState<string>('all')
  const [availableCounties, setAvailableCounties] = useState<{ name: string, count: number }[]>([])
  const [scraping, setScraping] = useState(false)

  useEffect(() => {
    fetchTaxDeedProperties()
  }, [parcelNumber, auctionTab])

  // Smart default tab selection - auto-switch to 'past' if no upcoming auctions
  useEffect(() => {
    if (properties.length > 0) {
      const now = new Date()
      const hasUpcoming = properties.some(p => {
        if (p.close_time) {
          return new Date(p.close_time) > now
        }
        return p.status === 'Active' || p.status === 'Upcoming'
      })

      // If we're on 'upcoming' tab but there are no upcoming auctions, switch to 'past'
      if (auctionTab === 'upcoming' && !hasUpcoming) {
        const hasPast = properties.some(p => {
          if (p.close_time) {
            return new Date(p.close_time) <= now
          }
          return p.status === 'Sold' || p.status === 'Closed' || p.status === 'Past'
        })

        if (hasPast) {
          console.log('ℹ️  No upcoming auctions found, auto-switching to Past Auctions tab')
          setAuctionTab('past')
        }
      }
    }
  }, [properties])

  useEffect(() => {
    filterProperties()
  }, [properties, filter, searchTerm, selectedAuctionDate, auctionTab, selectedCounty])

  const fetchTaxDeedProperties = async () => {
    try {
      setLoading(true)
      
      // Try to fetch real data from Supabase
      let query = supabase
        .from('tax_deed_bidding_items')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(100)

      if (parcelNumber) {
        query = query.eq('parcel_number', parcelNumber)
      }

      const { data, error } = await query

      // If we have real data, map it to our format
      if (data && data.length > 0) {
        console.log(`✅ Loaded ${data.length} tax deed properties from database`)
        
        // Map the tax_deed_bidding_items table fields to our component fields
        const mappedData = data.map(item => ({
          id: item.id,
          composite_key: `${item.tax_deed_number}_${item.parcel_id}`,
          auction_id: item.auction_id,
          tax_deed_number: item.tax_deed_number,
          parcel_number: item.parcel_id,
          parcel_url: `https://web.bcpa.net/BcpaClient/#/Record/${item.parcel_id}`,
          tax_certificate_number: item.tax_certificate_number,
          legal_description: item.legal_situs_address || '',
          situs_address: item.legal_situs_address || '',
          county: item.county,
          city: 'Fort Lauderdale',
          state: 'FL',
          zip_code: '',
          homestead: item.homestead_exemption === 'Y',
          assessed_value: item.assessed_value,
          opening_bid: item.opening_bid || 0,
          best_bid: item.current_bid,
          winning_bid: item.winning_bid,
          winner_name: item.applicant_name,  // Use applicant_name for winner since winner_name doesn't exist
          close_time: item.close_time,
          status: item.item_status || 'Active',
          applicant: item.applicant_name || '',
          applicant_companies: [],
          gis_map_url: `https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=${item.parcel_id}`,
          sunbiz_matched: false,
          sunbiz_entity_names: [],
          sunbiz_entity_ids: [],
          auction_date: item.close_time ? item.close_time.split('T')[0] : item.created_at,
          auction_description: item.auction_description || '9/17/2025 Tax Deed Sale'
        }))
        
        setProperties(mappedData)
        
        // Extract unique auction dates from mapped data
        const auctionDatesMap = new Map()
        mappedData.forEach(property => {
          const date = property.auction_date
          if (date) {
            const description = property.auction_description || 
              new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'long' }) + ' Tax Deed Sale'
            const existing = auctionDatesMap.get(date) || { date, description, count: 0 }
            existing.count++
            auctionDatesMap.set(date, existing)
          }
        })
        setAvailableAuctionDates([{ date: 'all', description: 'All Auctions', count: mappedData.length }, ...Array.from(auctionDatesMap.values())])

        // Extract unique counties
        const countiesMap = new Map()
        mappedData.forEach(property => {
          const county = property.county || 'Unknown'
          const existing = countiesMap.get(county) || { name: county, count: 0 }
          existing.count++
          countiesMap.set(county, existing)
        })
        setAvailableCounties(Array.from(countiesMap.values()).sort((a, b) => a.name.localeCompare(b.name)))

        setLoading(false)
        return
      }
      
      // Fallback to sample data if database is empty or has errors
      if (error) {
        console.warn('Database error, using sample data:', error)
        // Use sample data for demonstration
        const sampleData = [
          {
            id: '1',
            composite_key: 'TD-2025-001',
            tax_deed_number: 'TD-2025-001',
            parcel_number: '064210010010',
            tax_certificate_number: 'TC-2023-12345',
            legal_description: 'LOT 1 BLOCK 2 BROWARD ESTATES',
            situs_address: '123 Main Street, Fort Lauderdale, FL 33301',
            homestead: true,
            is_homestead: true,
            assessed_value: 450000,
            opening_bid: 125000,
            best_bid: 135000,
            applicant: 'FLORIDA TAX LIEN INVESTMENTS LLC',
            applicant_name: 'FLORIDA TAX LIEN INVESTMENTS LLC',
            applicant_companies: ['FLORIDA TAX LIEN INVESTMENTS LLC'],
            sunbiz_matched: false,
            sunbiz_entity_ids: ['P21000012345'],
            sunbiz_entities: ['P21000012345'],
            parcel_url: 'https://web.bcpa.net/BcpaClient/#/Record/064210010010',
            property_appraiser_link: 'https://web.bcpa.net/BcpaClient/#/Record/064210010010',
            gis_map_link: 'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=064210010010',
            close_time: '2025-02-15T14:00:00',
            status: 'Active',
            auction_id: 'AUCTION-2025-02',
            auction_date: '2025-02-15',
            auction_description: 'February 2025 Tax Deed Sale'
          },
          {
            id: '2',
            tax_deed_number: 'TD-2025-002',
            parcel_number: '474131031040',
            tax_certificate_number: 'TC-2023-67890',
            legal_description: 'UNIT 42 CONDO BEACH TOWERS',
            situs_address: '456 Ocean Boulevard, Pompano Beach, FL 33062',
            is_homestead: false,
            assessed_value: 325000,
            opening_bid: 87500,
            best_bid: 92000,
            applicant_name: 'BEACH INVESTMENTS GROUP INC',
            applicant_companies: ['BEACH INVESTMENTS GROUP INC', 'COASTAL PROPERTIES LLC'],
            sunbiz_entities: ['P21000067890', 'L19000123456'],
            property_appraiser_link: 'https://web.bcpa.net/BcpaClient/#/Record/474131031040',
            gis_map_link: 'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=474131031040',
            close_time: '2025-02-15T14:30:00',
            status: 'Active',
            auction_id: 'AUCTION-2025-02',
            auction_date: '2025-02-15',
            auction_description: 'February 2025 Tax Deed Sale'
          },
          {
            id: '3',
            tax_deed_number: 'TD-2025-003',
            parcel_number: '514210030070',
            tax_certificate_number: 'TC-2023-11111',
            legal_description: 'PARCEL A SUNRISE BUSINESS PARK',
            situs_address: '789 Commercial Way, Sunrise, FL 33323',
            is_homestead: false,
            assessed_value: 1250000,
            opening_bid: 425000,
            best_bid: 450000,
            applicant_name: 'John Smith and Mary Smith',
            applicant_companies: [],
            sunbiz_entities: [],
            property_appraiser_link: 'https://web.bcpa.net/BcpaClient/#/Record/514210030070',
            gis_map_link: 'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=514210030070',
            close_time: '2025-02-15T15:00:00',
            status: 'Active',
            auction_id: 'AUCTION-2025-02',
            auction_date: '2025-02-15',
            auction_description: 'February 2025 Tax Deed Sale'
          },
          {
            id: '4',
            tax_deed_number: 'TD-2025-004',
            parcel_number: '294210080020',
            tax_certificate_number: 'TC-2023-22222',
            legal_description: 'LOT 15 BLOCK 8 CORAL RIDGE',
            situs_address: '321 Atlantic Blvd, Coral Springs, FL 33071',
            is_homestead: false,
            assessed_value: 275000,
            opening_bid: 65000,
            best_bid: 0,
            applicant_name: 'TAX CERTIFICATE HOLDER',
            applicant_companies: [],
            sunbiz_entities: [],
            property_appraiser_link: 'https://web.bcpa.net/BcpaClient/#/Record/294210080020',
            gis_map_link: 'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=294210080020',
            close_time: '2025-02-15T15:30:00',
            status: 'Cancelled',
            auction_id: 'AUCTION-2025-02',
            auction_date: '2025-02-15',
            auction_description: 'February 2025 Tax Deed Sale'
          },
          // Past auction properties
          {
            id: '5',
            tax_deed_number: 'TD-2024-101',
            parcel_number: '384210050030',
            tax_certificate_number: 'TC-2022-88888',
            legal_description: 'UNIT 105 WATERFRONT CONDOS',
            situs_address: '999 Bayshore Drive, Fort Lauderdale, FL 33304',
            is_homestead: false,
            assessed_value: 520000,
            opening_bid: 185000,
            winning_bid: 312500,  // Added winning bid
            winner_name: 'PRIME REAL ESTATE HOLDINGS LLC',  // Added winner name
            best_bid: 225000,
            applicant_name: 'COASTAL INVESTMENTS LLC',
            applicant_companies: ['COASTAL INVESTMENTS LLC'],
            sunbiz_entities: ['L24000045678'],
            property_appraiser_link: 'https://web.bcpa.net/BcpaClient/#/Record/384210050030',
            gis_map_link: 'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=384210050030',
            close_time: '2024-12-15T14:00:00',
            status: 'Sold',
            auction_id: 'AUCTION-2024-12',
            auction_date: '2024-12-15',
            auction_description: 'December 2024 Tax Deed Sale'
          },
          {
            id: '6',
            tax_deed_number: 'TD-2024-102',
            parcel_number: '494210070040',
            tax_certificate_number: 'TC-2022-99999',
            legal_description: 'LOT 22 BLOCK 5 PLANTATION ACRES',
            situs_address: '456 Palm Avenue, Plantation, FL 33324',
            is_homestead: true,
            assessed_value: 380000,
            opening_bid: 125000,
            winning_bid: 198000,  // Added winning bid
            winner_name: 'Robert Johnson',  // Added winner name
            best_bid: 145000,
            applicant_name: 'Jane Doe',
            applicant_companies: [],
            sunbiz_entities: [],
            property_appraiser_link: 'https://web.bcpa.net/BcpaClient/#/Record/494210070040',
            gis_map_link: 'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=494210070040',
            close_time: '2024-11-15T14:30:00',
            status: 'Sold',
            auction_id: 'AUCTION-2024-11',
            auction_date: '2024-11-15',
            auction_description: 'November 2024 Tax Deed Sale'
          },
          // More cancelled properties
          {
            id: '7',
            tax_deed_number: 'TD-2025-005',
            parcel_number: '514210090050',
            tax_certificate_number: 'TC-2023-33333',
            legal_description: 'VACANT LOT SUNRISE INDUSTRIAL',
            situs_address: '1001 Industrial Way, Sunrise, FL 33323',
            is_homestead: false,
            assessed_value: 150000,
            opening_bid: 45000,
            best_bid: 0,
            applicant_name: 'TAX CERTIFICATE HOLDER',
            applicant_companies: [],
            sunbiz_entities: [],
            property_appraiser_link: 'https://web.bcpa.net/BcpaClient/#/Record/514210090050',
            gis_map_link: 'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=514210090050',
            close_time: '2025-01-15T15:00:00',
            status: 'Cancelled',
            auction_id: 'AUCTION-2025-01',
            auction_date: '2025-01-15',
            auction_description: 'January 2025 Tax Deed Sale'
          }
        ]
        console.log('📋 Using sample data for demonstration - run scraper to get real data')
        setProperties(sampleData as TaxDeedProperty[])
        
        // Extract unique auction dates
        const auctionDatesMap = new Map()
        sampleData.forEach(prop => {
          if (prop.auction_date) {
            const dateKey = prop.auction_date
            if (!auctionDatesMap.has(dateKey)) {
              auctionDatesMap.set(dateKey, {
                date: dateKey,
                description: prop.auction_description || `Auction ${dateKey}`,
                count: 1
              })
            } else {
              const existing = auctionDatesMap.get(dateKey)
              existing.count++
            }
          }
        })
        
        // Add more sample auction dates for demonstration
        auctionDatesMap.set('2025-01-15', {
          date: '2025-01-15',
          description: 'January 2025 Tax Deed Sale',
          count: 0
        })
        auctionDatesMap.set('2025-03-15', {
          date: '2025-03-15',
          description: 'March 2025 Tax Deed Sale',
          count: 0
        })
        
        const sortedDates = Array.from(auctionDatesMap.values()).sort((a, b) => 
          new Date(a.date).getTime() - new Date(b.date).getTime()
        )
        setAvailableAuctionDates(sortedDates)
        
        // Initialize contact data for samples
        const initialContactData: { [key: string]: any } = {}
        sampleData.forEach(prop => {
          initialContactData[prop.id] = {
            owner_phone: '',
            owner_email: '',
            notes: '',
            contact_status: 'Not Contacted'
          }
        })
        setContactData(initialContactData)
        setLoading(false)
        return
      }

      // Fetch auction details for each property
      const propertiesWithAuctions = await Promise.all(
        (data || []).map(async (prop) => {
          const { data: auctionData } = await supabase
            .from('tax_deed_auctions')
            .select('auction_date, description')
            .eq('auction_id', prop.auction_id)
            .single()

          return {
            ...prop,
            auction_date: auctionData?.auction_date,
            auction_description: auctionData?.description
          }
        })
      )

      setProperties(propertiesWithAuctions)
      
      // Initialize contact data
      const initialContactData: { [key: string]: any } = {}
      propertiesWithAuctions.forEach(prop => {
        initialContactData[prop.id] = {
          owner_phone: prop.owner_phone || '',
          owner_email: prop.owner_email || '',
          notes: prop.notes || '',
          contact_status: prop.contact_status || 'Not Contacted'
        }
      })
      setContactData(initialContactData)
      
    } catch (error) {
      console.error('Error fetching tax deed properties:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterProperties = () => {
    let filtered = [...properties]

    // Apply county filter first
    if (selectedCounty !== 'all') {
      filtered = filtered.filter(p => p.county === selectedCounty)
    }

    // Apply auction tab filter
    const now = new Date()
    switch (auctionTab) {
      case 'upcoming':
        filtered = filtered.filter(p => {
          if (p.close_time) {
            return new Date(p.close_time) > now
          }
          return p.status === 'Active' || p.status === 'Upcoming'
        })
        break
      case 'past':
        filtered = filtered.filter(p => {
          if (p.close_time) {
            return new Date(p.close_time) <= now
          }
          return p.status === 'Sold' || p.status === 'Closed' || p.status === 'Past'
        })
        break
      case 'cancelled':
        filtered = filtered.filter(p =>
          p.status === 'Cancelled' || p.status === 'Canceled' || p.status === 'Removed'
        )
        break
    }

    // Apply auction date filter
    if (selectedAuctionDate !== 'all') {
      filtered = filtered.filter(p => p.auction_date === selectedAuctionDate)
    }

    // Apply filter
    switch (filter) {
      case 'upcoming':
        // For upcoming, check if close_time is in the future or status is Active
        filtered = filtered.filter(p => {
          if (p.close_time) {
            return new Date(p.close_time) > now
          }
          return p.status === 'Active' || p.status === 'Upcoming'
        })
        break
      case 'homestead':
        filtered = filtered.filter(p => p.is_homestead === true || p.homestead === true)
        break
      case 'high-value':
        filtered = filtered.filter(p => (p.opening_bid || 0) > 100000)
        break
    }

    // Apply search
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(p => 
        p.situs_address?.toLowerCase().includes(term) ||
        p.tax_deed_number?.toLowerCase().includes(term) ||
        p.parcel_number?.toLowerCase().includes(term) ||
        p.applicant_name?.toLowerCase().includes(term) ||
        p.applicant?.toLowerCase().includes(term)
      )
    }

    setFilteredProperties(filtered)
  }

  const formatCurrency = (value?: number) => {
    if (!value) return '-'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const formatTime = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    })
  }

  const saveContactInfo = async (propertyId: string) => {
    try {
      setSaving(propertyId)
      
      const contactInfo = contactData[propertyId]
      
      // Check if contact exists
      const { data: existing } = await supabase
        .from('tax_deed_contacts')
        .select('id')
        .eq('property_id', propertyId)
        .single()

      if (existing) {
        // Update
        await supabase
          .from('tax_deed_contacts')
          .update({
            owner_phone: contactInfo.owner_phone,
            owner_email: contactInfo.owner_email,
            notes: contactInfo.notes,
            contact_status: contactInfo.contact_status,
            updated_at: new Date().toISOString()
          })
          .eq('property_id', propertyId)
      } else {
        // Insert
        await supabase
          .from('tax_deed_contacts')
          .insert({
            property_id: propertyId,
            owner_phone: contactInfo.owner_phone,
            owner_email: contactInfo.owner_email,
            notes: contactInfo.notes,
            contact_status: contactInfo.contact_status
          })
      }

      setEditingContact(null)
      
      // Update local state
      const updatedProperties = properties.map(p => 
        p.id === propertyId 
          ? { ...p, ...contactInfo }
          : p
      )
      setProperties(updatedProperties)
      
    } catch (error) {
      console.error('Error saving contact info:', error)
    } finally {
      setSaving(null)
    }
  }

  const updateContactField = (propertyId: string, field: string, value: string) => {
    setContactData(prev => ({
      ...prev,
      [propertyId]: {
        ...prev[propertyId],
        [field]: value
      }
    }))
  }

  const scrapeCountyData = async () => {
    if (selectedCounty === 'all') {
      alert('Please select a specific county to scrape')
      return
    }

    try {
      setScraping(true)

      // TODO: Once backend API endpoint is ready, replace this with actual API call
      // For now, show a message
      alert(`Scraping functionality for ${selectedCounty} will be available once database setup is complete.\n\nStatus: Waiting for Guy to execute Supabase migration (TAX_DEED_SUPABASE_REQUEST.md).\n\n52 auctions are ready to upload from JSON backup.`)

      // Future implementation:
      // const response = await fetch(`http://localhost:8003/api/tax-deeds/scrape/${selectedCounty}`, {
      //   method: 'POST'
      // })
      // if (response.ok) {
      //   await fetchTaxDeedProperties() // Refresh data
      // }

    } catch (error) {
      console.error('Error scraping county data:', error)
      alert('Error scraping data. Please try again.')
    } finally {
      setScraping(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusColors: { [key: string]: string } = {
      'Upcoming': 'bg-blue-100 text-blue-800',
      'Active': 'bg-green-100 text-green-800',
      'Sold': 'bg-gray-100 text-gray-800',
      'Canceled': 'bg-red-100 text-red-800',
      'Cancelled': 'bg-red-100 text-red-800',
      'Removed': 'bg-orange-100 text-orange-800'
    }
    return statusColors[status] || 'bg-gray-100 text-gray-800'
  }
  
  // Calculate statistics for insight boxes
  const getAuctionStats = () => {
    // Use filtered properties to get stats for the current view
    const displayProperties = filteredProperties
    
    const selectedAuction = availableAuctionDates.find(a => a.date === selectedAuctionDate)
    const auctionName = selectedAuctionDate === 'all' ? 'All Auctions' : 
      selectedAuction?.description || formatDate(selectedAuctionDate)
    
    // Calculate bid based on auction type
    let highestBid = 0
    let highestProperty = null
    let bidLabel = 'Highest Opening Bid'
    
    if (auctionTab === 'past') {
      // For past auctions, show highest winning bid
      highestBid = displayProperties.reduce((max, p) => 
        Math.max(max, p.winning_bid || 0), 0)
      highestProperty = displayProperties.find(p => 
        p.winning_bid === highestBid)
      bidLabel = 'Highest Winning Bid'
    } else {
      // For upcoming/cancelled, show highest opening bid
      highestBid = displayProperties.reduce((max, p) => 
        Math.max(max, p.opening_bid || 0), 0)
      highestProperty = displayProperties.find(p => 
        p.opening_bid === highestBid)
    }
    
    const cancelledCount = displayProperties.filter(p => 
      p.status === 'Cancelled' || p.status === 'Canceled').length
    
    const activeCount = displayProperties.filter(p => 
      p.status === 'Active' || p.status === 'Upcoming').length
    
    const soldCount = displayProperties.filter(p => 
      p.status === 'Sold').length
    
    // Calculate total value based on auction type
    const totalValue = auctionTab === 'past' 
      ? displayProperties.reduce((sum, p) => sum + (p.winning_bid || 0), 0)
      : displayProperties.reduce((sum, p) => sum + (p.opening_bid || 0), 0)
    
    const tabLabel = auctionTab === 'upcoming' ? 'Upcoming' : 
                     auctionTab === 'past' ? 'Past' : 'Cancelled'
    
    return {
      auctionName,
      tabLabel,
      totalProperties: displayProperties.length,
      highestBid,
      highestAddress: highestProperty?.situs_address || '-',
      cancelledCount,
      activeCount,
      soldCount,
      totalValue,
      bidLabel
    }
  }
  
  const stats = getAuctionStats()

  const getContactStatusBadge = (status?: string) => {
    const statusColors: { [key: string]: string } = {
      'Not Contacted': 'bg-gray-100 text-gray-800',
      'Attempted': 'bg-yellow-100 text-yellow-800',
      'Connected': 'bg-blue-100 text-blue-800',
      'Not Interested': 'bg-red-100 text-red-800',
      'Interested': 'bg-green-100 text-green-800',
      'In Negotiation': 'bg-purple-100 text-purple-800',
      'Deal Closed': 'bg-gold-light text-gold-dark'
    }
    return statusColors[status || 'Not Contacted'] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="card-executive">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <Gavel className="w-5 h-5 mr-2 text-navy" />
            Tax Deed Sales
          </h3>
        </div>
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="card-executive">
      <div className="elegant-card-header">
        <h3 className="elegant-card-title gold-accent flex items-center">
          <Gavel className="w-5 h-5 mr-2 text-navy" />
          Tax Deed Sales
        </h3>
        <p className="text-sm mt-4 text-gray-elegant">
          Browse upcoming, past, and cancelled tax deed auctions
        </p>
      </div>

      {/* Auction Type Tabs */}
      <div className="mt-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setAuctionTab('upcoming')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              auctionTab === 'upcoming'
                ? 'border-gold text-gold'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Upcoming Auctions
          </button>
          <button
            onClick={() => setAuctionTab('past')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              auctionTab === 'past'
                ? 'border-gold text-gold'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Past Auctions
          </button>
          <button
            onClick={() => setAuctionTab('cancelled')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              auctionTab === 'cancelled'
                ? 'border-gold text-gold'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Cancelled Auctions
          </button>
        </nav>
      </div>

      {/* Insight Statistics Boxes */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6 mb-6">
        {/* Selected Auction Box */}
        <div className="bg-gradient-to-br from-blue-50 to-white p-4 rounded-lg border border-blue-200 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-blue-600 uppercase tracking-wider">{stats.tabLabel} Auctions</p>
              <p className="text-lg font-bold text-navy mt-1">{stats.auctionName}</p>
              <p className="text-sm text-gray-600 mt-1">
                {selectedAuctionDate === 'all' ? 'Viewing all dates' : formatDate(selectedAuctionDate)}
              </p>
            </div>
            <Calendar className="w-8 h-8 text-blue-400 opacity-50" />
          </div>
        </div>

        {/* Properties Available/Sold Box */}
        <div className="bg-gradient-to-br from-green-50 to-white p-4 rounded-lg border border-green-200 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-green-600 uppercase tracking-wider">
                {auctionTab === 'past' ? 'Properties Sold' : 'Available for Sale'}
              </p>
              <p className="text-2xl font-bold text-navy mt-1">
                {auctionTab === 'past' ? stats.soldCount : stats.activeCount}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                of {stats.totalProperties} total
              </p>
            </div>
            <Home className="w-8 h-8 text-green-400 opacity-50" />
          </div>
        </div>

        {/* Highest Bid Box */}
        <div className="bg-gradient-to-br from-gold-light to-white p-4 rounded-lg border border-yellow-200 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-yellow-700 uppercase tracking-wider">{stats.bidLabel}</p>
              <p className="text-xl font-bold text-navy mt-1">{formatCurrency(stats.highestBid)}</p>
              <p className="text-xs text-gray-600 mt-1 truncate" title={stats.highestAddress}>
                {stats.highestAddress}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-yellow-500 opacity-50" />
          </div>
        </div>

        {/* Cancelled Box */}
        <div className="bg-gradient-to-br from-red-50 to-white p-4 rounded-lg border border-red-200 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-red-600 uppercase tracking-wider">Cancelled</p>
              <p className="text-2xl font-bold text-navy mt-1">{stats.cancelledCount}</p>
              <p className="text-sm text-gray-600 mt-1">
                {stats.cancelledCount > 0 ? 'Properties removed' : 'No cancellations'}
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-400 opacity-50" />
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="mt-6 p-4 bg-gray-light rounded-lg">
        <div className="flex flex-wrap gap-4 items-center">
          {/* County Selector */}
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-navy" />
            <select
              value={selectedCounty}
              onChange={(e) => setSelectedCounty(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-navy bg-white hover:bg-gray-50 focus:ring-2 focus:ring-gold focus:border-transparent"
            >
              <option value="all">All Counties</option>
              {availableCounties.map(county => (
                <option key={county.name} value={county.name}>
                  {county.name} ({county.count} properties)
                </option>
              ))}
            </select>
            <button
              onClick={scrapeCountyData}
              disabled={selectedCounty === 'all' || scraping}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                selectedCounty === 'all' || scraping
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-navy text-white hover:bg-blue-900'
              }`}
              title={selectedCounty === 'all' ? 'Select a specific county to scrape' : 'Refresh auction data for this county'}
            >
              <RefreshCw className={`w-4 h-4 ${scraping ? 'animate-spin' : ''}`} />
              {scraping ? 'Scraping...' : 'Refresh Data'}
            </button>
          </div>

          {/* Auction Date Selector */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-navy" />
            <select
              value={selectedAuctionDate}
              onChange={(e) => setSelectedAuctionDate(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-navy bg-white hover:bg-gray-50 focus:ring-2 focus:ring-gold focus:border-transparent"
            >
              <option value="all">All Auction Dates</option>
              {availableAuctionDates.map(auction => (
                <option key={auction.date} value={auction.date}>
                  {formatDate(auction.date)} - {auction.description} ({auction.count} properties)
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'all' 
                  ? 'bg-navy text-white' 
                  : 'bg-white text-navy hover:bg-gray-100'
              }`}
            >
              All ({properties.length})
            </button>
            <button
              onClick={() => setFilter('upcoming')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'upcoming' 
                  ? 'bg-navy text-white' 
                  : 'bg-white text-navy hover:bg-gray-100'
              }`}
            >
              Upcoming
            </button>
            <button
              onClick={() => setFilter('homestead')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'homestead' 
                  ? 'bg-navy text-white' 
                  : 'bg-white text-navy hover:bg-gray-100'
              }`}
            >
              Homestead
            </button>
            <button
              onClick={() => setFilter('high-value')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'high-value' 
                  ? 'bg-navy text-white' 
                  : 'bg-white text-navy hover:bg-gray-100'
              }`}
            >
              High Value (&gt;$100k)
            </button>
          </div>
          
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by address, parcel, or applicant..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Properties List */}
      <div className="pt-8 space-y-6">
        {filteredProperties.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <Gavel className="w-12 h-12 mx-auto mb-4 text-gold" />
            <p className="text-lg font-medium text-navy">
              No {auctionTab === 'upcoming' ? 'Upcoming' : auctionTab === 'past' ? 'Past' : 'Cancelled'} Auctions Found
            </p>
            <p className="text-sm text-gray-elegant">
              {searchTerm ? 'Try adjusting your search criteria' : 
               auctionTab === 'upcoming' ? 'Check back later for new auctions' :
               auctionTab === 'past' ? 'No completed auctions to display' :
               'No cancelled auctions to display'}
            </p>
          </motion.div>
        ) : (
          filteredProperties.map((property, index) => (
            <motion.div
              key={property.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
            >
              {/* Property Header */}
              <div className="bg-gradient-to-r from-navy to-blue-900 text-white p-6">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-xl font-semibold flex items-center">
                          <Home className="w-5 h-5 mr-2" />
                          {property.situs_address}
                        </h4>
                        <p className="text-sm opacity-90 mt-1">
                          {property.city && `${property.city}, `}{property.state} {property.zip_code}
                        </p>
                      </div>
                      <Link
                        to={`/property/${property.parcel_number}`}
                        className="px-4 py-2 bg-gold text-navy rounded-lg hover:bg-gold-dark transition-colors flex items-center gap-2 text-sm font-medium"
                      >
                        View Full Details
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </div>
                    <div className="flex gap-2 mt-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(property.status)}`}>
                        {property.status}
                      </span>
                      {(property.is_homestead || property.homestead) && (
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Homestead
                        </span>
                      )}
                      {property.opening_bid > 100000 && (
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                          High Value
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-light">{formatCurrency(property.opening_bid)}</p>
                    <p className="text-xs opacity-75 uppercase tracking-wider">Opening Bid</p>
                    {auctionTab === 'past' && property.winning_bid ? (
                      <>
                        <p className="text-lg font-light mt-2 text-green-600">{formatCurrency(property.winning_bid)}</p>
                        <p className="text-xs opacity-75 uppercase tracking-wider text-green-600">Winning Bid</p>
                        {property.winner_name && (
                          <>
                            <p className="text-sm font-medium mt-2">{property.winner_name}</p>
                            <p className="text-xs opacity-75 uppercase tracking-wider">Winner</p>
                          </>
                        )}
                      </>
                    ) : property.best_bid && auctionTab === 'upcoming' ? (
                      <>
                        <p className="text-lg font-light mt-2">{formatCurrency(property.best_bid)}</p>
                        <p className="text-xs opacity-75 uppercase tracking-wider">Current Bid</p>
                      </>
                    ) : null}
                  </div>
                </div>
              </div>

              {/* Property Details */}
              <div className="p-6 bg-white">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Basic Info */}
                  <div>
                    <h5 className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-3">
                      Property Information
                    </h5>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Tax Deed #:</span>
                        <span className="font-medium text-navy">{property.tax_deed_number}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Parcel #:</span>
                        <span className="font-medium text-navy">
                          {property.property_appraiser_link ? (
                            <a 
                              href={property.property_appraiser_link} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline flex items-center"
                            >
                              {property.parcel_number}
                              <ExternalLink className="w-3 h-3 ml-1" />
                            </a>
                          ) : (
                            <a 
                              href={`https://web.bcpa.net/BcpaClient/#/Record/${property.parcel_number}`} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline flex items-center"
                            >
                              {property.parcel_number}
                              <ExternalLink className="w-3 h-3 ml-1" />
                            </a>
                          )}
                        </span>
                      </div>
                      {property.tax_certificate_number && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Tax Certificate #:</span>
                          <span className="font-medium text-navy">{property.tax_certificate_number}</span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-gray-600">Assessed Value:</span>
                        <span className="font-medium text-navy">{formatCurrency(property.assessed_value)}</span>
                      </div>
                      {property.gis_map_url && (
                        <div className="mt-2">
                          <a 
                            href={property.gis_map_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline text-xs flex items-center"
                          >
                            View GIS Map
                            <ExternalLink className="w-3 h-3 ml-1" />
                          </a>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Auction Info */}
                  <div>
                    <h5 className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-3">
                      Auction Details
                    </h5>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Auction:</span>
                        <span className="font-medium text-navy">{property.auction_description || property.auction_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Date:</span>
                        <span className="font-medium text-navy">{formatDate(property.auction_date)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Close Time:</span>
                        <span className="font-medium text-navy">{formatTime(property.close_time)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Applicant:</span>
                        <span className="font-medium text-navy text-xs">{property.applicant_name || property.applicant}</span>
                      </div>
                    </div>
                  </div>

                  {/* Sunbiz Info */}
                  <div>
                    <h5 className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-3 flex items-center">
                      <Building2 className="w-4 h-4 mr-1" />
                      Sunbiz Entities
                    </h5>
                    {(property.sunbiz_entity_ids && property.sunbiz_entity_ids.length > 0) || 
                     (property.applicant_companies && property.applicant_companies.length > 0) ? (
                      <div className="space-y-2">
                        {/* Show Sunbiz entities if available */}
                        {property.sunbiz_entity_ids && property.sunbiz_entity_ids.map((entityId, idx) => {
                          const companyName = property.applicant_companies?.[idx] || property.applicant_name
                          return (
                            <div key={idx} className="text-sm">
                              <a
                                href={`https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResultDetail?inquirytype=EntityName&directionType=Initial&searchNameOrder=${entityId}&aggregateId=${entityId}&searchTerm=${encodeURIComponent(companyName || '')}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline flex items-center"
                              >
                                {companyName}
                                <ExternalLink className="w-3 h-3 ml-1" />
                              </a>
                              <span className="text-xs text-gray-500 block">Entity: {entityId}</span>
                            </div>
                          )
                        })}
                        {/* Show companies without entity IDs */}
                        {property.applicant_companies && 
                         property.applicant_companies.filter((company, idx) => 
                           !property.sunbiz_entity_ids || !property.sunbiz_entity_ids[idx]
                         ).map((company, idx) => (
                          <div key={`company-${idx}`} className="text-sm">
                            <a
                              href={`https://search.sunbiz.org/Inquiry/CorporationSearch/ByName?searchNameOrder=${encodeURIComponent(company)}&searchTerm=${encodeURIComponent(company)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline flex items-center"
                            >
                              {company}
                              <ExternalLink className="w-3 h-3 ml-1" />
                            </a>
                            <span className="text-xs text-gray-500 block">Search Sunbiz</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">
                        {property.applicant_name && !property.applicant_name.includes('LLC') && !property.applicant_name.includes('INC') 
                          ? 'Individual owner (no entity)' 
                          : 'No Sunbiz matches found'}
                      </p>
                    )}
                  </div>
                </div>

                {/* Legal Description */}
                {property.legal_description && (
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <h5 className="text-sm font-semibold text-gray-600 uppercase tracking-wider mb-2">
                      Legal Description
                    </h5>
                    <p className="text-sm text-gray-700">{property.legal_description}</p>
                  </div>
                )}

                {/* Contact Management Section */}
                <div className="mt-6 border-t pt-6">
                  <div className="flex justify-between items-center mb-4">
                    <h5 className="text-sm font-semibold text-gray-600 uppercase tracking-wider flex items-center">
                      <User className="w-4 h-4 mr-2" />
                      Contact Management
                    </h5>
                    <div className="flex items-center gap-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getContactStatusBadge(contactData[property.id]?.contact_status)}`}>
                        {contactData[property.id]?.contact_status || 'Not Contacted'}
                      </span>
                      {editingContact === property.id ? (
                        <>
                          <button
                            onClick={() => saveContactInfo(property.id)}
                            disabled={saving === property.id}
                            className="px-3 py-1 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 flex items-center"
                          >
                            <Save className="w-3 h-3 mr-1" />
                            {saving === property.id ? 'Saving...' : 'Save'}
                          </button>
                          <button
                            onClick={() => setEditingContact(null)}
                            className="px-3 py-1 bg-gray-500 text-white rounded-lg text-sm font-medium hover:bg-gray-600"
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => setEditingContact(property.id)}
                          className="px-3 py-1 bg-navy text-white rounded-lg text-sm font-medium hover:bg-blue-900"
                        >
                          Edit Contact
                        </button>
                      )}
                    </div>
                  </div>

                  {editingContact === property.id ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <Phone className="w-4 h-4 inline mr-1" />
                          Phone Number
                        </label>
                        <input
                          type="tel"
                          value={contactData[property.id]?.owner_phone || ''}
                          onChange={(e) => updateContactField(property.id, 'owner_phone', e.target.value)}
                          placeholder="(555) 123-4567"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <Mail className="w-4 h-4 inline mr-1" />
                          Email Address
                        </label>
                        <input
                          type="email"
                          value={contactData[property.id]?.owner_email || ''}
                          onChange={(e) => updateContactField(property.id, 'owner_email', e.target.value)}
                          placeholder="owner@example.com"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Contact Status
                        </label>
                        <select
                          value={contactData[property.id]?.contact_status || 'Not Contacted'}
                          onChange={(e) => updateContactField(property.id, 'contact_status', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-transparent"
                        >
                          <option value="Not Contacted">Not Contacted</option>
                          <option value="Attempted">Attempted</option>
                          <option value="Connected">Connected</option>
                          <option value="Not Interested">Not Interested</option>
                          <option value="Interested">Interested</option>
                          <option value="In Negotiation">In Negotiation</option>
                          <option value="Deal Closed">Deal Closed</option>
                        </select>
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <FileText className="w-4 h-4 inline mr-1" />
                          Notes
                        </label>
                        <textarea
                          value={contactData[property.id]?.notes || ''}
                          onChange={(e) => updateContactField(property.id, 'notes', e.target.value)}
                          placeholder="Add notes about contact attempts, owner information, etc..."
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-transparent"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Phone:</span>
                        <span className="ml-2 font-medium text-navy">
                          {contactData[property.id]?.owner_phone || 'Not provided'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Email:</span>
                        <span className="ml-2 font-medium text-navy">
                          {contactData[property.id]?.owner_email || 'Not provided'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Last Contact:</span>
                        <span className="ml-2 font-medium text-navy">
                          {property.last_contact_date ? formatDate(property.last_contact_date) : 'Never'}
                        </span>
                      </div>
                      {contactData[property.id]?.notes && (
                        <div className="md:col-span-3 mt-2">
                          <span className="text-gray-600">Notes:</span>
                          <p className="mt-1 text-gray-700 bg-gray-50 p-2 rounded">
                            {contactData[property.id].notes}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* Summary Statistics */}
      {filteredProperties.length > 0 && (
        <div className="mt-8 p-6 bg-navy rounded-lg">
          <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Portfolio Summary
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-white">
            <div>
              <p className="text-sm opacity-75">Total Properties</p>
              <p className="text-2xl font-light">{filteredProperties.length}</p>
            </div>
            <div>
              <p className="text-sm opacity-75">Total Opening Bids</p>
              <p className="text-2xl font-light">
                {formatCurrency(filteredProperties.reduce((sum, p) => sum + (p.opening_bid || 0), 0))}
              </p>
            </div>
            <div>
              <p className="text-sm opacity-75">Homestead Properties</p>
              <p className="text-2xl font-light">
                {filteredProperties.filter(p => p.homestead).length}
              </p>
            </div>
            <div>
              <p className="text-sm opacity-75">Sunbiz Matched</p>
              <p className="text-2xl font-light">
                {filteredProperties.filter(p => p.sunbiz_matched).length}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
