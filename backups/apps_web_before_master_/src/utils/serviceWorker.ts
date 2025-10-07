// Service Worker registration and management utilities

const isLocalhost = Boolean(
  window.location.hostname === 'localhost' ||
  window.location.hostname === '[::1]' ||
  window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/)
);

interface ServiceWorkerConfig {
  onSuccess?: (registration: ServiceWorkerRegistration) => void;
  onUpdate?: (registration: ServiceWorkerRegistration) => void;
  onOfflineReady?: () => void;
}

export function registerSW(config?: ServiceWorkerConfig) {
  if ('serviceWorker' in navigator) {
    const publicUrl = new URL(window.location.href);
    if (publicUrl.origin !== window.location.origin) {
      return;
    }

    window.addEventListener('load', () => {
      const swUrl = '/sw.js';

      if (isLocalhost) {
        checkValidServiceWorker(swUrl, config);
        navigator.serviceWorker.ready.then(() => {
          console.log('Service Worker: Ready for offline use');
          config?.onOfflineReady?.();
        });
      } else {
        registerValidSW(swUrl, config);
      }
    });
  }
}

function registerValidSW(swUrl: string, config?: ServiceWorkerConfig) {
  navigator.serviceWorker
    .register(swUrl)
    .then((registration) => {
      console.log('Service Worker: Registered successfully');

      registration.onupdatefound = () => {
        const installingWorker = registration.installing;
        if (installingWorker == null) {
          return;
        }

        installingWorker.onstatechange = () => {
          if (installingWorker.state === 'installed') {
            if (navigator.serviceWorker.controller) {
              console.log('Service Worker: New content available');
              config?.onUpdate?.(registration);
            } else {
              console.log('Service Worker: Content cached for offline use');
              config?.onSuccess?.(registration);
            }
          }
        };
      };
    })
    .catch((error) => {
      console.error('Service Worker: Registration failed', error);
    });
}

function checkValidServiceWorker(swUrl: string, config?: ServiceWorkerConfig) {
  fetch(swUrl, {
    headers: { 'Service-Worker': 'script' },
  })
    .then((response) => {
      const contentType = response.headers.get('content-type');
      if (
        response.status === 404 ||
        (contentType != null && contentType.indexOf('javascript') === -1)
      ) {
        navigator.serviceWorker.ready.then((registration) => {
          registration.unregister().then(() => {
            window.location.reload();
          });
        });
      } else {
        registerValidSW(swUrl, config);
      }
    })
    .catch(() => {
      console.log('Service Worker: No internet connection. App is running in offline mode.');
    });
}

export function unregister() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error('Service Worker: Unregistration error', error);
      });
  }
}

// Utility functions for cache management
export class ServiceWorkerManager {
  private registration: ServiceWorkerRegistration | null = null;

  constructor(registration?: ServiceWorkerRegistration) {
    this.registration = registration || null;
  }

  // Clear all caches
  async clearCache(cacheNames?: string[]): Promise<void> {
    if (this.registration?.active) {
      this.registration.active.postMessage({
        type: 'CLEAR_CACHE',
        payload: { cacheNames }
      });
    }
  }

  // Prefetch common property searches
  async prefetchProperties(): Promise<void> {
    if (this.registration?.active) {
      this.registration.active.postMessage({
        type: 'PREFETCH_PROPERTIES'
      });
    }
  }

  // Get cache size
  async getCacheSize(): Promise<number> {
    return new Promise((resolve) => {
      if (!this.registration?.active) {
        resolve(0);
        return;
      }

      const channel = new MessageChannel();
      channel.port1.onmessage = (event) => {
        if (event.data.type === 'CACHE_SIZE') {
          resolve(event.data.size);
        }
      };

      this.registration.active.postMessage(
        { type: 'GET_CACHE_SIZE' },
        [channel.port2]
      );
    });
  }

  // Check if app is offline
  get isOffline(): boolean {
    return !navigator.onLine;
  }

  // Format cache size for display
  formatCacheSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';

    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }
}

// Hook for using service worker in React components
export function useServiceWorker() {
  const [registration, setRegistration] = React.useState<ServiceWorkerRegistration | null>(null);
  const [isOffline, setIsOffline] = React.useState(!navigator.onLine);
  const [cacheSize, setCacheSize] = React.useState(0);

  React.useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Register service worker
    registerSW({
      onSuccess: (reg) => {
        setRegistration(reg);
        console.log('Service Worker: Successfully registered');
      },
      onUpdate: (reg) => {
        setRegistration(reg);
        console.log('Service Worker: New version available');
      },
      onOfflineReady: () => {
        console.log('Service Worker: App ready for offline use');
      }
    });

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const manager = React.useMemo(() => {
    return new ServiceWorkerManager(registration);
  }, [registration]);

  const updateCacheSize = React.useCallback(async () => {
    const size = await manager.getCacheSize();
    setCacheSize(size);
  }, [manager]);

  React.useEffect(() => {
    updateCacheSize();
  }, [updateCacheSize]);

  return {
    registration,
    isOffline,
    cacheSize,
    manager,
    updateCacheSize,
    clearCache: manager.clearCache.bind(manager),
    prefetchProperties: manager.prefetchProperties.bind(manager),
    formatCacheSize: manager.formatCacheSize.bind(manager)
  };
}

// Add React import at the top for the hook
import React from 'react';