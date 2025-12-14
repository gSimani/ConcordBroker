# ConcordBroker UX/UI Comprehensive Redesign Plan

## Executive Summary

This document outlines a complete UX/UI redesign for ConcordBroker, a Florida property analytics platform. The redesign maintains all existing data while dramatically improving how that data is presented, discovered, and interacted with.

**Design Philosophy**: Clean, professional, data-dense but not cluttered. Inspired by modern fintech dashboards (Bloomberg Terminal meets Robinhood simplicity).

---

## Part 1: Current State Analysis

### What We Have (14 Routes, 84+ Components)

| Page | Data Displayed | Current Issues |
|------|---------------|----------------|
| Home | Marketing content, features, testimonials | Generic, doesn't showcase platform value |
| Dashboard | Stats, quick actions, tabbed data | Limited insights, basic visualizations |
| Property Search | 15+ filters, grid/list/map views | 2,819-line monolith, overwhelming UI |
| Property Detail | 14 tabs of comprehensive data | Tab overload, poor mobile experience |
| Tax Deed Sales | Opportunities, contacts, tracking | Functional but basic |
| Analytics | Stub page | Not implemented |
| Entity | Stub page | Not implemented |

### Key Pain Points Identified

1. **Information Overload**: Too many tabs, filters, and options
2. **No Progressive Disclosure**: All complexity shown at once
3. **Weak Data Visualization**: Numbers without context or trends
4. **Inconsistent Navigation**: Multiple routes to same content
5. **Mobile Experience**: Desktop-first, cramped on mobile
6. **No Personalization**: Same view for all users regardless of intent

---

## Part 2: Redesign Vision

### Design Principles

1. **Progressive Disclosure** - Show summary first, details on demand
2. **Context Over Data** - Numbers with meaning (trends, comparisons)
3. **Action-Oriented** - Every screen has a clear primary action
4. **Mobile-First** - Design for mobile, scale up to desktop
5. **Personalized** - Adapt to user behavior and preferences
6. **Speed** - Sub-200ms interactions, instant feedback

### Visual Identity (Based on Ilora Design System)

```
Primary Brand: Tiffany (#0ABAB5) - Trust, clarity, professional
Accent: Gold (#D4AF37) - Premium, value, success
Background: Clean whites and subtle grays
Typography: Inter - Modern, highly readable
Shadows: Subtle, layered for depth
Animations: Smooth 200ms transitions, purposeful motion
```

---

## Part 3: New Information Architecture

### Simplified Navigation Structure

```
┌─────────────────────────────────────────────────────────────┐
│  CONCORDBROKER                          🔍 ⌘K    👤 Profile │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ 🏠 Home │ │📊 Explore│ │💼 Portfolio│ │📈 Insights│       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Route Consolidation

| Old Routes | New Route | Purpose |
|------------|-----------|---------|
| `/`, `/dashboard` | `/` | Unified home/dashboard |
| `/search`, `/properties`, `/ai-search`, `/properties/fast` | `/explore` | Single search experience |
| `/property/:folio`, `/properties/:slug`, `/properties/:city/:address` | `/property/:id` | Single property route |
| `/tax-deed-sales` | `/opportunities` | Investment opportunities |
| `/analytics` (stub) | `/insights` | Market intelligence |
| `/entity/:id` | `/entity/:id` | Keep as-is |

### New Navigation Items

1. **Home** (`/`) - Personalized dashboard
2. **Explore** (`/explore`) - Property search & discovery
3. **Portfolio** (`/portfolio`) - Saved properties & watchlists
4. **Opportunities** (`/opportunities`) - Tax deeds, foreclosures, deals
5. **Insights** (`/insights`) - Analytics & market trends
6. **Settings** (`/settings`) - Preferences & account

---

## Part 4: Page-by-Page Redesign

### 4.1 Home / Dashboard (Unified)

**Current**: Generic marketing OR basic stats dashboard
**New**: Personalized command center

```
┌─────────────────────────────────────────────────────────────────┐
│  Good morning, John                               Dec 14, 2025  │
│  Here's what's happening in your market                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ 📊 MARKET PULSE │  │ 🔥 HOT LEADS    │  │ 📈 YOUR PORTFOLIO│ │
│  │                 │  │                 │  │                 │
│  │ Broward County  │  │ 12 New Tax Deed │  │ 8 Properties    │
│  │ ▲ 3.2% this mo  │  │ Sales This Week │  │ $2.4M Total Val │
│  │                 │  │                 │  │ ▲ $42K (30d)    │
│  │ [View Trends]   │  │ [View All →]    │  │ [Manage →]      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔍 QUICK SEARCH                                    ⌘K   │   │
│  │ ┌─────────────────────────────────────────────────────┐ │   │
│  │ │ Search by address, owner, parcel ID...             │ │   │
│  │ └─────────────────────────────────────────────────────┘ │   │
│  │                                                         │   │
│  │ Recent: 123 Ocean Dr • 456 Beach Blvd • SMITH JOHN     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────────────┐    │
│  │ 📋 RECENT ACTIVITY   │  │ 🎯 RECOMMENDED FOR YOU       │    │
│  │                      │  │                              │    │
│  │ • Viewed 123 Ocean   │  │ Based on your search history │    │
│  │ • Saved 456 Beach    │  │                              │    │
│  │ • Exported 12 props  │  │ [Property Card] [Property]   │    │
│  │                      │  │ [Property Card] [Property]   │    │
│  └──────────────────────┘  └──────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Changes**:
- Personalized greeting with context
- Market pulse widget with trend indicators
- Hot leads (tax deed sales, foreclosures) prominently featured
- Quick search with command palette (`⌘K`)
- AI-powered recommendations
- Recent activity for quick access

