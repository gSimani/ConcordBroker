/**
 * BEM (Block Element Modifier) methodology utilities for consistent CSS class naming
 *
 * @example
 * // Basic usage
 * const bem = createBem('button');
 * bem() // 'button'
 * bem('text') // 'button__text'
 * bem('text', 'large') // 'button__text--large'
 * bem(null, 'primary') // 'button--primary'
 *
 * // With Tailwind integration
 * const className = bemWithTailwind('button__text--large', 'text-white bg-blue-500');
 */

export type BemBlock = string;
export type BemElement = string | null;
export type BemModifier = string | string[] | Record<string, boolean> | null;

/**
 * Creates a BEM class name string
 */
export function bem(block: BemBlock, element?: BemElement, modifier?: BemModifier): string {
  let className = block;

  // Add element
  if (element) {
    className += `__${element}`;
  }

  // Add modifiers
  if (modifier) {
    if (typeof modifier === 'string') {
      className += `--${modifier}`;
    } else if (Array.isArray(modifier)) {
      modifier.forEach(mod => {
        if (mod) className += `--${mod}`;
      });
    } else if (typeof modifier === 'object') {
      Object.entries(modifier).forEach(([mod, condition]) => {
        if (condition) className += `--${mod}`;
      });
    }
  }

  return className;
}

/**
 * Creates a BEM class name generator for a specific block
 */
export function createBem(block: BemBlock) {
  return (element?: BemElement, modifier?: BemModifier): string => {
    return bem(block, element, modifier);
  };
}

/**
 * Combines BEM classes with Tailwind utility classes
 */
export function bemWithTailwind(bemClasses: string, tailwindClasses?: string): string {
  const classes = [bemClasses];

  if (tailwindClasses) {
    classes.push(tailwindClasses);
  }

  return classes.filter(Boolean).join(' ');
}

/**
 * Creates a comprehensive BEM utility with Tailwind integration
 */
export function createBemWithTailwind(block: BemBlock) {
  const bemGenerator = createBem(block);

  return {
    /**
     * Generate BEM class name
     */
    bem: bemGenerator,

    /**
     * Generate BEM class name with Tailwind classes
     */
    cn: (element?: BemElement, modifier?: BemModifier, tailwindClasses?: string): string => {
      const bemClass = bemGenerator(element, modifier);
      return bemWithTailwind(bemClass, tailwindClasses);
    },

    /**
     * Get block class name
     */
    block: (modifier?: BemModifier, tailwindClasses?: string): string => {
      const bemClass = bemGenerator(null, modifier);
      return bemWithTailwind(bemClass, tailwindClasses);
    },

    /**
     * Get element class name
     */
    element: (element: string, modifier?: BemModifier, tailwindClasses?: string): string => {
      const bemClass = bemGenerator(element, modifier);
      return bemWithTailwind(bemClass, tailwindClasses);
    }
  };
}

/**
 * Utility for conditional BEM classes similar to clsx/classnames
 */
export function bemClassNames(
  block: BemBlock,
  conditions: Record<string, boolean | undefined>,
  tailwindClasses?: string
): string {
  const classes = [block];

  Object.entries(conditions).forEach(([className, condition]) => {
    if (condition) {
      // Check if it's a BEM modifier (contains --)
      if (className.includes('--')) {
        classes.push(className);
      } else {
        // Treat as element or modifier
        if (className.includes('__')) {
          classes.push(className);
        } else {
          classes.push(`${block}--${className}`);
        }
      }
    }
  });

  if (tailwindClasses) {
    classes.push(tailwindClasses);
  }

  return classes.join(' ');
}

/**
 * TypeScript interfaces for BEM patterns
 */
export interface BemConfig {
  block: string;
  elements?: Record<string, string>;
  modifiers?: Record<string, string>;
}

/**
 * Create a type-safe BEM configuration
 */
export function createTypedBem<T extends BemConfig>(config: T) {
  const { block, elements = {}, modifiers = {} } = config;

  return {
    block: (modifier?: keyof T['modifiers'], tailwindClasses?: string) => {
      const bemClass = modifier ? `${block}--${modifiers[modifier as string]}` : block;
      return bemWithTailwind(bemClass, tailwindClasses);
    },

    element: <E extends keyof T['elements']>(
      element: E,
      modifier?: keyof T['modifiers'],
      tailwindClasses?: string
    ) => {
      const elementName = elements[element as string];
      const bemClass = modifier
        ? `${block}__${elementName}--${modifiers[modifier as string]}`
        : `${block}__${elementName}`;
      return bemWithTailwind(bemClass, tailwindClasses);
    }
  };
}

/**
 * Common BEM patterns for the ConcordBroker application
 */
export const ConcordBemPatterns = {
  // Property card patterns
  propertyCard: createBemWithTailwind('property-card'),

  // Search form patterns
  searchForm: createBemWithTailwind('search-form'),

  // Layout patterns
  layout: createBemWithTailwind('layout'),
  header: createBemWithTailwind('header'),
  sidebar: createBemWithTailwind('sidebar'),
  main: createBemWithTailwind('main'),

  // Button patterns
  button: createBemWithTailwind('btn'),

  // Form patterns
  formField: createBemWithTailwind('form-field'),
  input: createBemWithTailwind('input'),

  // Navigation patterns
  nav: createBemWithTailwind('nav'),

  // Modal patterns
  modal: createBemWithTailwind('modal'),
} as const;

/**
 * Helper to validate BEM naming conventions
 */
export function validateBemNaming(className: string): {
  isValid: boolean;
  errors: string[];
  parts: {
    block?: string;
    element?: string;
    modifiers?: string[];
  };
} {
  const errors: string[] = [];
  const parts: { block?: string; element?: string; modifiers?: string[] } = {};

  // Check for valid BEM structure
  const bemRegex = /^[a-z]([a-z0-9-]*[a-z0-9])?(__[a-z]([a-z0-9-]*[a-z0-9])?)?(--[a-z]([a-z0-9-]*[a-z0-9])?)*$/;

  if (!bemRegex.test(className)) {
    errors.push('Invalid BEM naming convention');
    return { isValid: false, errors, parts };
  }

  // Parse the parts
  const [blockAndElement, ...modifierParts] = className.split('--');
  const [block, element] = blockAndElement.split('__');

  parts.block = block;
  if (element) parts.element = element;
  if (modifierParts.length > 0) parts.modifiers = modifierParts;

  // Validate block name
  if (!block || block.length < 2) {
    errors.push('Block name must be at least 2 characters');
  }

  // Validate element name
  if (element && element.length < 2) {
    errors.push('Element name must be at least 2 characters');
  }

  // Validate modifier names
  if (modifierParts.some(mod => mod.length < 2)) {
    errors.push('Modifier names must be at least 2 characters');
  }

  return {
    isValid: errors.length === 0,
    errors,
    parts
  };
}