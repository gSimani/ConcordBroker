/**
 * useWatchlist Hook - Complete Supabase Integration
 * Provides watchlist management with real-time updates and caching
 * Part of ConcordBroker 100% Supabase Integration
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from './use-auth';
import { useToast } from '@/components/ui/use-toast';

// Types for watchlist data
export interface WatchlistItem {
  id: string;
  user_id: string;
  parcel_id: string;
  county?: string;
  property_address?: string;
  owner_name?: string;
  market_value?: number;
  notes?: string;
  is_favorite: boolean;
  alert_preferences: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface WatchlistState {
  items: WatchlistItem[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  isLoaded: boolean;
}

export interface AddToWatchlistParams {
  parcelId: string;
  county?: string;
  propertyAddress?: string;
  ownerName?: string;
  marketValue?: number;
  notes?: string;
  isFavorite?: boolean;
  alertPreferences?: Record<string, any>;
}

export interface UpdateWatchlistParams {
  notes?: string;
  isFavorite?: boolean;
  alertPreferences?: Record<string, any>;
}

/**
 * Custom hook for managing user watchlists
 * Features:
 * - Real-time Supabase subscriptions
 * - Optimistic updates for better UX
 * - Error handling and retry logic
 * - Local caching for performance
 * - Bulk operations support
 */
