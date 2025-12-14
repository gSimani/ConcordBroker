import type { Meta, StoryObj } from '@storybook/react';
import { AppShell } from '../../components/ui/app-shell';
import { MetricCard } from '../../components/ui/metric-card';
import { Home, DollarSign, Building2, ScrollText } from 'lucide-react';

const meta: Meta<typeof AppShell> = {
  title: 'Components/AppShell',
  component: AppShell,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Main application layout shell with responsive navigation.',
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof AppShell>;

const DashboardContent = () => (
  <div className="space-y-6">
    <div>
      <h1 className="text-2xl font-bold text-neutral-900">Dashboard</h1>
      <p className="text-neutral-500">Welcome back! Here's your property overview.</p>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        label="Total Properties"
        value="9,113,150"
        icon={Home}
        comparisonValue={2.3}
      />
      <MetricCard
        label="Average Value"
        value="$325,000"
        icon={DollarSign}
        comparisonValue={5.1}
        isGold
      />
      <MetricCard
        label="Tax Certificates"
        value="45,320"
        icon={ScrollText}
        comparisonValue={-1.2}
      />
      <MetricCard
        label="Active Listings"
        value="12,456"
        icon={Building2}
        comparisonValue={3.2}
      />
    </div>

    <div className="bg-white rounded-lg border border-neutral-200 p-6">
      <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="flex items-center justify-between py-3 border-b border-neutral-100 last:border-0"
          >
            <div>
              <p className="font-medium text-neutral-900">
                Property #{Math.floor(Math.random() * 1000000)}
              </p>
              <p className="text-sm text-neutral-500">
                {i} hour{i > 1 ? 's' : ''} ago
              </p>
            </div>
            <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">
              New
            </span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export const Default: Story = {
  args: {
    activeNavId: 'dashboard',
    userName: 'John Smith',
    notificationCount: 3,
    children: <DashboardContent />,
  },
};

export const CollapsedSidebar: Story = {
  args: {
    ...Default.args,
  },
  parameters: {
    docs: {
      description: {
        story: 'Click the collapse button in the sidebar header to collapse the navigation.',
      },
    },
  },
};

export const PropertiesPage: Story = {
  args: {
    activeNavId: 'properties',
    userName: 'John Smith',
    children: (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-neutral-900">Properties</h1>
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <p className="text-neutral-500">Property search and listing content goes here...</p>
        </div>
      </div>
    ),
  },
};

export const WithoutSearch: Story = {
  args: {
    ...Default.args,
    showSearch: false,
  },
};

export const WithoutNotifications: Story = {
  args: {
    ...Default.args,
    showNotifications: false,
  },
};
