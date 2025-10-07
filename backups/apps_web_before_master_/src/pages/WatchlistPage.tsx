import React, { useState, useEffect } from 'react';
import { Star, Bell, TrendingUp, TrendingDown, AlertTriangle, Calendar, Settings, Trash2 } from 'lucide-react';

interface WatchlistEntry {
  id: number;
  parcel_id: string;
  county: string;
  notify_score_change: boolean;
  notify_ownership_change: boolean;
  min_score_change: number;
  created_at: string;
  // Simulated property data
  address?: string;
  owner_name?: string;
  current_score?: number;
  last_score?: number;
  assessed_value?: number;
  last_notification?: string;
}

interface RecentChange {
  id: number;
  parcel_id: string;
  county: string;
  change_type: 'score_change' | 'ownership_change';
  old_value: string;
  new_value: string;
  change_date: string;
  magnitude: number;
}

export function WatchlistPage() {
  const [watchlist, setWatchlist] = useState<WatchlistEntry[]>([]);
  const [recentChanges, setRecentChanges] = useState<RecentChange[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userId] = useState('demo-user');
  const [selectedTab, setSelectedTab] = useState<'properties' | 'changes' | 'settings'>('properties');

  useEffect(() => {
    loadWatchlistData();
  }, []);

  const loadWatchlistData = async () => {
    setIsLoading(true);
    try {
      // Load from localStorage (mock API)
      const watchlistKey = `watchlist_${userId}`;
      const storedWatchlist = JSON.parse(localStorage.getItem(watchlistKey) || '[]');

      // Enhance with mock property data
      const enhancedWatchlist = storedWatchlist.map((entry: WatchlistEntry) => ({
        ...entry,
        address: `${Math.floor(Math.random() * 9999)} SW ${Math.floor(Math.random() * 100)} St`,
        owner_name: ['SMITH LLC', 'JOHNSON TRUST', 'BROWN HOLDINGS', 'DAVIS CORP'][Math.floor(Math.random() * 4)],
        current_score: Math.floor(Math.random() * 40) + 60, // 60-100
        last_score: Math.floor(Math.random() * 40) + 50, // 50-90
        assessed_value: Math.floor(Math.random() * 200000) + 100000, // $100k-$300k
        last_notification: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
      }));

      setWatchlist(enhancedWatchlist);

      // Generate mock recent changes
      const changes: RecentChange[] = enhancedWatchlist.slice(0, 3).map((entry, index) => ({
        id: index + 1,
        parcel_id: entry.parcel_id,
        county: entry.county,
        change_type: Math.random() > 0.5 ? 'score_change' : 'ownership_change',
        old_value: entry.change_type === 'score_change' ? '75' : 'OLD OWNER LLC',
        new_value: entry.change_type === 'score_change' ? '85' : 'NEW OWNER CORP',
        change_date: new Date(Date.now() - Math.random() * 3 * 24 * 60 * 60 * 1000).toISOString(),
        magnitude: Math.floor(Math.random() * 20) + 5
      }));

      setRecentChanges(changes);
    } catch (error) {
      console.error('Error loading watchlist:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const removeFromWatchlist = (entryId: number) => {
    const watchlistKey = `watchlist_${userId}`;
    const updatedWatchlist = watchlist.filter(entry => entry.id !== entryId);
    setWatchlist(updatedWatchlist);
    localStorage.setItem(watchlistKey, JSON.stringify(updatedWatchlist));
  };

  const updateNotificationSettings = (entryId: number, settings: Partial<WatchlistEntry>) => {
    const watchlistKey = `watchlist_${userId}`;
    const updatedWatchlist = watchlist.map(entry =>
      entry.id === entryId ? { ...entry, ...settings } : entry
    );
    setWatchlist(updatedWatchlist);
    localStorage.setItem(watchlistKey, JSON.stringify(updatedWatchlist));
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getScoreChangeIcon = (current: number, last: number) => {
    if (current > last) {
      return <TrendingUp size={16} className="text-green-500" />;
    } else if (current < last) {
      return <TrendingDown size={16} className="text-red-500" />;
    }
    return null;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading your watchlist...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Star className="text-yellow-500" fill="currentColor" />
            Property Watchlist
          </h1>
          <p className="mt-2 text-gray-600">
            Monitor your investment properties for score changes and ownership updates
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <Star className="h-8 w-8 text-yellow-500" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-gray-900">{watchlist.length}</p>
                <p className="text-sm text-gray-600">Watched Properties</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <Bell className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-gray-900">{recentChanges.length}</p>
                <p className="text-sm text-gray-600">Recent Changes</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-gray-900">
                  {watchlist.filter(p => (p.current_score || 0) > (p.last_score || 0)).length}
                </p>
                <p className="text-sm text-gray-600">Score Increases</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-orange-500" />
              <div className="ml-4">
                <p className="text-2xl font-semibold text-gray-900">
                  {watchlist.filter(p => p.notify_score_change || p.notify_ownership_change).length}
                </p>
                <p className="text-sm text-gray-600">Active Alerts</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setSelectedTab('properties')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 'properties'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Properties ({watchlist.length})
            </button>
            <button
              onClick={() => setSelectedTab('changes')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 'changes'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Recent Changes ({recentChanges.length})
            </button>
            <button
              onClick={() => setSelectedTab('settings')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                selectedTab === 'settings'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Settings
            </button>
          </nav>
        </div>

        {/* Content */}
        {selectedTab === 'properties' && (
          <div className="space-y-4">
            {watchlist.length === 0 ? (
              <div className="text-center py-12">
                <Star size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No properties in watchlist</h3>
                <p className="text-gray-600 mb-4">Start by adding properties from the search results</p>
                <a
                  href="/mvp"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Browse Properties
                </a>
              </div>
            ) : (
              watchlist.map((property) => (
                <div key={property.id} className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-3">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {property.address}
                        </h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getScoreColor(property.current_score || 0)}`}>
                          {property.current_score} Score
                        </span>
                        {getScoreChangeIcon(property.current_score || 0, property.last_score || 0)}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                        <div>
                          <p><span className="font-medium">Parcel:</span> {property.parcel_id}</p>
                          <p><span className="font-medium">County:</span> {property.county}</p>
                        </div>
                        <div>
                          <p><span className="font-medium">Owner:</span> {property.owner_name}</p>
                          <p><span className="font-medium">Value:</span> {formatCurrency(property.assessed_value || 0)}</p>
                        </div>
                        <div>
                          <p><span className="font-medium">Added:</span> {formatDate(property.created_at)}</p>
                          <p><span className="font-medium">Last Alert:</span> {property.last_notification ? formatDate(property.last_notification) : 'Never'}</p>
                        </div>
                      </div>

                      <div className="mt-4 flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <Bell size={16} className={property.notify_score_change ? 'text-blue-500' : 'text-gray-400'} />
                          <span className={property.notify_score_change ? 'text-blue-600' : 'text-gray-500'}>
                            Score alerts ({property.min_score_change}+ pts)
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Bell size={16} className={property.notify_ownership_change ? 'text-blue-500' : 'text-gray-400'} />
                          <span className={property.notify_ownership_change ? 'text-blue-600' : 'text-gray-500'}>
                            Ownership alerts
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => {/* Settings logic */}}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Settings"
                      >
                        <Settings size={16} />
                      </button>
                      <button
                        onClick={() => removeFromWatchlist(property.id)}
                        className="p-2 text-gray-400 hover:text-red-600"
                        title="Remove from watchlist"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {selectedTab === 'changes' && (
          <div className="space-y-4">
            {recentChanges.length === 0 ? (
              <div className="text-center py-12">
                <Calendar size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No recent changes</h3>
                <p className="text-gray-600">Changes to your watched properties will appear here</p>
              </div>
            ) : (
              recentChanges.map((change) => (
                <div key={change.id} className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-semibold text-gray-900">
                          {change.parcel_id} ({change.county})
                        </span>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          change.change_type === 'score_change' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                        }`}>
                          {change.change_type === 'score_change' ? 'Score Change' : 'Ownership Change'}
                        </span>
                      </div>

                      <div className="text-sm text-gray-600">
                        <p>
                          {change.change_type === 'score_change' ? 'Score changed' : 'Owner changed'} from{' '}
                          <span className="font-medium">{change.old_value}</span> to{' '}
                          <span className="font-medium">{change.new_value}</span>
                        </p>
                        <p className="mt-1">
                          <Calendar size={14} className="inline mr-1" />
                          {formatDate(change.change_date)}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        change.magnitude > 15 ? 'bg-red-100 text-red-800' :
                        change.magnitude > 10 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        Magnitude: {change.magnitude}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {selectedTab === 'settings' && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Global Notification Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default minimum score change threshold
                </label>
                <select className="block w-48 pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                  <option value={5}>5 points</option>
                  <option value={10}>10 points</option>
                  <option value={15}>15 points</option>
                  <option value={20}>20 points</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notification frequency
                </label>
                <select className="block w-48 pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                  <option value="immediate">Immediate</option>
                  <option value="daily">Daily digest</option>
                  <option value="weekly">Weekly digest</option>
                </select>
              </div>

              <div className="pt-4 border-t">
                <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
                  Save Settings
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default WatchlistPage;