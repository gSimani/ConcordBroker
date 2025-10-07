import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  MapPin,
  Home,
  DollarSign,
  User,
  Calendar,
  Square,
  Bed,
  Bath,
  Building,
  TreePine,
  Briefcase,
  FileText,
  TrendingUp,
  Info,
  ExternalLink,
  Mail,
  Phone,
  CheckCircle
} from 'lucide-react';
import Link from 'next/link';

interface PropertyCardProps {
  property: any;
  showAllData?: boolean;
  onViewDetails?: () => void;
}

export function ComprehensivePropertyCard({ property, showAllData = false, onViewDetails }: PropertyCardProps) {
  // Format currency
  const formatCurrency = (value: number | null | undefined) => {
    if (!value || value === 0) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format number
  const formatNumber = (value: number | null | undefined) => {
    if (!value) return '0';
    return new Intl.NumberFormat('en-US').format(value);
  };

  // Format date
  const formatDate = (date: string | null | undefined) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Get property type icon
  const getPropertyIcon = () => {
    const type = property.property_type?.toLowerCase() || property.use_category?.toLowerCase();
    if (type?.includes('residential')) return <Home className="w-4 h-4" />;
    if (type?.includes('commercial')) return <Building className="w-4 h-4" />;
    if (type?.includes('industrial')) return <Briefcase className="w-4 h-4" />;
    if (type?.includes('agricultural')) return <TreePine className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  // Get status color
  const getStatusColor = () => {
    if (property.taxable_value > 1000000) return 'bg-purple-100 text-purple-800';
    if (property.taxable_value > 500000) return 'bg-blue-100 text-blue-800';
    if (property.taxable_value > 100000) return 'bg-green-100 text-green-800';
    return 'bg-gray-100 text-gray-800';
  };

  // Check if property data has been enhanced with NAP or NAL data
  const isNAPEnhanced = property?.data_source === 'NAP_Enhanced';
  const isNALEnhanced = property?.data_source === 'NAL_Enhanced';
  const isRecentlyUpdated = property?.import_date && new Date(property.import_date) > new Date('2025-09-26');

  // Check data quality indicators
  const hasEnhancedOwnerData = property?.owner_name && property?.owner_addr1 && property?.owner_city && property?.owner_state;
  const hasEnhancedAddressData = property?.phy_addr1 && property?.phy_city && property?.phy_zipcd;
  const hasEnhancedValuationData = property?.just_value && property?.assessed_value && property?.taxable_value;
  const hasEnhancedPropertyData = property?.year_built && (property?.total_living_area || property?.land_sqft);

  const isEnhanced = isNAPEnhanced || isNALEnhanced || isRecentlyUpdated ||
                    (hasEnhancedOwnerData && hasEnhancedAddressData && hasEnhancedValuationData);

  // Determine enhancement type for badge text
  const getEnhancementType = () => {
    if (isNALEnhanced) return 'NAL Enhanced';
    if (isNAPEnhanced) return 'NAP Enhanced';
    if (isRecentlyUpdated) return 'Recently Updated';
    if (hasEnhancedPropertyData) return 'Enhanced';
    return 'Enhanced';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow duration-300 h-full" id={`property-card-${property.parcel_id}`}>
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              {getPropertyIcon()}
              <span className="line-clamp-1">
                {property.address || property.full_address || 'No Address'}
              </span>
            </CardTitle>

            <div className="mt-2 space-y-1">
              <div className="flex items-center text-sm text-muted-foreground">
                <MapPin className="w-3 h-3 mr-1" />
                {property.city || 'Unknown City'}, {property.state || 'FL'} {property.zip_code || property.zip}
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="outline" className="text-xs">
                  {property.county || 'Unknown'} County
                </Badge>
                <Badge className={`text-xs ${getStatusColor()}`}>
                  {property.property_type || property.use_category || 'Unknown Type'}
                </Badge>
                {property.parcel_id && (
                  <Badge variant="secondary" className="text-xs font-mono">
                    {property.parcel_id}
                  </Badge>
                )}
                {isEnhanced && (
                  <Badge variant="secondary" className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" />
                    {getEnhancementType()}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Owner Information */}
        <div className="border-t pt-3">
          <h4 className="text-sm font-semibold mb-2 flex items-center">
            <User className="w-3 h-3 mr-1" />
            Owner Information
          </h4>
          <div className="space-y-1">
            <p className="text-sm font-medium">{property.owner_name || property.owner?.name || 'Unknown Owner'}</p>
            {(property.owner_address || property.owner?.address) && (
              <p className="text-xs text-muted-foreground">
                {property.owner_address || property.owner?.address}
                {property.owner?.city && `, ${property.owner.city}, ${property.owner.state} ${property.owner.zip}`}
              </p>
            )}
          </div>
        </div>

        {/* Property Values */}
        <div className="border-t pt-3">
          <h4 className="text-sm font-semibold mb-2 flex items-center">
            <DollarSign className="w-3 h-3 mr-1" />
            Property Values
          </h4>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-xs text-muted-foreground">Just/Market Value</p>
              <p className="text-sm font-semibold">
                {formatCurrency(property.just_value || property.market_value || property.values?.market_value)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Assessed Value</p>
              <p className="text-sm font-semibold">
                {formatCurrency(property.assessed_value || property.values?.assessed_value)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Taxable Value</p>
              <p className="text-sm font-semibold">
                {formatCurrency(property.taxable_value || property.values?.taxable_value)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Land Value</p>
              <p className="text-sm font-semibold">
                {formatCurrency(property.land_value || property.values?.land_value)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Building Value</p>
              <p className="text-sm font-semibold">
                {formatCurrency(property.building_value || property.values?.building_value)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Annual Tax</p>
              <p className="text-sm font-semibold">
                {formatCurrency(property.annual_tax || property.tax_amount)}
              </p>
            </div>
          </div>
        </div>

        {/* Property Characteristics */}
        <div className="border-t pt-3">
          <h4 className="text-sm font-semibold mb-2 flex items-center">
            <Home className="w-3 h-3 mr-1" />
            Property Details
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {(property.year_built || property.characteristics?.year_built) && (
              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3 text-muted-foreground" />
                <span className="text-xs">Built: {property.year_built || property.characteristics?.year_built}</span>
              </div>
            )}
            {(property.living_area || property.characteristics?.living_area) ? (
              <div className="flex items-center gap-1">
                <Square className="w-3 h-3 text-muted-foreground" />
                <span className="text-xs">
                  {formatNumber(property.living_area || property.characteristics?.living_area)} sq ft
                </span>
              </div>
            ) : null}
            {(property.bedrooms || property.characteristics?.bedrooms) && (
              <div className="flex items-center gap-1">
                <Bed className="w-3 h-3 text-muted-foreground" />
                <span className="text-xs">{property.bedrooms || property.characteristics?.bedrooms} beds</span>
              </div>
            )}
            {(property.bathrooms || property.characteristics?.bathrooms) && (
              <div className="flex items-center gap-1">
                <Bath className="w-3 h-3 text-muted-foreground" />
                <span className="text-xs">{property.bathrooms || property.characteristics?.bathrooms} baths</span>
              </div>
            )}
            {(property.land_sqft || property.lot_size || property.characteristics?.lot_size) && (
              <div className="flex items-center gap-1">
                <TreePine className="w-3 h-3 text-muted-foreground" />
                <span className="text-xs">
                  Lot: {formatNumber(property.land_sqft || property.lot_size || property.characteristics?.lot_size)} sq ft
                </span>
              </div>
            )}
            {(property.stories || property.characteristics?.stories) && (
              <div className="flex items-center gap-1">
                <Building className="w-3 h-3 text-muted-foreground" />
                <span className="text-xs">{property.stories || property.characteristics?.stories} stories</span>
              </div>
            )}
          </div>
        </div>

        {/* Sale Information */}
        {(property.sale_price || property.sale_date) && (
          <div className="border-t pt-3">
            <h4 className="text-sm font-semibold mb-2 flex items-center">
              <TrendingUp className="w-3 h-3 mr-1" />
              Last Sale
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {property.sale_price && (
                <div>
                  <p className="text-xs text-muted-foreground">Sale Price</p>
                  <p className="text-sm font-semibold">{formatCurrency(property.sale_price)}</p>
                </div>
              )}
              {property.sale_date && (
                <div>
                  <p className="text-xs text-muted-foreground">Sale Date</p>
                  <p className="text-sm font-semibold">{formatDate(property.sale_date)}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Additional Data (when showAllData is true) */}
        {showAllData && (
          <>
            {/* Legal Description */}
            {property.legal_description && (
              <div className="border-t pt-3">
                <h4 className="text-sm font-semibold mb-2">Legal Description</h4>
                <p className="text-xs text-muted-foreground">{property.legal_description}</p>
              </div>
            )}

            {/* Tax Information */}
            {(property.tax_district || property.millage_rate) && (
              <div className="border-t pt-3">
                <h4 className="text-sm font-semibold mb-2">Tax Information</h4>
                <div className="grid grid-cols-2 gap-2">
                  {property.tax_district && (
                    <div>
                      <p className="text-xs text-muted-foreground">Tax District</p>
                      <p className="text-sm">{property.tax_district}</p>
                    </div>
                  )}
                  {property.millage_rate && (
                    <div>
                      <p className="text-xs text-muted-foreground">Millage Rate</p>
                      <p className="text-sm">{property.millage_rate}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Metadata */}
            {property._metadata && (
              <div className="border-t pt-3">
                <h4 className="text-sm font-semibold mb-2 flex items-center">
                  <Info className="w-3 h-3 mr-1" />
                  Data Source
                </h4>
                <div className="text-xs text-muted-foreground">
                  <p>Source: {property._metadata.source || 'florida_parcels'}</p>
                  <p>Production: {property._metadata.is_production ? 'Yes' : 'No'}</p>
                  <p>Updated: {formatDate(property._metadata.timestamp)}</p>
                </div>
              </div>
            )}
          </>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Link href={`/property/${property.parcel_id}`} className="flex-1">
            <Button variant="default" className="w-full" size="sm">
              <ExternalLink className="w-3 h-3 mr-1" />
              View Full Details
            </Button>
          </Link>
          {onViewDetails && (
            <Button variant="outline" size="sm" onClick={onViewDetails}>
              <Info className="w-3 h-3" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default ComprehensivePropertyCard;