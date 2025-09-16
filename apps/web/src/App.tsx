import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/toaster'
import { ThemeProvider } from '@/components/theme-provider'
import Layout from '@/components/layout'

// Loading component for lazy-loaded pages
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
  </div>
)

// Critical pages loaded immediately
import HomePage from '@/pages/home'

// Lazy load all other pages for code splitting
const DashboardPage = lazy(() => import('@/pages/dashboard'))
const SearchPage = lazy(() => import('@/pages/search'))
const PropertyPage = lazy(() => import('@/pages/property'))
const EntityPage = lazy(() => import('@/pages/entity'))
const AnalyticsPage = lazy(() => import('@/pages/analytics'))
const AISearchPage = lazy(() => import('@/pages/AISearch').then(module => ({ default: module.AISearchPage })))

// Property Pages - lazy loaded
const PropertySearch = lazy(() => import('@/pages/properties/PropertySearchRestored'))
const LivePropertySearch = lazy(() => import('@/pages/properties/LivePropertySearch'))
const PropertySearchFixed = lazy(() => import('@/pages/properties/PropertySearchFixed'))
const PropertyDetailPage = lazy(() => import('@/pages/properties/[...slug]'))
const EnhancedPropertyProfile = lazy(() => import('@/pages/property/EnhancedPropertyProfile'))
const TaxDeedSales = lazy(() => import('@/pages/TaxDeedSales'))

// Admin Pages - lazy loaded
const Gate14 = lazy(() => import('@/pages/Gate14'))
const AdminDashboard = lazy(() => import('@/pages/admin/dashboard'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light" storageKey="concordbroker-theme">
        <Router>
          <Routes>
            {/* Admin Routes (without Layout) */}
            <Route path="/Gate14" element={
              <Suspense fallback={<PageLoader />}>
                <Gate14 />
              </Suspense>
            } />
            <Route path="/admin/dashboard" element={
              <Suspense fallback={<PageLoader />}>
                <AdminDashboard />
              </Suspense>
            } />
            
            {/* Main App Routes (with Layout) */}
            <Route path="/*" element={
              <Layout>
                <Suspense fallback={<PageLoader />}>
                  <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/search" element={<SearchPage />} />
                    <Route path="/ai-search" element={<AISearchPage />} />
                    <Route path="/properties" element={<PropertySearch />} />
                    <Route path="/properties/:city/:address" element={<EnhancedPropertyProfile />} />
                    <Route path="/properties/:slug" element={<PropertyDetailPage />} />
                    <Route path="/property/:folio" element={<EnhancedPropertyProfile />} />
                    <Route path="/entity/:id" element={<EntityPage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/tax-deed-sales" element={<TaxDeedSales />} />
                  </Routes>
                </Suspense>
              </Layout>
            } />
          </Routes>
        </Router>
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App