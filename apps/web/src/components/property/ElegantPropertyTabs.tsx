import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { getUseCodeName, getUseCodeDescription } from '@/lib/useCodeMapping';
import {
  DollarSign,
  Calendar,
  Building,
  Home,
  User,
  FileText,
  Receipt,
  Briefcase,
  TreePine,
  Scale,
  MapPin,
  Clock,
  TrendingUp,
  Star,
  Gavel,
  Info
} from 'lucide-react';
import { SunbizTab } from './tabs/SunbizTab';
import { TaxesTab } from './tabs/TaxesTab';
import { PermitTab } from './tabs/PermitTab';
import { SalesTaxDeedTab } from './tabs/SalesTaxDeedTab';
import { TaxDeedSalesTab } from './tabs/TaxDeedSalesTab';
import { CorePropertyTab } from './tabs/CorePropertyTab';
import { SalesHistoryTabUpdated } from './tabs/SalesHistoryTab';
import '@/styles/elegant-property.css';

interface ElegantPropertyTabsProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  data: any;
  formatCurrency: (value: number) => string;
  formatArea: (sqft?: number) => string;
  formatDate: (year?: number, month?: number) => string;
  getPropertyUseDescription: (useCode?: string) => string;
}

export function ElegantPropertyTabs({ 
  activeTab, 
  setActiveTab, 
  data, 
  formatCurrency, 
  formatArea, 
  formatDate, 
  getPropertyUseDescription 
}: ElegantPropertyTabsProps) {
  
  // Extract bcpaData if it exists, otherwise use data directly (for backward compatibility)
  const propertyData = data.bcpaData || data;
  const salesHistory = data.sdfData || data.salesHistory || [];
  
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'core-property', label: 'Core Property Info', icon: Info },
    { id: 'valuation', label: 'Valuation', icon: DollarSign },
    { id: 'permit', label: 'Permit', icon: FileText },
    { id: 'sunbiz', label: 'Sunbiz Info', icon: Building },
    { id: 'taxes', label: 'Property Tax Info', icon: Receipt },
    { id: 'sales-tax-deed', label: 'Sales Tax Deed', icon: Scale },
    { id: 'tax-deed-sales', label: 'Tax Deed Sales', icon: Gavel },
    { id: 'owner', label: 'Owner', icon: User },
    { id: 'sales', label: 'Sales History', icon: TrendingUp },
    { id: 'building', label: 'Building', icon: Building },
    { id: 'land', label: 'Land & Legal', icon: TreePine },
    { id: 'exemptions', label: 'Exemptions', icon: FileText },
    { id: 'notes', label: 'Notes', icon: FileText }
  ];

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
      {/* Executive Tabs Navigation */}
      <div className="tabs-executive flex justify-center mb-8">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`tab-executive ${activeTab === tab.id ? 'active' : ''}`}
            >
              {Icon && <Icon className="w-4 h-4 inline mr-2" />}
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* OVERVIEW TAB */}
      <TabsContent value="overview" className="animate-elegant">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Property Location */}
          <div className="card-executive animate-elegant">
            <div className="elegant-card-header">
              <h3 className="elegant-card-title gold-accent">Property Location</h3>
            </div>
            <div className="pt-4">
              <div className="space-y-2">
                <div>
                  <p className="text-lg font-medium text-navy">
                    {propertyData.phy_addr1 || 'No Street Address'}
                  </p>
                  <p className="text-sm text-gray-elegant">
                    {propertyData.phy_city}, FL {propertyData.phy_zipcd}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gold">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-gray-elegant">Parcel ID</p>
                    <p className="text-sm font-medium text-navy">{propertyData.parcel_id}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wider text-gray-elegant">Property Type</p>
                    <p className="text-sm font-medium text-navy">{getUseCodeName(propertyData.dor_uc || propertyData.property_use_code || '000')}</p>
                    <p className="text-xs text-gray-elegant">{getUseCodeDescription(propertyData.dor_uc || propertyData.property_use_code || '000')}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Property Values */}
          <div className="card-executive animate-elegant">
            <div className="elegant-card-header">
              <h3 className="elegant-card-title gold-accent flex items-center">
                <DollarSign className="w-5 h-5 mr-2 text-gold" />
                Valuation Summary
              </h3>
            </div>
            <div className="pt-4">
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-gray-elegant">Just Value</p>
                    <p className="text-xl font-medium text-navy">{formatCurrency(propertyData.jv || propertyData.just_value)}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wider text-gray-elegant">Taxable Value</p>
                    <p className="text-xl font-medium text-navy">{formatCurrency(propertyData.tv_sd || propertyData.taxable_value)}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gold">
                  <div className="p-2 rounded-lg bg-gold-light">
                    <p className="text-xs mb-1 uppercase tracking-wider text-gray-elegant">Land Value</p>
                    <p className="font-medium text-navy">{formatCurrency(propertyData.lnd_val || propertyData.land_value)}</p>
                  </div>
                  <div className="p-2 rounded-lg bg-gray-light">
                    <p className="text-xs mb-1 uppercase tracking-wider text-gray-elegant">Building Value</p>
                    <p className="font-medium text-navy">
                      {formatCurrency((propertyData.jv || propertyData.just_value || 0) - (propertyData.lnd_val || propertyData.land_value || 0))}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Sale */}
          <div className="card-executive animate-elegant">
            <div className="elegant-card-header">
              <h3 className="elegant-card-title gold-accent flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-gold" />
                Most Recent Sale
              </h3>
            </div>
            <div className="pt-4">
              {(() => {
                // DEBUGGING: Log all data sources for sales

                // Use sales history from data structure - prioritize sales over $1000, but fallback to any sale
                const validSalesHistory = salesHistory.filter(sale => {
                  const price = typeof sale.sale_price === 'string' ? parseFloat(sale.sale_price) : sale.sale_price;
                  return price && price >= 1000;
                });

                // If no sales over $1000, get the most recent sale regardless of price
                const fallbackSalesHistory = validSalesHistory.length === 0 ?
                  salesHistory.filter(sale => {
                    const price = typeof sale.sale_price === 'string' ? parseFloat(sale.sale_price) : sale.sale_price;
                    return price && price > 0;
                  }) : [];

                let mostRecentSale = null;
                if (validSalesHistory.length > 0) {
                  mostRecentSale = validSalesHistory[0];
                } else if (fallbackSalesHistory.length > 0) {
                  mostRecentSale = fallbackSalesHistory[0];
                } else if (data.lastSale && data.lastSale.sale_price) {
                  const lastSalePrice = parseFloat(data.lastSale.sale_price);
                  if (lastSalePrice >= 1000) {
                    mostRecentSale = data.lastSale;
                  } else if (lastSalePrice > 0) {
                    mostRecentSale = data.lastSale; // Use any sale if no better option
                  }
                }

                // Extract sale price from various possible fields
                let salePrice = null;
                if (mostRecentSale) {
                  salePrice = (typeof mostRecentSale.sale_price === 'string' ? parseFloat(mostRecentSale.sale_price) : mostRecentSale.sale_price) ||
                    mostRecentSale.sales_price ||
                    mostRecentSale.price ||
                    null;
                } else {
                  // Check property data - prioritize over $1000, but accept any sale
                  const propSalePrice = propertyData.sale_prc1 || propertyData.sale_price;
                  if (propSalePrice) {
                    salePrice = parseFloat(propSalePrice);
                  }
                }

                // Only show real sales data - no mock/test data
                const saleDate = mostRecentSale ?
                  (mostRecentSale.sale_date ? new Date(mostRecentSale.sale_date) : null) :
                  (propertyData.sale_mo1 && propertyData.sale_yr1 ? `${propertyData.sale_mo1}/${propertyData.sale_yr1}` : propertyData.sale_date);

                const deedType = mostRecentSale ?
                  (mostRecentSale.deed_type || mostRecentSale.sale_type ||
                   (mostRecentSale.sale_qualification?.includes('Deed') ? mostRecentSale.sale_qualification : null)) :
                  (propertyData.qual_cd1 === 'Q' ? 'Qualified' : propertyData.qual_cd1 ? 'Unqualified' : null);

                return salePrice && salePrice > 0 ? (
                  <div className="space-y-3">
                    <div className="text-center p-3 rounded-lg bg-gray-light">
                      <p className="text-3xl font-medium text-navy">
                        {formatCurrency(salePrice)}
                      </p>
                      <p className="text-sm mt-1 text-gray-elegant">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {saleDate instanceof Date ? saleDate.toLocaleDateString() : saleDate}
                      </p>
                      {salePrice < 1000 && (
                        <p className="text-xs text-orange-600 mt-1">
                          Low-value transfer
                        </p>
                      )}
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-xs uppercase tracking-wider text-gray-elegant">Type:</span>
                        <span className="badge-elegant text-navy">
                          {deedType || 'N/A'}
                        </span>
                      </div>
                      {mostRecentSale && mostRecentSale.price_per_sqft && (
                        <div className="flex justify-between">
                          <span className="text-xs uppercase tracking-wider text-gray-elegant">$/Sq Ft:</span>
                          <span className="badge-elegant text-green-700">
                            ${mostRecentSale.price_per_sqft}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-2xl font-light elegant-text text-navy">N/A</p>
                    <p className="text-sm text-gray-elegant mt-1">
                      No recent sales recorded
                    </p>
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      </TabsContent>

      {/* VALUATION TAB */}
      <TabsContent value="valuation" className="animate-elegant">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Current Assessment */}
          <div className="card-executive animate-elegant">
            <div className="elegant-card-header">
              <h3 className="elegant-card-title gold-accent flex items-center">
                <DollarSign className="w-5 h-5 mr-2 text-gold" />
                Current Assessment
              </h3>
              <p className="text-gray-elegant">2025 Assessment Year</p>
            </div>
            <div className="pt-4">
              <div className="space-y-4">
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Just Value (Market)</p>
                  <p className="text-2xl font-medium text-navy">{formatCurrency(propertyData.jv || propertyData.just_value)}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Assessed Value (School)</p>
                  <p className="text-xl font-medium text-navy">{formatCurrency(propertyData.av_sd || propertyData.assessed_value)}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-gray-elegant">Taxable Value (School)</p>
                  <p className="text-xl font-medium text-navy">{formatCurrency(propertyData.tv_sd || propertyData.taxable_value)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Property Details */}
          <div className="card-executive animate-elegant">
            <div className="elegant-card-header">
              <h3 className="elegant-card-title gold-accent flex items-center">
                <Building className="w-5 h-5 mr-2 text-gold" />
                Property Details
              </h3>
            </div>
            <div className="pt-4">
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2 rounded-lg hover:bg-gray-light transition-all">
                    <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                      <Home className="w-3 h-3 mr-1" />
                      Building Area
                    </p>
                    <p className="text-lg font-medium text-navy">
                      {propertyData.tot_lvg_area || propertyData.living_area ? `${(propertyData.tot_lvg_area || propertyData.living_area).toLocaleString()} sq ft` : 'N/A'}
                    </p>
                  </div>
                  <div className="p-2 rounded-lg hover:bg-gray-light transition-all">
                    <p className="text-xs mb-1 flex items-center uppercase tracking-wider text-gray-elegant">
                      <Calendar className="w-3 h-3 mr-1" />
                      Year Built
                    </p>
                    <p className="text-lg font-medium text-navy">{propertyData.act_yr_blt || propertyData.year_built || 'N/A'}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Additional Info */}
          <div className="card-executive animate-elegant">
            <div className="elegant-card-header">
              <h3 className="elegant-card-title gold-accent">Additional Information</h3>
            </div>
            <div className="pt-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-gray-light">
                  <span className="text-sm text-gray-elegant">Land Square Feet</span>
                  <span className="font-medium text-navy">{(propertyData.lnd_sqfoot || propertyData.lot_size_sqft)?.toLocaleString() || 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-gray-elegant">Number of Units</span>
                  <span className="font-medium text-navy">{propertyData.no_res_unts || propertyData.units || '1'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </TabsContent>

      {/* PERMIT TAB */}
      <TabsContent value="permit" className="animate-elegant">
        <PermitTab propertyData={{ 
          bcpaData: {
            parcel_id: propertyData.parcel_id,
            property_address_street: propertyData.phy_addr1,
            property_address_city: propertyData.phy_city,
            property_address_full: `${propertyData.phy_addr1}, ${propertyData.phy_city}, FL ${propertyData.phy_zipcd}`,
            owner_name: propertyData.own_name || propertyData.owner_name,
            owner_address: propertyData.owner_address,
            living_area: propertyData.tot_lvg_area || propertyData.living_area,
            lot_size_sqft: propertyData.lnd_sqfoot || propertyData.lot_size_sqft,
            year_built: propertyData.act_yr_blt || propertyData.year_built
          }
        }} />
      </TabsContent>

      {/* SUNBIZ TAB */}
      <TabsContent value="sunbiz" className="animate-elegant">
        <SunbizTab propertyData={{
          bcpaData: {
            owner_name: propertyData.own_name || propertyData.owner_name,
            own_name: propertyData.own_name || propertyData.owner_name,
            property_address_street: propertyData.phy_addr1,
            property_address_city: propertyData.phy_city,
            property_address_full: `${propertyData.phy_addr1}, ${propertyData.phy_city}, FL ${propertyData.phy_zipcd}`,
            phy_addr1: propertyData.phy_addr1,
            phy_city: propertyData.phy_city,
            phy_zipcd: propertyData.phy_zipcd,
            parcel_id: propertyData.parcel_id
          },
          sunbizData: data.sunbizData || []
        }} />
      </TabsContent>

      {/* TAXES TAB */}
      <TabsContent value="taxes" className="animate-elegant">
        <TaxesTab data={{
          navData: data.navData || [],
          totalNavAssessment: data.totalNavAssessment || 0,
          isInCDD: data.isInCDD || false,
          bcpaData: {
            parcel_id: propertyData.parcel_id || 'N/A',
            market_value: propertyData.jv || propertyData.just_value,
            assessed_value: propertyData.av_sd || propertyData.assessed_value,
            taxable_value: propertyData.tv_sd || propertyData.taxable_value,
            land_value: propertyData.lnd_val || propertyData.land_value,
            building_value: (propertyData.jv || propertyData.just_value || 0) - (propertyData.lnd_val || propertyData.land_value || 0),
            tax_amount: propertyData.tax_amount,
            homestead_exemption: propertyData.homestead_exemption,
            owner_name: propertyData.own_name || propertyData.owner_name
          },
          sdfData: data.sdfData || { sales: [] },
          tppData: data.tppData || {},
          sunbizData: data.sunbizData || {},
          lastSale: data.lastSale || null,
          calculated_value: data.calculated_value,
          investment_score: data.investment_score,
          roi_potential: data.roi_potential,
          market_appreciation: data.market_appreciation
        }} />
      </TabsContent>

      {/* SALES TAX DEED TAB */}
      <TabsContent value="sales-tax-deed" className="animate-elegant">
        <SalesTaxDeedTab propertyData={{ 
          bcpaData: {
            parcel_id: propertyData.parcel_id || 'N/A',
            property_address_street: propertyData.phy_addr1,
            property_address_city: propertyData.phy_city,
            property_address_zip: propertyData.phy_zipcd,
            assessed_value: propertyData.jv || propertyData.just_value,
            homestead_exemption: propertyData.homestead_exemption,
            owner_name: propertyData.own_name || propertyData.owner_name
          }
        }} />
      </TabsContent>

      {/* TAX DEED SALES TAB */}
      <TabsContent value="tax-deed-sales" className="animate-elegant">
        <TaxDeedSalesTab parcelNumber={propertyData.parcel_id || propertyData.parcel_number || ''} />
      </TabsContent>

      {/* CORE PROPERTY TAB */}
      <TabsContent value="core-property" className="animate-elegant">
        <CorePropertyTab propertyData={propertyData} />
      </TabsContent>

      {/* SALES HISTORY TAB */}
      <TabsContent value="sales" className="animate-elegant">
        <SalesHistoryTabUpdated
          parcelId={propertyData.parcel_id || ''}
          data={data}
        />
      </TabsContent>

      {/* OTHER TABS - Placeholder for now */}
      {['owner', 'building', 'land', 'exemptions', 'notes'].map(tabId => (
        <TabsContent key={tabId} value={tabId} className="animate-elegant">
          <div className="card-executive animate-elegant text-center py-12">
            <div className="elegant-card-header">
              <h3 className="elegant-card-title gold-accent capitalize">{tabId} Information</h3>
            </div>
            <div className="pt-4">
              <p className="text-gray-elegant">
                {tabId.charAt(0).toUpperCase() + tabId.slice(1)} tab content coming soon
              </p>
            </div>
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}