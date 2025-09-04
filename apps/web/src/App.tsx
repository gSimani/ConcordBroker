import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/toaster'
import { ThemeProvider } from '@/components/theme-provider'
import Layout from '@/components/layout'

// Pages
import HomePage from '@/pages/home'
import DashboardPage from '@/pages/dashboard'
import SearchPage from '@/pages/search'
import PropertyPage from '@/pages/property'
import EntityPage from '@/pages/entity'
import AnalyticsPage from '@/pages/analytics'

// Property Pages
import { PropertySearch } from '@/pages/properties/PropertySearch'
import PropertyDetailPage from '@/pages/properties/[...slug]'
import { PropertyProfile } from '@/pages/property/PropertyProfile'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light" storageKey="concordbroker-theme">
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/properties" element={<PropertySearch />} />
              <Route path="/properties/:slug" element={<PropertyDetailPage />} />
              <Route path="/properties/:city/:address" element={<PropertyDetailPage />} />
              <Route path="/property/:folio" element={<PropertyPage />} />
              <Route path="/entity/:id" element={<EntityPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Routes>
          </Layout>
        </Router>
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App