# ConcordBroker Project Rules and Guidelines

## HTML/JSX Component Rules

### 1. Unique Element IDs Requirement
**CRITICAL:** Every element that displays data or accepts user input in HTML files and JSX/TSX components MUST have a unique ID attribute. This includes:
- All `<div>` elements
- All `<input>`, `<select>`, `<textarea>` form elements
- All `<button>` elements
- All `<span>` and `<p>` elements that display data
- All `<section>`, `<article>`, `<aside>` structural elements
- All custom React components that render data

#### Purpose
- Enables precise element identification for communication with AI assistants
- Facilitates debugging and element tracking
- Improves accessibility and testing capabilities

#### Implementation Guidelines

##### For React/JSX/TSX Components:
```jsx
// ✅ CORRECT - Every div has a unique ID
<div id="main-header-container">
  <div id="nav-menu-wrapper">
    <div id="logo-section">Logo</div>
    <div id="menu-items-list">Menu</div>
  </div>
</div>

// ❌ INCORRECT - Missing IDs
<div>
  <div>
    <div>Logo</div>
    <div>Menu</div>
  </div>
</div>
```

##### For Dynamic Components:
```jsx
// Use component name + index/key for lists
{items.map((item, index) => (
  <div id={`item-card-${item.id || index}`} key={item.id}>
    <div id={`item-title-${item.id || index}`}>{item.title}</div>
    <div id={`item-content-${item.id || index}`}>{item.content}</div>
  </div>
))}
```

##### For HTML Files:
```html
<!-- ✅ CORRECT -->
<div id="page-wrapper">
  <div id="header-section">
    <div id="branding-area">Brand</div>
  </div>
</div>

<!-- ❌ INCORRECT -->
<div>
  <div>
    <div>Brand</div>
  </div>
</div>
```

#### Naming Conventions for IDs

1. **Use descriptive, kebab-case names:**
   - `id="property-search-container"`
   - `id="user-profile-section"`
   - `id="main-navigation-bar"`

2. **Include context in the ID:**
   - `id="dashboard-stats-panel"`
   - `id="property-list-filter-section"`
   - `id="chat-message-container"`

3. **For repeated components, include unique identifiers:**
   - `id="property-card-${propertyId}"`
   - `id="message-bubble-${messageId}"`
   - `id="tab-panel-${tabName}"`

4. **Avoid generic names:**
   - ❌ `id="container"`
   - ❌ `id="wrapper"`
   - ❌ `id="div1"`
   - ✅ `id="search-results-container"`
   - ✅ `id="property-details-wrapper"`

#### Validation Checklist

Before committing code, ensure:
- [ ] All `<div>` elements have an `id` attribute
- [ ] All IDs are unique within the component/page
- [ ] IDs follow the naming convention (kebab-case, descriptive)
- [ ] Dynamic components use proper ID generation with unique keys
- [ ] No duplicate IDs exist across the application

#### Example Component Structure

```tsx
// PropertyCard.tsx
export const PropertyCard: React.FC<{property: Property, index: number}> = ({property, index}) => {
  const cardId = `property-card-${property.id}`;
  
  return (
    <div id={cardId} className="property-card">
      <div id={`${cardId}-header`}>
        <div id={`${cardId}-title`}>{property.title}</div>
        <div id={`${cardId}-price`}>{property.price}</div>
      </div>
      <div id={`${cardId}-body`}>
        <div id={`${cardId}-description`}>{property.description}</div>
        <div id={`${cardId}-features`}>
          {property.features.map((feature, idx) => (
            <div id={`${cardId}-feature-${idx}`} key={idx}>
              {feature}
            </div>
          ))}
        </div>
      </div>
      <div id={`${cardId}-footer`}>
        <div id={`${cardId}-actions`}>
          <button id={`${cardId}-view-btn`}>View</button>
          <button id={`${cardId}-save-btn`}>Save</button>
        </div>
      </div>
    </div>
  );
};
```

### 8. Data Field ID Naming Convention

**MANDATORY:** All elements that display data from Supabase MUST follow this ID pattern:

#### For Static Elements:
```
{page}-{section}-{field}
```
Examples:
- `property-profile-owner-name`
- `dashboard-stats-total-value`
- `search-filter-city`

#### For Dynamic Elements (in lists/maps):
```
{component}-{uniqueId}-{field}
```
Examples:
- `property-card-504232100001-address`
- `sales-entry-1-price`
- `nav-assessment-item-2-amount`

#### For Filter/Input Elements:
```
{page}-filter-{field}-input
```
Examples:
- `properties-filter-city-select`
- `search-filter-owner-input`
- `dashboard-filter-date-range`

#### For Tab Content:
```
{page}-tab-{tabname}-{field}
```
Examples:
- `property-tab-overview-living-area`
- `property-tab-taxes-homestead`
- `property-tab-sales-last-price`

## Additional Rules

### 2. Component Organization
- Keep components small and focused (single responsibility)
- Use TypeScript interfaces for all props
- Document complex logic with comments

### 3. State Management
- Use appropriate state management (local state, context, or global store)
- Avoid prop drilling beyond 2 levels

### 4. Error Handling
- All API calls must have error handling
- Display user-friendly error messages
- Log errors for debugging

### 5. Performance
- Use React.memo for expensive components
- Implement lazy loading for routes
- Optimize images and assets

### 6. Accessibility
- All interactive elements must be keyboard accessible
- Include proper ARIA labels
- Maintain proper heading hierarchy

### 7. Testing
- Write unit tests for utility functions
- Include integration tests for critical paths
- Test accessibility with screen readers

## Enforcement

These rules should be enforced through:
1. Code reviews
2. ESLint rules (where applicable)
3. Pre-commit hooks
4. Regular audits

## Updates

Last Updated: January 2025
Version: 1.0.0

---

**Note for AI Assistants:** When generating or modifying HTML/JSX/TSX code, always ensure every `<div>` element has a unique, descriptive ID following the conventions outlined above. This is critical for maintaining communication and debugging capabilities.