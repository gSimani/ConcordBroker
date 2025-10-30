import { PropertyData } from '@/hooks/usePropertyData'
import { DollarSign, Home, Building, Calendar, TrendingUp, Clock, TreePine, Ruler, Info, ExternalLink, Phone, Smartphone, Mail, Linkedin, Facebook, Twitter, Globe, StickyNote, Plus, X, Edit3, Save } from 'lucide-react'
import { getUseCodeName, getUseCodeDescription } from '@/lib/useCodeMapping'
import { PropertyDataAnalyzer } from '@/utils/property-intelligence'
import { useState } from 'react'

// Contact info types
interface ContactInfo {
  id: string
  type: 'phone' | 'cell' | 'email' | 'linkedin' | 'facebook' | 'instagram' | 'twitter' | 'website' | 'note'
  value: string
  label?: string
}

// Utility function to display bed/bath info based on property type (simpler version for Overview)
function getBedBathDisplay(bcpaData: any): string {
  const propertyUse = bcpaData?.propertyUse || bcpaData?.property_use || bcpaData?.property_use_code || bcpaData?.dor_uc;
  const buildingSqFt = bcpaData?.buildingSqFt || bcpaData?.building_sqft || bcpaData?.tot_lvg_area || bcpaData?.living_area || 0;
  const hasBuilding = buildingSqFt && buildingSqFt > 0;
  const bedrooms = bcpaData?.bedrooms;
  const bathrooms = bcpaData?.bathrooms;

  // Property use codes: 0=Vacant Land, 1-3=Residential, 4-7=Commercial, 8-9=Industrial, 10-12=Agricultural
  const propertyUseNum = parseInt(String(propertyUse || '0'));

  // For Vacant Land (no building)
  if (propertyUseNum === 0 || !hasBuilding) {
    return '-';
  }

  // For Residential properties (use codes 1, 2, 3, and 4 for condos/townhomes)
  if (propertyUseNum >= 1 && propertyUseNum <= 4) {
    // If we have bedroom/bathroom data, show it
    if (bedrooms && bathrooms) {
      return `${bedrooms} / ${bathrooms}`;
    }
    // If no bed/bath data but has building, estimate based on square footage
    if (hasBuilding) {
      const estimatedBeds = Math.max(1, Math.floor(buildingSqFt / 500)); // Rough estimate: 500 sqft per bedroom
      const estimatedBaths = Math.max(1, Math.floor(estimatedBeds / 1.5)); // Rough ratio
      return `${estimatedBeds}* / ${estimatedBaths}*`;
    }
    return '- / -';
  }

  // For Non-residential properties
  return '-';
}

interface OverviewTabProps {
  data: PropertyData
}

