import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/toaster'
import { ThemeProvider } from '@/components/theme-provider'
import Layout from '@/components/layout'
import ErrorBoundary from '@/components/ErrorBoundary'
import ServiceWorkerManager from '@/components/ServiceWorkerManager'
import { QueryProvider } from '@/providers/QueryProvider'
import { initializeCriticalPreloading, preloader, routePreloadConfigs } from '@/lib/preloader'
import { generateElementId } from '@/utils/generateElementId'

// Log to debug rendering issues
console.log('App.tsx loaded with performance optimizations')

// Enhanced loading component with skeleton UI
const PageLoader = () => (
  <div id={generateElementId('app', 'main', 'page-loader', 1)} className="flex items-center justify-center min-h-screen">
    <div id={generateElementId('app', 'main', 'loader-content', 1)} className="space-y-4 w-full max-w-md">
      <div id={generateElementId('app', 'main', 'spinner', 1)} className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <div id={generateElementId('app', 'main', 'skeleton-container', 1)} className="space-y-2">
        <div id={generateElementId('app', 'main', 'skeleton-bar', 1)} className="h-4 bg-gray-200 rounded-full animate-pulse"></div>
        <div id={generateElementId('app', 'main', 'skeleton-bar', 2)} className="h-4 bg-gray-200 rounded-full animate-pulse w-3/4"></div>
      </div>
    </div>
  </div>
)

// Route-based preloading component
function RoutePreloader() {
  const location = useLocation();

  useEffect(() => {
    // Preload resources for current route
    const matchingConfig = routePreloadConfigs.find(config => {
      const routePattern = config.route.replace(/:[^/]+/g, '[^/]+');
      const regex = new RegExp(`^${routePattern}$`);
      return regex.test(location.pathname);
    });

    if (matchingConfig) {
      preloader.preloadRoute(matchingConfig).catch(error => {
        console.warn('[RoutePreloader] Failed to preload route resources:', error);
      });
    }
  }, [location.pathname]);

  return null;
}

// Critical pages loaded immediately
import HomePage from '@/pages/home'

// Lazy load all other pages for code splitting
const DashboardPage = lazy(() => import('@/pages/dashboard'))
const SearchPage = lazy(() => import('@/pages/search'))
const PropertyPage = lazy(() => import('@/pages/property'))
const EntityPage = lazy(() => import('@/pages/entity'))
const AnalyticsPage = lazy(() => import('@/pages/analytics'))
const AISearchPage = lazy(() => import('@/pages/AISearch'))

// Property Pages - lazy loaded
// const PropertySearch = lazy(() => import('@/pages/PropertySearch'))
const ProductionPropertySearch = lazy(() => import('@/pages/ProductionPropertySearch'))
// const OptimizedPropertySearch = lazy(() => import('@/pages/properties/OptimizedPropertySearch'))
// const FastPropertySearch = lazy(() => import('@/components/FastPropertySearch'))
const PropertyDetailPage = lazy(() => import('@/pages/properties/[...slug]'))
const EnhancedPropertyProfile = lazy(() => import('@/pages/property/EnhancedPropertyProfile'))
const SimplePropertyPage = lazy(() => import('@/pages/properties/SimplePropertyPage'))
const TaxDeedSales = lazy(() => import('@/pages/TaxDeedSales'))
const CalculatorDemo = lazy(() => import('@/pages/CalculatorDemo'))
const MortgageTools = lazy(() => import('@/pages/MortgageTools'))
const PerformanceTest = lazy(() => import('@/pages/PerformanceTest'))
const TestDORCodes = lazy(() => import('@/pages/TestDORCodes'))
const DiagnosticsProperties = lazy(() => import('@/pages/DiagnosticsProperties'))
const TestPropertyCards = lazy(() => import('@/pages/TestPropertyCards'))
const AIPropertyProfile = lazy(() => import('@/pages/property/AIPropertyProfile'))

// Admin Pages - lazy loaded
const Gate14 = lazy(() => import('@/pages/Gate14'))
const AdminDashboard = lazy(() => import('@/pages/admin/dashboard'))
const AdminSettings = lazy(() => import('@/pages/AdminSettings'))

function App() {
  console.log('App component rendering with advanced performance optimizations')

  useEffect(() => {
    console.log('App mounted - initializing performance features')

    // Initialize critical resource preloading
    initializeCriticalPreloading();

    // Register performance observer for Core Web Vitals
    if (typeof PerformanceObserver !== 'undefined') {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'largest-contentful-paint') {
              console.log(`[Performance] LCP: ${entry.startTime.toFixed(2)}ms`);
            }
            if (entry.entryType === 'first-input') {
              const fid = (entry as any).processingStart - entry.startTime;
              console.log(`[Performance] FID: ${fid.toFixed(2)}ms`);
            }
          }
        });

        observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input'] });

        return () => {
          observer.disconnect();
        };
      } catch (error) {
        console.warn('[Performance] PerformanceObserver not fully supported:', error);
      }
    }
  }, [])

  return (
    <ErrorBoundary>
      <QueryProvider>
        <ThemeProvider defaultTheme="light" storageKey="concordbroker-theme">
          <Router>
            <RoutePreloader />
            <div id={generateElementId('app', 'main', 'root-container', 1)}>
              <Layout>
                <div id={generateElementId('app', 'content', 'routes-container', 1)}>
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/search" element={<SearchPage />} />
                  <Route path="/ai-search" element={<AISearchPage />} />
                  <Route path="/properties" element={<ProductionPropertySearch />} />
                  <Route path="/diagnostics/properties" element={<DiagnosticsProperties />} />
                  {/* <Route path="/properties/fast" element={<FastPropertySearch />} /> */}

                  {/* New Enhanced Property URL Structure - /property/{county}/{parcel-id}/{address} */}
                  <Route path="/property/:county/:parcelId/:addressSlug" element={<EnhancedPropertyProfile />} />

                  {/* Legacy route support for backwards compatibility */}
                  <Route path="/properties/:city/:address" element={<SimplePropertyPage />} />
                  <Route path="/properties/:slug" element={<PropertyDetailPage />} />
                  <Route path="/property/:folio" element={<EnhancedPropertyProfile />} />

                  <Route path="/entity/:id" element={<EntityPage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                  <Route path="/tax-deed-sales" element={<TaxDeedSales />} />
                  <Route path="/calculator" element={<CalculatorDemo />} />
                  <Route path="/mortgage" element={<MortgageTools />} />
                  <Route path="/performance-test" element={<PerformanceTest />} />
                  <Route path="/test-dor-codes" element={<TestDORCodes />} />
                  <Route path="/test/property-cards" element={<TestPropertyCards />} />
                  <Route path="/ai-property/:parcelId" element={<AIPropertyProfile />} />
                  <Route path="/Gate14" element={<Gate14 />} />
                  <Route path="/admin/dashboard" element={<AdminDashboard />} />
                  <Route path="/admin/settings" element={<AdminSettings />} />
                    </Routes>
                  </Suspense>
                </div>
              </Layout>
            </div>

            {/* Service Worker Manager for offline support and performance monitoring */}
            <div id={generateElementId('app', 'footer', 'service-worker-container', 1)}>
              {/* ServiceWorkerManager removed - was blocking UI */}
            </div>

            <div id={generateElementId('app', 'footer', 'toaster-container', 1)}>
              <Toaster />
            </div>
          </Router>
        </ThemeProvider>
      </QueryProvider>
    </ErrorBoundary>
  )
}

export default App