### 4.2 Explore (Property Search)

**Current**: Complex filter sidebar + results grid
**New**: Progressive filter experience with smart defaults

```
┌─────────────────────────────────────────────────────────────────┐
│  Explore Properties                                    🗺️ 📊 📋 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔍 Find properties in Florida...                    AI ✨│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ │
│  │ County ▼│ │ Type ▼  │ │ Value ▼ │ │ Status ▼│ │ + Filters │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────┘ │
│                                                                 │
│  Showing 1,234 properties                    Sort: Value ▼     │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ ┌──────────────────┐  ┌──────────────────┐             │    │
│  │ │ 📍 123 Ocean Dr  │  │ 📍 456 Beach Blvd│             │    │
│  │ │ Fort Lauderdale  │  │ Hollywood        │             │    │
│  │ │                  │  │                  │             │    │
│  │ │ $485,000         │  │ $325,000         │             │    │
│  │ │ 🏠 Residential   │  │ 🏠 Residential   │             │    │
│  │ │ 1,800 sqft       │  │ 1,500 sqft       │             │    │
│  │ │                  │  │                  │             │    │
│  │ │ ▲ +5.2% YoY      │  │ ▼ -2.1% YoY      │             │    │
│  │ │                  │  │                  │             │    │
│  │ │ [Save] [Compare] │  │ [Save] [Compare] │             │    │
│  │ └──────────────────┘  └──────────────────┘             │    │
│  │                                                        │    │
│  │ ┌──────────────────┐  ┌──────────────────┐             │    │
│  │ │ 📍 789 Palm Ave  │  │ 📍 321 Sunset Rd │             │    │
│  │ │ Miami            │  │ Boca Raton       │             │    │
│  │ │ ...              │  │ ...              │             │    │
│  │ └──────────────────┘  └──────────────────┘             │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [Load More]                                        Page 1 of 52│
└─────────────────────────────────────────────────────────────────┘
```

**Key Changes**:
- AI-enhanced natural language search ("Show me waterfront homes under 500k")
- Smart filter chips (most-used filters inline)
- Progressive filter panel (expands on "+ Filters")
- Property cards with trend indicators (YoY change)
- Quick actions on cards (Save, Compare)
- View toggle (Grid / Map / List) in header
- Infinite scroll with lazy loading

### 4.3 Property Detail Page

