import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { NavLink, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  BarChart3,
  Building2,
  Home,
  Search,
  Settings,
  Users,
  PieChart,
  TrendingUp,
  FileText,
  Bell,
  User,
  Menu,
  X,
  ChevronDown,
  Activity,
  Zap,
  Gavel,
  Brain,
} from 'lucide-react'

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: number
  isNew?: boolean
  children?: NavItem[]
}

const navigation: NavItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: Home,
  },
  {
    name: 'Search Properties',
    href: '/properties',
    icon: Search,
  },
  {
    name: 'Tax Deed Sales',
    href: '/tax-deed-sales',
    icon: Gavel,
    isNew: true,
    badge: 109,
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
    badge: 3,
  },
  {
    name: 'AI Agents',
    href: '/agents',
    icon: Brain,
    isNew: true,
    badge: 11,
  },
  {
    name: 'Portfolio',
    href: '/portfolio',
    icon: Building2,
    children: [
      { name: 'All Properties', href: '/portfolio/all', icon: Building2 },
      { name: 'Performance', href: '/portfolio/performance', icon: TrendingUp },
      { name: 'Reports', href: '/portfolio/reports', icon: FileText },
    ],
  },
  {
    name: 'Market Insights',
    href: '/insights',
    icon: PieChart,
    isNew: true,
    children: [
      { name: 'Trends', href: '/insights/trends', icon: TrendingUp },
      { name: 'Forecasts', href: '/insights/forecasts', icon: Activity },
      { name: 'Opportunities', href: '/insights/opportunities', icon: Zap },
    ],
  },
  {
    name: 'Clients',
    href: '/clients',
    icon: Users,
    badge: 12,
  },
]

const bottomNavigation: NavItem[] = [
  {
    name: 'Notifications',
    href: '/notifications',
    icon: Bell,
    badge: 5,
  },
  {
    name: 'Profile',
    href: '/profile',
    icon: User,
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
  },
]

interface SidebarProps {
  collapsed?: boolean
  onCollapse?: (collapsed: boolean) => void
  className?: string
}

