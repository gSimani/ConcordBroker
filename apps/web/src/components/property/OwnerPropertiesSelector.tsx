import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  ChevronDown,
  Building,
  MapPin,
  DollarSign,
  Home,
  User,
  CheckCircle
} from 'lucide-react';
import { useOwnerProperties } from '@/hooks/useOwnerProperties';

interface OwnerProperty {
  parcel_id: string;
  property_address_street: string;
  property_address_city: string;
  property_address_zip: string;
  owner_name: string;
  market_value: number;
  property_use_code: string;
  land_value: number;
  building_value: number;
  just_value: number;
  assessed_value: number;
  taxable_value: number;
  living_area: number;
  lot_size_sqft: number;
  year_built: number;
  sale_price: number;
  sale_date: string;
}

interface OwnerPropertiesSelectorProps {
  ownerName: string;
  currentParcelId: string;
  onPropertySelect: (property: OwnerProperty) => void;
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

export function OwnerPropertiesSelector({
  ownerName,
  currentParcelId,
  onPropertySelect
}: OwnerPropertiesSelectorProps) {
  const { ownerProperties, loading, error, hasMultipleProperties } = useOwnerProperties(
    ownerName,
    currentParcelId
  );
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>(currentParcelId);

  const formatCurrency = (value: number) => {
    if (!value) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getPropertyUseDescription = (useCode: string) => {
    return USE_CODE_DESCRIPTIONS[useCode] || useCode;
  };

  const handlePropertySelect = (property: OwnerProperty) => {
    setSelectedPropertyId(property.parcel_id);
    onPropertySelect(property);
  };

  // Don't render if no owner name or no multiple properties
  if (!ownerName || !hasMultipleProperties || loading) {
    return null;
  }

  if (error) {
    return (
      <Card className="p-4 border-yellow-200 bg-yellow-50">
        <p className="text-sm text-yellow-700">
          Unable to load other properties for this owner
        </p>
      </Card>
    );
  }

  // If 5 or fewer properties, show as tabs
  if (ownerProperties.length <= 5) {
    return (
      <Card className="p-4 mb-6 border-blue-200 bg-blue-50">
        <div className="mb-3">
          <h4 className="text-sm font-semibold text-navy flex items-center">
            <User className="w-4 h-4 mr-2 text-gold" />
            Other Properties Owned by {ownerName}
          </h4>
          <p className="text-xs text-gray-600 mt-1">
            Found {ownerProperties.length} additional propert{ownerProperties.length === 1 ? 'y' : 'ies'}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {ownerProperties.map((property) => (
            <Button
              key={property.parcel_id}
              variant={selectedPropertyId === property.parcel_id ? "default" : "outline"}
              size="sm"
              onClick={() => handlePropertySelect(property)}
              className={`relative transition-all ${
                selectedPropertyId === property.parcel_id
                  ? 'bg-navy text-white shadow-md'
                  : 'hover:bg-gold-light hover:border-gold'
              }`}
            >
              <div className="flex items-center space-x-2">
                <div className="text-left">
                  <div className="flex items-center">
                    <MapPin className="w-3 h-3 mr-1" />
                    <span className="text-xs font-medium">
                      {property.property_address_street}
                    </span>
                    {selectedPropertyId === property.parcel_id && (
                      <CheckCircle className="w-3 h-3 ml-1" />
                    )}
                  </div>
                  <div className="text-xs opacity-75">
                    {formatCurrency(property.market_value)}
                  </div>
                </div>
              </div>
            </Button>
          ))}
        </div>
      </Card>
    );
  }

  // If more than 5 properties, show as dropdown
  return (
    <Card className="p-4 mb-6 border-blue-200 bg-blue-50">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-navy flex items-center">
          <User className="w-4 h-4 mr-2 text-gold" />
          Other Properties Owned by {ownerName}
        </h4>
        <p className="text-xs text-gray-600 mt-1">
          Found {ownerProperties.length} additional properties
        </p>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            className="w-full justify-between hover:bg-gold-light hover:border-gold"
          >
            <span className="flex items-center">
              <Building className="w-4 h-4 mr-2" />
              Select Property ({ownerProperties.length} total)
            </span>
            <ChevronDown className="w-4 h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-80 max-h-96 overflow-y-auto">
          {ownerProperties.map((property) => (
            <DropdownMenuItem
              key={property.parcel_id}
              onClick={() => handlePropertySelect(property)}
              className={`cursor-pointer p-3 ${
                selectedPropertyId === property.parcel_id ? 'bg-blue-100' : ''
              }`}
            >
              <div className="flex justify-between items-start w-full">
                <div className="flex-1">
                  <div className="flex items-center mb-1">
                    <MapPin className="w-3 h-3 mr-1 text-gray-500" />
                    <span className="text-sm font-medium text-navy">
                      {property.property_address_street}
                    </span>
                    {selectedPropertyId === property.parcel_id && (
                      <CheckCircle className="w-3 h-3 ml-2 text-green-600" />
                    )}
                  </div>
                  <p className="text-xs text-gray-600 mb-1">
                    {property.property_address_city}, FL {property.property_address_zip}
                  </p>
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-medium text-green-600">
                      {formatCurrency(property.market_value)}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {getPropertyUseDescription(property.property_use_code)}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 font-mono">
                    Parcel: {property.parcel_id}
                  </p>
                </div>
              </div>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </Card>
  );
}