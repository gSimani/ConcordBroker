import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import Sidebar from './sidebar'
import { cn } from '@/lib/utils'

function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const location = useLocation()

  // Determine if we should show the modern sidebar layout
  const useModernLayout = location.pathname.startsWith('/dashboard') || 
                         location.pathname.startsWith('/analytics') ||
                         location.pathname.startsWith('/portfolio') ||
                         location.pathname.startsWith('/insights') ||
                         location.pathname.startsWith('/clients') ||
                         location.pathname.startsWith('/tax-deed-sales') ||
                         location.pathname.startsWith('/properties')

  if (useModernLayout) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-gray-50/30">
        <Sidebar 
          collapsed={sidebarCollapsed} 
          onCollapse={setSidebarCollapsed} 
        />
        
        <motion.main
          initial={false}
          animate={{
            marginLeft: sidebarCollapsed ? 72 : 280,
          }}
          transition={{
            type: "spring",
            damping: 25,
            stiffness: 200,
          }}
          className="min-h-screen custom-scrollbar"
        >
          <div className="relative">
            {children}
          </div>
        </motion.main>
      </div>
    )
  }

  // Fallback to original layout for other pages
  return (
    <div className="min-h-screen bg-background">
      {/* Executive Header */}
      <header 
        className="sticky top-0 z-30 shadow-lg"
        style={{
          background: 'linear-gradient(135deg, #4a5568 0%, #2d3748 100%)',
          borderBottom: '1px solid rgba(212, 175, 55, 0.3)'
        }}
      >
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div 
                className="flex items-center justify-center w-10 h-10 rounded-lg shadow-lg"
                style={{
                  background: 'linear-gradient(135deg, #d4af37 0%, #f4e5c2 100%)'
                }}
              >
                <span className="font-bold text-lg" style={{ color: '#2c3e50' }}>C</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">ConcordBroker</h1>
                <p className="text-xs font-light" style={{ color: '#95a5a6' }}>
                  Executive Real Estate Platform
                </p>
              </div>
            </div>
            
            <nav className="hidden md:flex items-center space-x-2">
              <a 
                href="/dashboard" 
                className={cn(
                  "px-6 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105",
                  "text-white hover:bg-white/10",
                  location.pathname === '/dashboard' && "bg-white/20 text-white font-semibold"
                )}
              >
                Dashboard
              </a>
              <a 
                href="/properties" 
                className={cn(
                  "px-6 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105",
                  "text-white hover:bg-white/10",
                  location.pathname.startsWith('/properties') && "bg-white/20 text-white font-semibold"
                )}
              >
                Properties
              </a>
              <a 
                href="/analytics" 
                className={cn(
                  "px-6 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105",
                  "text-white hover:bg-white/10",
                  location.pathname === '/analytics' && "bg-white/20 text-white font-semibold"
                )}
              >
                Analytics
              </a>
            </nav>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
      
      {/* Footer */}
      <footer className="border-t border-border/30 mt-12">
        <div className="container mx-auto px-6 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center mb-4">
              <div className="flex items-center justify-center w-6 h-6 rounded-lg bg-gradient-primary shadow-sm mr-3">
                <span className="text-white font-bold text-xs">C</span>
              </div>
              <span className="text-sm font-semibold text-foreground">ConcordBroker</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2025 ConcordBroker. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
export { Layout }