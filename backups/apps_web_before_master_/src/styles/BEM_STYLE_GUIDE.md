# BEM Style Guide for ConcordBroker

## Overview

This document outlines the BEM (Block Element Modifier) methodology implementation for the ConcordBroker application. BEM provides a structured approach to CSS naming that improves maintainability, reusability, and team collaboration.

## BEM Methodology

### Basic Structure

```
block__element--modifier
```

- **Block**: The standalone entity that is meaningful on its own
- **Element**: A part of a block that has no standalone meaning
- **Modifier**: A flag on a block or element that changes appearance or behavior

### Naming Rules

1. **Use lowercase letters and hyphens only**
2. **Separate words with hyphens (`-`)**
3. **Separate elements with double underscores (`__`)**
4. **Separate modifiers with double hyphens (`--`)**

## ConcordBroker BEM Implementation

### 1. Block Naming Conventions

Blocks represent major UI components:

```css
/* ✅ Good */
.property-card { }
.search-form { }
.navigation-menu { }
.modal-dialog { }

/* ❌ Bad */
.PropertyCard { }
.search_form { }
.navigationMenu { }
```

### 2. Element Naming

Elements are parts of blocks that cannot exist independently:

```css
/* Property Card Elements */
.property-card__header { }
.property-card__title { }
.property-card__address { }
.property-card__metrics { }
.property-card__actions { }

/* Search Form Elements */
.search-form__input { }
.search-form__button { }
.search-form__filters { }
.search-form__results { }
```

### 3. Modifier Naming

Modifiers change the appearance or behavior of blocks or elements:

```css
/* Block Modifiers */
.property-card--featured { }
.property-card--selected { }
.property-card--loading { }

/* Element Modifiers */
.property-card__title--large { }
.property-card__address--highlighted { }
.search-form__input--error { }
```

## TypeScript Integration

### Using the BEM Utilities

```typescript
import { createBemWithTailwind, ConcordBemPatterns } from '@/utils/bemClassNames';

// Method 1: Using pre-configured patterns
const propertyCard = ConcordBemPatterns.propertyCard;

// Generate classes
const cardClass = propertyCard.block('featured', 'bg-white shadow-lg');
// Result: "property-card--featured bg-white shadow-lg"

const titleClass = propertyCard.element('title', 'large', 'text-xl font-bold');
// Result: "property-card__title--large text-xl font-bold"

// Method 2: Creating custom BEM generators
const searchBem = createBemWithTailwind('search-form');

const formClass = searchBem.block('expanded', 'p-6 rounded-lg');
// Result: "search-form--expanded p-6 rounded-lg"
```

### Component Implementation Example

```typescript
import React from 'react';
import { ConcordBemPatterns } from '@/utils/bemClassNames';
import styles from '@/styles/components/property-card.module.css';

interface PropertyCardProps {
  featured?: boolean;
  selected?: boolean;
  variant?: 'grid' | 'list';
}

export function PropertyCard({ featured, selected, variant = 'grid' }: PropertyCardProps) {
  const bem = ConcordBemPatterns.propertyCard;

  return (
    <div className={bem.block({
      featured,
      selected,
      [variant]: true
    }, 'cursor-pointer transition-all')}>

      <div className={bem.element('header')}>
        <h3 className={bem.element('title', 'large', 'text-xl font-semibold')}>
          Property Title
        </h3>
      </div>

      <div className={bem.element('content')}>
        <div className={bem.element('address')}>
          123 Main Street
        </div>

        <div className={bem.element('metrics')}>
          <span className={bem.element('metric-value', 'primary', 'text-gold')}>
            $450,000
          </span>
        </div>
      </div>

      <div className={bem.element('actions')}>
        <button className={bem.element('action-button', 'primary', 'btn-primary')}>
          View Details
        </button>
      </div>
    </div>
  );
}
```

## CSS Module Integration

### File Structure

```
src/styles/components/
├── property-card.module.css
├── search-form.module.css
├── layout.module.css
└── navigation.module.css
```

### Using CSS Modules with BEM

```typescript
import React from 'react';
import styles from '@/styles/components/property-card.module.css';
import { ConcordBemPatterns } from '@/utils/bemClassNames';

export function PropertyCard({ featured, loading }: PropertyCardProps) {
  const bem = ConcordBemPatterns.propertyCard;

  // Combine CSS modules with BEM utilities and Tailwind
  const cardClass = [
    styles['property-card'],
    featured && styles['property-card--featured'],
    loading && styles['property-card--loading'],
    'hover:shadow-lg transition-shadow' // Tailwind utilities
  ].filter(Boolean).join(' ');

  // Or use the BEM utility for Tailwind integration
  const titleClass = bem.element('title', null, 'text-lg font-semibold');

  return (
    <div className={cardClass}>
      <h3 className={titleClass}>Property Title</h3>
    </div>
  );
}
```

