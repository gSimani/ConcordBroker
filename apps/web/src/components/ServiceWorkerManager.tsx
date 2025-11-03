/**
 * Service Worker Manager Component
 * Handles service worker registration, updates, and communication
 */

import React, { useEffect, useState, useCallback, memo } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  RefreshCw,
  Download,
  Wifi,
  WifiOff,
  CheckCircle2,
  AlertTriangle,
  Info,
  X
} from 'lucide-react';

interface ServiceWorkerState {
  isSupported: boolean;
  isRegistered: boolean;
  isActive: boolean;
  hasUpdate: boolean;
  isOnline: boolean;
  registration: ServiceWorkerRegistration | null;
  version: string;
  cacheStats: {
    size: number;
    hitRate: number;
  } | null;
}

interface ServiceWorkerMessage {
  type: string;
  payload?: any;
}

export const ServiceWorkerManager = memo(function ServiceWorkerManager() {
  const [state, setState] = useState<ServiceWorkerState>({
    isSupported: false,
    isRegistered: false,
    isActive: false,
    hasUpdate: false,
    isOnline: navigator.onLine,
    registration: null,
    version: '',
    cacheStats: null,
  });

  const [showUpdatePrompt, setShowUpdatePrompt] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [notifications, setNotifications] = useState<Array<{
    id: string;
    type: 'info' | 'warning' | 'error' | 'success';
    message: string;
    timestamp: number;
  }>>([]);

  // Add notification
  const addNotification = useCallback((type: 'info' | 'warning' | 'error' | 'success', message: string) => {
    const notification = {
      id: Date.now().toString(),
      type,
      message,
      timestamp: Date.now(),
    };

    setNotifications(prev => [...prev, notification]);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  }, []);

  // Remove notification
  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  // Send message to service worker
  const sendMessageToSW = useCallback(async (message: ServiceWorkerMessage): Promise<any> => {
    if (!state.registration?.active) {
      throw new Error('Service worker not active');
    }

    return new Promise((resolve, reject) => {
      const channel = new MessageChannel();

      channel.port1.onmessage = (event) => {
        if (event.data.error) {
          reject(new Error(event.data.error));
        } else {
          resolve(event.data);
        }
      };

      state.registration.active.postMessage(message, [channel.port2]);

      // Timeout after 5 seconds
      setTimeout(() => {
        reject(new Error('Service worker message timeout'));
      }, 5000);
    });
  }, [state.registration]);

  // Register service worker
  const registerServiceWorker = useCallback(async () => {
    if (!('serviceWorker' in navigator)) {
      setState(prev => ({ ...prev, isSupported: false }));
      return;
    }

    setState(prev => ({ ...prev, isSupported: true }));

    // Skip service worker registration in development (sw.js doesn't exist in dev)
    if (import.meta.env.DEV) {
      console.log('[SW Manager] Service worker disabled in development mode');
      return;
    }

    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
        updateViaCache: 'none', // Always check for updates
      });

      console.log('[SW Manager] Service worker registered successfully');

      setState(prev => ({
        ...prev,
        isRegistered: true,
        registration,
        isActive: registration.active !== null,
        version: 'v1.2.0',
      }));

      // Listen for updates
      registration.addEventListener('updatefound', () => {
        console.log('[SW Manager] Service worker update found');
        const newWorker = registration.installing;

        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              console.log('[SW Manager] New service worker installed');
              setState(prev => ({ ...prev, hasUpdate: true }));
              setShowUpdatePrompt(true);
              addNotification('info', 'A new version is available. Refresh to update.');
            }
          });
        }
      });

      // Get cache stats (only if service worker is active)
      if (registration.active) {
        try {
          const stats = await sendMessageToSW({ type: 'GET_CACHE_STATUS' });
          setState(prev => ({
            ...prev,
            cacheStats: {
              size: Object.values(stats).reduce((a: number, b: number) => a + b, 0),
              hitRate: 0, // This would need to be tracked separately
            },
          }));
        } catch (error) {
          // Silently fail - cache stats are optional
          console.debug('[SW Manager] Cache stats not available:', error.message);
        }
      }

      addNotification('success', 'Service worker activated successfully');
    } catch (error) {
      console.error('[SW Manager] Service worker registration failed:', error);
      addNotification('error', 'Failed to activate offline support');
    }
  }, [addNotification, sendMessageToSW]);

  // Update service worker
  const updateServiceWorker = useCallback(async () => {
    if (!state.registration) return;

    setIsUpdating(true);

    try {
      // Skip waiting and take control
      if (state.registration.waiting) {
        state.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      }

      // Reload page to activate new service worker
      setTimeout(() => {
        window.location.reload();
      }, 500);

      addNotification('info', 'Updating to latest version...');
    } catch (error) {
      console.error('[SW Manager] Service worker update failed:', error);
      addNotification('error', 'Failed to update');
      setIsUpdating(false);
    }
  }, [state.registration, addNotification]);

  // Clear cache
  const clearCache = useCallback(async () => {
    try {
      await sendMessageToSW({ type: 'CLEAR_CACHE' });
      addNotification('success', 'Cache cleared successfully');

      // Update cache stats
      setState(prev => ({
        ...prev,
        cacheStats: prev.cacheStats ? { ...prev.cacheStats, size: 0 } : null,
      }));
    } catch (error) {
      console.error('[SW Manager] Failed to clear cache:', error);
      addNotification('error', 'Failed to clear cache');
    }
  }, [sendMessageToSW, addNotification]);

  // Prefetch resources
  const prefetchResources = useCallback(async () => {
    try {
      await sendMessageToSW({ type: 'PREFETCH_PROPERTIES' });
      addNotification('success', 'Popular searches cached for faster loading');
    } catch (error) {
      console.error('[SW Manager] Failed to prefetch resources:', error);
      addNotification('error', 'Failed to cache resources');
    }
  }, [sendMessageToSW, addNotification]);

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setState(prev => ({ ...prev, isOnline: true }));
      addNotification('success', 'Back online');
    };

    const handleOffline = () => {
      setState(prev => ({ ...prev, isOnline: false }));
      addNotification('warning', 'You are offline. Cached data will be used.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [addNotification]);

  // Listen for service worker messages
  useEffect(() => {
    if (!('serviceWorker' in navigator)) return;

    const handleMessage = (event: MessageEvent) => {
      const { type, payload } = event.data;

      switch (type) {
        case 'CACHE_UPDATED':
          addNotification('info', 'Cache updated with fresh data');
          break;
        case 'OFFLINE_FALLBACK':
          addNotification('warning', 'Serving cached content while offline');
          break;
        case 'PERFORMANCE_METRICS':
          if (state.cacheStats) {
            setState(prev => ({
              ...prev,
              cacheStats: {
                ...prev.cacheStats!,
                hitRate: payload.hitRate,
              },
            }));
          }
          break;
      }
    };

    navigator.serviceWorker.addEventListener('message', handleMessage);

    return () => {
      navigator.serviceWorker.removeEventListener('message', handleMessage);
    };
  }, [addNotification, state.cacheStats]);

  // Initialize service worker on mount
  useEffect(() => {
    registerServiceWorker();
  }, [registerServiceWorker]);

  // Format bytes
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!state.isSupported) {
    return null; // Don't show anything if service workers aren't supported
  }

  return (
    <>
      {/* Update Prompt */}
      {showUpdatePrompt && (
        <Alert className="fixed top-4 right-4 z-50 w-80 border-blue-200 bg-blue-50">
          <Info className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>New version available!</span>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={updateServiceWorker}
                disabled={isUpdating}
                className="h-6 px-2 text-xs"
              >
                {isUpdating ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Update'}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowUpdatePrompt(false)}
                className="h-6 w-6 p-0"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Notifications */}
      <div className="fixed top-4 left-4 z-50 space-y-2">
        {notifications.map((notification) => (
          <Alert
            key={notification.id}
            className={`w-80 ${
              notification.type === 'error' ? 'border-red-200 bg-red-50' :
              notification.type === 'warning' ? 'border-yellow-200 bg-yellow-50' :
              notification.type === 'success' ? 'border-green-200 bg-green-50' :
              'border-blue-200 bg-blue-50'
            }`}
          >
            {notification.type === 'error' ? <AlertTriangle className="h-4 w-4" /> :
             notification.type === 'warning' ? <AlertTriangle className="h-4 w-4" /> :
             notification.type === 'success' ? <CheckCircle2 className="h-4 w-4" /> :
             <Info className="h-4 w-4" />}
            <AlertDescription className="flex items-center justify-between">
              <span className="text-sm">{notification.message}</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => removeNotification(notification.id)}
                className="h-4 w-4 p-0 ml-2"
              >
                <X className="w-3 h-3" />
              </Button>
            </AlertDescription>
          </Alert>
        ))}
      </div>

      {/* Service Worker Status (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <Card className="fixed bottom-4 right-4 w-80 bg-white/90 backdrop-blur-sm border-gray-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center justify-between">
              <div className="flex items-center gap-2">
                {state.isOnline ? (
                  <Wifi className="w-4 h-4 text-green-500" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-500" />
                )}
                Service Worker
              </div>
              <Badge variant={state.isActive ? 'default' : 'secondary'}>
                {state.isActive ? 'Active' : 'Inactive'}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-xs">
              <span>Version:</span>
              <span className="font-mono">{state.version}</span>
            </div>

            {state.cacheStats && (
              <>
                <div className="flex justify-between text-xs">
                  <span>Cache Size:</span>
                  <span>{formatBytes(state.cacheStats.size * 1024)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span>Hit Rate:</span>
                  <span>{state.cacheStats.hitRate.toFixed(1)}%</span>
                </div>
              </>
            )}

            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={clearCache}
                className="flex-1 text-xs h-7"
              >
                Clear Cache
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={prefetchResources}
                className="flex-1 text-xs h-7"
              >
                <Download className="w-3 h-3 mr-1" />
                Prefetch
              </Button>
            </div>

            {state.hasUpdate && (
              <Button
                size="sm"
                onClick={updateServiceWorker}
                disabled={isUpdating}
                className="w-full text-xs h-7"
              >
                {isUpdating ? (
                  <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                ) : (
                  <Download className="w-3 h-3 mr-1" />
                )}
                Update Available
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </>
  );
});

// Hook for service worker communication
export function useServiceWorker() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [swRegistration, setSwRegistration] = useState<ServiceWorkerRegistration | null>(null);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Get service worker registration
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistration().then(setSwRegistration);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const sendMessage = useCallback(async (message: ServiceWorkerMessage) => {
    if (!swRegistration?.active) {
      throw new Error('Service worker not available');
    }

    return new Promise((resolve, reject) => {
      const channel = new MessageChannel();

      channel.port1.onmessage = (event) => {
        if (event.data.error) {
          reject(new Error(event.data.error));
        } else {
          resolve(event.data);
        }
      };

      swRegistration.active.postMessage(message, [channel.port2]);

      setTimeout(() => {
        reject(new Error('Service worker message timeout'));
      }, 5000);
    });
  }, [swRegistration]);

  return {
    isOnline,
    swRegistration,
    sendMessage,
    isServiceWorkerSupported: 'serviceWorker' in navigator,
  };
}

export default ServiceWorkerManager;