# ConcordBroker Design System Plan

## Executive Summary

This document outlines a comprehensive design system implementation plan for ConcordBroker, inspired by the Ilora Design System (localhost:3003) and tailored for Florida property analytics. The plan addresses all 17 requirements for building a production-ready, accessible, and performant design system.

---

## 1. Design Foundations

### 1.1 Color System

Based on Ilora's color architecture with ConcordBroker branding:

```css
/* Primary Brand - Tiffany (from Ilora) */
--color-brand-50: #E6F7F6;
--color-brand-100: #B3EBE9;
--color-brand-200: #80DFDC;
--color-brand-300: #4DD3CF;
--color-brand-400: #26C9C4;
--color-brand-500: #0ABAB5;  /* Primary */
--color-brand-600: #099A96;
--color-brand-700: #077A77;
--color-brand-800: #055A58;
--color-brand-900: #033A39;

/* Accent - Gold (Executive branding) */
--color-gold-50: #FBF6E9;
--color-gold-100: #F4E7C3;
--color-gold-200: #EDD89D;
--color-gold-300: #E6C977;
--color-gold-400: #DFBA51;
--color-gold-500: #D4AF37;  /* Primary Gold */
--color-gold-600: #B8962F;
--color-gold-700: #9C7D27;
--color-gold-800: #80641F;
--color-gold-900: #644B17;

/* Semantic Colors */
--color-success-500: #10B981;
--color-warning-500: #F59E0B;
--color-error-500: #EF4444;
--color-info-500: #3B82F6;

/* Neutral Scale */
--color-neutral-50: #FAFAFA;
--color-neutral-100: #F5F5F5;
--color-neutral-200: #E5E5E5;
--color-neutral-300: #D4D4D4;
--color-neutral-400: #A3A3A3;
--color-neutral-500: #737373;
--color-neutral-600: #525252;
--color-neutral-700: #404040;
--color-neutral-800: #262626;
--color-neutral-900: #171717;
```

### 1.2 Spacing Scale (4px base)

| Token | Value | Usage |
|-------|-------|-------|
| space-1 | 4px | Icon padding, tight gaps |
| space-2 | 8px | Input padding, card gaps |
| space-3 | 12px | Button padding, form gaps |
| space-4 | 16px | Section padding, card padding |
| space-5 | 20px | Component margins |
| space-6 | 24px | Card padding, section gaps |
| space-8 | 32px | Section margins |
| space-10 | 40px | Major sections |
| space-12 | 48px | Page padding |
| space-16 | 64px | Hero sections |

### 1.3 Typography Scale

```css
/* Font Families */
--font-header: 'Inter', system-ui, sans-serif;
--font-body: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', monospace;

/* Type Scale */
--text-display-lg: 48px / 1.1;  /* Hero headings */
--text-display-md: 36px / 1.2;  /* Page titles */
--text-display-sm: 30px / 1.2;  /* Section titles */
--text-heading-lg: 24px / 1.3;  /* Card titles */
--text-heading-md: 20px / 1.4;  /* Sub-headings */
--text-heading-sm: 18px / 1.4;  /* Minor headings */
--text-body-lg: 18px / 1.6;     /* Large text */
--text-body-md: 16px / 1.5;     /* Default body */
--text-body-sm: 14px / 1.5;     /* Secondary text */
--text-label: 12px / 1.4;       /* Labels, captions */
```

### 1.4 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| radius-sm | 4px | Buttons, badges |
| radius-md | 8px | Inputs, small cards |
| radius-lg | 12px | Cards, modals |
| radius-xl | 16px | Large cards |
| radius-2xl | 24px | Hero sections |
| radius-full | 9999px | Pills, avatars |

### 1.5 Shadows

```css
--shadow-xs: 0 1px 2px rgba(0,0,0,0.05);
--shadow-sm: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
--shadow-md: 0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06);
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05);
--shadow-xl: 0 20px 25px rgba(0,0,0,0.1), 0 10px 10px rgba(0,0,0,0.04);
--shadow-glow: 0 0 20px rgba(10,186,181,0.3);  /* Brand glow */
```

### 1.6 Z-Index Scale

| Token | Value | Usage |
|-------|-------|-------|
| z-dropdown | 1000 | Dropdowns, tooltips |
| z-sticky | 1100 | Sticky headers |
| z-fixed | 1200 | Fixed elements |
| z-modal-backdrop | 1300 | Modal overlays |
| z-modal | 1400 | Modal content |
| z-popover | 1500 | Popovers |
| z-toast | 1600 | Toast notifications |
| z-command | 1700 | Command palette |

