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

// Log to debug rendering issues
console.log('App.tsx loaded with performance optimizations')

// Enhanced loading component with skeleton UI
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="space-y-4 w-full max-w-md">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded-full animate-pulse"></div>
        <div className="h-4 bg-gray-200 rounded-full animate-pulse w-3/4"></div>
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
const PropertySearch = lazy(() => import('@/pages/properties/PropertySearch'))
// Removed: OptimizedPropertySearch - consolidated into PropertySearch
const FastPropertySearch = lazy(() => import('@/components/FastPropertySearch'))
const PropertyDetailPage = lazy(() => import('@/pages/properties/[...slug]'))
const EnhancedPropertyProfile = lazy(() => import('@/pages/property/EnhancedPropertyProfile'))
// Removed: SimplePropertyPage - consolidated into PropertyDetail
const TaxDeedSales = lazy(() => import('@/pages/TaxDeedSales'))
const PerformanceTest = lazy(() => import('@/pages/PerformanceTest'))

// Admin Pages - lazy loaded
// const AdminLogin = lazy(() => import('@/pages/admin/login'))
const AdminDashboard = lazy(() => import('@/pages/admin/dashboard'))
const AdminUsers = lazy(() => import('@/pages/admin/users'))
const AdminScrapers = lazy(() => import('@/pages/admin/scrapers'))

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
            <Layout>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/search" element={<SearchPage />} />
                  <Route path="/ai-search" element={<AISearchPage />} />
                  <Route path="/properties" element={<PropertySearch />} />
                  <Route path="/properties/fast" element={<FastPropertySearch />} />
                  <Route path="/properties/:city/:address" element={<EnhancedPropertyProfile />} />
                  <Route path="/properties/:slug" element={<PropertyDetailPage />} />
                  <Route path="/property/:folio" element={<EnhancedPropertyProfile />} />
                  <Route path="/entity/:id" element={<EntityPage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                  <Route path="/tax-deed-sales" element={<TaxDeedSales />} />
                  <Route path="/performance-test" element={<PerformanceTest />} />
                  <Route path="/admin/login" element={<AdminLogin />} />
                  <Route path="/admin/dashboard" element={<AdminDashboard />} />
                  <Route path="/admin/users" element={<AdminUsers />} />
                  <Route path="/admin/scrapers" element={<AdminScrapers />} />
                </Routes>
              </Suspense>
            </Layout>

            {/* Service Worker Manager for offline support and performance monitoring */}
            <ServiceWorkerManager />

            <Toaster />
          </Router>
        </ThemeProvider>
      </QueryProvider>
    </ErrorBoundary>
  )
}

export default App