**Current**: 14+ tabs with overwhelming amount of data
**New**: Sectioned single-page with collapsible modules

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Search                                    ⭐ 📤 🖨️   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  📍 123 Ocean Drive                                     │   │
│  │  Fort Lauderdale, FL 33301                              │   │
│  │                                                         │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│  │  │$485,000 │  │ 1,800   │  │  1985   │  │ 0.25 ac │    │   │
│  │  │Just Val │  │ Sq Ft   │  │ Year    │  │ Lot Size│    │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│  │                                                         │   │
│  │  Parcel: 484330110110  •  Residential Single Family     │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📊 VALUATION                                        [−] │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  Just Value     $485,000    ▲ +12.5% from 2023         │   │
│  │  Land Value     $125,000                                │   │
│  │  Building Val   $360,000                                │   │
│  │                                                         │   │
│  │  [Mini Chart: 5-Year Value History]                     │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 👤 OWNERSHIP                                        [−] │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  SMITH JOHN & MARY                                      │   │
│  │  456 Main Street, Miami, FL 33139                       │   │
│  │                                                         │   │
│  │  [View Owner's Other Properties (3)]                    │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 💰 SALES HISTORY                                    [−] │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  Date        Price       Type        Change             │   │
│  │  ─────────────────────────────────────────────         │   │
│  │  2021-03     $420,000    Warranty    —                  │   │
│  │  2015-06     $310,000    Warranty    +35.5%             │   │
│  │  2008-01     $275,000    Warranty    +12.7%             │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🏛️ TAX INFORMATION                                  [+] │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🏢 BUILDING DETAILS                                 [+] │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📋 PERMITS                                          [+] │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🏦 SUNBIZ / ENTITY INFO                             [+] │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Changes**:
- Hero section with key metrics at a glance
- Collapsible sections replace tabs
- Most important sections expanded by default
- Less important sections collapsed (click to expand)
- Inline visualizations (sparklines, mini-charts)
- Sticky header with property address
- Quick actions (Save, Share, Print) in header

### 4.4 Opportunities (Tax Deed Sales)

**Current**: Basic list with contact management
**New**: Deal pipeline with investment analysis

```
┌─────────────────────────────────────────────────────────────────┐
│  Investment Opportunities                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ 🔥 42   │ │ 📅 18   │ │ 💰 $2.1M│ │ 📈 8.2% │               │
│  │ Active  │ │ This Wk │ │ Pot Val │ │ Avg ROI │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
│                                                                 │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                     │
│  │Tax Deeds │ │Foreclosures│ │ Pre-Forec │                     │
│  │    (42)   │ │    (15)    │ │   (28)    │                     │
│  └───────────┘ └───────────┘ └───────────┘                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │ 🏠 123 Ocean Dr, Fort Lauderdale                │   │   │
│  │  │                                                 │   │   │
│  │  │ Tax Deed Sale: Jan 15, 2025                     │   │   │
│  │  │ Opening Bid: $45,000                            │   │   │
│  │  │ Est. Market Value: $485,000                     │   │   │
│  │  │                                                 │   │   │
│  │  │ ┌────────────────────────────────────────────┐  │   │   │
│  │  │ │ Potential ROI: 978%  ████████████████████  │  │   │   │
│  │  │ └────────────────────────────────────────────┘  │   │   │
│  │  │                                                 │   │   │
│  │  │ [View Details] [Add to Watchlist] [Analyze]     │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │ 🏢 456 Commerce Blvd, Miami                     │   │   │
│  │  │ ...                                             │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Changes**:
- Investment-focused metrics (ROI, potential value)
- Category tabs (Tax Deeds, Foreclosures, Pre-Foreclosures)
- Visual ROI indicator bars
- Auction countdown timers
- Watchlist integration
- Investment analysis tool integration

### 4.5 Insights (Analytics - New)

**Current**: Stub page
**New**: Full market intelligence dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  Market Insights                                    📅 Last 30d │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ MARKET OVERVIEW                                         │   │
│  │                                                         │   │
│  │  [Full-width Area Chart: Property Values Over Time]     │   │
│  │                                                         │   │
│  │  ▲ +3.2% avg value increase  •  12,450 sales this month │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │ TOP PERFORMING     │  │ SALES VOLUME       │                │
│  │ COUNTIES           │  │ BY PROPERTY TYPE   │                │
│  │                    │  │                    │                │
│  │ 1. Miami-Dade ▲5.1%│  │ [Donut Chart]      │                │
│  │ 2. Broward    ▲4.2%│  │ Residential: 68%   │                │
│  │ 3. Palm Beach ▲3.8%│  │ Commercial: 22%    │                │
│  │ 4. Orange     ▲3.1%│  │ Industrial: 7%     │                │
│  │ 5. Hillsborough▲2.9│  │ Other: 3%          │                │
│  └────────────────────┘  └────────────────────┘                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ PRICE DISTRIBUTION                                      │   │
│  │                                                         │   │
│  │  [Histogram: Property Values Distribution]              │   │
│  │                                                         │   │
│  │  Median: $385,000  •  Avg: $452,000  •  Mode: $300-350k │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ AI INSIGHTS                                         ✨   │   │
│  │                                                         │   │
│  │ "Broward County showing strong buyer activity in the    │   │
│  │  $300-500k range. Tax deed opportunities up 23% MoM."   │   │
│  │                                                         │   │
│  │ [Generate Custom Report]                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 5: Component Redesign Specifications

### 5.1 Property Card (New Design)

```tsx
// New PropertyCard component structure
<PropertyCard>
  <PropertyCard.Image /> {/* Optional street view */}
  <PropertyCard.Header>
    <PropertyCard.Address />
    <PropertyCard.Badge /> {/* Tax Deed, Foreclosure, etc. */}
  </PropertyCard.Header>
  <PropertyCard.Metrics>
    <Metric label="Value" value="$485,000" trend="+5.2%" />
    <Metric label="Size" value="1,800 sqft" />
    <Metric label="Type" value="Residential" icon={Home} />
  </PropertyCard.Metrics>
  <PropertyCard.Actions>
    <Button variant="ghost" icon={Heart} />
    <Button variant="ghost" icon={Compare} />
    <Button variant="primary">View</Button>
  </PropertyCard.Actions>
</PropertyCard>
```

### 5.2 Search Component (New Design)

```tsx
// AI-Enhanced Search
<SearchCommand>
  <SearchCommand.Input placeholder="Search properties..." />
  <SearchCommand.AIToggle /> {/* Toggle natural language mode */}
  <SearchCommand.Results>
    <SearchCommand.Group heading="Properties">
      <SearchCommand.Item />
    </SearchCommand.Group>
    <SearchCommand.Group heading="Owners">
      <SearchCommand.Item />
    </SearchCommand.Group>
    <SearchCommand.Group heading="Recent">
      <SearchCommand.Item />
    </SearchCommand.Group>
  </SearchCommand.Results>
</SearchCommand>
```

### 5.3 Metric Card (New Design)

```tsx
// Contextual Metric Display
<MetricCard>
  <MetricCard.Icon icon={DollarSign} />
  <MetricCard.Value>$485,000</MetricCard.Value>
  <MetricCard.Label>Just Value</MetricCard.Label>
  <MetricCard.Trend direction="up" value="12.5%" />
  <MetricCard.Sparkline data={[...]} />
</MetricCard>
```

### 5.4 Collapsible Section (New Component)

```tsx
// For Property Detail page
<CollapsibleSection
  title="Valuation"
  icon={DollarSign}
  defaultOpen={true}
  badge="Updated 2024"
>
  {/* Section content */}
</CollapsibleSection>
```

---

## Part 6: Mobile-First Responsive Design

### Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Single column, bottom nav |
| Tablet | 640-1024px | Two columns, sidebar collapse |
| Desktop | 1024-1440px | Full sidebar, multi-column |
| Wide | > 1440px | Max-width container, extra spacing |

### Mobile Navigation

```
┌─────────────────────────┐
│  ≡  CONCORDBROKER   👤  │
├─────────────────────────┤
│                         │
│   [Mobile Content]      │
│                         │
├─────────────────────────┤
│ 🏠   🔍   💼   📊   ⚙️  │
│ Home Explore Port Insights│
└─────────────────────────┘
```

### Touch Targets

- Minimum 44x44px for all interactive elements
- 8px minimum spacing between touch targets
- Swipe gestures for common actions (save, dismiss)

---

## Part 7: Animation & Micro-interactions

### Page Transitions

```css
/* Smooth page transitions */
.page-enter {
  opacity: 0;
  transform: translateY(10px);
}
.page-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: all 200ms ease-out;
}
```

### Interactive Feedback

| Action | Animation |
|--------|-----------|
| Button hover | Scale 1.02, shadow increase |
| Card hover | Lift (translateY -2px), shadow |
| Save property | Heart fill animation |
| Load data | Skeleton shimmer |
| Success | Green checkmark pulse |
| Error | Red shake animation |

### Loading States

- Skeleton screens for initial load
- Inline spinners for partial updates
- Progress bars for long operations
- Optimistic UI updates where possible

---

## Part 8: Accessibility Improvements

### WCAG 2.2 AA Compliance

1. **Color Contrast**: All text meets 4.5:1 ratio
2. **Focus Indicators**: Visible focus rings on all interactive elements
3. **Keyboard Navigation**: Full keyboard support, logical tab order
4. **Screen Readers**: Proper ARIA labels, live regions for updates
5. **Motion**: Respects `prefers-reduced-motion`
6. **Touch**: Adequate spacing for motor impairments

### Specific Improvements

```tsx
// Example: Accessible Property Card
<article aria-label="Property at 123 Ocean Drive">
  <h3>123 Ocean Drive</h3>
  <p>Value: <span aria-label="Four hundred eighty-five thousand dollars">$485,000</span></p>
  <p>
    Trend:
    <span aria-label="Increased by 5.2 percent" className="text-success">
      ▲ +5.2%
    </span>
  </p>
  <button aria-label="Save property to favorites">
    <HeartIcon aria-hidden="true" />
  </button>
