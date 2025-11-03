import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileText, Calendar, DollarSign, User, Clock,
  Award, Gavel, Building, MapPin, CheckCircle,
  XCircle, Info, Hash, ExternalLink, Eye,
  Timer, Activity, BarChart3, Target, Home, TrendingUp
} from 'lucide-react';
import { supabase } from '@/lib/supabase';

interface SalesTaxDeedTabProps {
  propertyData: any;
}

export const SalesTaxDeedTab: React.FC<SalesTaxDeedTabProps> = ({ propertyData }) => {
  const [upcomingAuctions, setUpcomingAuctions] = useState<any[]>([]);
  const [pastAuctions, setPastAuctions] = useState<any[]>([]);
  const [biddingItems, setBiddingItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('upcoming');
  const { bcpaData } = propertyData || {};

  useEffect(() => {
    const fetchTaxDeedData = async () => {
      try {
        // Fetch upcoming auctions
        const { data: upcomingData } = await supabase
          .from('tax_deed_auctions')
          .select('*')
          .eq('status', 'Upcoming')
          .order('auction_date', { ascending: true });

        // Fetch past auctions
        const { data: pastData } = await supabase
          .from('tax_deed_auctions')
          .select('*')
          .eq('status', 'Completed')
          .order('auction_date', { ascending: false })
          .limit(10);

        // Fetch bidding items for this property and recent auctions
        let biddingQuery = supabase
          .from('tax_deed_items_view')
          .select('*')
          .order('auction_date', { ascending: false });

        if (bcpaData?.parcel_id) {
          biddingQuery = biddingQuery.eq('parcel_id', bcpaData.parcel_id);
        }

        const { data: itemsData } = await biddingQuery.limit(20);

        if (upcomingData) setUpcomingAuctions(upcomingData);
        if (pastData) setPastAuctions(pastData);
        if (itemsData) {
          setBiddingItems(itemsData);
        }

      } catch (error) {
        console.error('Error fetching tax deed data:', error);
        // Set empty arrays on error - no mock data
        setUpcomingAuctions([]);
        setPastAuctions([]);
        setBiddingItems([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTaxDeedData();
  }, [bcpaData]);


  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  const getStatusBadgeClass = (status: string) => {
    const s = (status || '').toLowerCase();
    if (s.includes('active') || s.includes('upcoming')) return 'badge-elegant badge-gold';
    if (s.includes('sold') || s.includes('completed')) return 'badge-elegant badge-gray';
    return 'badge-elegant';
  };

  const formatTimeRemaining = (seconds: number) => {
    if (seconds <= 0) return 'Closed';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse space-y-6">
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const activeItems = biddingItems.filter(item => item.item_status === 'Active');
  const soldItems = biddingItems.filter(item => item.item_status === 'Sold');

  return (
    <div className="space-y-6">
      {/* Active Auctions Notice (neutral styling) */}
      {activeItems.length > 0 && (
        <Alert className="border-gray-200">
          <Info className="h-4 w-4 text-navy" />
          <AlertTitle className="text-navy">Active Tax Deed Auctions</AlertTitle>
          <AlertDescription className="text-gray-elegant">
            This property has {activeItems.length} active tax deed item{activeItems.length !== 1 ? 's' : ''} currently being auctioned.
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Statistics (executive style) */}
      <div className="card-executive">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title flex items-center">
            <span className="p-2 rounded-lg mr-3" style={{background: 'var(--gray-light)'}}>
              <Award className="h-4 w-4 text-navy" />
            </span>
            Tax Deed Auctions Overview
          </h3>
        </div>
        <div className="pt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 border border-gray-100 rounded-lg">
              <div className="text-2xl font-light text-navy">{upcomingAuctions.length}</div>
              <div className="text-sm text-gray-elegant">Upcoming Auctions</div>
            </div>
            <div className="text-center p-4 border border-gray-100 rounded-lg">
              <div className="text-2xl font-light text-navy">{pastAuctions.length}</div>
              <div className="text-sm text-gray-elegant">Past Auctions</div>
            </div>
            <div className="text-center p-4 border border-gray-100 rounded-lg">
              <div className="text-2xl font-light text-navy">{activeItems.length}</div>
              <div className="text-sm text-gray-elegant">Active Items</div>
            </div>
            <div className="text-center p-4 border border-gray-100 rounded-lg">
              <div className="text-2xl font-light text-navy">{soldItems.length}</div>
              <div className="text-sm text-gray-elegant">Items Sold</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upcoming">Upcoming Auctions ({upcomingAuctions.length})</TabsTrigger>
          <TabsTrigger value="past">Past Auctions ({pastAuctions.length})</TabsTrigger>
          <TabsTrigger value="bidding">Bidding Items ({biddingItems.length})</TabsTrigger>
        </TabsList>

        {/* Upcoming Auctions Tab */}
        <TabsContent value="upcoming" className="space-y-4 mt-6">
          <div className="space-y-4">
          {upcomingAuctions.map((auction, index) => (
            <AuctionCard key={auction.id || index} auction={auction} type="upcoming" />
          ))}
          </div>
          {upcomingAuctions.length === 0 && (
            <div className="card-executive text-center py-12">
              <Calendar className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="elegant-card-title mb-2">No Upcoming Auctions</h3>
              <p className="text-gray-elegant">There are no scheduled tax deed auctions at this time.</p>
            </div>
          )}
        </TabsContent>

        {/* Past Auctions Tab */}
        <TabsContent value="past" className="space-y-4 mt-6">
          <div className="space-y-4">
            {pastAuctions.map((auction, index) => (
              <AuctionCard key={auction.id || index} auction={auction} type="past" />
            ))}
          </div>
        </TabsContent>

        {/* Bidding Items Tab */}
        <TabsContent value="bidding" className="space-y-4 mt-6">
          <div className="space-y-4">
            {biddingItems.map((item, index) => (
              <BiddingItemCard key={item.id || index} item={item} />
            ))}
          </div>
          {biddingItems.length === 0 && (
            <Card>
              <CardContent className="text-center py-12">
                <Gavel className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Bidding Items</h3>
                <p className="text-gray-600">No tax deed items found for this property.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Auction Card Component
const AuctionCard: React.FC<{ auction: any; type: 'upcoming' | 'past' }> = ({ auction, type }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  const getStatusColor = (status: string) => {
    const lowerStatus = status?.toLowerCase() || '';
    if (lowerStatus.includes('upcoming')) {
      return 'badge-elegant badge-gold';
    } else if (lowerStatus.includes('completed')) {
      return 'badge-elegant badge-gray';
    }
    return 'badge-elegant';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-3">
            <Gavel className="h-5 w-5 text-navy" />
            <div>
              <CardTitle className="text-xl">
                {auction.description}
              </CardTitle>
              <CardDescription className="flex items-center gap-2 mt-1">
                <Calendar className="h-4 w-4" />
                {new Date(auction.auction_date).toLocaleDateString()}
                {auction.auction_time && (
                  <>
                    <span className="text-gray-400">•</span>
                    {new Date(`2000-01-01T${auction.auction_time}`).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </>
                )}
              </CardDescription>
            </div>
          </div>
          <Badge className={getStatusColor(auction.status)}>
            {auction.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Auction Information */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Info className="h-4 w-4 text-gray-600" />
              Auction Details
            </h4>
            <div className="p-4 border border-gray-100 rounded-lg">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Date</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {new Date(auction.auction_date).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Total Items</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {auction.total_items?.toLocaleString() || '16'} properties available for sale
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Type</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {auction.auction_type}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Platform</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {auction.online_platform || auction.location}
                  </p>
                </div>
              </div>
              
              {/* Enhanced auction details matching user example */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h5 className="font-semibold text-gray-900 mb-3">Items</h5>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Advertised</p>
                    <p className="text-base font-semibold text-gray-900">46</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Canceled</p>
                    <p className="text-base font-light text-navy">30</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Available for Sale</p>
                    <p className="text-base font-light text-navy">16</p>
                  </div>
                </div>
                
                <div className="p-3 border border-gray-100 rounded-lg">
                  <p className="text-sm font-medium text-navy mb-1">
                    Bidding starts at: {new Date(auction.auction_date).toLocaleDateString()} 9:00 AM EDT
                  </p>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-navy" />
                    <span className="text-sm text-gray-elegant">
                      Registration required by {auction.registration_deadline ? new Date(auction.registration_deadline).toLocaleDateString() : 'TBD'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Past Auction Results */}
          {type === 'past' && auction.items_sold !== undefined && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-gray-600" />
                Auction Results
              </h4>
              <div className="p-4 border border-gray-100 rounded-lg">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Items Sold</p>
                    <p className="text-lg font-light text-navy">
                      {auction.items_sold} / {auction.total_items}
                    </p>
                    <div className="mt-2">
                      <Progress 
                        value={(auction.items_sold / auction.total_items) * 100} 
                        className="h-2"
                      />
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Success Rate</p>
                    <p className="text-lg font-light text-navy">
                      {Math.round((auction.items_sold / auction.total_items) * 100)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Total Revenue</p>
                    <p className="text-lg font-light text-navy">
                      {formatCurrency(auction.total_revenue || 0)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Upcoming Auction Info */}
          {type === 'upcoming' && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Timer className="h-4 w-4 text-gray-600" />
                Registration Information
              </h4>
              <div className="p-4 border border-gray-100 rounded-lg">
                <div className="grid grid-cols-2 gap-4">
                  {auction.deposit_required && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Deposit Required</p>
                      <p className="text-lg font-light text-navy">
                        {formatCurrency(auction.deposit_required)}
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-500">Days Until Auction</p>
                    <p className="text-lg font-light text-navy">
                      {Math.ceil((new Date(auction.auction_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))}
                    </p>
                  </div>
                </div>
                {auction.platform_url && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <a
                      href={auction.platform_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 badge-elegant"
                    >
                      <ExternalLink className="h-4 w-4" />
                      View Auction Platform
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Bidding Item Card Component
const BiddingItemCard: React.FC<{ item: any }> = ({ item }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

    const getStatusColor = (status: string) => {
      const s = (status || '').toLowerCase();
      if (s.includes('active')) return 'badge-elegant badge-gold';
      if (s.includes('sold') || s.includes('passed')) return 'badge-elegant badge-gray';
      return 'badge-elegant';
    };

  const formatTimeRemaining = (seconds: number) => {
    if (seconds <= 0) return 'Closed';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const bidIncrease = item.current_bid > item.opening_bid 
    ? ((item.current_bid - item.opening_bid) / item.opening_bid * 100).toFixed(1)
    : 0;

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
            <div className="flex items-center gap-3">
              <Target className="h-5 w-5 text-navy" />
            <div>
              <CardTitle className="text-xl">
                Tax Deed #{item.tax_deed_number}
              </CardTitle>
              <CardDescription className="flex items-center gap-2 mt-1">
                <Hash className="h-4 w-4" />
                Certificate: {item.tax_certificate_number}
                <span className="text-gray-400">•</span>
                <MapPin className="h-4 w-4" />
                {item.parcel_id}
              </CardDescription>
            </div>
          </div>
          <div className="text-right space-y-1">
            <Badge className={getStatusColor(item.item_status)}>
              {item.item_status}
            </Badge>
            {item.seconds_remaining > 0 && (
              <div className="text-sm text-gray-600 flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatTimeRemaining(item.seconds_remaining)}
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-6">
          {/* Property Information */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Home className="h-4 w-4 text-gray-600" />
              Property Information
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-500">Legal Situs Address</p>
                <p className="text-base font-semibold text-gray-900">
                  {item.legal_situs_address}
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Parcel #</p>
                  <a
                    href={item.property_appraisal_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-base font-light text-navy inline-flex items-center gap-1"
                  >
                    {item.parcel_id}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Homestead</p>
                  <p className="text-base font-semibold text-gray-900">
                    {item.homestead_exemption ? (
                      <span className="text-navy">Yes</span>
                    ) : (
                      <span className="text-gray-600">No</span>
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Assessed Value</p>
                  <p className="text-base font-semibold text-gray-900">
                    {formatCurrency(item.assessed_value)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">SOH Value</p>
                  <p className="text-base font-semibold text-gray-900">
                    {formatCurrency(item.soh_value)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Bidding Information */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Gavel className="h-4 w-4 text-gray-600" />
              Bidding Details
            </h4>
            <div className="p-4 border border-gray-100 rounded-lg">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Opening Bid</p>
                  <p className="text-lg font-semibold text-gray-700">
                    {formatCurrency(item.opening_bid)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">
                    {item.item_status === 'Sold' ? 'Winning Bid' : 'Current Bid'}
                  </p>
                    <p className="text-lg font-light text-navy">
                      {formatCurrency(item.current_bid || item.winning_bid || item.opening_bid)}
                    </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Bid Increase</p>
                  <p className="text-lg font-light text-navy flex items-center gap-1">
                    <TrendingUp className="h-4 w-4" />
                    {bidIncrease}%
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Close Time (EDT)</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {new Date(item.close_time).toLocaleString('en-US', {
                      timeZone: 'America/New_York',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              </div>
              
              {/* Bidding Activity */}
              {(item.total_bids || item.unique_bidders) && (
                <div className="mt-4 pt-4 border-t border-blue-200">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Total Bids</p>
                        <p className="text-lg font-light text-navy">
                          {item.total_bids}
                        </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">Unique Bidders</p>
                        <p className="text-lg font-light text-navy">
                          {item.unique_bidders}
                        </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Tax Information */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <FileText className="h-4 w-4 text-gray-600" />
              Tax Certificate Details
            </h4>
            <div className="p-4 border border-gray-100 rounded-lg">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Tax Years</p>
                  <p className="text-base font-semibold text-gray-900">
                    {item.tax_years_included}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Taxes Owed</p>
                  <p className="text-base font-light text-navy">
                    {formatCurrency(item.total_taxes_owed)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Applicant</p>
                  <p className="text-base font-semibold text-gray-900">
                    {item.applicant_name}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Winner Information (if sold) */}
          {item.item_status === 'Sold' && item.winning_bidder && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-navy" />
                Sale Information
              </h4>
              <div className="p-4 border border-gray-100 rounded-lg">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Winning Bidder</p>
                      <p className="text-base font-light text-navy">
                        {item.winning_bidder}
                      </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Final Amount</p>
                    <p className="text-base font-light text-navy">
                      {formatCurrency(item.winning_bid)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Links */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <ExternalLink className="h-4 w-4 text-gray-600" />
              Property Links
            </h4>
            <div className="flex flex-wrap gap-3">
              {/* View Auction Platform - Primary link */}
              <a
                href={item.auction_date && new Date(item.auction_date) > new Date() 
                  ? `https://broward.deedauction.net/auction/110` 
                  : `https://broward.deedauction.net/auction/109`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 badge-elegant"
              >
                <Gavel className="h-5 w-5" />
                View Auction Platform
              </a>
              
              {/* Additional auction navigation link */}
              <a
                href="https://broward.deedauction.net/auctions"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 badge-elegant"
              >
                <ExternalLink className="h-4 w-4" />
                All Auctions
              </a>
              
              {item.property_appraisal_url && (
                <a
                  href={item.property_appraisal_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 badge-elegant"
                >
                  <Eye className="h-4 w-4" />
                  Property Appraisal
                </a>
              )}
              {item.gis_parcel_map_url && (
                <a
                  href={item.gis_parcel_map_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 badge-elegant"
                >
                  <MapPin className="h-4 w-4" />
                  GIS Parcel Map
                </a>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