export function OverviewTab({ data }: OverviewTabProps) {
  const { bcpaData, lastSale, investmentScore, opportunities, riskFactors } = data

  // Contact info state management
  const [contactInfos, setContactInfos] = useState<ContactInfo[]>([])
  const [isAddingContact, setIsAddingContact] = useState(false)
  const [newContactType, setNewContactType] = useState<ContactInfo['type']>('phone')
  const [newContactValue, setNewContactValue] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [notesExpanded, setNotesExpanded] = useState(false)

  // Add new contact
  const addContact = () => {
    if (newContactValue.trim()) {
      setContactInfos([...contactInfos, {
        id: Date.now().toString(),
        type: newContactType,
        value: newContactValue.trim()
      }])
      setNewContactValue('')
      setIsAddingContact(false)
    }
  }

  // Delete contact
  const deleteContact = (id: string) => {
    setContactInfos(contactInfos.filter(c => c.id !== id))
  }

  // Update contact
  const updateContact = (id: string, value: string) => {
    setContactInfos(contactInfos.map(c => c.id === id ? { ...c, value } : c))
    setEditingId(null)
  }

  // Get icon for contact type
  const getContactIcon = (type: ContactInfo['type']) => {
    const iconClass = "w-4 h-4"
    switch (type) {
      case 'phone': return <Phone className={iconClass} />
      case 'cell': return <Smartphone className={iconClass} />
      case 'email': return <Mail className={iconClass} />
      case 'linkedin': return <Linkedin className={iconClass} />
      case 'facebook': return <Facebook className={iconClass} />
      case 'instagram': return <StickyNote className={iconClass} />
      case 'twitter': return <Twitter className={iconClass} />
      case 'website': return <Globe className={iconClass} />
      case 'note': return <StickyNote className={iconClass} />
      default: return <Info className={iconClass} />
    }
  }

  // Get label for contact type
  const getContactLabel = (type: ContactInfo['type']) => {
    return type.charAt(0).toUpperCase() + type.slice(1)
  }

  // Format currency
  const formatCurrency = (value?: number) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Helper function to get tax values with fallback from multiple sources
  const getTaxValue = (fieldName: string) => {
    // Map common field names to actual database fields
    const fieldMappings: Record<string, string[]> = {
      'market_value': ['just_value', 'market_value', 'jv', 'marketValue'],
      'assessed_value': ['just_value', 'assessed_value', 'assessedValue', 'jv'],
      'land_value': ['land_val', 'land_value', 'landValue', 'lnd_val'],
      'building_value': ['building_value', 'buildingValue', 'bldg_val']
    };

    // Try mapped fields first
    if (fieldMappings[fieldName]) {
      for (const field of fieldMappings[fieldName]) {
        const value = bcpaData?.[field];
        if (value && value > 0) return value;
      }
    }

    // Special case: For vacant land, land_value = just_value
    if (fieldName === 'land_value') {
      const propertyUse = bcpaData?.dor_uc || bcpaData?.property_use_code || bcpaData?.property_use || '0';
      const isVacant = propertyUse === '0' || propertyUse === '00' ||
                       String(propertyUse).toUpperCase().includes('VACANT');
      const yearBuilt = bcpaData?.yr_blt || bcpaData?.year_built || bcpaData?.act_yr_blt;
      const noBuilding = !yearBuilt || yearBuilt === 0 || yearBuilt === '0';

      // If it's vacant land or no building exists, land value = just value
      if ((isVacant || noBuilding) && !bcpaData?.land_val && !bcpaData?.land_value) {
        const justValue = bcpaData?.just_value || bcpaData?.jv || 0;
        if (justValue > 0) return justValue;
      }
    }

    // Special case: calculate building value if not available
    if (fieldName === 'building_value') {
      const justValue = bcpaData?.just_value || bcpaData?.jv || 0;
      const landValue = bcpaData?.land_val || bcpaData?.land_value || 0;
      if (justValue > 0 && landValue > 0 && justValue > landValue) {
        return justValue - landValue;
      }
      // For vacant land, building value is 0
      const propertyUse = bcpaData?.dor_uc || bcpaData?.property_use_code || bcpaData?.property_use || '0';
      const isVacant = propertyUse === '0' || propertyUse === '00' ||
                       String(propertyUse).toUpperCase().includes('VACANT');
      if (isVacant) return 0;
    }

    // Fallback to original logic
    const apiField = fieldName.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
    return bcpaData?.[fieldName] || bcpaData?.[apiField] || 0;
  };

  return (
    <div className="grid grid-cols-3 gap-6">
      {/* Left Column - Property & Investment */}
      <div className="space-y-6">
        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent">
              Property Location
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-3">
              <div>
                <p className="text-base font-medium text-navy">
                  {bcpaData?.phy_addr1 || bcpaData?.property_address_full || 'Address Not Available'}
                </p>
                <p className="text-sm text-gray-elegant mt-1">
                  {bcpaData?.phy_city || 'Fort Lauderdale'}, FL {bcpaData?.phy_zipcd || ''}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gold">
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Property Type</p>
                  <p className="text-sm font-medium text-navy mb-1">{getUseCodeName(bcpaData?.property_use_code || bcpaData?.dor_uc || '000')}</p>
                  <p className="text-xs text-gray-elegant">{getUseCodeDescription(bcpaData?.property_use_code || bcpaData?.dor_uc || '000')}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Year Built</p>
                  <p className="text-sm font-medium text-navy">
                    {bcpaData?.year_built || bcpaData?.yr_blt || bcpaData?.yearBuilt || bcpaData?.act_yr_blt || 'Unknown'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent flex items-center">
              <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
                <DollarSign className="w-4 h-4 text-white" />
              </div>
              Investment Analysis
            </h3>
          </div>
          <div className="pt-4">
            <div className="text-center p-5 rounded-lg mb-4" style={{background: 'linear-gradient(135deg, #f4e5c2 0%, #fff 100%)'}}>
              <div className="text-4xl font-light text-gold mb-2">
                {investmentScore}/100
              </div>
              <p className="text-xs text-gray-elegant uppercase tracking-wider">Investment Score</p>
            </div>

            {/* Opportunities */}
            {opportunities.length > 0 && (
              <div className="mb-4">
                <h4 className="elegant-heading text-navy mb-2 text-xs uppercase tracking-wider">✅ Opportunities</h4>
                <ul className="space-y-2">
                  {opportunities.slice(0, 2).map((opp, index) => (
                    <li key={index} className="text-xs elegant-text bg-green-50 p-2.5 rounded border-l-2 border-gold">
                      {opp}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Risk Factors */}
            {riskFactors.length > 0 && (
              <div>
                <h4 className="elegant-heading text-navy mb-2 text-xs uppercase tracking-wider">⚠️ Risk Factors</h4>
                <ul className="space-y-2">
                  {riskFactors.slice(0, 2).map((risk, index) => (
                    <li key={index} className="text-xs elegant-text bg-orange-50 p-2.5 rounded border-l-2 border-orange-400">
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Middle Column - Valuation & Details */}
      <div className="space-y-6">
        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center">
              <DollarSign className="w-4 h-4 mr-2 text-gold" />
              Valuation Summary
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Market Value</p>
                  <p className="text-lg font-light text-navy">
                    {getTaxValue('market_value') ? formatCurrency(getTaxValue('market_value')) : '-'}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant mb-1">Assessed Value</p>
                  <p className="text-lg font-light text-navy">
                    {getTaxValue('assessed_value') ? formatCurrency(getTaxValue('assessed_value')) : '-'}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gold">
                <div className="p-3 rounded-lg hover:scale-105 transition-transform cursor-pointer bg-gold-light">
                  <p className="text-xs mb-1 uppercase tracking-wider text-gray-elegant">Land Value</p>
                  <p className="text-sm font-medium text-navy">{getTaxValue('land_value') ? formatCurrency(getTaxValue('land_value')) : '-'}</p>
                </div>
                <div className="p-3 rounded-lg hover:scale-105 transition-transform cursor-pointer bg-gray-light">
                  <p className="text-xs mb-1 uppercase tracking-wider text-gray-elegant">Building Value</p>
                  <p className="text-sm font-medium text-navy">
                    {formatCurrency(getTaxValue('building_value'))}
                  </p>
                </div>
              </div>
              {lastSale && (
                <div className="flex items-center pt-2 border-t border-gray-light">
                  <TrendingUp className="w-4 h-4 mr-2 text-blue-500" />
                  <span className="text-sm elegant-text text-navy">
                    Last Sale: {formatCurrency(parseInt(lastSale.sale_price || '0'))}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center">
              <div className="p-2 bg-navy rounded-lg mr-3">
                <Building className="w-4 h-4 text-white" />
              </div>
              Property Details
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg hover:bg-gray-50 transition-all group relative">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <Home className="w-3 h-3 mr-1" />
                    Living Area
                  </p>
                  {(() => {
                    const analysis = PropertyDataAnalyzer.analyzeLivingArea(bcpaData);
                    return (
                      <>
                        <p className="text-base font-light text-navy">
                          {analysis.value || '-'}
                        </p>
                        {analysis.reason && (
                          <div className="absolute bottom-full left-0 mb-1 hidden group-hover:block z-10">
                            <div className="bg-gray-900 text-white text-xs p-2 rounded shadow-lg whitespace-nowrap">
                              <Info className="w-3 h-3 inline mr-1" />
                              {analysis.reason}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
                <div className="p-3 rounded-lg hover:bg-gray-50 transition-all group relative">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <Calendar className="w-3 h-3 mr-1" />
                    Year Built
                  </p>
                  {(() => {
                    const analysis = PropertyDataAnalyzer.analyzeYearBuilt(bcpaData);
                    return (
                      <>
                        <p className="text-base font-light text-navy">
                          {analysis.value || '-'}
                        </p>
                        {analysis.reason && (
                          <div className="absolute bottom-full right-0 mb-1 hidden group-hover:block z-10">
                            <div className="bg-gray-900 text-white text-xs p-2 rounded shadow-lg whitespace-nowrap">
                              <Info className="w-3 h-3 inline mr-1" />
                              {analysis.reason}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg hover:bg-gray-50 transition-all group relative">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <TreePine className="w-3 h-3 mr-1" />
                    Lot Size
                  </p>
                  {(() => {
                    const analysis = PropertyDataAnalyzer.analyzeLotSize(bcpaData);
                    return (
                      <>
                        <p className="text-base font-light text-navy">
                          {analysis.value || '-'}
                        </p>
                        {analysis.reason && (
                          <div className="absolute bottom-full left-0 mb-1 hidden group-hover:block z-10">
                            <div className="bg-gray-900 text-white text-xs p-2 rounded shadow-lg whitespace-nowrap">
                              <Info className="w-3 h-3 inline mr-1" />
                              {analysis.reason}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
                <div className="p-3 rounded-lg hover:bg-gray-50 transition-all group relative">
                  <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                    <Building className="w-3 h-3 mr-1" />
                    Bed/Bath
                  </p>
                  {(() => {
                    const analysis = PropertyDataAnalyzer.analyzeBedBath(bcpaData);
                    return (
                      <>
                        <p className="text-base font-light text-navy">
                          {analysis.value || '-'}
                        </p>
                        {analysis.reason && (
                          <div className="absolute bottom-full right-0 mb-1 hidden group-hover:block z-10">
                            <div className="bg-gray-900 text-white text-xs p-2 rounded shadow-lg whitespace-nowrap">
                              <Info className="w-3 h-3 inline mr-1" />
                              {analysis.reason}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column - Recent Sale & Owner */}
      <div className="space-y-6">
        <div className="card-executive animate-elegant">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title flex items-center">
              <div className="p-2 bg-gold rounded-lg mr-3">
                <Calendar className="w-4 h-4 text-navy" />
              </div>
              Most Recent Sale
            </h3>
          </div>
          <div className="pt-4">
            {(() => {
              const saleAnalysis = PropertyDataAnalyzer.analyzeSaleData(bcpaData, lastSale);

              if (lastSale || saleAnalysis.saleInfo) {
                return (
                  <div className="space-y-3">
                    <div className="text-center p-4 rounded-lg bg-gray-light">
                      <p className="text-2xl font-light text-navy mb-2">
                        {lastSale?.sale_price ? formatCurrency(parseInt(lastSale.sale_price)) :
                         saleAnalysis.saleInfo ? saleAnalysis.saleInfo.split(' on ')[0] : '-'}
                      </p>
                      <p className="text-xs text-gray-elegant">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {lastSale?.sale_date ? new Date(lastSale.sale_date).toLocaleDateString() :
                         saleAnalysis.saleInfo ? saleAnalysis.saleInfo.split(' on ')[1] : '-'}
                      </p>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-xs uppercase tracking-wider text-gray-elegant">Type:</span>
                        <span className="text-sm font-medium badge-elegant text-navy">
                          {lastSale?.qualified_sale ? 'Qualified' : lastSale ? 'Unqualified' : '-'}
                        </span>
                      </div>
                      {lastSale?.is_distressed && (
                        <div className="flex justify-between">
                          <span className="text-xs uppercase tracking-wider text-gray-elegant">Status:</span>
                          <span className="text-sm text-red-600">Distressed</span>
                        </div>
                      )}
                      {bcpaData?.market_value && (
                        <div className="flex justify-between">
                          <span className="text-xs uppercase tracking-wider text-gray-elegant">vs Market:</span>
                          <span className="text-sm font-medium text-navy">
                            {lastSale?.sale_price && bcpaData.market_value ? ((parseInt(lastSale.sale_price) / parseInt(bcpaData.market_value)) * 100).toFixed(0) + '%' : '-'}
                          </span>
                        </div>
                      )}
                      {/* Add Official Record Link */}
                      {saleAnalysis.recordLink && (
                        <div className="pt-2 mt-2 border-t border-gold">
                          <a
                            href={saleAnalysis.recordLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center text-xs font-medium text-navy hover:underline transition-colors"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            View Official Record
                            {lastSale?.book && lastSale?.page && (
                              <span className="ml-1 text-gray-500">
                                (Book {lastSale.book}/Page {lastSale.page})
                              </span>
                            )}
                            {lastSale?.cin && (
                              <span className="ml-1 text-gray-500">
                                (CIN: {lastSale.cin})
                              </span>
                            )}
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                );
              } else {
                return (
                  <div className="text-center py-4">
                    <p className="text-gray-elegant">
                      {saleAnalysis.reason || 'No recent sales recorded'}
                    </p>
                    {bcpaData?.owner_name && bcpaData?.owner_name !== 'UNKNOWN' && (
                      <p className="text-xs text-gray-500 mt-2">
                        <Info className="w-3 h-3 inline mr-1" />
                        {saleAnalysis.reason}
                      </p>
                    )}
                  </div>
                );
              }
            })()}
          </div>
        </div>

        <div className="card-executive animate-elegant min-h-[600px]">
          <div className="elegant-card-header">
            <h3 className="elegant-card-title gold-accent">
              Property Owner
            </h3>
          </div>
          <div className="pt-4">
            <div className="space-y-4">
              {/* Owner Name & Address */}
              <div className="bg-gold-light p-4 rounded-lg border border-gold-light">
                <p className="text-lg font-semibold text-navy mb-2 break-words leading-relaxed">{bcpaData?.owner_name || 'Unknown Owner'}</p>
                {(bcpaData?.owner_addr1 || bcpaData?.owner_address) && (
                  <p className="text-sm text-gray-elegant break-words">
                    {bcpaData.owner_addr1 || bcpaData.owner_address}
                  </p>
                )}
                {bcpaData?.owner_city && (
                  <p className="text-sm text-gray-elegant break-words">
                    {bcpaData.owner_city}, {bcpaData.owner_state || 'FL'} {bcpaData.owner_zipcd || ''}
                  </p>
                )}
              </div>

              {/* Property Status Badge */}
              <div className="pt-2 border-t border-gold">
                <div className="flex items-center space-x-2">
                  {bcpaData?.homestead_exemption ? (
                    <span className="badge-elegant badge-gold text-xs">Homesteaded</span>
                  ) : (
                    <span className="badge-elegant badge-gray text-xs">Investment Property</span>
                  )}
                </div>
              </div>

              {/* Contact Information Section */}
              <div className="pt-3 border-t border-gold">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs uppercase tracking-wider text-gray-elegant font-medium">Contact Information</h4>
                  <button
                    onClick={() => setIsAddingContact(!isAddingContact)}
                    className="p-1.5 rounded-lg hover:bg-gold-light transition-colors"
                    title="Add Contact Info"
                  >
                    <Plus className="w-4 h-4 text-gold" />
                  </button>
                </div>

                {/* Add Contact Form */}
                {isAddingContact && (
                  <div className="mb-3 p-3 bg-gray-50 rounded-lg border border-gold-light animate-elegant">
                    <div className="space-y-2">
                      <select
                        value={newContactType}
                        onChange={(e) => setNewContactType(e.target.value as ContactInfo['type'])}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold text-navy"
                      >
                        <option value="phone">Phone</option>
                        <option value="cell">Cell Phone</option>
                        <option value="email">Email</option>
                        <option value="linkedin">LinkedIn</option>
                        <option value="facebook">Facebook</option>
                        <option value="instagram">Instagram</option>
                        <option value="twitter">X (Twitter)</option>
                        <option value="website">Website</option>
                        <option value="note">Note</option>
                      </select>
                      {newContactType === 'note' ? (
                        <textarea
                          value={newContactValue}
                          onChange={(e) => setNewContactValue(e.target.value)}
                          placeholder="Enter note..."
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold text-navy resize-none"
                          rows={3}
                        />
                      ) : (
                        <input
                          type="text"
                          value={newContactValue}
                          onChange={(e) => setNewContactValue(e.target.value)}
                          placeholder={`Enter ${getContactLabel(newContactType).toLowerCase()}...`}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold text-navy"
                          onKeyPress={(e) => e.key === 'Enter' && addContact()}
                        />
                      )}
                      <div className="flex space-x-2">
                        <button
                          onClick={addContact}
                          className="flex-1 px-3 py-1.5 bg-gold text-navy text-xs font-medium rounded-lg hover:bg-gold-dark transition-colors"
                        >
                          Add
                        </button>
                        <button
                          onClick={() => {
                            setIsAddingContact(false)
                            setNewContactValue('')
                          }}
                          className="flex-1 px-3 py-1.5 bg-gray-200 text-gray-700 text-xs font-medium rounded-lg hover:bg-gray-300 transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Contact List */}
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {contactInfos.map((contact) => (
                    <div
                      key={contact.id}
                      className="group flex items-start space-x-2 p-2.5 bg-white border border-gray-200 rounded-lg hover:border-gold-light hover:bg-gray-50 transition-all"
                    >
                      <div className="flex-shrink-0 p-1.5 rounded-lg bg-gold-light text-gold">
                        {getContactIcon(contact.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs uppercase tracking-wider text-gray-elegant mb-0.5">
                          {getContactLabel(contact.type)}
                        </p>
                        {editingId === contact.id ? (
                          <div className="flex space-x-2">
                            {contact.type === 'note' ? (
                              <textarea
                                defaultValue={contact.value}
                                onBlur={(e) => updateContact(contact.id, e.target.value)}
                                className="flex-1 px-2 py-1 text-sm border border-gold rounded text-navy resize-none"
                                rows={3}
                                autoFocus
                              />
                            ) : (
                              <input
                                type="text"
                                defaultValue={contact.value}
                                onBlur={(e) => updateContact(contact.id, e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && updateContact(contact.id, (e.target as HTMLInputElement).value)}
                                className="flex-1 px-2 py-1 text-sm border border-gold rounded text-navy"
                                autoFocus
                              />
                            )}
                          </div>
                        ) : (
                          <p className={`text-sm text-navy break-words ${contact.type === 'note' ? 'whitespace-pre-wrap' : ''}`}>
                            {contact.type === 'email' ? (
                              <a href={`mailto:${contact.value}`} className="hover:text-gold hover:underline">
                                {contact.value}
                              </a>
                            ) : contact.type === 'website' ? (
                              <a href={contact.value.startsWith('http') ? contact.value : `https://${contact.value}`} target="_blank" rel="noopener noreferrer" className="hover:text-gold hover:underline">
                                {contact.value}
                              </a>
                            ) : contact.type === 'linkedin' ? (
                              <a href={contact.value.startsWith('http') ? contact.value : `https://linkedin.com/in/${contact.value}`} target="_blank" rel="noopener noreferrer" className="hover:text-gold hover:underline">
                                {contact.value}
                              </a>
                            ) : contact.type === 'facebook' ? (
                              <a href={contact.value.startsWith('http') ? contact.value : `https://facebook.com/${contact.value}`} target="_blank" rel="noopener noreferrer" className="hover:text-gold hover:underline">
                                {contact.value}
                              </a>
                            ) : contact.type === 'instagram' ? (
                              <a href={contact.value.startsWith('http') ? contact.value : `https://instagram.com/${contact.value}`} target="_blank" rel="noopener noreferrer" className="hover:text-gold hover:underline">
                                {contact.value}
                              </a>
                            ) : contact.type === 'twitter' ? (
                              <a href={contact.value.startsWith('http') ? contact.value : `https://twitter.com/${contact.value}`} target="_blank" rel="noopener noreferrer" className="hover:text-gold hover:underline">
                                {contact.value}
                              </a>
                            ) : (
                              contact.value
                            )}
                          </p>
                        )}
                      </div>
                      <div className="flex-shrink-0 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => setEditingId(contact.id)}
                          className="p-1 rounded hover:bg-gold-light text-gray-600 hover:text-gold transition-colors"
                          title="Edit"
                        >
                          <Edit3 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => deleteContact(contact.id)}
                          className="p-1 rounded hover:bg-red-50 text-gray-600 hover:text-red-600 transition-colors"
                          title="Delete"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}

                  {contactInfos.length === 0 && !isAddingContact && (
                    <div className="text-center py-4">
                      <p className="text-xs text-gray-elegant">No contact information added yet</p>
                      <p className="text-xs text-gray-400 mt-1">Click + to add contact details</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
