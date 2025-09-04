import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import Sidebar from './sidebar'
import { cn } from '@/lib/utils'

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const location = useLocation()

  // Determine if we should show the modern sidebar layout
  const useModernLayout = location.pathname.startsWith('/dashboard') || 
                         location.pathname.startsWith('/analytics') ||
                         location.pathname.startsWith('/portfolio') ||
                         location.pathname.startsWith('/insights') ||
                         location.pathname.startsWith('/clients')

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
      {/* Simple header for non-dashboard pages */}
      <header className="border-b border-border/50 glass-card sticky top-0 z-30">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-xl bg-gradient-primary shadow-lg">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">ConcordBroker</h1>
                <p className="text-xs text-muted-foreground">Real Estate Platform</p>
              </div>
            </div>
            
            <nav className="hidden md:flex items-center space-x-6">
              <a 
                href="/dashboard" 
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                  "hover:bg-accent/50",
                  location.pathname === '/dashboard' && "bg-brand-500/10 text-brand-600"
                )}
              >
                Dashboard
              </a>
              <a 
                href="/search" 
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                  "hover:bg-accent/50",
                  location.pathname === '/search' && "bg-brand-500/10 text-brand-600"
                )}
              >
                Search
              </a>
              <a 
                href="/analytics" 
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                  "hover:bg-accent/50",
                  location.pathname === '/analytics' && "bg-brand-500/10 text-brand-600"
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