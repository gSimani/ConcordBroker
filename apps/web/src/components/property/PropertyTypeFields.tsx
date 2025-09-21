import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  Home,
  Building,
  Factory,
  Trees,
  School,
  ShoppingCart,
  Utensils,
  Hotel,
  Warehouse,
  Car,
  MapPin
} from 'lucide-react';

interface PropertyTypeFieldsProps {
  useCode: string;
  data: any;
  editMode: boolean;
  onChange?: (field: string, value: any) => void;
}

export function PropertyTypeFields({ useCode, data, editMode, onChange }: PropertyTypeFieldsProps) {
  const category = useCode?.substring(0, 1);
  
  // Helper to handle field changes
  const handleChange = (field: string, value: any) => {
    if (onChange) {
      onChange(field, value);
    }
  };

  // RESIDENTIAL PROPERTIES (000-099)
  if (category === '0') {
    const isMultiFamily = useCode === '003';
    const isCondo = useCode === '004';
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Home className="w-5 h-5 mr-2 text-green-600" />
            Residential Property Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {/* Basic Residential Info */}
            <div>
              <Label>Bedrooms</Label>
              <Input
                type="number"
                min="0"
                max="20"
                value={data.bedrooms || ''}
                onChange={(e) => handleChange('bedrooms', e.target.value)}
                disabled={!editMode}
                placeholder="Number of bedrooms"
              />
            </div>
            
            <div>
              <Label>Bathrooms</Label>
              <Input
                type="number"
                step="0.5"
                min="0"
                max="20"
                value={data.bathrooms || ''}
                onChange={(e) => handleChange('bathrooms', e.target.value)}
                disabled={!editMode}
                placeholder="Number of bathrooms"
              />
            </div>
            
            <div>
              <Label>Garage Spaces</Label>
              <Input
                type="number"
                min="0"
                max="10"
                value={data.garageSpaces || ''}
                onChange={(e) => handleChange('garageSpaces', e.target.value)}
                disabled={!editMode}
                placeholder="Garage spaces"
              />
            </div>

            <div>
              <Label>Stories</Label>
              <Input
                type="number"
                min="1"
                max="10"
                value={data.stories || ''}
                onChange={(e) => handleChange('stories', e.target.value)}
                disabled={!editMode}
                placeholder="Number of floors"
              />
            </div>

            <div>
              <Label>Pool</Label>
              <Select
                value={data.pool || 'none'}
                onValueChange={(value) => handleChange('pool', value)}
                disabled={!editMode}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Pool</SelectItem>
                  <SelectItem value="private">Private Pool</SelectItem>
                  <SelectItem value="community">Community Pool</SelectItem>
                  <SelectItem value="both">Both</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>View</Label>
              <Select
                value={data.view || 'none'}
                onValueChange={(value) => handleChange('view', value)}
                disabled={!editMode}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="water">Water</SelectItem>
                  <SelectItem value="golf">Golf Course</SelectItem>
                  <SelectItem value="garden">Garden</SelectItem>
                  <SelectItem value="city">City</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Multi-family specific */}
            {isMultiFamily && (
              <>
                <div>
                  <Label>Number of Units</Label>
                  <Input
                    type="number"
                    min="2"
                    max="100"
                    value={data.unitCount || ''}
                    onChange={(e) => handleChange('unitCount', e.target.value)}
                    disabled={!editMode}
                    placeholder="Total units"
                  />
                </div>
                
                <div>
                  <Label>Avg Rent/Unit</Label>
                  <Input
                    type="number"
                    value={data.avgRent || ''}
                    onChange={(e) => handleChange('avgRent', e.target.value)}
                    disabled={!editMode}
                    placeholder="$ per month"
                  />
                </div>
                
                <div>
                  <Label>Occupancy Rate</Label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={data.occupancyRate || ''}
                    onChange={(e) => handleChange('occupancyRate', e.target.value)}
                    disabled={!editMode}
                    placeholder="%"
                  />
                </div>
              </>
            )}

            {/* Condo specific */}
            {isCondo && (
              <>
                <div>
                  <Label>HOA Fee</Label>
                  <Input
                    type="number"
                    value={data.hoaFee || ''}
                    onChange={(e) => handleChange('hoaFee', e.target.value)}
                    disabled={!editMode}
                    placeholder="$ per month"
                  />
                </div>
                
                <div>
                  <Label>Floor Number</Label>
                  <Input
                    type="number"
                    min="1"
                    value={data.floorNumber || ''}
                    onChange={(e) => handleChange('floorNumber', e.target.value)}
                    disabled={!editMode}
                    placeholder="Floor"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={data.penthouse || false}
                    onCheckedChange={(checked) => handleChange('penthouse', checked)}
                    disabled={!editMode}
                  />
                  <Label>Penthouse</Label>
                </div>
              </>
            )}
          </div>

          {/* Additional Features */}
          <div className="mt-4">
            <Label>Special Features</Label>
            <div className="grid grid-cols-4 gap-2 mt-2">
              {['Waterfront', 'Corner Lot', 'Cul-de-sac', 'Gated Community', 
                'Updated Kitchen', 'New Roof', 'Solar Panels', 'Smart Home'].map(feature => (
                <div key={feature} className="flex items-center space-x-2">
                  <Switch
                    checked={data.features?.[feature] || false}
                    onCheckedChange={(checked) => 
                      handleChange('features', { ...data.features, [feature]: checked })
                    }
                    disabled={!editMode}
                  />
                  <Label className="text-sm">{feature}</Label>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // COMMERCIAL PROPERTIES (100-199)
  if (category === '1') {
    const propertySubType = useCode.substring(1, 3);
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            {propertySubType === '01' && <ShoppingCart className="w-5 h-5 mr-2 text-blue-600" />}
            {propertySubType === '02' && <Building className="w-5 h-5 mr-2 text-blue-600" />}
            {propertySubType === '04' && <Utensils className="w-5 h-5 mr-2 text-orange-600" />}
            {propertySubType === '05' && <Hotel className="w-5 h-5 mr-2 text-purple-600" />}
            {!['01', '02', '04', '05'].includes(propertySubType) && <Building className="w-5 h-5 mr-2 text-blue-600" />}
            Commercial Property Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {/* Basic Commercial Info */}
            <div>
              <Label>Rentable Area (SF)</Label>
              <Input
                type="number"
                value={data.rentableArea || ''}
                onChange={(e) => handleChange('rentableArea', e.target.value)}
                disabled={!editMode}
                placeholder="Square feet"
              />
            </div>
            
            <div>
              <Label>Number of Tenants</Label>
              <Input
                type="number"
                min="0"
                value={data.tenantCount || ''}
                onChange={(e) => handleChange('tenantCount', e.target.value)}
                disabled={!editMode}
                placeholder="Current tenants"
              />
            </div>
            
            <div>
              <Label>Occupancy Rate</Label>
              <Input
                type="number"
                min="0"
                max="100"
                value={data.occupancyRate || ''}
                onChange={(e) => handleChange('occupancyRate', e.target.value)}
                disabled={!editMode}
                placeholder="%"
              />
            </div>

            <div>
              <Label>Avg Lease Rate</Label>
              <Input
                type="number"
                step="0.01"
                value={data.avgLeaseRate || ''}
                onChange={(e) => handleChange('avgLeaseRate', e.target.value)}
                disabled={!editMode}
                placeholder="$/SF/Year"
              />
            </div>

            <div>
              <Label>Parking Spaces</Label>
              <Input
                type="number"
                min="0"
                value={data.parkingSpaces || ''}
                onChange={(e) => handleChange('parkingSpaces', e.target.value)}
                disabled={!editMode}
                placeholder="Total spaces"
              />
            </div>

            <div>
              <Label>Parking Ratio</Label>
              <Input
                type="text"
                value={data.parkingRatio || ''}
                onChange={(e) => handleChange('parkingRatio', e.target.value)}
                disabled={!editMode}
                placeholder="per 1,000 SF"
              />
            </div>

            {/* Retail specific */}
            {propertySubType === '01' && (
              <>
                <div>
                  <Label>Anchor Tenant</Label>
                  <Input
                    type="text"
                    value={data.anchorTenant || ''}
                    onChange={(e) => handleChange('anchorTenant', e.target.value)}
                    disabled={!editMode}
                    placeholder="Main tenant"
                  />
                </div>
                
                <div>
                  <Label>Traffic Count</Label>
                  <Input
                    type="number"
                    value={data.trafficCount || ''}
                    onChange={(e) => handleChange('trafficCount', e.target.value)}
                    disabled={!editMode}
                    placeholder="Daily traffic"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={data.signage || false}
                    onCheckedChange={(checked) => handleChange('signage', checked)}
                    disabled={!editMode}
                  />
                  <Label>Monument Signage</Label>
                </div>
              </>
            )}

            {/* Office specific */}
            {propertySubType === '02' && (
              <>
                <div>
                  <Label>Class</Label>
                  <Select
                    value={data.officeClass || ''}
                    onValueChange={(value) => handleChange('officeClass', value)}
                    disabled={!editMode}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select class" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="A">Class A</SelectItem>
                      <SelectItem value="B">Class B</SelectItem>
                      <SelectItem value="C">Class C</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>Elevators</Label>
                  <Input
                    type="number"
                    min="0"
                    value={data.elevators || ''}
                    onChange={(e) => handleChange('elevators', e.target.value)}
                    disabled={!editMode}
                    placeholder="Number"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={data.conferenceRooms || false}
                    onCheckedChange={(checked) => handleChange('conferenceRooms', checked)}
                    disabled={!editMode}
                  />
                  <Label>Conference Rooms</Label>
                </div>
              </>
            )}

            {/* Restaurant specific */}
            {propertySubType === '04' && (
              <>
                <div>
                  <Label>Seating Capacity</Label>
                  <Input
                    type="number"
                    value={data.seatingCapacity || ''}
                    onChange={(e) => handleChange('seatingCapacity', e.target.value)}
                    disabled={!editMode}
                    placeholder="Seats"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={data.driveThru || false}
                    onCheckedChange={(checked) => handleChange('driveThru', checked)}
                    disabled={!editMode}
                  />
                  <Label>Drive-Thru</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={data.liquorLicense || false}
                    onCheckedChange={(checked) => handleChange('liquorLicense', checked)}
                    disabled={!editMode}
                  />
                  <Label>Liquor License</Label>
                </div>
              </>
            )}

            {/* Hotel specific */}
            {propertySubType === '05' && (
              <>
                <div>
                  <Label>Number of Rooms</Label>
                  <Input
                    type="number"
                    value={data.roomCount || ''}
                    onChange={(e) => handleChange('roomCount', e.target.value)}
                    disabled={!editMode}
                    placeholder="Total rooms"
                  />
                </div>
                
                <div>
                  <Label>ADR (Avg Daily Rate)</Label>
                  <Input
                    type="number"
                    value={data.adr || ''}
                    onChange={(e) => handleChange('adr', e.target.value)}
                    disabled={!editMode}
                    placeholder="$"
                  />
                </div>
                
                <div>
                  <Label>RevPAR</Label>
                  <Input
                    type="number"
                    value={data.revpar || ''}
                    onChange={(e) => handleChange('revpar', e.target.value)}
                    disabled={!editMode}
                    placeholder="$"
                  />
                </div>
              </>
            )}
          </div>

          {/* Lease Terms */}
          <div className="mt-4 p-3 bg-gray-50 rounded">
            <Label>Major Tenants & Lease Terms</Label>
            <Textarea
              value={data.leaseNotes || ''}
              onChange={(e) => handleChange('leaseNotes', e.target.value)}
              disabled={!editMode}
              placeholder="List major tenants and their lease expiration dates..."
              className="mt-2"
              rows={3}
            />
          </div>
        </CardContent>
      </Card>
    );
  }

  // INDUSTRIAL PROPERTIES (200-299)
  if (category === '2') {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Factory className="w-5 h-5 mr-2 text-purple-600" />
            Industrial Property Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>Warehouse Space (SF)</Label>
              <Input
                type="number"
                value={data.warehouseSpace || ''}
                onChange={(e) => handleChange('warehouseSpace', e.target.value)}
                disabled={!editMode}
                placeholder="Square feet"
              />
            </div>
            
            <div>
              <Label>Office Space (SF)</Label>
              <Input
                type="number"
                value={data.officeSpace || ''}
                onChange={(e) => handleChange('officeSpace', e.target.value)}
                disabled={!editMode}
                placeholder="Square feet"
              />
            </div>
            
            <div>
              <Label>Clear Height (ft)</Label>
              <Input
                type="number"
                value={data.clearHeight || ''}
                onChange={(e) => handleChange('clearHeight', e.target.value)}
                disabled={!editMode}
                placeholder="Feet"
              />
            </div>

            <div>
              <Label>Loading Docks</Label>
              <Input
                type="number"
                min="0"
                value={data.loadingDocks || ''}
                onChange={(e) => handleChange('loadingDocks', e.target.value)}
                disabled={!editMode}
                placeholder="Number"
              />
            </div>

            <div>
              <Label>Grade-Level Doors</Label>
              <Input
                type="number"
                min="0"
                value={data.gradeDoors || ''}
                onChange={(e) => handleChange('gradeDoors', e.target.value)}
                disabled={!editMode}
                placeholder="Number"
              />
            </div>

            <div>
              <Label>Power (Amps)</Label>
              <Input
                type="number"
                value={data.powerCapacity || ''}
                onChange={(e) => handleChange('powerCapacity', e.target.value)}
                disabled={!editMode}
                placeholder="Amperage"
              />
            </div>

            <div>
              <Label>Sprinkler System</Label>
              <Select
                value={data.sprinkler || ''}
                onValueChange={(value) => handleChange('sprinkler', value)}
                disabled={!editMode}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="wet">Wet System</SelectItem>
                  <SelectItem value="dry">Dry System</SelectItem>
                  <SelectItem value="esfr">ESFR</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Crane Capacity</Label>
              <Input
                type="text"
                value={data.craneCapacity || ''}
                onChange={(e) => handleChange('craneCapacity', e.target.value)}
                disabled={!editMode}
                placeholder="Tons"
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                checked={data.railAccess || false}
                onCheckedChange={(checked) => handleChange('railAccess', checked)}
                disabled={!editMode}
              />
              <Label>Rail Access</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                checked={data.fenced || false}
                onCheckedChange={(checked) => handleChange('fenced', checked)}
                disabled={!editMode}
              />
              <Label>Fenced Yard</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                checked={data.refrigerated || false}
                onCheckedChange={(checked) => handleChange('refrigerated', checked)}
                disabled={!editMode}
              />
              <Label>Refrigerated</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                checked={data.crossDock || false}
                onCheckedChange={(checked) => handleChange('crossDock', checked)}
                disabled={!editMode}
              />
              <Label>Cross-Dock</Label>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // AGRICULTURAL PROPERTIES (300-399)
  if (category === '3') {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Trees className="w-5 h-5 mr-2 text-yellow-600" />
            Agricultural Property Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>Tillable Acres</Label>
              <Input
                type="number"
                step="0.01"
                value={data.tillableAcres || ''}
                onChange={(e) => handleChange('tillableAcres', e.target.value)}
                disabled={!editMode}
                placeholder="Acres"
              />
            </div>
            
            <div>
              <Label>Pasture Acres</Label>
              <Input
                type="number"
                step="0.01"
                value={data.pastureAcres || ''}
                onChange={(e) => handleChange('pastureAcres', e.target.value)}
                disabled={!editMode}
                placeholder="Acres"
              />
            </div>
            
            <div>
              <Label>Woodland Acres</Label>
              <Input
                type="number"
                step="0.01"
                value={data.woodlandAcres || ''}
                onChange={(e) => handleChange('woodlandAcres', e.target.value)}
                disabled={!editMode}
                placeholder="Acres"
              />
            </div>

            <div>
              <Label>Crop Type</Label>
              <Input
                type="text"
                value={data.cropType || ''}
                onChange={(e) => handleChange('cropType', e.target.value)}
                disabled={!editMode}
                placeholder="Primary crop"
              />
            </div>

            <div>
              <Label>Irrigation</Label>
              <Select
                value={data.irrigation || ''}
                onValueChange={(value) => handleChange('irrigation', value)}
                disabled={!editMode}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="drip">Drip</SelectItem>
                  <SelectItem value="sprinkler">Sprinkler</SelectItem>
                  <SelectItem value="flood">Flood</SelectItem>
                  <SelectItem value="pivot">Center Pivot</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Water Rights</Label>
              <Input
                type="text"
                value={data.waterRights || ''}
                onChange={(e) => handleChange('waterRights', e.target.value)}
                disabled={!editMode}
                placeholder="Acre-feet"
              />
            </div>

            <div className="col-span-3">
              <Label>Farm Buildings</Label>
              <Textarea
                value={data.farmBuildings || ''}
                onChange={(e) => handleChange('farmBuildings', e.target.value)}
                disabled={!editMode}
                placeholder="List barns, silos, storage buildings..."
                rows={2}
                className="mt-2"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // VACANT LAND
  if (useCode === '000' || useCode === '100' || useCode === '200') {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <MapPin className="w-5 h-5 mr-2 text-gray-600" />
            Vacant Land Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>Zoning</Label>
              <Input
                type="text"
                value={data.zoning || ''}
                onChange={(e) => handleChange('zoning', e.target.value)}
                disabled={!editMode}
                placeholder="Zoning code"
              />
            </div>
            
            <div>
              <Label>Future Land Use</Label>
              <Input
                type="text"
                value={data.futureLandUse || ''}
                onChange={(e) => handleChange('futureLandUse', e.target.value)}
                disabled={!editMode}
                placeholder="FLU designation"
              />
            </div>
            
            <div>
              <Label>Max Density</Label>
              <Input
                type="text"
                value={data.maxDensity || ''}
                onChange={(e) => handleChange('maxDensity', e.target.value)}
                disabled={!editMode}
                placeholder="Units/acre"
              />
            </div>

            <div>
              <Label>Topography</Label>
              <Select
                value={data.topography || ''}
                onValueChange={(value) => handleChange('topography', value)}
                disabled={!editMode}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="flat">Flat</SelectItem>
                  <SelectItem value="sloped">Sloped</SelectItem>
                  <SelectItem value="rolling">Rolling</SelectItem>
                  <SelectItem value="steep">Steep</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                checked={data.utilities || false}
                onCheckedChange={(checked) => handleChange('utilities', checked)}
                disabled={!editMode}
              />
              <Label>Utilities Available</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                checked={data.wetlands || false}
                onCheckedChange={(checked) => handleChange('wetlands', checked)}
                disabled={!editMode}
              />
              <Label>Wetlands Present</Label>
            </div>

            <div className="col-span-3">
              <Label>Development Potential</Label>
              <Textarea
                value={data.developmentNotes || ''}
                onChange={(e) => handleChange('developmentNotes', e.target.value)}
                disabled={!editMode}
                placeholder="Describe development potential, restrictions, opportunities..."
                rows={3}
                className="mt-2"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // DEFAULT - Unknown property type
  return (
    <Card>
      <CardHeader>
        <CardTitle>Property Type: {useCode}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-500">
          No specific fields configured for use code: {useCode}
        </p>
      </CardContent>
    </Card>
  );
}