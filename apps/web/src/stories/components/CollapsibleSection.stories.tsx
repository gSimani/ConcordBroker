import type { Meta, StoryObj } from '@storybook/react';
import {
  CollapsibleSection,
  CollapsibleGroup,
} from '../../components/ui/collapsible-section';
import {
  Home,
  User,
  FileText,
  DollarSign,
  MapPin,
  ScrollText,
  Building2,
  History,
} from 'lucide-react';

const meta: Meta<typeof CollapsibleSection> = {
  title: 'Components/CollapsibleSection',
  component: CollapsibleSection,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'A collapsible/accordion section component for progressive disclosure UX pattern.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'bordered', 'card', 'minimal'],
    },
    defaultExpanded: {
      control: 'boolean',
    },
    disabled: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof CollapsibleSection>;

const SampleContent = () => (
  <div className="space-y-2 text-sm text-neutral-600">
    <p>
      This is the content that will be shown when the section is expanded.
      It can contain any React components.
    </p>
    <ul className="list-disc list-inside space-y-1">
      <li>First item</li>
      <li>Second item</li>
      <li>Third item</li>
    </ul>
  </div>
);

export const Default: Story = {
  args: {
    title: 'Property Details',
    children: <SampleContent />,
    defaultExpanded: false,
  },
  render: (args) => (
    <div className="max-w-md">
      <CollapsibleSection {...args} />
    </div>
  ),
};

export const WithIcon: Story = {
  args: {
    title: 'Property Details',
    icon: Home,
    children: <SampleContent />,
    defaultExpanded: true,
  },
  render: (args) => (
    <div className="max-w-md">
      <CollapsibleSection {...args} />
    </div>
  ),
};

export const WithSubtitle: Story = {
  args: {
    title: 'Owner Information',
    subtitle: 'Current property owner details',
    icon: User,
    children: <SampleContent />,
    defaultExpanded: true,
  },
  render: (args) => (
    <div className="max-w-md">
      <CollapsibleSection {...args} />
    </div>
  ),
};

export const WithBadge: Story = {
  args: {
    title: 'Sales History',
    icon: History,
    badge: 5,
    children: <SampleContent />,
    defaultExpanded: true,
  },
  render: (args) => (
    <div className="max-w-md">
      <CollapsibleSection {...args} />
    </div>
  ),
};

export const Variants: Story = {
  name: 'All Variants',
  render: () => (
    <div className="max-w-md space-y-6">
      <div>
        <p className="text-sm text-neutral-500 mb-2">Default</p>
        <CollapsibleSection title="Default Variant" defaultExpanded>
          <SampleContent />
        </CollapsibleSection>
      </div>

      <div>
        <p className="text-sm text-neutral-500 mb-2">Bordered</p>
        <CollapsibleSection
          title="Bordered Variant"
          variant="bordered"
          defaultExpanded
        >
          <SampleContent />
        </CollapsibleSection>
      </div>

      <div>
        <p className="text-sm text-neutral-500 mb-2">Card</p>
        <CollapsibleSection title="Card Variant" variant="card" defaultExpanded>
          <SampleContent />
        </CollapsibleSection>
      </div>

      <div>
        <p className="text-sm text-neutral-500 mb-2">Minimal</p>
        <CollapsibleSection
          title="Minimal Variant"
          variant="minimal"
          defaultExpanded
        >
          <SampleContent />
        </CollapsibleSection>
      </div>
    </div>
  ),
};

export const Disabled: Story = {
  args: {
    title: 'Disabled Section',
    icon: FileText,
    children: <SampleContent />,
    disabled: true,
    defaultExpanded: false,
  },
  render: (args) => (
    <div className="max-w-md">
      <CollapsibleSection {...args} />
    </div>
  ),
};