export default function Sidebar({ collapsed: externalCollapsed, onCollapse, className }: SidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false)
  const [expandedItems, setExpandedItems] = useState<string[]>([])
  const location = useLocation()

  const collapsed = externalCollapsed !== undefined ? externalCollapsed : internalCollapsed

  const toggleCollapse = () => {
    if (onCollapse) {
      onCollapse(!collapsed)
    } else {
      setInternalCollapsed(!collapsed)
    }
  }

  const toggleExpanded = (itemName: string) => {
    if (collapsed) return
    
    setExpandedItems(prev => 
      prev.includes(itemName) 
        ? prev.filter(item => item !== itemName)
        : [...prev, itemName]
    )
  }

  // Auto-expand active parent items
  useEffect(() => {
    navigation.forEach(item => {
      if (item.children && item.children.some(child => location.pathname.startsWith(child.href))) {
        setExpandedItems(prev => prev.includes(item.name) ? prev : [...prev, item.name])
      }
    })
  }, [location.pathname])

  const sidebarVariants = {
    expanded: {
      width: 280,
      transition: {
        type: "spring" as const,
        damping: 25,
        stiffness: 200,
      }
    },
    collapsed: {
      width: 72,
      transition: {
        type: "spring" as const,
        damping: 25,
        stiffness: 200,
      }
    }
  }

  const contentVariants = {
    expanded: {
      opacity: 1,
      transition: {
        delay: 0.1,
        duration: 0.2,
      }
    },
    collapsed: {
      opacity: 0,
      transition: {
        duration: 0.1,
      }
    }
  }

  return (
    <motion.div
      initial={false}
      animate={collapsed ? "collapsed" : "expanded"}
      variants={sidebarVariants}
      className={cn(
        "fixed left-0 top-0 z-40 h-screen",
        "glass-card border-r border-border/50",
        "flex flex-col",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border/30">
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="flex items-center space-x-3"
            >
              <div className="flex items-center justify-center w-8 h-8 rounded-xl bg-gradient-primary shadow-lg">
                <Building2 className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-foreground">ConcordBroker</span>
                <span className="text-xs text-muted-foreground">Real Estate Platform</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          onClick={toggleCollapse}
          className={cn(
            "p-2 rounded-lg transition-colors duration-200",
            "hover:bg-accent/50 active:scale-95",
            "flex items-center justify-center",
            collapsed && "mx-auto"
          )}
        >
          <motion.div
            animate={{ rotate: collapsed ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            {collapsed ? <Menu className="w-4 h-4" /> : <X className="w-4 h-4" />}
          </motion.div>
        </button>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="px-3 py-4">
          {/* Main Navigation */}
          <nav className="space-y-1">
            {navigation.map((item) => (
              <NavItem
                key={item.name}
                item={item}
                collapsed={collapsed}
                expanded={expandedItems.includes(item.name)}
                onToggleExpanded={() => toggleExpanded(item.name)}
              />
            ))}
          </nav>

          {/* Divider */}
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              variants={contentVariants}
              className="my-6 border-t border-border/30"
            />
          )}

          {/* Bottom Navigation */}
          <nav className="space-y-1">
            {bottomNavigation.map((item) => (
              <NavItem
                key={item.name}
                item={item}
                collapsed={collapsed}
                expanded={false}
                onToggleExpanded={() => {}}
              />
            ))}
          </nav>
        </div>
      </div>

      {/* User Section */}
      <div className="p-3 border-t border-border/30">
        <motion.div
          className={cn(
            "flex items-center space-x-3 p-3 rounded-xl",
            "glass transition-colors duration-200",
            "hover:bg-accent/30",
            collapsed && "justify-center"
          )}
        >
          <div className="relative">
            <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center">
              <span className="text-xs font-medium text-white">JD</span>
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-success-500 border-2 border-background status-dot" />
          </div>
          
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="flex-1 min-w-0"
              >
                <p className="text-sm font-medium text-foreground truncate">John Doe</p>
                <p className="text-xs text-muted-foreground truncate">Real Estate Agent</p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </motion.div>
  )
}

interface NavItemProps {
  item: NavItem
  collapsed: boolean
  expanded: boolean
  onToggleExpanded: () => void
  depth?: number
}

function NavItem({ item, collapsed, expanded, onToggleExpanded, depth = 0 }: NavItemProps) {
  const location = useLocation()
  const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/')
  const hasChildren = item.children && item.children.length > 0
  const Icon = item.icon

  return (
    <div className="relative">
      {/* Main Item */}
      <motion.div
        whileHover={{ scale: collapsed ? 1.05 : 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="relative"
      >
        {hasChildren && !collapsed ? (
          <button
            onClick={onToggleExpanded}
            className={cn(
              "w-full flex items-center justify-between p-3 rounded-xl",
              "transition-all duration-200",
              "hover:bg-accent/50 active:bg-accent/70",
              "text-left",
              isActive && "bg-brand-500/10 text-brand-600",
              depth > 0 && "ml-4"
            )}
          >
            <div className="flex items-center space-x-3">
              <div className={cn(
                "flex items-center justify-center w-5 h-5",
                isActive && "text-brand-600"
              )}>
                <Icon className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium">{item.name}</span>
              {item.isNew && (
                <span className="px-2 py-0.5 text-xs font-medium bg-brand-500 text-white rounded-full">
                  New
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {item.badge && (
                <span className="px-2 py-0.5 text-xs font-medium bg-error-500 text-white rounded-full min-w-[1.25rem] text-center">
                  {item.badge}
                </span>
              )}
              <motion.div
                animate={{ rotate: expanded ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              </motion.div>
            </div>
          </button>
        ) : (
          <NavLink
            to={item.href}
            className={({ isActive }) => cn(
              "flex items-center justify-between p-3 rounded-xl",
              "transition-all duration-200 group relative",
              "hover:bg-accent/50 active:bg-accent/70",
              collapsed && "justify-center",
              isActive && "bg-brand-500/10 text-brand-600 shadow-sm",
              depth > 0 && !collapsed && "ml-4"
            )}
          >
            <div className="flex items-center space-x-3">
              <div className={cn(
                "flex items-center justify-center w-5 h-5 transition-colors",
                isActive && "text-brand-600"
              )}>
                <Icon className="w-5 h-5" />
              </div>
              
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    className="text-sm font-medium"
                  >
                    {item.name}
                  </motion.span>
                )}
              </AnimatePresence>

              {!collapsed && item.isNew && (
                <motion.span
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="px-2 py-0.5 text-xs font-medium bg-brand-500 text-white rounded-full"
                >
                  New
                </motion.span>
              )}
            </div>

            {item.badge && (
              <AnimatePresence>
                {!collapsed ? (
                  <motion.span
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0 }}
                    className="px-2 py-0.5 text-xs font-medium bg-error-500 text-white rounded-full min-w-[1.25rem] text-center"
                  >
                    {item.badge}
                  </motion.span>
                ) : (
                  <motion.div
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0 }}
                    className="absolute -top-1 -right-1 w-3 h-3 bg-error-500 rounded-full"
                  />
                )}
              </AnimatePresence>
            )}

            {/* Tooltip for collapsed state */}
            {collapsed && (
              <div className="absolute left-full ml-2 px-3 py-2 bg-popover text-popover-foreground text-sm rounded-lg shadow-lg border opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-all duration-200 z-50 whitespace-nowrap">
                {item.name}
                <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-2 h-2 bg-popover rotate-45 border-l border-b" />
              </div>
            )}
          </NavLink>
        )}
      </motion.div>

      {/* Children */}
      <AnimatePresence>
        {hasChildren && expanded && !collapsed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-1 space-y-1">
              {item.children?.map((child) => (
                <NavItem
                  key={child.name}
                  item={child}
                  collapsed={collapsed}
                  expanded={false}
                  onToggleExpanded={() => {}}
                  depth={depth + 1}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}