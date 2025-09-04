import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  MapPin, 
  User, 
  Home, 
  DollarSign, 
  Calendar,
  Building,
  FileText,
  Phone,
  Mail,
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Edit,
  Save,
  Plus,
  Star
} from 'lucide-react';

interface PropertyProfileProps {
  parcelId: string;
  data: any; // NAL data
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
  const [editMode, setEditMode] = useState(false);
  const [contactInfo, setContactInfo] = useState({
    phone: '',
    email: '',
    alternatePhone: ''
  });
  const [notes, setNotes] = useState<Array<{
    id: string;
    text: string;
    priority: 'low' | 'medium' | 'high';
    timestamp: Date;
    author: string;
    status: 'open' | 'completed';
  }>>([]);

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format area
  const formatArea = (sqft: number) => {
    const acres = sqft / 43560;
    if (acres > 1) {
      return `${sqft.toLocaleString()} sq ft (${acres.toFixed(2)} acres)`;
    }
    return `${sqft.toLocaleString()} sq ft`;
  };

  // Get property type specific fields
  const getPropertyTypeFields = (useCode: string) => {
    const category = useCode.substring(0, 1);
    switch (category) {
      case '0': // Residential
        return ['bedrooms', 'bathrooms', 'pool', 'garage'];
      case '1': // Commercial
        return ['tenants', 'leaseRate', 'occupancy', 'parking'];
      case '2': // Industrial
        return ['loadingDocks', 'ceilingHeight', 'powerCapacity'];
      default:
        return [];
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header Bar */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-gray-900">
              Property Profile: {parcelId}
            </h1>
            <Badge variant={data.JV > 1000000 ? 'default' : 'secondary'}>
              {USE_CODE_DESCRIPTIONS[data.DOR_UC] || `Code: ${data.DOR_UC}`}
            </Badge>
            {data.JV_HMSTD && (
              <Badge variant="outline" className="bg-green-50">
                <Home className="w-3 h-3 mr-1" />
                Homestead
              </Badge>
            )}
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm">
              <Star className="w-4 h-4 mr-1" />
              Watch
            </Button>
            <Button variant="outline" size="sm">
              <FileText className="w-4 h-4 mr-1" />
              Report
            </Button>
            <Button 
              variant={editMode ? 'default' : 'outline'} 
              size="sm"
              onClick={() => setEditMode(!editMode)}
            >
              {editMode ? <Save className="w-4 h-4 mr-1" /> : <Edit className="w-4 h-4 mr-1" />}
              {editMode ? 'Save' : 'Edit'}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content - No Scroll */}
      <div className="flex-1 p-6 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
          <TabsList className="grid w-full grid-cols-8">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="valuation">Valuation</TabsTrigger>
            <TabsTrigger value="owner">Owner</TabsTrigger>
            <TabsTrigger value="sales">Sales History</TabsTrigger>
            <TabsTrigger value="building">Building</TabsTrigger>
            <TabsTrigger value="land">Land & Legal</TabsTrigger>
            <TabsTrigger value="exemptions">Exemptions</TabsTrigger>
            <TabsTrigger value="notes">Notes & Tasks</TabsTrigger>
          </TabsList>

          {/* OVERVIEW TAB */}
          <TabsContent value="overview" className="h-[calc(100%-3rem)] mt-4">
            <div className="grid grid-cols-3 gap-4 h-full">
              {/* Left Column - Property & Owner */}
              <div className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center">
                      <MapPin className="w-4 h-4 mr-2 text-blue-600" />
                      Property Location
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div>
                        <p className="text-lg font-semibold">
                          {data.PHY_ADDR1 || 'No Street Address'}
                        </p>
                        <p className="text-gray-600">
                          {data.PHY_CITY}, FL {data.PHY_ZIPCD}
                        </p>
                      </div>
                      <div className="grid grid-cols-2 gap-2 pt-2 border-t">
                        <div>
                          <p className="text-xs text-gray-500">Section-Township-Range</p>
                          <p className="font-medium">{data.SEC}-{data.TWN}-{data.RNG}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Neighborhood</p>
                          <p className="font-medium">{data.NBRHD_CD || 'N/A'}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center">
                      <User className="w-4 h-4 mr-2 text-green-600" />
                      Owner Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="font-semibold text-lg">{data.OWN_NAME}</p>
                        <p className="text-sm text-gray-600">
                          {data.OWN_ADDR1}<br />
                          {data.OWN_CITY}, {data.OWN_STATE} {data.OWN_ZIPCD}
                        </p>
                      </div>
                      
                      {/* Contact Info - Editable */}
                      <div className="border-t pt-3 space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <Label className="text-xs">Phone</Label>
                            <Input
                              size="sm"
                              placeholder="(954) 555-0000"
                              value={contactInfo.phone}
                              onChange={(e) => setContactInfo({...contactInfo, phone: e.target.value})}
                              disabled={!editMode}
                              className="h-8"
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Email</Label>
                            <Input
                              size="sm"
                              placeholder="email@example.com"
                              value={contactInfo.email}
                              onChange={(e) => setContactInfo({...contactInfo, email: e.target.value})}
                              disabled={!editMode}
                              className="h-8"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Middle Column - Values & Areas */}
              <div className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center">
                      <DollarSign className="w-4 h-4 mr-2 text-yellow-600" />
                      Valuation Summary
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-gray-500">Just Value</p>
                          <p className="text-xl font-bold text-green-600">
                            {formatCurrency(data.JV)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Taxable Value</p>
                          <p className="text-xl font-bold">
                            {formatCurrency(data.TV_SD)}
                          </p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                        <div>
                          <p className="text-xs text-gray-500">Land Value</p>
                          <p className="font-semibold">{formatCurrency(data.LND_VAL)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Building Value</p>
                          <p className="font-semibold">
                            {formatCurrency(data.JV - data.LND_VAL)}
                          </p>
                        </div>
                      </div>
                      {data.JV_CHNG && (
                        <div className="flex items-center pt-2 border-t">
                          <TrendingUp className="w-4 h-4 mr-2 text-blue-500" />
                          <span className="text-sm">
                            Change: {formatCurrency(data.JV_CHNG)} 
                            ({((data.JV_CHNG / (data.JV - data.JV_CHNG)) * 100).toFixed(1)}%)
                          </span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center">
                      <Building className="w-4 h-4 mr-2 text-purple-600" />
                      Property Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <p className="text-xs text-gray-500">Building Area</p>
                          <p className="font-semibold">
                            {data.TOT_LVG_AREA ? `${data.TOT_LVG_AREA.toLocaleString()} sq ft` : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Year Built</p>
                          <p className="font-semibold">{data.ACT_YR_BLT || 'N/A'}</p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <p className="text-xs text-gray-500">Land Area</p>
                          <p className="font-semibold">
                            {data.LND_SQFOOT ? formatArea(data.LND_SQFOOT) : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Units</p>
                          <p className="font-semibold">{data.NO_RES_UNTS || '1'} unit(s)</p>
                        </div>
                      </div>
                      
                      {/* Property Type Specific Fields */}
                      {data.DOR_UC?.startsWith('00') && (
                        <div className="grid grid-cols-2 gap-3 pt-2 border-t">
                          <div>
                            <p className="text-xs text-gray-500">Bedrooms</p>
                            <p className="font-semibold">{data.NO_BDRMS || 'N/A'}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Bathrooms</p>
                            <p className="font-semibold">{data.NO_BTHRMS || 'N/A'}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Right Column - Recent Sale & Quick Notes */}
              <div className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center">
                      <Calendar className="w-4 h-4 mr-2 text-red-600" />
                      Most Recent Sale
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {data.SALE_PRC1 ? (
                      <div className="space-y-3">
                        <div>
                          <p className="text-2xl font-bold text-blue-600">
                            {formatCurrency(data.SALE_PRC1)}
                          </p>
                          <p className="text-sm text-gray-600">
                            {data.SALE_MO1}/{data.SALE_YR1}
                          </p>
                        </div>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Type:</span>
                            <Badge variant={data.QUAL_CD1 === 'Q' ? 'default' : 'secondary'}>
                              {data.QUAL_CD1 === 'Q' ? 'Qualified' : 'Unqualified'}
                            </Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Book/Page:</span>
                            <span>{data.OR_BOOK1}/{data.OR_PAGE1}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Price/Value:</span>
                            <span className="font-semibold">
                              {((data.SALE_PRC1 / data.JV) * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-4 text-gray-500">
                        No recent sales recorded
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center justify-between">
                      <span className="flex items-center">
                        <Clock className="w-4 h-4 mr-2 text-indigo-600" />
                        Quick Notes
                      </span>
                      {editMode && (
                        <Button size="sm" variant="ghost">
                          <Plus className="w-3 h-3" />
                        </Button>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {notes.slice(0, 3).map((note) => (
                        <div key={note.id} className="border-l-2 border-gray-200 pl-2 py-1">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm">{note.text}</p>
                              <p className="text-xs text-gray-500 mt-1">
                                {new Date(note.timestamp).toLocaleDateString()}
                              </p>
                            </div>
                            <Badge 
                              variant={
                                note.priority === 'high' ? 'destructive' : 
                                note.priority === 'medium' ? 'default' : 'secondary'
                              }
                              className="ml-2 text-xs"
                            >
                              {note.priority}
                            </Badge>
                          </div>
                        </div>
                      ))}
                      {notes.length === 0 && (
                        <p className="text-sm text-gray-500 text-center py-4">
                          No notes yet
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* VALUATION TAB */}
          <TabsContent value="valuation" className="h-[calc(100%-3rem)] mt-4">
            <div className="grid grid-cols-2 gap-4 h-full">
              <Card>
                <CardHeader>
                  <CardTitle>Current Values</CardTitle>
                  <CardDescription>2025 Assessment Year</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-3">
                        <div>
                          <Label className="text-sm text-gray-500">Just Value (Market)</Label>
                          <p className="text-2xl font-bold">{formatCurrency(data.JV)}</p>
                        </div>
                        <div>
                          <Label className="text-sm text-gray-500">Assessed Value (School)</Label>
                          <p className="text-xl font-semibold">{formatCurrency(data.AV_SD)}</p>
                        </div>
                        <div>
                          <Label className="text-sm text-gray-500">Taxable Value (School)</Label>
                          <p className="text-xl font-semibold">{formatCurrency(data.TV_SD)}</p>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <Label className="text-sm text-gray-500">Land Value</Label>
                          <p className="text-xl font-semibold">{formatCurrency(data.LND_VAL)}</p>
                        </div>
                        <div>
                          <Label className="text-sm text-gray-500">Building Value</Label>
                          <p className="text-xl font-semibold">
                            {formatCurrency(data.JV - data.LND_VAL)}
                          </p>
                        </div>
                        <div>
                          <Label className="text-sm text-gray-500">Special Features</Label>
                          <p className="text-xl font-semibold">
                            {formatCurrency(data.SPEC_FEAT_VAL || 0)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Value Breakdown</CardTitle>
                  <CardDescription>Component Analysis</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {data.JV_HMSTD > 0 && (
                      <div className="flex justify-between items-center py-2 border-b">
                        <span>Homestead Portion</span>
                        <span className="font-semibold">{formatCurrency(data.JV_HMSTD)}</span>
                      </div>
                    )}
                    {data.JV_NON_HMSTD_RESD > 0 && (
                      <div className="flex justify-between items-center py-2 border-b">
                        <span>Non-Homestead Residential</span>
                        <span className="font-semibold">{formatCurrency(data.JV_NON_HMSTD_RESD)}</span>
                      </div>
                    )}
                    {data.NCONST_VAL > 0 && (
                      <div className="flex justify-between items-center py-2 border-b">
                        <span>New Construction</span>
                        <span className="font-semibold text-green-600">
                          +{formatCurrency(data.NCONST_VAL)}
                        </span>
                      </div>
                    )}
                    {data.DEL_VAL > 0 && (
                      <div className="flex justify-between items-center py-2 border-b">
                        <span>Demolition</span>
                        <span className="font-semibold text-red-600">
                          -{formatCurrency(data.DEL_VAL)}
                        </span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* OWNER TAB */}
          <TabsContent value="owner" className="h-[calc(100%-3rem)] mt-4">
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Primary Owner</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label>Owner Name</Label>
                      <p className="text-lg font-semibold">{data.OWN_NAME}</p>
                    </div>
                    <div>
                      <Label>Mailing Address</Label>
                      <p className="font-medium">
                        {data.OWN_ADDR1}<br />
                        {data.OWN_ADDR2 && <>{data.OWN_ADDR2}<br /></>}
                        {data.OWN_CITY}, {data.OWN_STATE} {data.OWN_ZIPCD}
                      </p>
                    </div>
                    {data.OWN_STATE_DOM && (
                      <div>
                        <Label>State of Domicile</Label>
                        <p className="font-medium">{data.OWN_STATE_DOM}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {data.FIDU_NAME && (
                <Card>
                  <CardHeader>
                    <CardTitle>Fiduciary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <Label>Fiduciary Name</Label>
                        <p className="text-lg font-semibold">{data.FIDU_NAME}</p>
                      </div>
                      <div>
                        <Label>Fiduciary Address</Label>
                        <p className="font-medium">
                          {data.FIDU_ADDR1}<br />
                          {data.FIDU_CITY}, {data.FIDU_STATE} {data.FIDU_ZIPCD}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* NOTES & TASKS TAB */}
          <TabsContent value="notes" className="h-[calc(100%-3rem)] mt-4">
            <div className="grid grid-cols-3 gap-4 h-full">
              <div className="col-span-2">
                <Card className="h-full">
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <CardTitle>Timeline & Notes</CardTitle>
                      <Button size="sm">
                        <Plus className="w-4 h-4 mr-1" />
                        Add Note
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 max-h-[400px] overflow-y-auto">
                      {notes.map((note) => (
                        <div key={note.id} className="border-l-4 border-gray-200 pl-4 py-2">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p className="font-medium">{note.text}</p>
                              <div className="flex items-center mt-2 text-xs text-gray-500">
                                <Clock className="w-3 h-3 mr-1" />
                                {new Date(note.timestamp).toLocaleString()}
                                <span className="mx-2">•</span>
                                {note.author}
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Badge 
                                variant={
                                  note.priority === 'high' ? 'destructive' : 
                                  note.priority === 'medium' ? 'default' : 'secondary'
                                }
                              >
                                {note.priority}
                              </Badge>
                              {note.status === 'completed' ? (
                                <CheckCircle2 className="w-4 h-4 text-green-500" />
                              ) : (
                                <AlertCircle className="w-4 h-4 text-yellow-500" />
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div>
                <Card>
                  <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <Button className="w-full justify-start" variant="outline">
                        <Phone className="w-4 h-4 mr-2" />
                        Call Owner
                      </Button>
                      <Button className="w-full justify-start" variant="outline">
                        <Mail className="w-4 h-4 mr-2" />
                        Send Email
                      </Button>
                      <Button className="w-full justify-start" variant="outline">
                        <Calendar className="w-4 h-4 mr-2" />
                        Schedule Visit
                      </Button>
                      <Button className="w-full justify-start" variant="outline">
                        <FileText className="w-4 h-4 mr-2" />
                        Generate Report
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Additional tabs content would go here... */}
        </Tabs>
      </div>
    </div>
  );
}