export const PropertyDetailsExample: Story = {
  name: 'Property Details Use Case',
  render: () => (
    <div className="max-w-lg bg-white rounded-lg border border-neutral-200 p-4">
      <h2 className="text-lg font-semibold mb-4">123 Ocean Drive</h2>

      <CollapsibleGroup>
        <CollapsibleSection
          title="Property Overview"
          icon={Home}
          badge="$485,000"
          defaultExpanded
        >
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-neutral-500">Property Type</span>
              <p className="font-medium">Single Family</p>
            </div>
            <div>
              <span className="text-neutral-500">Year Built</span>
              <p className="font-medium">2015</p>
            </div>
            <div>
              <span className="text-neutral-500">Bedrooms</span>
              <p className="font-medium">4</p>
            </div>
            <div>
              <span className="text-neutral-500">Bathrooms</span>
              <p className="font-medium">3</p>
            </div>
            <div>
              <span className="text-neutral-500">Square Feet</span>
              <p className="font-medium">2,450</p>
            </div>
            <div>
              <span className="text-neutral-500">Lot Size</span>
              <p className="font-medium">0.25 acres</p>
            </div>
          </div>
        </CollapsibleSection>

        <CollapsibleSection title="Owner Information" icon={User}>
          <div className="text-sm space-y-2">
            <p>
              <span className="text-neutral-500">Owner: </span>
              <span className="font-medium">SMITH JOHN & MARY</span>
            </p>
            <p>
              <span className="text-neutral-500">Mailing Address: </span>
              <span>456 Main Street, Miami, FL 33139</span>
            </p>
          </div>
        </CollapsibleSection>

        <CollapsibleSection title="Sales History" icon={History} badge={3}>
          <div className="text-sm space-y-3">
            <div className="flex justify-between items-center pb-2 border-b border-neutral-100">
              <div>
                <p className="font-medium">$485,000</p>
                <p className="text-neutral-500">Jan 2023</p>
              </div>
              <span className="text-green-600 text-sm">+8.5%</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b border-neutral-100">
              <div>
                <p className="font-medium">$447,000</p>
                <p className="text-neutral-500">Mar 2020</p>
              </div>
              <span className="text-green-600 text-sm">+12.3%</span>
            </div>
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium">$398,000</p>
                <p className="text-neutral-500">Jun 2017</p>
              </div>
              <span className="text-neutral-400 text-sm">Initial</span>
            </div>
          </div>
        </CollapsibleSection>

        <CollapsibleSection title="Tax Information" icon={DollarSign}>
          <div className="text-sm space-y-2">
            <div className="flex justify-between">
              <span className="text-neutral-500">Just Value</span>
              <span className="font-medium">$485,000</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Land Value</span>
              <span className="font-medium">$125,000</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Building Value</span>
              <span className="font-medium">$360,000</span>
            </div>
            <div className="flex justify-between pt-2 border-t border-neutral-100">
              <span className="text-neutral-500">Annual Taxes</span>
              <span className="font-medium text-[#0ABAB5]">$7,850</span>
            </div>
          </div>
        </CollapsibleSection>

        <CollapsibleSection title="Location" icon={MapPin}>
          <div className="text-sm space-y-2">
            <p>
              <span className="text-neutral-500">County: </span>
              <span className="font-medium">Broward</span>
            </p>
            <p>
              <span className="text-neutral-500">Subdivision: </span>
              <span>Ocean Heights</span>
            </p>
            <p>
              <span className="text-neutral-500">Parcel ID: </span>
              <code className="bg-neutral-100 px-1.5 py-0.5 rounded text-xs">
                484330110110
              </code>
            </p>
          </div>
        </CollapsibleSection>
      </CollapsibleGroup>
    </div>
  ),
};

export const AccordionMode: Story = {
  name: 'Accordion Mode',
  render: () => (
    <div className="max-w-md">
      <CollapsibleGroup accordion defaultExpandedIndex={0}>
        <CollapsibleSection
          title="Section 1"
          icon={Home}
          variant="bordered"
        >
          <p className="text-sm text-neutral-600">
            This is the content for section 1. In accordion mode, only one
            section can be open at a time.
          </p>
        </CollapsibleSection>

        <CollapsibleSection
          title="Section 2"
          icon={Building2}
          variant="bordered"
        >
          <p className="text-sm text-neutral-600">
            This is the content for section 2. Opening this will close section 1.
          </p>
        </CollapsibleSection>

        <CollapsibleSection
          title="Section 3"
          icon={ScrollText}
          variant="bordered"
        >
          <p className="text-sm text-neutral-600">
            This is the content for section 3. The accordion behavior ensures a
            cleaner UI.
          </p>
        </CollapsibleSection>
      </CollapsibleGroup>
    </div>
  ),
};