</article>
```

---

## Part 9: Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| LCP | < 2.5s | Preload critical assets, optimize images |
| FID | < 100ms | Code splitting, defer non-critical JS |
| INP | < 200ms | Debounce inputs, virtualize lists |
| CLS | < 0.1 | Reserved space for dynamic content |
| TTI | < 4s | Progressive hydration, lazy loading |

### Optimization Strategies

1. **Code Splitting**: Route-based lazy loading (already implemented)
2. **Image Optimization**: WebP format, responsive sizes, lazy load
3. **List Virtualization**: Only render visible items
4. **Data Caching**: React Query with smart invalidation
5. **Prefetching**: Preload likely next pages on hover

---

## Part 10: Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up new design tokens
- [ ] Create base components (MetricCard, PropertyCard, CollapsibleSection)
- [ ] Implement new navigation structure
- [ ] Set up route consolidation

### Phase 2: Core Pages (Week 3-4)
- [ ] Redesign Home/Dashboard
- [ ] Redesign Explore (Property Search)
- [ ] Redesign Property Detail page
- [ ] Mobile responsive layouts

### Phase 3: Features (Week 5-6)
- [ ] Implement Opportunities page
- [ ] Implement Insights page
- [ ] Add AI search integration
- [ ] Command palette (`⌘K`)

### Phase 4: Polish (Week 7-8)
- [ ] Animations and transitions
- [ ] Accessibility audit and fixes
- [ ] Performance optimization
- [ ] Visual regression testing

### Phase 5: Launch (Week 9)
- [ ] User testing
- [ ] Bug fixes
- [ ] Documentation
- [ ] Deployment

---

## Part 11: Data Preservation Matrix

| Current Data | New Location | Presentation Change |
|--------------|--------------|---------------------|
| Property address | PropertyCard header, Detail hero | Larger, more prominent |
| Just Value | MetricCard with trend | Add YoY comparison |
| Owner name | Ownership section | Link to owner's other properties |
| Sales history | Collapsible section | Add price change indicators |
| Tax info | Collapsible section | Add delinquency alerts |
| Building details | Collapsible section | Visual sqft comparison |
| Permits | Collapsible section | Timeline view |
| Sunbiz/Entity | Collapsible section | Status badges |
| Parcel ID | Detail hero, copyable | Click to copy |
| Filters | Smart filter chips | Most-used promoted to inline |
| Map view | Toggle in Explore | Keep existing, improve markers |

**No data will be removed. Only presentation changes.**

---

## Appendix A: Nano Banana API Integration

See `apps/agents/nano-banana/` for AI design generation integration.

API Endpoint: Google AI Studio (Gemini)
Purpose: Generate design assets, mockups, and style variations

---

## Appendix B: Design Asset Requirements

### Required from Nano Banana API

1. Hero illustrations for Home page
2. Empty state illustrations
3. Property type icons (modern style)
4. Loading animation assets
5. Success/error state illustrations
6. Onboarding illustrations

---

*Document Version: 1.0*
*Created: December 14, 2025*
*Author: Claude Code AI Assistant*
