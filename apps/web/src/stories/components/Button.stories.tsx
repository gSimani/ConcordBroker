import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '../../components/ui/button';
import { Search, Download, ChevronRight, Loader2 } from 'lucide-react';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    docs: {
      description: {
        component: 'Primary action button with multiple variants and sizes. Built on Radix UI Slot for composition.',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
      description: 'Visual style variant',
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
      description: 'Button size',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
    asChild: {
      control: 'boolean',
      description: 'Render as child element (for composition)',
    },
  },
  args: {
    children: 'Button',
    variant: 'default',
    size: 'default',
    disabled: false,
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

// Basic variants
export const Default: Story = {
  args: {
    children: 'Search Properties',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Cancel',
  },
};

export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'View Details',
  },
};

export const Destructive: Story = {
  args: {
    variant: 'destructive',
    children: 'Delete',
  },
};

export const Ghost: Story = {
  args: {
    variant: 'ghost',
    children: 'Learn More',
  },
};

export const Link: Story = {
  args: {
    variant: 'link',
    children: 'View Documentation',
  },
};

// Sizes
export const Small: Story = {
  args: {
    size: 'sm',
    children: 'Small Button',
  },
};

export const Large: Story = {
  args: {
    size: 'lg',
    children: 'Large Button',
  },
};

export const IconButton: Story = {
  args: {
    size: 'icon',
    children: <Search className="h-4 w-4" />,
    'aria-label': 'Search',
  },
};

// With icons
export const WithLeftIcon: Story = {
  render: () => (
    <Button>
      <Search className="h-4 w-4 mr-2" />
      Search Properties
    </Button>
  ),
};

export const WithRightIcon: Story = {
  render: () => (
    <Button>
      View All
      <ChevronRight className="h-4 w-4 ml-2" />
    </Button>
  ),
};

export const WithDownloadIcon: Story = {
  render: () => (
    <Button variant="outline">
      <Download className="h-4 w-4 mr-2" />
      Export CSV
    </Button>
  ),
};

// States
export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'Disabled Button',
  },
};

export const Loading: Story = {
  render: () => (
    <Button disabled>
      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      Loading...
    </Button>
  ),
};

// All Variants Overview
export const AllVariants: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-sm font-medium text-neutral-500 mb-3">Variants</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="default">Default</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="link">Link</Button>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-neutral-500 mb-3">Sizes</h3>
        <div className="flex flex-wrap items-center gap-3">
          <Button size="sm">Small</Button>
          <Button size="default">Default</Button>
          <Button size="lg">Large</Button>
          <Button size="icon" aria-label="Search">
            <Search className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-neutral-500 mb-3">With Icons</h3>
        <div className="flex flex-wrap gap-3">
          <Button>
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button variant="secondary">
            View All
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-neutral-500 mb-3">States</h3>
        <div className="flex flex-wrap gap-3">
          <Button>Normal</Button>
          <Button disabled>Disabled</Button>
          <Button disabled>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Loading
          </Button>
        </div>
      </div>
    </div>
  ),
};

// Property-specific actions
export const PropertyActions: Story = {
  name: 'Property Action Buttons',
  render: () => (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-neutral-500">Common Property Actions</h3>
      <div className="flex flex-wrap gap-3">
        <Button>
          <Search className="h-4 w-4 mr-2" />
          Search Properties
        </Button>
        <Button variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Export to CSV
        </Button>
        <Button variant="secondary">View on Map</Button>
        <Button variant="ghost">Clear Filters</Button>
      </div>
      <div className="flex flex-wrap gap-3 mt-4">
        <Button variant="destructive" size="sm">Remove from List</Button>
        <Button variant="link" size="sm">View Property History</Button>
      </div>
    </div>
  ),
};