---

## 2. Component Architecture

### 2.1 Core UI Components (Priority 1)

| Component | States | Variants | Accessibility |
|-----------|--------|----------|---------------|
| Button | default, hover, focus, active, disabled, loading | primary, secondary, outline, ghost, danger | aria-label, aria-disabled |
| Input | default, focus, error, disabled, readonly | text, password, email, number, search | aria-invalid, aria-describedby |
| Select | closed, open, focused, error | single, multi, searchable | aria-expanded, role="listbox" |
| Card | default, hover, selected, loading | property, summary, action | role="article" |
| Badge | - | success, warning, error, info, neutral | role="status" |
| Alert | - | success, warning, error, info | role="alert", aria-live |
| Dialog | closed, open | small, medium, large, fullscreen | role="dialog", aria-modal |
| Tabs | active, inactive, disabled | line, contained, pills | role="tablist" |
| Table | default, loading, empty, error | simple, sortable, selectable | role="grid" |

### 2.2 Property-Specific Components (Priority 2)

| Component | Description | States |
|-----------|-------------|--------|
| MiniPropertyCard | Compact property summary | loading, loaded, error |
| PropertyMap | Interactive map view | loading, loaded, empty, error |
| ValueChart | Property value trends | loading, loaded, no-data |
| TaxBadge | Tax status indicator | current, delinquent, exempt |
| OwnerChip | Owner name with link | default, hover, active |
| ParcelLink | Clickable parcel ID | default, hover, copied |

### 2.3 Composition Rules

```tsx
// CORRECT: Composable components
<Card>
  <CardHeader>
    <CardTitle>Property Overview</CardTitle>
    <CardDescription>Last updated: Dec 13, 2025</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
  <CardFooter>
    <Button>View Details</Button>
  </CardFooter>
</Card>

// WRONG: Monolithic prop-based components
<PropertyCard
  title="..."
  description="..."
  content={...}
  footerButton={...}
/>
```

---

## 3. States-First Design

### 3.1 Required States for Every Data Component

```tsx
interface DataComponentProps<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  isEmpty: boolean;
  hasPermission: boolean;
}
```

### 3.2 State Components

```tsx
// Loading State
<Skeleton className="h-48 w-full rounded-lg" />
<Skeleton className="h-4 w-3/4 mt-4" />
<Skeleton className="h-4 w-1/2 mt-2" />

// Empty State
<EmptyState
  icon={<SearchIcon />}
  title="No properties found"
  description="Try adjusting your search filters"
  action={<Button>Clear Filters</Button>}
/>

// Error State
<ErrorState
  icon={<AlertCircle />}
  title="Failed to load properties"
  description={error.message}
  action={<Button onClick={retry}>Try Again</Button>}
/>

// No Permission State
<NoPermissionState
  title="Access Denied"
  description="You don't have permission to view this data"
  action={<Button>Request Access</Button>}
/>
```

### 3.3 State Priority Order

1. **isLoading** → Show skeleton
2. **error** → Show error state
3. **!hasPermission** → Show permission denied
4. **isEmpty** → Show empty state
5. **data** → Show actual content

---

## 4. Accessibility (WCAG 2.2 AA)

### 4.1 Color Contrast Requirements

| Text Type | Minimum Ratio | Tools |
|-----------|--------------|-------|
| Normal text | 4.5:1 | WebAIM Contrast Checker |
| Large text (18px+) | 3:1 | axe DevTools |
| UI components | 3:1 | Stark (Figma plugin) |

### 4.2 Focus Management

```css
/* Visible focus ring */
:focus-visible {
  outline: 2px solid var(--color-brand-500);
  outline-offset: 2px;
}

/* Skip focus ring on mouse click */
:focus:not(:focus-visible) {
  outline: none;
}
```

### 4.3 Keyboard Navigation

| Component | Keys | Action |
|-----------|------|--------|
| Button | Enter, Space | Activate |
| Dialog | Escape | Close |
| Menu | Arrow keys | Navigate |
| Tabs | Arrow keys | Switch tabs |
| Command Palette | Ctrl+K | Open |

### 4.4 Screen Reader Support

