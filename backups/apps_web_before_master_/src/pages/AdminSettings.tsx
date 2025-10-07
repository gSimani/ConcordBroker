import React, { useState } from 'react';
import BackupManager from '../components/admin/BackupManager';
import {
  CogIcon,
  ServerIcon,
  ShieldCheckIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

interface TabItem {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  component: React.ComponentType;
}

const tabs: TabItem[] = [
  {
    id: 'backup',
    name: 'Backup Management',
    icon: ServerIcon,
    component: BackupManager,
  },
  {
    id: 'security',
    name: 'Security',
    icon: ShieldCheckIcon,
    component: () => (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium mb-4">Security Settings</h3>
        <p className="text-gray-500">Security configuration coming soon...</p>
      </div>
    ),
  },
  {
    id: 'analytics',
    name: 'Analytics',
    icon: ChartBarIcon,
    component: () => (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium mb-4">Analytics Dashboard</h3>
        <p className="text-gray-500">Analytics dashboard coming soon...</p>
      </div>
    ),
  },
];

export default function AdminSettings() {
  const [activeTab, setActiveTab] = useState('backup');

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || BackupManager;

  return (
    <div id="admin-settings-page-1" className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <CogIcon className="h-8 w-8 mr-3 text-gray-600" />
              Admin Settings
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage system configuration and settings
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div id="admin-tabs-navigation-1" className="mb-8">
          <nav className="flex space-x-4">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors
                    ${activeTab === tab.id
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-white text-gray-600 hover:bg-gray-50'
                    }
                  `}
                >
                  <Icon className="h-5 w-5 mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Active Tab Content */}
        <div id="admin-tab-content-1">
          <ActiveComponent />
        </div>

        {/* Admin Notice */}
        <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex">
            <ShieldCheckIcon className="h-5 w-5 text-yellow-400 mr-3 flex-shrink-0" />
            <div className="text-sm text-yellow-700">
              <p className="font-medium">Admin Access Required</p>
              <p className="mt-1">
                These settings are restricted to administrators only. All changes are logged for security purposes.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}