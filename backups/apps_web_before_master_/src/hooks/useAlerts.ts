/**
 * useAlerts Hook - Complete Real-time Alert System
 * Provides property alerts, notifications, and user preferences management
 * Part of ConcordBroker 100% Supabase Integration
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from './use-auth';
import { useToast } from '@/components/ui/use-toast';

// Types for property alerts
export interface PropertyAlert {
  id: string;
  user_id: string;
  parcel_id: string;
  county?: string;
  alert_type: 'price_change' | 'new_sale' | 'foreclosure' | 'tax_deed' | 'permit' | 'owner_change' | 'market_event' | 'score_change';
  alert_title: string;
  alert_message: string;
  alert_data: Record<string, any>;
  is_read: boolean;
  is_dismissed: boolean;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  expires_at?: string;
  created_at: string;
}

export interface AlertPreferences {
  id: string;
  user_id: string;
  price_change_threshold: number;
  enable_price_alerts: boolean;
  enable_sale_alerts: boolean;
  enable_foreclosure_alerts: boolean;
  enable_tax_deed_alerts: boolean;
  enable_permit_alerts: boolean;
  enable_owner_change_alerts: boolean;
  enable_market_alerts: boolean;
  enable_score_alerts: boolean;
  alert_frequency: 'immediate' | 'daily' | 'weekly';
  email_alerts: boolean;
  push_notifications: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertsState {
  alerts: PropertyAlert[];
  loading: boolean;
  error: string | null;
  unreadCount: number;
  preferences?: AlertPreferences;
  preferencesLoading: boolean;
}

export interface CreateAlertParams {
  parcelId: string;
  county?: string;
  alertType: PropertyAlert['alert_type'];
  title: string;
  message: string;
  alertData?: Record<string, any>;
  priority?: PropertyAlert['priority'];
  expiresAt?: string;
}

/**
 * Custom hook for managing property alerts and notifications
 * Features:
 * - Real-time Supabase subscriptions for alerts
 * - User alert preferences management
 * - Alert filtering and prioritization
 * - Batch operations for alert management
 * - Auto-dismissal of expired alerts
 */