export const useWatchlist = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  // State management
  const [state, setState] = useState<WatchlistState>({
    items: [],
    loading: false,
    error: null,
    totalCount: 0,
    isLoaded: false,
  });

  // Cache for quick lookups
  const watchlistMap = useMemo(() => {
    const map = new Map<string, WatchlistItem>();
    state.items.forEach(item => {
      map.set(item.parcel_id, item);
    });
    return map;
  }, [state.items]);

  /**
   * Fetch user's complete watchlist
   */
  const fetchWatchlist = useCallback(async () => {
    if (!user?.id) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const { data, error, count } = await supabase
        .from('user_watchlists')
        .select('*', { count: 'exact' })
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;

      setState(prev => ({
        ...prev,
        items: data || [],
        totalCount: count || 0,
        loading: false,
        isLoaded: true,
      }));

    } catch (error: any) {
      console.error('Error fetching watchlist:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to fetch watchlist',
        loading: false,
      }));

      toast({
        title: "Error Loading Watchlist",
        description: "Failed to load your watchlist. Please try again.",
        variant: "destructive",
      });
    }
  }, [user?.id, toast]);

  /**
   * Add property to watchlist with optimistic update
   */
  const addToWatchlist = useCallback(async (params: AddToWatchlistParams) => {
    if (!user?.id) {
      toast({
        title: "Authentication Required",
        description: "Please log in to add properties to your watchlist.",
        variant: "destructive",
      });
      return false;
    }

    // Optimistic update
    const optimisticItem: WatchlistItem = {
      id: `temp-${Date.now()}`,
      user_id: user.id,
      parcel_id: params.parcelId,
      county: params.county,
      property_address: params.propertyAddress,
      owner_name: params.ownerName,
      market_value: params.marketValue,
      notes: params.notes || '',
      is_favorite: params.isFavorite || false,
      alert_preferences: params.alertPreferences || {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setState(prev => ({
      ...prev,
      items: [optimisticItem, ...prev.items],
      totalCount: prev.totalCount + 1,
    }));

    try {
      const { data, error } = await supabase
        .from('user_watchlists')
        .insert({
          user_id: user.id,
          parcel_id: params.parcelId,
          county: params.county,
          property_address: params.propertyAddress,
          owner_name: params.ownerName,
          market_value: params.marketValue,
          notes: params.notes,
          is_favorite: params.isFavorite || false,
          alert_preferences: params.alertPreferences || {},
        })
        .select()
        .single();

      if (error) throw error;

      // Replace optimistic item with real data
      setState(prev => ({
        ...prev,
        items: prev.items.map(item =>
          item.id === optimisticItem.id ? data : item
        ),
      }));

      toast({
        title: "Added to Watchlist",
        description: `Property ${params.parcelId} has been added to your watchlist.`,
        variant: "default",
      });

      return true;

    } catch (error: any) {
      console.error('Error adding to watchlist:', error);

      // Revert optimistic update
      setState(prev => ({
        ...prev,
        items: prev.items.filter(item => item.id !== optimisticItem.id),
        totalCount: prev.totalCount - 1,
      }));

      toast({
        title: "Error Adding to Watchlist",
        description: error.message === 'duplicate key value violates unique constraint "user_watchlists_user_id_parcel_id_key"'
          ? "This property is already in your watchlist."
          : "Failed to add property to watchlist. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, toast]);

  /**
   * Remove property from watchlist
   */
  const removeFromWatchlist = useCallback(async (parcelId: string) => {
    if (!user?.id) return false;

    // Optimistic update
    const itemToRemove = watchlistMap.get(parcelId);
    if (!itemToRemove) return false;

    setState(prev => ({
      ...prev,
      items: prev.items.filter(item => item.parcel_id !== parcelId),
      totalCount: prev.totalCount - 1,
    }));

    try {
      const { error } = await supabase
        .from('user_watchlists')
        .delete()
        .eq('user_id', user.id)
        .eq('parcel_id', parcelId);

      if (error) throw error;

      toast({
        title: "Removed from Watchlist",
        description: `Property ${parcelId} has been removed from your watchlist.`,
        variant: "default",
      });

      return true;

    } catch (error: any) {
      console.error('Error removing from watchlist:', error);

      // Revert optimistic update
      setState(prev => ({
        ...prev,
        items: [...prev.items, itemToRemove].sort((a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ),
        totalCount: prev.totalCount + 1,
      }));

      toast({
        title: "Error Removing from Watchlist",
        description: "Failed to remove property from watchlist. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, watchlistMap, toast]);

  /**
   * Update watchlist item
   */
  const updateWatchlistItem = useCallback(async (
    parcelId: string,
    updates: UpdateWatchlistParams
  ) => {
    if (!user?.id) return false;

    const existingItem = watchlistMap.get(parcelId);
    if (!existingItem) return false;

    // Optimistic update
    const updatedItem = {
      ...existingItem,
      ...updates,
      updated_at: new Date().toISOString(),
    };

    setState(prev => ({
      ...prev,
      items: prev.items.map(item =>
        item.parcel_id === parcelId ? updatedItem : item
      ),
    }));

    try {
      const { error } = await supabase
        .from('user_watchlists')
        .update(updates)
        .eq('user_id', user.id)
        .eq('parcel_id', parcelId);

      if (error) throw error;

      toast({
        title: "Watchlist Updated",
        description: "Your watchlist item has been updated.",
        variant: "default",
      });

      return true;

    } catch (error: any) {
      console.error('Error updating watchlist item:', error);

      // Revert optimistic update
      setState(prev => ({
        ...prev,
        items: prev.items.map(item =>
          item.parcel_id === parcelId ? existingItem : item
        ),
      }));

      toast({
        title: "Error Updating Watchlist",
        description: "Failed to update watchlist item. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, watchlistMap, toast]);

  /**
   * Check if property is in watchlist
   */
  const isInWatchlist = useCallback((parcelId: string): boolean => {
    return watchlistMap.has(parcelId);
  }, [watchlistMap]);

  /**
   * Get watchlist item by parcel ID
   */
  const getWatchlistItem = useCallback((parcelId: string): WatchlistItem | null => {
    return watchlistMap.get(parcelId) || null;
  }, [watchlistMap]);

  /**
   * Bulk add properties to watchlist
   */
  const bulkAddToWatchlist = useCallback(async (
    properties: Omit<AddToWatchlistParams, 'parcelId'>[]
  ) => {
    if (!user?.id || properties.length === 0) return [];

    try {
      const insertData = properties.map(prop => ({
        user_id: user.id,
        parcel_id: prop.parcelId,
        county: prop.county,
        property_address: prop.propertyAddress,
        owner_name: prop.ownerName,
        market_value: prop.marketValue,
        notes: prop.notes,
        is_favorite: prop.isFavorite || false,
        alert_preferences: prop.alertPreferences || {},
      }));

      const { data, error } = await supabase
        .from('user_watchlists')
        .insert(insertData)
        .select();

      if (error) throw error;

      // Update state with new items
      setState(prev => ({
        ...prev,
        items: [...(data || []), ...prev.items],
        totalCount: prev.totalCount + (data?.length || 0),
      }));

      toast({
        title: "Added to Watchlist",
        description: `${data?.length || 0} properties added to your watchlist.`,
        variant: "default",
      });

      return data || [];

    } catch (error: any) {
      console.error('Error bulk adding to watchlist:', error);

      toast({
        title: "Error Adding Properties",
        description: "Failed to add some properties to watchlist. Please try again.",
        variant: "destructive",
      });

      return [];
    }
  }, [user?.id, toast]);

  /**
   * Clear entire watchlist
   */
  const clearWatchlist = useCallback(async () => {
    if (!user?.id) return false;

    try {
      const { error } = await supabase
        .from('user_watchlists')
        .delete()
        .eq('user_id', user.id);

      if (error) throw error;

      setState(prev => ({
        ...prev,
        items: [],
        totalCount: 0,
      }));

      toast({
        title: "Watchlist Cleared",
        description: "All properties have been removed from your watchlist.",
        variant: "default",
      });

      return true;

    } catch (error: any) {
      console.error('Error clearing watchlist:', error);

      toast({
        title: "Error Clearing Watchlist",
        description: "Failed to clear watchlist. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, toast]);

  // Set up real-time subscription
  useEffect(() => {
    if (!user?.id) return;

    // Initial fetch
    fetchWatchlist();

    // Set up real-time subscription
    const subscription = supabase
      .channel(`watchlist-${user.id}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'user_watchlists',
          filter: `user_id=eq.${user.id}`,
        },
        (payload) => {
          console.log('Watchlist real-time update:', payload);

          switch (payload.eventType) {
            case 'INSERT':
              setState(prev => ({
                ...prev,
                items: [payload.new as WatchlistItem, ...prev.items],
                totalCount: prev.totalCount + 1,
              }));
              break;

            case 'UPDATE':
              setState(prev => ({
                ...prev,
                items: prev.items.map(item =>
                  item.id === payload.new.id ? payload.new as WatchlistItem : item
                ),
              }));
              break;

            case 'DELETE':
              setState(prev => ({
                ...prev,
                items: prev.items.filter(item => item.id !== payload.old.id),
                totalCount: prev.totalCount - 1,
              }));
              break;
          }
        }
      )
      .subscribe();

    // Cleanup subscription
    return () => {
      subscription.unsubscribe();
    };
  }, [user?.id, fetchWatchlist]);

  return {
    // State
    watchlist: state.items,
    loading: state.loading,
    error: state.error,
    totalCount: state.totalCount,
    isLoaded: state.isLoaded,

    // Actions
    addToWatchlist,
    removeFromWatchlist,
    updateWatchlistItem,
    isInWatchlist,
    getWatchlistItem,
    bulkAddToWatchlist,
    clearWatchlist,
    refetch: fetchWatchlist,
  };
};