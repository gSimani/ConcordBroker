import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta = {
  title: 'Design System/Typography',
  parameters: {
    docs: {
      description: {
        component: 'ConcordBroker typography scale and text styles.',
      },
    },
  },
};

export default meta;

export const TypeScale: StoryObj = {
  render: () => (
    <div className="space-y-4 bg-white rounded-xl p-6 border border-neutral-200">
      <div className="text-5xl font-bold tracking-tight">Display Large (48px)</div>
      <div className="text-4xl font-bold">Display Medium (36px)</div>
      <div className="text-3xl font-semibold">Display Small (30px)</div>
      <div className="text-2xl font-semibold">Heading Large (24px)</div>
      <div className="text-xl font-semibold">Heading Medium (20px)</div>
      <div className="text-lg font-medium">Heading Small (18px)</div>
      <div className="text-lg">Body Large (18px)</div>
      <div className="text-base">Body Medium (16px) - Default</div>
      <div className="text-sm">Body Small (14px)</div>
      <div className="text-xs font-medium uppercase tracking-wider">Label (12px)</div>
    </div>
  ),
};

export const FontWeights: StoryObj = {
  render: () => (
    <div className="space-y-4 bg-white rounded-xl p-6 border border-neutral-200">
      <div className="text-xl font-normal">Font Weight: Normal (400)</div>
      <div className="text-xl font-medium">Font Weight: Medium (500)</div>
      <div className="text-xl font-semibold">Font Weight: Semibold (600)</div>
      <div className="text-xl font-bold">Font Weight: Bold (700)</div>
    </div>
  ),
};

export const TextColors: StoryObj = {
  render: () => (
    <div className="space-y-3 bg-white rounded-xl p-6 border border-neutral-200">
      <p className="text-neutral-900">Primary Text - High emphasis content</p>
      <p className="text-neutral-600">Secondary Text - Medium emphasis content</p>
      <p className="text-neutral-500">Tertiary Text - Low emphasis content</p>
      <p className="text-neutral-400">Disabled Text - Inactive content</p>
      <p className="text-[#099A96]">Brand Text - Links and emphasis</p>
      <p className="text-green-600">Success Text - Positive messages</p>
      <p className="text-amber-600">Warning Text - Caution messages</p>
      <p className="text-red-600">Error Text - Error messages</p>
      <p className="text-blue-600">Info Text - Informational messages</p>
    </div>
  ),
};

export const PropertyDataDisplay: StoryObj = {
  name: 'Property Data Display',
  render: () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 border border-neutral-200">
        <h3 className="text-lg font-semibold mb-4">Property Value Display</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm text-neutral-500">Just Value</span>
            <span className="text-lg font-semibold text-neutral-900">$485,000</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-neutral-500">Land Value</span>
            <span className="text-base text-neutral-700">$125,000</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-neutral-500">Building Value</span>
            <span className="text-base text-neutral-700">$360,000</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 border border-neutral-200">
        <h3 className="text-lg font-semibold mb-4">Address Display</h3>
        <p className="text-base font-medium text-neutral-900">123 Ocean Drive</p>
        <p className="text-sm text-neutral-600">Fort Lauderdale, FL 33301</p>
        <p className="text-xs text-neutral-400 font-mono mt-2">Parcel: 484330110110</p>
      </div>

      <div className="bg-white rounded-xl p-6 border border-neutral-200">
        <h3 className="text-lg font-semibold mb-4">Owner Information</h3>
        <p className="text-base font-medium text-neutral-900">SMITH JOHN & MARY</p>
        <p className="text-sm text-neutral-600">456 Main Street</p>
        <p className="text-sm text-neutral-600">Miami, FL 33139</p>
      </div>
    </div>
  ),
};

export const Truncation: StoryObj = {
  render: () => (
    <div className="space-y-4 bg-white rounded-xl p-6 border border-neutral-200 max-w-md">
      <div>
        <h4 className="text-sm font-medium text-neutral-500 mb-2">Single Line Truncate</h4>
        <p className="truncate text-base">
          This is a very long text that will be truncated with an ellipsis at the end when it overflows the container
        </p>
      </div>
      <div>
        <h4 className="text-sm font-medium text-neutral-500 mb-2">Two Line Clamp</h4>
        <p className="line-clamp-2 text-base">
          This is a very long text that will be clamped to two lines. When the content exceeds two lines, it will show an ellipsis. This is useful for card descriptions and previews.
        </p>
      </div>
      <div>
        <h4 className="text-sm font-medium text-neutral-500 mb-2">Three Line Clamp</h4>
        <p className="line-clamp-3 text-base">
          This text will be clamped to three lines maximum. It's perfect for longer descriptions where you want to give users a preview but not show the entire content. After three lines, the text will be cut off with an ellipsis to indicate there's more content available.
        </p>
      </div>
    </div>
  ),
};