```tsx
// Announce dynamic content
<div role="status" aria-live="polite">
  {`Found ${count} properties`}
</div>

// Hidden but accessible
<span className="sr-only">Loading property data</span>

// Descriptive buttons
<Button aria-label="View property details for 123 Main St">
  <EyeIcon /> View
</Button>
```

---

## 5. Performance (Core Web Vitals)

### 5.1 Targets

| Metric | Target | Current |
|--------|--------|---------|
| LCP (Largest Contentful Paint) | <2.5s | TBD |
| FID (First Input Delay) | <100ms | TBD |
| INP (Interaction to Next Paint) | <200ms | TBD |
| CLS (Cumulative Layout Shift) | <0.1 | TBD |

### 5.2 Optimization Strategies

```tsx
// 1. Virtualized Lists
<VirtualizedPropertyList
  items={properties}
  itemHeight={120}
  overscan={5}
/>

// 2. Image Optimization
<OptimizedImage
  src="/property.jpg"
  placeholder="blur"
  loading="lazy"
  sizes="(max-width: 768px) 100vw, 50vw"
/>

// 3. Code Splitting
const PropertyMap = lazy(() => import('./PropertyMap'));

// 4. Skeleton Loading
const PropertySkeleton = () => (
  <div className="animate-pulse">
    <div className="h-48 bg-neutral-200 rounded-lg" />
  </div>
);
```

### 5.3 INP Optimization

```tsx
// Defer non-critical updates
import { startTransition } from 'react';

const handleSearch = (query: string) => {
  // Urgent: Update input
  setSearchQuery(query);

  // Non-urgent: Update results
  startTransition(() => {
    setFilteredResults(filterProperties(query));
  });
};
```

---

## 6. Motion & Animation

### 6.1 Animation Tokens

```css
/* Durations */
--duration-instant: 100ms;
--duration-fast: 150ms;
--duration-normal: 200ms;
--duration-slow: 300ms;

/* Easings */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

### 6.2 Animation Guidelines

| Interaction | Animation | Duration |
|-------------|-----------|----------|
| Button hover | Scale 1.02 | 150ms |
| Card hover | Shadow increase, translateY -2px | 200ms |
| Modal open | Fade + scale from 0.95 | 200ms |
| Toast appear | Slide in from right | 300ms |
| Skeleton shimmer | Gradient sweep | 1.5s loop |

### 6.3 Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 7. Forms System

### 7.1 Form Component Library

```tsx
// Text Input with validation
<FormField
  name="parcelId"
  label="Parcel ID"
  required
  pattern="[0-9]{12}"
  errorMessage="Enter a valid 12-digit parcel ID"
>
  <Input placeholder="484330110110" />
</FormField>

// Formatted Currency Input
<FormattedInput
  type="currency"
  prefix="$"
  thousandSeparator=","
  decimalScale={0}
/>

// Address Autocomplete
<AddressAutocomplete
  placeholder="Start typing an address..."
  onSelect={handleAddressSelect}
  county="BROWARD"
/>

// Range Filter
<RangeFilter
  label="Property Value"
  min={0}
  max={10000000}
  step={10000}
  formatValue={(v) => `$${v.toLocaleString()}`}
/>
```

### 7.2 Validation States

```tsx
// Real-time validation
<Input
  value={value}
  onChange={handleChange}
  aria-invalid={!!error}
  aria-describedby={error ? 'error-message' : undefined}
/>
{error && (
  <p id="error-message" className="text-error-500 text-sm mt-1">
    {error}
  </p>
)}
```

---

## 8. Command Palette

### 8.1 Implementation

```tsx
// Trigger: Ctrl+K or Cmd+K
<CommandPalette
  open={open}
  onOpenChange={setOpen}
>
  <CommandInput placeholder="Search properties, actions, pages..." />
  <CommandList>
    <CommandGroup heading="Properties">
      <CommandItem onSelect={() => navigate('/properties')}>
        <SearchIcon /> Search Properties
      </CommandItem>
    </CommandGroup>
    <CommandGroup heading="Actions">
      <CommandItem onSelect={exportToCsv}>
        <DownloadIcon /> Export to CSV
      </CommandItem>
    </CommandGroup>
    <CommandGroup heading="Navigation">
      <CommandItem onSelect={() => navigate('/dashboard')}>
        <LayoutIcon /> Dashboard
      </CommandItem>
    </CommandGroup>
  </CommandList>
