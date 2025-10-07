/**
 * Utility for generating standardized element IDs following naming conventions
 * Pattern: {page}-{section}-{component}-{index}
 */

export type PageName =
  | 'home'
  | 'property-search'
  | 'property-detail'
  | 'dashboard'
  | 'analytics'
  | 'admin'
  | 'entity'
  | 'tax-deed'
  | 'login'
  | 'profile';

export type SectionName =
  | 'header'
  | 'main'
  | 'footer'
  | 'sidebar'
  | 'content'
  | 'filters'
  | 'results'
  | 'form'
  | 'modal'
  | 'hero'
  | 'nav'
  | 'toolbar';

/**
 * Generate a unique element ID following the naming convention
 * @param page - The page or route name
 * @param section - The section within the page
 * @param component - The component or element type
 * @param index - Optional index for repeated elements (default: 1)
 * @returns Formatted element ID string
 */
export function generateElementId(
  page: PageName | string,
  section: SectionName | string,
  component: string,
  index: number = 1
): string {
  // Convert to kebab-case and lowercase
  const pageName = page.toLowerCase().replace(/\s+/g, '-');
  const sectionName = section.toLowerCase().replace(/\s+/g, '-');
  const componentName = component.toLowerCase().replace(/\s+/g, '-');

  return `${pageName}-${sectionName}-${componentName}-${index}`;
}

/**
 * Generate a data-testid attribute value
 * @param component - Component or action name
 * @param action - Action being performed
 * @param target - Optional target of the action
 * @returns Formatted data-testid string
 */
export function generateTestId(
  component: string,
  action: string,
  target?: string
): string {
  const parts = [
    component.toLowerCase().replace(/\s+/g, '-'),
    action.toLowerCase().replace(/\s+/g, '-')
  ];

  if (target) {
    parts.push(target.toLowerCase().replace(/\s+/g, '-'));
  }

  return parts.join('-');
}

/**
 * Generate IDs for a list of elements
 * @param page - The page name
 * @param section - The section name
 * @param component - The component name
 * @param count - Number of IDs to generate
 * @returns Array of formatted element IDs
 */
export function generateElementIdList(
  page: PageName | string,
  section: SectionName | string,
  component: string,
  count: number
): string[] {
  return Array.from({ length: count }, (_, index) =>
    generateElementId(page, section, component, index + 1)
  );
}

/**
 * React hook for generating element IDs with consistent page context
 */
export function useElementId(page: PageName | string) {
  return {
    generateId: (section: SectionName | string, component: string, index = 1) =>
      generateElementId(page, section, component, index),
    generateTestId: (action: string, target?: string) =>
      generateTestId(page, action, target),
    generateIdList: (section: SectionName | string, component: string, count: number) =>
      generateElementIdList(page, section, component, count)
  };
}

// Common ID patterns for reuse
export const CommonIds = {
  searchInput: (page: PageName | string) => generateElementId(page, 'filters', 'search-input', 1),
  submitButton: (page: PageName | string) => generateElementId(page, 'form', 'submit-button', 1),
  resultsContainer: (page: PageName | string) => generateElementId(page, 'results', 'container', 1),
  loadingSpinner: (page: PageName | string) => generateElementId(page, 'content', 'loading-spinner', 1),
  errorMessage: (page: PageName | string) => generateElementId(page, 'content', 'error-message', 1),
} as const;

// Validation function to ensure IDs follow convention
export function validateElementId(id: string): boolean {
  // Pattern: {page}-{section}-{component}-{index}
  const pattern = /^[a-z]+-[a-z]+-[a-z-]+-\d+$/;
  return pattern.test(id);
}