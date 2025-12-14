/**
 * AppShell Component
 * ==================
 *
 * The main application layout shell with responsive navigation.
 * Provides consistent layout structure across all pages.
 *
 * Features:
 * - Responsive sidebar navigation (collapsible on mobile)
 * - Top header with search and user menu
 * - Main content area with proper spacing
 * - Mobile-first design
 * - Keyboard navigation support
 */

import React, { useState, useCallback } from 'react';
import {
  Menu,
  X,
  Search,
  Bell,
  User,
  Home,
  Building2,
  ScrollText,
  MapPin,
  TrendingUp,
  Settings,
  HelpCircle,
  ChevronLeft,
  LogOut,
  LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface NavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  badge?: string | number;
  children?: NavItem[];
}

export interface AppShellProps {
  /** The main content */
  children: React.ReactNode;
  /** Current active navigation item ID */
  activeNavId?: string;
  /** Navigation items */
  navItems?: NavItem[];
  /** User display name */
  userName?: string;
  /** User avatar URL */
  userAvatar?: string;
  /** Callback when navigation item is clicked */
  onNavClick?: (item: NavItem) => void;
  /** Callback when search is submitted */
  onSearch?: (query: string) => void;
  /** Callback when user menu item is clicked */
  onUserMenuClick?: (action: 'profile' | 'settings' | 'logout') => void;
  /** Show search in header */
  showSearch?: boolean;
  /** Show notifications in header */
  showNotifications?: boolean;
  /** Notification count */
  notificationCount?: number;
}

const defaultNavItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Home, href: '/' },
  { id: 'properties', label: 'Properties', icon: Building2, href: '/properties' },
  { id: 'tax-deeds', label: 'Tax Deeds', icon: ScrollText, href: '/tax-deeds' },
  { id: 'map', label: 'Map View', icon: MapPin, href: '/map' },
  { id: 'analytics', label: 'Analytics', icon: TrendingUp, href: '/analytics' },
];

/**
 * AppShell provides the main application layout with navigation.
 */