</CommandPalette>
```

### 8.2 Search Features

- Fuzzy matching for property addresses
- Recent searches
- Quick actions (export, print, share)
- Navigation shortcuts
- AI-powered suggestions (HuggingFace integration)

---

## 9. Data Visualization Standards

### 9.1 Chart Library: Recharts

```tsx
// Property Value Chart
<PropertyValueChart
  data={valueHistory}
  colors={{
    justValue: '#0ABAB5',
    landValue: '#D4AF37',
    buildingValue: '#3B82F6'
  }}
  showLegend
  showTooltip
  accessible
/>
```

### 9.2 Chart Accessibility

```tsx
// Screen reader support
<LineChart aria-label="Property value trends from 2019 to 2024">
  <desc>
    Property value increased from $350,000 in 2019 to $485,000 in 2024
  </desc>
  {/* Chart elements */}
</LineChart>
```

### 9.3 Color-Blind Friendly Palette

```css
/* Distinct colors for data visualization */
--chart-1: #0ABAB5; /* Teal */
--chart-2: #D4AF37; /* Gold */
--chart-3: #3B82F6; /* Blue */
--chart-4: #8B5CF6; /* Purple */
--chart-5: #EC4899; /* Pink */
--chart-6: #F59E0B; /* Amber */
```

---

## 10. Container Queries

### 10.1 Responsive Components

```css
/* Card that adapts to container, not viewport */
.property-card {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .property-card__content {
    display: grid;
    grid-template-columns: 1fr 2fr;
  }
}

@container (min-width: 600px) {
  .property-card__content {
    grid-template-columns: 1fr 2fr 1fr;
  }
}
```

### 10.2 Use Cases

- Property cards in different layouts
- Dashboard widgets
- Sidebar components
- Table cells with dynamic content

---

## 11. Storybook Documentation

### 11.1 Structure

```
stories/
├── foundations/
│   ├── Colors.stories.tsx
│   ├── Typography.stories.tsx
│   ├── Spacing.stories.tsx
│   └── Icons.stories.tsx
├── components/
│   ├── Button.stories.tsx
│   ├── Card.stories.tsx
│   ├── Input.stories.tsx
│   └── ...
├── patterns/
│   ├── Forms.stories.tsx
│   ├── DataDisplay.stories.tsx
│   └── Navigation.stories.tsx
└── pages/
    ├── PropertySearch.stories.tsx
    └── PropertyDetail.stories.tsx
```

### 11.2 Story Template

```tsx
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '@/components/ui/button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    docs: {
      description: {
        component: 'Primary action button with multiple variants.',
      },
    },
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline', 'ghost', 'danger'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
    disabled: { control: 'boolean' },
    loading: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    children: 'Search Properties',
    variant: 'primary',
  },
};

export const Loading: Story = {
  args: {
    children: 'Loading...',
    loading: true,
  },
};

export const AllStates: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <Button>Default</Button>
      <Button disabled>Disabled</Button>
      <Button loading>Loading</Button>
    </div>
  ),
};
```

---

## 12. Visual Regression Testing

### 12.1 Tools

- **Chromatic**: Visual diff testing with Storybook
- **Percy**: Cross-browser visual testing
- **Playwright**: E2E visual comparisons

### 12.2 Critical Paths

| Page | Critical Elements |
|------|------------------|
| Property Search | Filter panel, results grid, pagination |
| Property Detail | Tabs, charts, map, action buttons |
| Dashboard | Widgets, metrics cards, charts |
| Login | Form fields, error states |

### 12.3 CI Integration

```yaml
# .github/workflows/visual-tests.yml
visual-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Install dependencies
      run: npm ci
    - name: Build Storybook
      run: npm run build-storybook
    - name: Run Chromatic
      uses: chromaui/action@v1
      with:
        projectToken: ${{ secrets.CHROMATIC_TOKEN }}
```

---

## 13. UX Observability

### 13.1 Metrics to Track

| Metric | Tool | Target |
|--------|------|--------|
| Page load time | Web Vitals | <3s |
| Time to interactive | Lighthouse | <4s |
| Error rate | Sentry | <1% |
| Rage clicks | PostHog | <5 per session |
| Form abandonment | Analytics | <20% |

### 13.2 Event Tracking

```tsx
// Track user interactions
const trackPropertyView = (propertyId: string) => {
  analytics.track('Property Viewed', {
    propertyId,
    source: 'search_results',
    timestamp: Date.now(),
  });
};