## Component Categories

### 1. Layout Components

```css
/* Main layout blocks */
.layout { }
.header { }
.sidebar { }
.main { }
.footer { }

/* Layout elements */
.header__logo { }
.header__navigation { }
.sidebar__menu { }
.main__content { }

/* Layout modifiers */
.layout--fullscreen { }
.header--sticky { }
.sidebar--collapsed { }
```

### 2. Property Components

```css
/* Property-related blocks */
.property-card { }
.property-list { }
.property-detail { }
.property-map { }

/* Property elements */
.property-card__image { }
.property-card__title { }
.property-card__address { }
.property-card__price { }
.property-card__metrics { }

/* Property modifiers */
.property-card--featured { }
.property-card--sold { }
.property-list--grid { }
.property-list--table { }
```

### 3. Form Components

```css
/* Form blocks */
.search-form { }
.filter-form { }
.contact-form { }

/* Form elements */
.search-form__input { }
.search-form__button { }
.search-form__filters { }
.filter-form__checkbox { }

/* Form modifiers */
.search-form--expanded { }
.search-form__input--error { }
.filter-form--compact { }
```

## Migration Patterns

### From Tailwind-only to BEM + Tailwind

```typescript
// Before: Pure Tailwind
<div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
  <h3 className="text-xl font-bold text-gray-900 mb-2">Title</h3>
  <p className="text-gray-600">Content</p>
</div>

// After: BEM + Tailwind
<div className={bem.block(null, 'bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow')}>
  <h3 className={bem.element('title', null, 'text-xl font-bold text-gray-900 mb-2')}>
    Title
  </h3>
  <p className={bem.element('content', null, 'text-gray-600')}>
    Content
  </p>
</div>
```

### From CSS-in-JS to BEM CSS Modules

```typescript
// Before: Styled components or CSS-in-JS
const StyledCard = styled.div`
  background: white;
  border-radius: 8px;
  padding: 24px;

  &.featured {
    border: 2px solid gold;
  }
`;

// After: BEM CSS Modules
// In property-card.module.css
.property-card {
  @apply bg-white rounded-lg p-6;
}

.property-card--featured {
  @apply border-2 border-yellow-400;
}

// In component
<div className={`${styles['property-card']} ${featured ? styles['property-card--featured'] : ''}`}>
```

## Best Practices

### 1. Consistent Naming

```css
/* ✅ Good - Consistent naming pattern */
.property-card { }
.property-card__title { }
.property-card__address { }
.property-card--featured { }

/* ❌ Bad - Inconsistent naming */
.propertyCard { }
.property-card__propertyTitle { }
.property-card-address { }
.featured-property-card { }
```

### 2. Avoid Deep Nesting

```css
/* ✅ Good - Flat structure */
.property-card { }
.property-card__header { }
.property-card__title { }
.property-card__subtitle { }

/* ❌ Bad - Deep nesting */
.property-card { }
.property-card__header { }
.property-card__header__title { }
.property-card__header__title__text { }
```

### 3. Meaningful Modifiers

```css
/* ✅ Good - Descriptive modifiers */
.button--primary { }
.button--disabled { }
.card--featured { }
.form--loading { }

/* ❌ Bad - Abstract modifiers */
.button--blue { }
.button--big { }
.card--special { }
.form--state1 { }
```

### 4. Combining with Tailwind

```typescript
// ✅ Good - BEM for component structure, Tailwind for utilities
const className = bem.element('title', 'large', 'text-xl font-bold text-gray-900');

// ✅ Good - Responsive and state utilities with Tailwind
const className = bem.block('loading', 'opacity-50 pointer-events-none md:flex');

// ❌ Avoid - Mixing layout concerns
const className = bem.block(null, 'property-card-custom-layout-specific-style');
```

## Validation and Tools

### ESLint Rules

Add to your ESLint configuration:

```json
{
  "rules": {
    "selector-class-pattern": "^[a-z]([a-z0-9-]+)?(__([a-z]([a-z0-9-]+)?)+)?(--([a-z]([a-z0-9-]+)?)+)?$"
  }
}
```

### Validation Helper

```typescript
import { validateBemNaming } from '@/utils/bemClassNames';

// Validate BEM class names
const validation = validateBemNaming('property-card__title--large');
console.log(validation.isValid); // true
console.log(validation.parts); // { block: 'property-card', element: 'title', modifiers: ['large'] }
```

## Resources

- [BEM Official Documentation](http://getbem.com/)
- [BEM 101 Guide](https://css-tricks.com/bem-101/)
- [ConcordBroker Component Library](./components/)

## Questions & Support

For questions about implementing BEM in ConcordBroker components, please refer to the team documentation or create an issue in the project repository.