export const AppShell: React.FC<AppShellProps> = ({
  children,
  activeNavId,
  navItems = defaultNavItems,
  userName = 'User',
  userAvatar,
  onNavClick,
  onSearch,
  onUserMenuClick,
  showSearch = true,
  showNotifications = true,
  notificationCount = 0,
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleNavClick = useCallback(
    (item: NavItem) => {
      onNavClick?.(item);
      setSidebarOpen(false);
    },
    [onNavClick]
  );

  const handleSearchSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      onSearch?.(searchQuery);
    },
    [onSearch, searchQuery]
  );

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-50 h-full bg-white border-r border-neutral-200',
          'transform transition-all duration-300 ease-in-out',
          'lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
          sidebarCollapsed ? 'lg:w-16' : 'lg:w-64',
          'w-64'
        )}
      >
        {/* Sidebar header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-neutral-200">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#0ABAB5] flex items-center justify-center">
                <span className="text-white font-bold text-sm">CB</span>
              </div>
              <span className="font-semibold text-neutral-900">ConcordBroker</span>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-2 rounded-lg hover:bg-neutral-100 lg:hidden"
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden lg:flex p-2 rounded-lg hover:bg-neutral-100"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronLeft
              size={20}
              className={cn(
                'transition-transform duration-200',
                sidebarCollapsed && 'rotate-180'
              )}
            />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNavId === item.id;

            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg',
                  'text-left transition-colors duration-150',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0ABAB5]',
                  isActive
                    ? 'bg-[#0ABAB5]/10 text-[#0ABAB5]'
                    : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon size={20} className="flex-shrink-0" />
                {!sidebarCollapsed && (
                  <>
                    <span className="flex-1 font-medium">{item.label}</span>
                    {item.badge !== undefined && (
                      <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-[#0ABAB5]/10 text-[#0ABAB5]">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </button>
            );
          })}
        </nav>

        {/* Sidebar footer */}
        <div className="absolute bottom-0 left-0 right-0 p-2 border-t border-neutral-200">
          <button
            onClick={() => onUserMenuClick?.('settings')}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg',
              'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900',
              'transition-colors duration-150'
            )}
          >
            <Settings size={20} />
            {!sidebarCollapsed && <span className="font-medium">Settings</span>}
          </button>
          <button
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg',
              'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900',
              'transition-colors duration-150'
            )}
          >
            <HelpCircle size={20} />
            {!sidebarCollapsed && <span className="font-medium">Help</span>}
          </button>
        </div>
      </aside>

      {/* Main content area */}
      <div
        className={cn(
          'transition-all duration-300',
          sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-64'
        )}
      >
        {/* Top header */}
        <header className="sticky top-0 z-30 h-16 bg-white border-b border-neutral-200">
          <div className="h-full flex items-center justify-between px-4 gap-4">
            {/* Mobile menu button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-lg hover:bg-neutral-100 lg:hidden"
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>

            {/* Search */}
            {showSearch && (
              <form
                onSubmit={handleSearchSubmit}
                className="flex-1 max-w-xl hidden sm:block"
              >
                <div className="relative">
                  <Search
                    size={18}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400"
                  />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search properties, owners, parcels..."
                    className={cn(
                      'w-full h-10 pl-10 pr-4 rounded-lg',
                      'bg-neutral-100 border border-transparent',
                      'text-neutral-900 placeholder:text-neutral-400',
                      'focus:outline-none focus:border-[#0ABAB5] focus:ring-1 focus:ring-[#0ABAB5]',
                      'transition-colors duration-150'
                    )}
                  />
                </div>
              </form>
            )}

            {/* Right side actions */}
            <div className="flex items-center gap-2">
              {/* Mobile search button */}
              <button
                className="p-2 rounded-lg hover:bg-neutral-100 sm:hidden"
                aria-label="Search"
              >
                <Search size={20} />
              </button>

              {/* Notifications */}
              {showNotifications && (
                <button
                  className="relative p-2 rounded-lg hover:bg-neutral-100"
                  aria-label={`Notifications${notificationCount > 0 ? ` (${notificationCount} unread)` : ''}`}
                >
                  <Bell size={20} />
                  {notificationCount > 0 && (
                    <span className="absolute top-1 right-1 w-4 h-4 text-[10px] font-bold text-white bg-red-500 rounded-full flex items-center justify-center">
                      {notificationCount > 9 ? '9+' : notificationCount}
                    </span>
                  )}
                </button>
              )}

              {/* User menu */}
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 p-2 rounded-lg hover:bg-neutral-100"
                  aria-expanded={userMenuOpen}
                  aria-haspopup="true"
                >
                  {userAvatar ? (
                    <img
                      src={userAvatar}
                      alt={userName}
                      className="w-8 h-8 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-[#0ABAB5]/10 flex items-center justify-center">
                      <User size={16} className="text-[#0ABAB5]" />
                    </div>
                  )}
                  <span className="hidden md:block text-sm font-medium text-neutral-700">
                    {userName}
                  </span>
                </button>

                {/* User dropdown menu */}
                {userMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setUserMenuOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-48 py-1 bg-white rounded-lg shadow-lg border border-neutral-200 z-50">
                      <button
                        onClick={() => {
                          onUserMenuClick?.('profile');
                          setUserMenuOpen(false);
                        }}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100"
                      >
                        <User size={16} />
                        Profile
                      </button>
                      <button
                        onClick={() => {
                          onUserMenuClick?.('settings');
                          setUserMenuOpen(false);
                        }}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100"
                      >
                        <Settings size={16} />
                        Settings
                      </button>
                      <hr className="my-1 border-neutral-200" />
                      <button
                        onClick={() => {
                          onUserMenuClick?.('logout');
                          setUserMenuOpen(false);
                        }}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        <LogOut size={16} />
                        Logout
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
};

export default AppShell;
