/**
 * Global React DevTools Configuration
 * This file ensures React DevTools work across all pages in the application
 */

// Type definitions for React DevTools
declare global {
  interface Window {
    React: typeof import('react');
    ReactDOM: typeof import('react-dom');
    __REACT_DEVTOOLS_GLOBAL_HOOK__?: any;
    __REACT_DEVTOOLS_GLOBAL_HOOK_BACKUP__?: any;
    _React?: typeof import('react');
    _ReactDOM?: typeof import('react-dom');
  }
}

export class ReactDevToolsManager {
  private static instance: ReactDevToolsManager;
  private isInitialized = false;
  private componentCount = 0;
  private lastUpdate: Date | null = null;

  private constructor() {}

  static getInstance(): ReactDevToolsManager {
    if (!ReactDevToolsManager.instance) {
      ReactDevToolsManager.instance = new ReactDevToolsManager();
    }
    return ReactDevToolsManager.instance;
  }

  /**
   * Initialize React DevTools globally
   * Should be called once at app startup
   */
  initialize(React: any, ReactDOM: any): void {
    if (this.isInitialized) {
      console.log('React DevTools: Already initialized');
      return;
    }

    // Only enable in development
    if (import.meta.env.PROD) {
      console.log('React DevTools: Disabled in production');
      return;
    }

    try {
      // Expose React globally for DevTools
      window.React = React;
      window.ReactDOM = ReactDOM;

      // Also expose with underscore as backup
      window._React = React;
      window._ReactDOM = ReactDOM;

      // Store React version info
      const reactVersion = React.version || 'Unknown';

      // Enhanced logging for debugging
      const devToolsStatus = {
        enabled: true,
        reactVersion,
        timestamp: new Date().toISOString(),
        environment: import.meta.env.MODE,
        devToolsDetected: !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__,
        url: window.location.href
      };

      console.group('🔧 React DevTools Configuration');
      console.log('✅ Status:', devToolsStatus);
      console.log('📍 Current Page:', window.location.pathname);
      console.log('⚛️ React Version:', reactVersion);

      if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
        console.log('✅ DevTools Extension: Detected');
        this.setupDevToolsHooks();
      } else {
        console.warn('⚠️ DevTools Extension: Not detected');
        console.log('📥 Install from:');
        console.log('Chrome: https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi');
        console.log('Edge: https://microsoftedge.microsoft.com/addons/detail/react-developer-tools/gpphkfbcpidddadnkolkpfckpihlkkil');
        console.log('Firefox: https://addons.mozilla.org/en-US/firefox/addon/react-devtools/');
      }
      console.groupEnd();

      // Set initialization flag
      this.isInitialized = true;
      this.lastUpdate = new Date();

      // Monitor component mount/unmount
      this.setupComponentTracking();

      // Setup keyboard shortcuts
      this.setupKeyboardShortcuts();

      // Broadcast to other systems
      this.broadcastStatus();

    } catch (error) {
      console.error('React DevTools: Initialization failed', error);
    }
  }

  /**
   * Setup DevTools hooks for enhanced functionality
   */
  private setupDevToolsHooks(): void {
    const hook = window.__REACT_DEVTOOLS_GLOBAL_HOOK__;

    if (hook && hook.onCommitFiberRoot) {
      const originalOnCommit = hook.onCommitFiberRoot.bind(hook);

      hook.onCommitFiberRoot = (id: any, root: any, priorityLevel: any) => {
        // Track component updates
        this.componentCount++;
        this.lastUpdate = new Date();

        // Call original hook
        originalOnCommit(id, root, priorityLevel);

        // Log significant updates (throttled)
        if (this.componentCount % 100 === 0) {
          console.debug(`React DevTools: ${this.componentCount} component updates`);
        }
      };
    }
  }

  /**
   * Track component mounting and unmounting
   */
  private setupComponentTracking(): void {
    // This helps identify memory leaks and performance issues
    if (import.meta.env.DEV) {
      const trackingData = {
        mounted: new Set<string>(),
        unmounted: new Set<string>()
      };

      // Store tracking data globally for debugging
      (window as any).__REACT_COMPONENT_TRACKING__ = trackingData;
    }
  }

  /**
   * Setup keyboard shortcuts for DevTools
   */
  private setupKeyboardShortcuts(): void {
    document.addEventListener('keydown', (e) => {
      // Ctrl+Shift+R: Open React tab in DevTools
      if (e.ctrlKey && e.shiftKey && e.key === 'R') {
        console.log('Opening React DevTools...');
        // This will work if DevTools is already open
        if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
          console.log('Use the Components or Profiler tab in DevTools');
        }
      }

      // Ctrl+Shift+D: Debug current page React info
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        this.debugCurrentPage();
      }
    });
  }

  /**
   * Debug current page React information
   */
  debugCurrentPage(): void {
    console.group('🔍 React Debug Information');
    console.log('Page:', window.location.pathname);
    console.log('React Exposed:', !!window.React);
    console.log('ReactDOM Exposed:', !!window.ReactDOM);
    console.log('DevTools Hook:', !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__);
    console.log('Component Updates:', this.componentCount);
    console.log('Last Update:', this.lastUpdate);

    // Check for React root
    const rootElement = document.getElementById('root');
    if (rootElement) {
      console.log('Root Element:', rootElement);
      console.log('Has React Fiber:', !!(rootElement as any)._reactRootContainer);
    }

    console.groupEnd();
  }

  /**
   * Broadcast DevTools status to other systems
   */
  private broadcastStatus(): void {
    // Create custom event for other systems to listen to
    const event = new CustomEvent('react-devtools-ready', {
      detail: {
        initialized: this.isInitialized,
        version: window.React?.version,
        timestamp: new Date().toISOString()
      }
    });

    window.dispatchEvent(event);

    // Also broadcast via postMessage for iframes
    window.postMessage({
      type: 'REACT_DEVTOOLS_STATUS',
      initialized: this.isInitialized,
      version: window.React?.version
    }, '*');
  }

  /**
   * Get current DevTools status
   */
  getStatus(): object {
    return {
      initialized: this.isInitialized,
      devToolsDetected: !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__,
      reactVersion: window.React?.version || 'Not detected',
      componentUpdates: this.componentCount,
      lastUpdate: this.lastUpdate,
      currentPage: window.location.pathname
    };
  }

  /**
   * Force refresh DevTools connection
   */
  refresh(): void {
    if (window.React && window.ReactDOM) {
      this.isInitialized = false;
      this.initialize(window.React, window.ReactDOM);
    }
  }
}

// Create singleton instance
export const reactDevTools = ReactDevToolsManager.getInstance();

// Auto-initialize helper
export function initializeReactDevTools(React: any, ReactDOM: any): void {
  reactDevTools.initialize(React, ReactDOM);
}

// Export status checker
export function checkReactDevToolsStatus(): object {
  return reactDevTools.getStatus();
}

// Export debugger
export function debugReactPage(): void {
  reactDevTools.debugCurrentPage();
}