export const useAlerts = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  // State management
  const [state, setState] = useState<AlertsState>({
    alerts: [],
    loading: false,
    error: null,
    unreadCount: 0,
    preferences: undefined,
    preferencesLoading: false,
  });

  // Computed values
  const unreadAlerts = useMemo(() =>
    state.alerts.filter(alert => !alert.is_read && !alert.is_dismissed),
    [state.alerts]
  );

  const urgentAlerts = useMemo(() =>
    state.alerts.filter(alert => alert.priority === 'urgent' && !alert.is_dismissed),
    [state.alerts]
  );

  const alertsByType = useMemo(() => {
    const grouped: Record<string, PropertyAlert[]> = {};
    state.alerts.forEach(alert => {
      if (!grouped[alert.alert_type]) {
        grouped[alert.alert_type] = [];
      }
      grouped[alert.alert_type].push(alert);
    });
    return grouped;
  }, [state.alerts]);

  /**
   * Fetch user's alerts
   */
  const fetchAlerts = useCallback(async (options: {
    unreadOnly?: boolean;
    limit?: number;
    alertType?: string;
  } = {}) => {
    if (!user?.id) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      let query = supabase
        .from('property_alerts')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (options.unreadOnly) {
        query = query.eq('is_read', false).eq('is_dismissed', false);
      }

      if (options.alertType) {
        query = query.eq('alert_type', options.alertType);
      }

      if (options.limit) {
        query = query.limit(options.limit);
      } else {
        query = query.limit(100); // Default limit
      }

      const { data, error } = await query;

      if (error) throw error;

      const alerts = data || [];
      const unreadCount = alerts.filter(alert => !alert.is_read && !alert.is_dismissed).length;

      setState(prev => ({
        ...prev,
        alerts,
        unreadCount,
        loading: false,
      }));

    } catch (error: any) {
      console.error('Error fetching alerts:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to fetch alerts',
        loading: false,
      }));

      toast({
        title: "Error Loading Alerts",
        description: "Failed to load your alerts. Please try again.",
        variant: "destructive",
      });
    }
  }, [user?.id, toast]);

  /**
   * Create a new alert
   */
  const createAlert = useCallback(async (params: CreateAlertParams) => {
    if (!user?.id) return null;

    try {
      const { data, error } = await supabase
        .from('property_alerts')
        .insert({
          user_id: user.id,
          parcel_id: params.parcelId,
          county: params.county,
          alert_type: params.alertType,
          alert_title: params.title,
          alert_message: params.message,
          alert_data: params.alertData || {},
          priority: params.priority || 'medium',
          expires_at: params.expiresAt,
        })
        .select()
        .single();

      if (error) throw error;

      toast({
        title: "Alert Created",
        description: params.title,
        variant: "default",
      });

      return data;

    } catch (error: any) {
      console.error('Error creating alert:', error);

      toast({
        title: "Error Creating Alert",
        description: "Failed to create alert. Please try again.",
        variant: "destructive",
      });

      return null;
    }
  }, [user?.id, toast]);

  /**
   * Mark alert as read
   */
  const markAsRead = useCallback(async (alertId: string) => {
    if (!user?.id) return false;

    // Optimistic update
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.map(alert =>
        alert.id === alertId ? { ...alert, is_read: true } : alert
      ),
      unreadCount: Math.max(0, prev.unreadCount - 1),
    }));

    try {
      const { error } = await supabase
        .from('property_alerts')
        .update({ is_read: true })
        .eq('id', alertId)
        .eq('user_id', user.id);

      if (error) throw error;
      return true;

    } catch (error: any) {
      console.error('Error marking alert as read:', error);

      // Revert optimistic update
      setState(prev => ({
        ...prev,
        alerts: prev.alerts.map(alert =>
          alert.id === alertId ? { ...alert, is_read: false } : alert
        ),
        unreadCount: prev.unreadCount + 1,
      }));

      toast({
        title: "Error Updating Alert",
        description: "Failed to mark alert as read. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, toast]);

  /**
   * Dismiss alert
   */
  const dismissAlert = useCallback(async (alertId: string) => {
    if (!user?.id) return false;

    const alertToUpdate = state.alerts.find(a => a.id === alertId);

    // Optimistic update
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.map(alert =>
        alert.id === alertId ? { ...alert, is_dismissed: true } : alert
      ),
      unreadCount: alertToUpdate && !alertToUpdate.is_read ?
        Math.max(0, prev.unreadCount - 1) : prev.unreadCount,
    }));

    try {
      const { error } = await supabase
        .from('property_alerts')
        .update({ is_dismissed: true })
        .eq('id', alertId)
        .eq('user_id', user.id);

      if (error) throw error;
      return true;

    } catch (error: any) {
      console.error('Error dismissing alert:', error);

      // Revert optimistic update
      setState(prev => ({
        ...prev,
        alerts: prev.alerts.map(alert =>
          alert.id === alertId ? { ...alert, is_dismissed: false } : alert
        ),
        unreadCount: alertToUpdate && !alertToUpdate.is_read ?
          prev.unreadCount + 1 : prev.unreadCount,
      }));

      toast({
        title: "Error Dismissing Alert",
        description: "Failed to dismiss alert. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, state.alerts, toast]);

  /**
   * Mark all alerts as read
   */
  const markAllAsRead = useCallback(async () => {
    if (!user?.id || unreadAlerts.length === 0) return false;

    // Optimistic update
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.map(alert => ({ ...alert, is_read: true })),
      unreadCount: 0,
    }));

    try {
      const { error } = await supabase
        .from('property_alerts')
        .update({ is_read: true })
        .eq('user_id', user.id)
        .eq('is_read', false);

      if (error) throw error;

      toast({
        title: "All Alerts Read",
        description: `Marked ${unreadAlerts.length} alerts as read`,
        variant: "default",
      });

      return true;

    } catch (error: any) {
      console.error('Error marking all alerts as read:', error);

      // Revert optimistic update (refetch to be safe)
      fetchAlerts();

      toast({
        title: "Error Updating Alerts",
        description: "Failed to mark all alerts as read. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, unreadAlerts, toast, fetchAlerts]);

  /**
   * Delete alert permanently
   */
  const deleteAlert = useCallback(async (alertId: string) => {
    if (!user?.id) return false;

    const alertToDelete = state.alerts.find(a => a.id === alertId);

    // Optimistic update
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.filter(alert => alert.id !== alertId),
      unreadCount: alertToDelete && !alertToDelete.is_read ?
        Math.max(0, prev.unreadCount - 1) : prev.unreadCount,
    }));

    try {
      const { error } = await supabase
        .from('property_alerts')
        .delete()
        .eq('id', alertId)
        .eq('user_id', user.id);

      if (error) throw error;
      return true;

    } catch (error: any) {
      console.error('Error deleting alert:', error);

      // Revert optimistic update (refetch to be safe)
      fetchAlerts();

      toast({
        title: "Error Deleting Alert",
        description: "Failed to delete alert. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, state.alerts, toast, fetchAlerts]);

  /**
   * Fetch user alert preferences
   */
  const fetchAlertPreferences = useCallback(async () => {
    if (!user?.id) return;

    setState(prev => ({ ...prev, preferencesLoading: true }));

    try {
      const { data, error } = await supabase
        .from('user_alert_preferences')
        .select('*')
        .eq('user_id', user.id)
        .single();

      if (error && error.code !== 'PGRST116') { // PGRST116 = not found
        throw error;
      }

      setState(prev => ({
        ...prev,
        preferences: data || undefined,
        preferencesLoading: false,
      }));

      // If no preferences exist, create default ones
      if (!data) {
        await createDefaultAlertPreferences();
      }

    } catch (error: any) {
      console.error('Error fetching alert preferences:', error);
      setState(prev => ({
        ...prev,
        preferencesLoading: false,
      }));
    }
  }, [user?.id]);

  /**
   * Create default alert preferences
   */
  const createDefaultAlertPreferences = useCallback(async () => {
    if (!user?.id) return;

    try {
      const { data, error } = await supabase
        .from('user_alert_preferences')
        .insert({
          user_id: user.id,
          price_change_threshold: 10.0,
          enable_price_alerts: true,
          enable_sale_alerts: true,
          enable_foreclosure_alerts: true,
          enable_tax_deed_alerts: true,
          enable_permit_alerts: false,
          enable_owner_change_alerts: true,
          enable_market_alerts: true,
          enable_score_alerts: true,
          alert_frequency: 'daily',
          email_alerts: true,
          push_notifications: false,
        })
        .select()
        .single();

      if (error) throw error;

      setState(prev => ({
        ...prev,
        preferences: data,
      }));

    } catch (error: any) {
      console.error('Error creating default alert preferences:', error);
    }
  }, [user?.id]);

  /**
   * Update alert preferences
   */
  const updateAlertPreferences = useCallback(async (updates: Partial<Omit<AlertPreferences, 'id' | 'user_id' | 'created_at' | 'updated_at'>>) => {
    if (!user?.id || !state.preferences) return false;

    // Optimistic update
    const updatedPreferences = { ...state.preferences, ...updates };
    setState(prev => ({
      ...prev,
      preferences: updatedPreferences,
    }));

    try {
      const { data, error } = await supabase
        .from('user_alert_preferences')
        .update(updates)
        .eq('user_id', user.id)
        .select()
        .single();

      if (error) throw error;

      setState(prev => ({
        ...prev,
        preferences: data,
      }));

      toast({
        title: "Preferences Updated",
        description: "Your alert preferences have been saved.",
        variant: "default",
      });

      return true;

    } catch (error: any) {
      console.error('Error updating alert preferences:', error);

      // Revert optimistic update
      setState(prev => ({
        ...prev,
        preferences: state.preferences,
      }));

      toast({
        title: "Error Updating Preferences",
        description: "Failed to update alert preferences. Please try again.",
        variant: "destructive",
      });

      return false;
    }
  }, [user?.id, state.preferences, toast]);

  /**
   * Clean up expired alerts
   */
  const cleanupExpiredAlerts = useCallback(async () => {
    if (!user?.id) return;

    try {
      const { error } = await supabase
        .from('property_alerts')
        .update({ is_dismissed: true })
        .eq('user_id', user.id)
        .lt('expires_at', new Date().toISOString())
        .is('is_dismissed', false);

      if (error) throw error;

      // Refresh alerts to show updated state
      fetchAlerts();

    } catch (error: any) {
      console.error('Error cleaning up expired alerts:', error);
    }
  }, [user?.id, fetchAlerts]);

  // Set up real-time subscription for alerts
  useEffect(() => {
    if (!user?.id) return;

    // Initial fetch
    fetchAlerts();
    fetchAlertPreferences();

    // Set up real-time subscription
    const subscription = supabase
      .channel(`alerts-${user.id}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'property_alerts',
          filter: `user_id=eq.${user.id}`,
        },
        (payload) => {
          console.log('Alerts real-time update:', payload);

          setState(prev => {
            let newAlerts = [...prev.alerts];
            let unreadCount = prev.unreadCount;

            switch (payload.eventType) {
              case 'INSERT':
                const newAlert = payload.new as PropertyAlert;
                newAlerts = [newAlert, ...newAlerts];
                if (!newAlert.is_read && !newAlert.is_dismissed) {
                  unreadCount += 1;

                  // Show toast for urgent alerts
                  if (newAlert.priority === 'urgent') {
                    toast({
                      title: "🚨 Urgent Alert",
                      description: newAlert.alert_title,
                      variant: "destructive",
                    });
                  }
                }
                break;

              case 'UPDATE':
                const updatedAlert = payload.new as PropertyAlert;
                const oldAlert = payload.old as PropertyAlert;

                newAlerts = newAlerts.map(alert =>
                  alert.id === updatedAlert.id ? updatedAlert : alert
                );

                // Update unread count
                if (!oldAlert.is_read && updatedAlert.is_read) {
                  unreadCount = Math.max(0, unreadCount - 1);
                } else if (oldAlert.is_read && !updatedAlert.is_read) {
                  unreadCount += 1;
                }
                break;

              case 'DELETE':
                const deletedAlert = payload.old as PropertyAlert;
                newAlerts = newAlerts.filter(alert => alert.id !== deletedAlert.id);
                if (!deletedAlert.is_read && !deletedAlert.is_dismissed) {
                  unreadCount = Math.max(0, unreadCount - 1);
                }
                break;
            }

            return {
              ...prev,
              alerts: newAlerts,
              unreadCount,
            };
          });
        }
      )
      .subscribe();

    // Cleanup expired alerts on load
    cleanupExpiredAlerts();

    // Cleanup subscription
    return () => {
      subscription.unsubscribe();
    };
  }, [user?.id, fetchAlerts, fetchAlertPreferences, cleanupExpiredAlerts, toast]);

  // Periodic cleanup of expired alerts
  useEffect(() => {
    const interval = setInterval(cleanupExpiredAlerts, 5 * 60 * 1000); // Every 5 minutes
    return () => clearInterval(interval);
  }, [cleanupExpiredAlerts]);

  return {
    // State
    alerts: state.alerts,
    unreadAlerts,
    urgentAlerts,
    alertsByType,
    loading: state.loading,
    error: state.error,
    unreadCount: state.unreadCount,
    preferences: state.preferences,
    preferencesLoading: state.preferencesLoading,

    // Actions
    createAlert,
    markAsRead,
    dismissAlert,
    markAllAsRead,
    deleteAlert,
    fetchAlerts,
    updateAlertPreferences,
    cleanupExpiredAlerts,

    // Computed values
    hasUnread: unreadAlerts.length > 0,
    hasUrgent: urgentAlerts.length > 0,
  };
};