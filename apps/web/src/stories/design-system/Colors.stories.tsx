import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta = {
  title: 'Design System/Colors',
  parameters: {
    docs: {
      description: {
        component: 'ConcordBroker Design System color palette based on Ilora Design System.',
      },
    },
  },
};

export default meta;

const ColorSwatch = ({ name, value, textDark = false }: { name: string; value: string; textDark?: boolean }) => (
  <div className="flex flex-col items-center">
    <div
      className="w-16 h-16 rounded-lg shadow-sm border border-neutral-200"
      style={{ backgroundColor: value }}
    />
    <span className="text-xs text-neutral-600 mt-2">{name}</span>
    <span className="text-xs text-neutral-400 font-mono">{value}</span>
  </div>
);

const ColorScale = ({ name, colors }: { name: string; colors: { name: string; value: string }[] }) => (
  <div className="mb-8">
    <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-4">{name}</h3>
    <div className="flex gap-2 flex-wrap">
      {colors.map((color) => (
        <ColorSwatch key={color.name} name={color.name} value={color.value} />
      ))}
    </div>
  </div>
);

export const BrandTiffany: StoryObj = {
  render: () => (
    <ColorScale
      name="Brand - Tiffany"
      colors={[
        { name: '50', value: '#E6F7F6' },
        { name: '100', value: '#B3EBE9' },
        { name: '200', value: '#80DFDC' },
        { name: '300', value: '#4DD3CF' },
        { name: '400', value: '#26C9C4' },
        { name: '500', value: '#0ABAB5' },
        { name: '600', value: '#099A96' },
        { name: '700', value: '#077A77' },
        { name: '800', value: '#055A58' },
        { name: '900', value: '#033A39' },
      ]}
    />
  ),
};

export const BrandGold: StoryObj = {
  render: () => (
    <ColorScale
      name="Brand - Gold"
      colors={[
        { name: '50', value: '#FBF6E9' },
        { name: '100', value: '#F4E7C3' },
        { name: '200', value: '#EDD89D' },
        { name: '300', value: '#E6C977' },
        { name: '400', value: '#DFBA51' },
        { name: '500', value: '#D4AF37' },
        { name: '600', value: '#B8962F' },
        { name: '700', value: '#9C7D27' },
        { name: '800', value: '#80641F' },
        { name: '900', value: '#644B17' },
      ]}
    />
  ),
};

export const SemanticColors: StoryObj = {
  render: () => (
    <div className="space-y-8">
      <ColorScale
        name="Success"
        colors={[
          { name: '50', value: '#ECFDF5' },
          { name: '100', value: '#D1FAE5' },
          { name: '500', value: '#10B981' },
          { name: '700', value: '#047857' },
          { name: '900', value: '#064E3B' },
        ]}
      />
      <ColorScale
        name="Warning"
        colors={[
          { name: '50', value: '#FFFBEB' },
          { name: '100', value: '#FEF3C7' },
          { name: '500', value: '#F59E0B' },
          { name: '700', value: '#B45309' },
          { name: '900', value: '#78350F' },
        ]}
      />
      <ColorScale
        name="Error"
        colors={[
          { name: '50', value: '#FEF2F2' },
          { name: '100', value: '#FEE2E2' },
          { name: '500', value: '#EF4444' },
          { name: '700', value: '#B91C1C' },
          { name: '900', value: '#7F1D1D' },
        ]}
      />
      <ColorScale
        name="Info"
        colors={[
          { name: '50', value: '#EFF6FF' },
          { name: '100', value: '#DBEAFE' },
          { name: '500', value: '#3B82F6' },
          { name: '700', value: '#1D4ED8' },
          { name: '900', value: '#1E3A8A' },
        ]}
      />
    </div>
  ),
};

export const NeutralScale: StoryObj = {
  render: () => (
    <ColorScale
      name="Neutral"
      colors={[
        { name: '50', value: '#FAFAFA' },
        { name: '100', value: '#F5F5F5' },
        { name: '200', value: '#E5E5E5' },
        { name: '300', value: '#D4D4D4' },
        { name: '400', value: '#A3A3A3' },
        { name: '500', value: '#737373' },
        { name: '600', value: '#525252' },
        { name: '700', value: '#404040' },
        { name: '800', value: '#262626' },
        { name: '900', value: '#171717' },
      ]}
    />
  ),
};

export const ChartColors: StoryObj = {
  render: () => (
    <div>
      <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-4">
        Chart Colors (Color-blind Safe)
      </h3>
      <div className="flex gap-4 flex-wrap">
        <ColorSwatch name="Chart 1" value="#0ABAB5" />
        <ColorSwatch name="Chart 2" value="#D4AF37" />
        <ColorSwatch name="Chart 3" value="#3B82F6" />
        <ColorSwatch name="Chart 4" value="#8B5CF6" />
        <ColorSwatch name="Chart 5" value="#EC4899" />
        <ColorSwatch name="Chart 6" value="#F59E0B" />
        <ColorSwatch name="Chart 7" value="#10B981" />
        <ColorSwatch name="Chart 8" value="#6366F1" />
      </div>
    </div>
  ),
};

export const AllColors: StoryObj = {
  render: () => (
    <div className="space-y-12">
      <BrandTiffany.render?.({} as any, {} as any) />
      <BrandGold.render?.({} as any, {} as any) />
      <NeutralScale.render?.({} as any, {} as any) />
      <SemanticColors.render?.({} as any, {} as any) />
      <ChartColors.render?.({} as any, {} as any) />
    </div>
  ),
};