// Track errors
const trackError = (error: Error, context: object) => {
  Sentry.captureException(error, { extra: context });
};
```

---

## 14. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Define design tokens in Tailwind config
- [ ] Create CSS custom properties file
- [ ] Set up Storybook
- [ ] Document color, typography, spacing systems

### Phase 2: Core Components (Week 3-4)
- [ ] Refactor Button, Input, Select, Card
- [ ] Add all required states
- [ ] Implement accessibility features
- [ ] Create Storybook stories

### Phase 3: Property Components (Week 5-6)
- [ ] Refactor MiniPropertyCard
- [ ] Refactor PropertyMap
- [ ] Create PropertyChart component
- [ ] Add state components (Empty, Error, Loading)

### Phase 4: Forms & Search (Week 7-8)
- [ ] Implement command palette
- [ ] Refactor all form components
- [ ] Add validation system
- [ ] Create address autocomplete

### Phase 5: Performance (Week 9-10)
- [ ] Add virtualization to lists
- [ ] Optimize images
- [ ] Implement code splitting
- [ ] Run Core Web Vitals audit

### Phase 6: Testing & Documentation (Week 11-12)
- [ ] Set up visual regression testing
- [ ] Complete Storybook documentation
- [ ] Add accessibility tests
- [ ] Create component usage guidelines

---

## 15. AI Agent Integration

### 15.1 HuggingFace UI/UX Agents

The following agents are available for design system assistance:

```python
# UI/UX Assistant Agent
from apps.agents.huggingface import get_ui_suggestions

suggestions = get_ui_suggestions(
    component="PropertyCard",
    issue="slow loading times"
)
# Returns: accessibility improvements, performance suggestions, design patterns

# Code Debug Agent
from apps.agents.huggingface import debug_code

fixed_code = debug_code(
    code="...",
    language="typescript"
)
# Returns: fixed code with explanations
```

### 15.2 Agent Capabilities

| Agent | Function | Use Case |
|-------|----------|----------|
| UIUXAssistantAgent | Design suggestions | Component improvements |
| PropertyAnalysisAgent | Data analysis | Property UX optimization |
| CodeDebugAgent | Code fixes | Component debugging |

---

## 16. Design System Page (localhost:3003 Reference)

The ConcordBroker design system page should include:

1. **Tokens Tab**
   - Colors (brand, semantic, neutral)
   - Typography scale
   - Spacing scale
   - Border radius
   - Shadows

2. **Forms Tab**
   - Input variants
   - Select components
   - Validation states
   - Form layouts

3. **States Tab**
   - Loading skeletons
   - Empty states
   - Error states
   - Permission states

4. **Command Palette Tab**
   - Search demo
   - Actions demo
   - Navigation demo

---

## 17. Success Criteria

### Quantitative Metrics

- [ ] 100% WCAG 2.2 AA compliance
- [ ] LCP < 2.5s on 3G
- [ ] INP < 200ms
- [ ] 0 accessibility violations (axe-core)
- [ ] 100% component documentation coverage
- [ ] < 5% visual regression failures

### Qualitative Metrics

- [ ] Consistent look and feel across all pages
- [ ] Intuitive navigation patterns
- [ ] Clear feedback for all user actions
- [ ] Professional, trustworthy appearance

---

## Appendix A: Component Inventory

### Current Components (85+)

**UI Primitives:**
- Button, Input, Select, Label, Textarea
- Card, Badge, Alert, Dialog
- Table, Tabs, Progress, Skeleton
- Toast, Switch, Slider

**Property Components:**
- MiniPropertyCard, PropertyCompleteView
- PropertyMap, PropertyCharts
- PropertyTypeFields, PropertyUseDisplay
- VirtualizedPropertyList

**Dashboard Components:**
- ComprehensiveDashboard
- CachePerformanceDashboard
- RealtimeMonitoringDashboard

**AI Components:**
- AIChatbox, AISearchBar
- AIPropertyCard, AISearchEnhanced

---

## Appendix B: Design Token Files

### Files to Create

```
apps/web/src/styles/
├── tokens/
│   ├── colors.css
│   ├── typography.css
│   ├── spacing.css
│   ├── shadows.css
│   └── index.css
├── components/
│   ├── button.css
│   ├── card.css
│   └── ...
└── patterns/
    ├── states.css
    ├── animations.css
    └── layouts.css
```

---

*Document Version: 1.0*
*Created: December 13, 2025*
*Last Updated: December 13, 2025*
*Author: Claude Code AI Assistant*
