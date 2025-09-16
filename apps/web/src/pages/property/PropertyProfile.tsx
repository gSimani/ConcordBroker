import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ElegantPropertyTabs } from '@/components/property/ElegantPropertyTabs';
import { BusinessEntitySection } from '@/components/property/BusinessEntitySection';
import '@/styles/elegant-property.css';
import { 
  Star,
  FileText
} from 'lucide-react';

interface PropertyProfileProps {
  parcelId: string;
  data: any; // Property data from API
}

// Property Use Code Descriptions
const USE_CODE_DESCRIPTIONS: Record<string, string> = {
  '000': 'Vacant Residential',
  '001': 'Single Family Residential',
  '002': 'Mobile Home',
  '003': 'Multi-Family (2-9 units)',
  '004': 'Condominium',
  '005': 'Cooperative',
  '006': 'Retirement Home',
  '100': 'Commercial - Vacant',
  '101': 'Retail Store',
  '102': 'Office Building',
  '103': 'Shopping Center',
  '104': 'Restaurant',
  '105': 'Hotel/Motel',
  '200': 'Industrial - Vacant',
  '201': 'Manufacturing',
  '202': 'Warehouse',
  '300': 'Agricultural',
  '400': 'Institutional',
  '500': 'Government',
  '082': 'Vacant Land - Conservation',
  '096': 'Vacant Land - Commercial'
};

export function PropertyProfile({ parcelId, data }: PropertyProfileProps) {
  const [activeTab, setActiveTab] = useState('overview');

  // Format currency
  const formatCurrency = (value?: number) => {
    if (!value) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format area
  const formatArea = (sqft?: number) => {
    if (!sqft) return 'N/A';
    const acres = sqft / 43560;
    if (acres > 1) {
      return `${sqft.toLocaleString()} sq ft (${acres.toFixed(2)} acres)`;
    }
    return `${sqft.toLocaleString()} sq ft`;
  };

  // Format date
  const formatDate = (year?: number, month?: number) => {
    if (!year) return 'N/A';
    if (month) {
      return new Date(year, month - 1).toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long' 
      });
    }
    return year.toString();
  };

  // Get property use description
  const getPropertyUseDescription = (useCode?: string) => {
    if (!useCode) return 'Unknown';
    return USE_CODE_DESCRIPTIONS[useCode] || `Use Code: ${useCode}`;
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Executive Header */}
      <div className="executive-header text-white">
        <div className="px-8 py-12">
          <div className="max-w-7xl mx-auto">
            <div className="animate-elegant">
              <h1 className="text-5xl elegant-heading text-white mb-3 font-bold">
                {data.phy_addr1 || 'Property Profile'}
              </h1>
              <p className="text-2xl font-light text-white opacity-90">
                {data.phy_city}, Florida {data.phy_zipcd}
              </p>
            </div>
            
            <div className="flex items-center justify-between mt-8">
              <div className="flex items-center space-x-4">
                <span className="badge-elegant badge-gold text-lg px-4 py-2">
                  {getPropertyUseDescription(data.dor_uc)}
                </span>
                <span className="text-lg font-light text-white opacity-75">
                  Investment Score: 50/100
                </span>
                <span className="text-lg font-light text-white opacity-75">
                  Parcel: {parcelId}
                </span>
              </div>
              
              <div className="flex space-x-3">
                <button className="btn-outline-executive text-gold border-gold hover:bg-gold hover:text-navy text-lg px-6 py-3">
                  <Star className="w-5 h-5 inline mr-2" />
                  <span>Watch</span>
                </button>
                <button className="btn-outline-executive text-gold border-gold hover:bg-gold hover:text-navy text-lg px-6 py-3">
                  <FileText className="w-5 h-5 inline mr-2" />
                  <span>Refresh</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Elegant Layout */}
      <div className="flex-1 px-8 py-6 max-w-7xl mx-auto">
        {/* Property Tabs */}
        <ElegantPropertyTabs
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          data={data}
          formatCurrency={formatCurrency}
          formatArea={formatArea}
          formatDate={formatDate}
          getPropertyUseDescription={getPropertyUseDescription}
        />
        
        {/* Business Entity Section */}
        <div className="mt-8">
          <BusinessEntitySection
            parcelId={parcelId}
            ownerName={data.owner_name || data.own_name || ''}
            address={data.owner_addr1 || data.own_addr1 || ''}
          />
        </div>
      </div>
    </div>
  );
}