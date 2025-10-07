/**
 * Feature flags for controlling optional components
 * Enables/disables features without code changes
 */

export interface FeatureFlags {
  // Core search features
  enableAutocomplete: boolean;
  enableAdvancedSearch: boolean;
  enableVoiceSearch: boolean;
  enableSearchHistory: boolean;

  // Display features
  showMap: boolean;
  showPropertyImages: boolean;
  showAnalytics: boolean;
  showAISearch: boolean;

  // Data features
  showSunbizDetails: boolean;
  showTaxDeeds: boolean;
  showInvestmentScoring: boolean;
  showPropertyComparisons: boolean;

  // Performance features
  enableCaching: boolean;
  enablePreloading: boolean;
  showPerformanceMetrics: boolean;
  enableServiceWorker: boolean;

  // UI features
  showAdvancedFilters: boolean;
  showExportTools: boolean;
  showBulkOperations: boolean;
  enableDarkMode: boolean;
}

// Production feature flags
export const PRODUCTION_FEATURES: FeatureFlags = {
  // Core search
  enableAutocomplete: true,
  enableAdvancedSearch: true,
  enableVoiceSearch: false,
  enableSearchHistory: true,

  // Display
  showMap: true,
  showPropertyImages: true,
  showAnalytics: true,
  showAISearch: true,

  // Data
  showSunbizDetails: true,
  showTaxDeeds: true,
  showInvestmentScoring: true,
  showPropertyComparisons: true,

  // Performance
  enableCaching: true,
  enablePreloading: true,
  showPerformanceMetrics: false,
  enableServiceWorker: true,

  // UI
  showAdvancedFilters: true,
  showExportTools: true,
  showBulkOperations: true,
  enableDarkMode: false
};

// MVP feature flags - minimal for Stage 4 testing
export const MVP_FEATURES: FeatureFlags = {
  // Core search - only essentials
  enableAutocomplete: true,
  enableAdvancedSearch: false,
  enableVoiceSearch: false,
  enableSearchHistory: false,

  // Display - focus on core functionality
  showMap: false,
  showPropertyImages: false,
  showAnalytics: false,
  showAISearch: false,

  // Data - core features only
  showSunbizDetails: true,
  showTaxDeeds: false,
  showInvestmentScoring: true,
  showPropertyComparisons: false,

  // Performance - enabled for testing
  enableCaching: true,
  enablePreloading: false,
  showPerformanceMetrics: true,
  enableServiceWorker: false,

  // UI - minimal interface
  showAdvancedFilters: false,
  showExportTools: false,
  showBulkOperations: false,
  enableDarkMode: false
};

// Development feature flags - all enabled for testing
export const DEVELOPMENT_FEATURES: FeatureFlags = {
  enableAutocomplete: true,
  enableAdvancedSearch: true,
  enableVoiceSearch: true,
  enableSearchHistory: true,
  showMap: true,
  showPropertyImages: true,
  showAnalytics: true,
  showAISearch: true,
  showSunbizDetails: true,
  showTaxDeeds: true,
  showInvestmentScoring: true,
  showPropertyComparisons: true,
  enableCaching: true,
  enablePreloading: true,
  showPerformanceMetrics: true,
  enableServiceWorker: true,
  showAdvancedFilters: true,
  showExportTools: true,
  showBulkOperations: true,
  enableDarkMode: true
};

// Get feature flags based on environment
export function getFeatureFlags(): FeatureFlags {
  const env = import.meta.env.VITE_APP_ENV || 'development';

  switch (env) {
    case 'production':
      return PRODUCTION_FEATURES;
    case 'mvp':
      return MVP_FEATURES;
    case 'development':
    default:
      return DEVELOPMENT_FEATURES;
  }
}

// Hook for using feature flags in components
export function useFeatureFlags(): FeatureFlags {
  return getFeatureFlags();
}

// Helper to check if a feature is enabled
export function isFeatureEnabled(feature: keyof FeatureFlags): boolean {
  const flags = getFeatureFlags();
  return flags[feature];
}

// Performance thresholds for Stage 4 gates
export const PERFORMANCE_THRESHOLDS = {
  LCP_TARGET: 2500,           // < 2.5s LCP target
  AUTOCOMPLETE_P95: 150,      // < 150ms autocomplete P95
  SEARCH_TIMEOUT: 5000,       // 5s search timeout
  MAX_NETWORK_ERRORS: 0       // 0 network errors allowed
};

// Counties for testing autocomplete performance
export const TEST_COUNTIES = ['COLUMBIA', 'JEFFERSON'];

export default getFeatureFlags;