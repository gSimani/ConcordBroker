import React, { useState, useEffect } from 'react';
import { Star, StarOff, Bell, BellOff } from 'lucide-react';

interface WatchlistButtonProps {
  parcelId: string;
  county: string;
  userId?: string;
  size?: 'sm' | 'md' | 'lg';
  onWatchlistChange?: (isWatched: boolean) => void;
}

interface WatchlistEntry {
  id: number;
  parcel_id: string;
  county: string;
  notify_score_change: boolean;
  notify_ownership_change: boolean;
  min_score_change: number;
  created_at: string;
}

export function WatchlistButton({
  parcelId,
  county,
  userId = 'demo-user',
  size = 'md',
  onWatchlistChange
}: WatchlistButtonProps) {
  const [isWatched, setIsWatched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [watchlistEntry, setWatchlistEntry] = useState<WatchlistEntry | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  // Check if property is already watched
  useEffect(() => {
    checkWatchlistStatus();
  }, [parcelId, county, userId]);

  const checkWatchlistStatus = async () => {
    try {
      // For now, use localStorage as mock API
      const watchlistKey = `watchlist_${userId}`;
      const watchlist = JSON.parse(localStorage.getItem(watchlistKey) || '[]');
      const entry = watchlist.find((item: any) =>
        item.parcel_id === parcelId && item.county === county
      );

      if (entry) {
        setIsWatched(true);
        setWatchlistEntry(entry);
      } else {
        setIsWatched(false);
        setWatchlistEntry(null);
      }
    } catch (error) {
      console.error('Error checking watchlist status:', error);
    }
  };

  const toggleWatchlist = async () => {
    if (isLoading) return;

    setIsLoading(true);

    try {
      const watchlistKey = `watchlist_${userId}`;
      const watchlist = JSON.parse(localStorage.getItem(watchlistKey) || '[]');

      if (isWatched) {
        // Remove from watchlist
        const updatedWatchlist = watchlist.filter((item: any) =>
          !(item.parcel_id === parcelId && item.county === county)
        );
        localStorage.setItem(watchlistKey, JSON.stringify(updatedWatchlist));
        setIsWatched(false);
        setWatchlistEntry(null);
        onWatchlistChange?.(false);
      } else {
        // Add to watchlist
        const newEntry: WatchlistEntry = {
          id: Date.now(),
          parcel_id: parcelId,
          county: county,
          notify_score_change: true,
          notify_ownership_change: true,
          min_score_change: 10,
          created_at: new Date().toISOString()
        };

        const updatedWatchlist = [...watchlist, newEntry];
        localStorage.setItem(watchlistKey, JSON.stringify(updatedWatchlist));
        setIsWatched(true);
        setWatchlistEntry(newEntry);
        onWatchlistChange?.(true);
      }
    } catch (error) {
      console.error('Error updating watchlist:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateNotificationSettings = async (settings: Partial<WatchlistEntry>) => {
    if (!watchlistEntry) return;

    try {
      const watchlistKey = `watchlist_${userId}`;
      const watchlist = JSON.parse(localStorage.getItem(watchlistKey) || '[]');

      const updatedWatchlist = watchlist.map((item: any) => {
        if (item.parcel_id === parcelId && item.county === county) {
          return { ...item, ...settings };
        }
        return item;
      });

      localStorage.setItem(watchlistKey, JSON.stringify(updatedWatchlist));
      setWatchlistEntry({ ...watchlistEntry, ...settings });
    } catch (error) {
      console.error('Error updating notification settings:', error);
    }
  };

  const getButtonSize = () => {
    switch (size) {
      case 'sm': return 'h-8 w-8';
      case 'lg': return 'h-12 w-12';
      default: return 'h-10 w-10';
    }
  };

  const getIconSize = () => {
    switch (size) {
      case 'sm': return 16;
      case 'lg': return 24;
      default: return 20;
    }
  };

  return (
    <div className="relative">
      {/* Main watchlist button */}
      <button
        onClick={toggleWatchlist}
        disabled={isLoading}
        className={`
          ${getButtonSize()} rounded-full border-2 transition-all duration-200
          ${isWatched
            ? 'bg-yellow-500 border-yellow-500 text-white hover:bg-yellow-600'
            : 'bg-white border-gray-300 text-gray-600 hover:border-yellow-500 hover:text-yellow-500'
          }
          ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'}
          focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2
        `}
        title={isWatched ? 'Remove from watchlist' : 'Add to watchlist'}
      >
        {isLoading ? (
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
        ) : isWatched ? (
          <Star size={getIconSize()} fill="currentColor" />
        ) : (
          <StarOff size={getIconSize()} />
        )}
      </button>

      {/* Notification settings button (only show if watched) */}
      {isWatched && (
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="absolute -top-1 -right-1 h-6 w-6 bg-blue-500 text-white rounded-full border-2 border-white hover:bg-blue-600 transition-colors"
          title="Notification settings"
        >
          <Bell size={12} className="mx-auto" />
        </button>
      )}

      {/* Notification settings panel */}
      {showSettings && watchlistEntry && (
        <div className="absolute top-12 right-0 bg-white border border-gray-200 rounded-lg shadow-lg p-4 w-72 z-50">
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Notification Settings</h4>

            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={watchlistEntry.notify_score_change}
                  onChange={(e) => updateNotificationSettings({ notify_score_change: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600"
                />
                <span className="text-sm text-gray-700">Score changes</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={watchlistEntry.notify_ownership_change}
                  onChange={(e) => updateNotificationSettings({ notify_ownership_change: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600"
                />
                <span className="text-sm text-gray-700">Ownership changes</span>
              </label>
            </div>

            <div className="space-y-1">
              <label className="block text-sm text-gray-700">
                Minimum score change
              </label>
              <select
                value={watchlistEntry.min_score_change}
                onChange={(e) => updateNotificationSettings({ min_score_change: Number(e.target.value) })}
                className="w-full text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value={5}>5 points</option>
                <option value={10}>10 points</option>
                <option value={15}>15 points</option>
                <option value={20}>20 points</option>
              </select>
            </div>

            <div className="pt-2 border-t">
              <button
                onClick={() => setShowSettings(false)}
                className="w-full text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 py-1 px-3 rounded transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default WatchlistButton;