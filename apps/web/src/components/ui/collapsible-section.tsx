/**
 * CollapsibleSection Component
 * ============================
 *
 * A reusable collapsible/accordion section component for progressive disclosure.
 * Part of the ConcordBroker UX/UI redesign.
 *
 * Features:
 * - Smooth expand/collapse animation
 * - Accessible with proper ARIA attributes
 * - Customizable header and content
 * - Optional badge/count display
 * - Multiple style variants
 * - Keyboard navigation support
 */

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronRight, LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface CollapsibleSectionProps {
  /** The title displayed in the header */
  title: string;
  /** Optional subtitle or description */
  subtitle?: string;
  /** Optional icon displayed before the title */
  icon?: LucideIcon;
  /** Optional badge content (e.g., count) */
  badge?: string | number;
  /** The content to show when expanded */
  children: React.ReactNode;
  /** Whether the section is initially expanded */
  defaultExpanded?: boolean;
  /** Controlled expanded state (overrides defaultExpanded) */
  expanded?: boolean;
  /** Callback when expanded state changes */
  onExpandedChange?: (expanded: boolean) => void;
  /** Visual variant */
  variant?: 'default' | 'bordered' | 'card' | 'minimal';
  /** Whether to disable the section */
  disabled?: boolean;
  /** Additional class names */
  className?: string;
  /** Header class names */
  headerClassName?: string;
  /** Content class names */
  contentClassName?: string;
}

/**
 * CollapsibleSection component for progressive disclosure UX pattern.
 * Allows content to be shown or hidden with a smooth animation.
 */
export const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  subtitle,
  icon: Icon,
  badge,
  children,
  defaultExpanded = false,
  expanded: controlledExpanded,
  onExpandedChange,
  variant = 'default',
  disabled = false,
  className,
  headerClassName,
  contentClassName,
}) => {
  // Handle controlled vs uncontrolled state
  const [internalExpanded, setInternalExpanded] = useState(defaultExpanded);
  const isControlled = controlledExpanded !== undefined;
  const expanded = isControlled ? controlledExpanded : internalExpanded;

  // Ref for measuring content height for animation
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState<number>(0);

  // Measure content height when children change or expanded state changes
  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, [children, expanded]);

  const toggleExpanded = () => {
    if (disabled) return;

    const newExpanded = !expanded;
    if (!isControlled) {
      setInternalExpanded(newExpanded);
    }
    onExpandedChange?.(newExpanded);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleExpanded();
    }
  };

  // Variant-specific styles
  const variantStyles = {
    default: {
      wrapper: 'border-b border-neutral-200',
      header: 'py-3 px-0',
      content: 'pb-4',
    },
    bordered: {
      wrapper: 'border border-neutral-200 rounded-lg',
      header: 'py-3 px-4',
      content: 'px-4 pb-4',
    },
    card: {
      wrapper: 'bg-white border border-neutral-200 rounded-lg shadow-sm',
      header: 'py-4 px-4',
      content: 'px-4 pb-4',
    },
    minimal: {
      wrapper: '',
      header: 'py-2',
      content: 'pt-2',
    },
  };

  const styles = variantStyles[variant];

  return (
    <div className={cn(styles.wrapper, className)}>
      {/* Header */}
      <button
        type="button"
        onClick={toggleExpanded}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={cn(
          'w-full flex items-center justify-between text-left',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0ABAB5] focus-visible:ring-offset-2 rounded',
          'transition-colors duration-150',
          !disabled && 'hover:bg-neutral-50/50',
          disabled && 'opacity-50 cursor-not-allowed',
          styles.header,
          headerClassName
        )}
        aria-expanded={expanded}
        aria-controls={`collapsible-content-${title.replace(/\s+/g, '-').toLowerCase()}`}
      >
        <div className="flex items-center gap-3 min-w-0">
          {/* Chevron indicator */}
          <span className="flex-shrink-0 text-neutral-400 transition-transform duration-200">
            {expanded ? (
              <ChevronDown size={20} />
            ) : (
              <ChevronRight size={20} />
            )}
          </span>

          {/* Optional icon */}
          {Icon && (
            <Icon
              size={20}
              className={cn(
                'flex-shrink-0',
                expanded ? 'text-[#0ABAB5]' : 'text-neutral-400'
              )}
            />
          )}

          {/* Title and subtitle */}
          <div className="min-w-0 flex-1">
            <span
              className={cn(
                'font-medium text-neutral-900 block truncate',
                variant === 'minimal' ? 'text-sm' : 'text-base'
              )}
            >
              {title}
            </span>
            {subtitle && (
              <span className="text-sm text-neutral-500 block truncate">
                {subtitle}
              </span>
            )}
          </div>
        </div>

        {/* Badge */}
        {badge !== undefined && (
          <span
            className={cn(
              'ml-2 flex-shrink-0 px-2 py-0.5 rounded-full text-xs font-medium',
              'bg-[#0ABAB5]/10 text-[#0ABAB5]'
            )}
          >
            {badge}
          </span>
        )}
      </button>

      {/* Collapsible content */}
      <div
        id={`collapsible-content-${title.replace(/\s+/g, '-').toLowerCase()}`}
        className="overflow-hidden transition-[max-height,opacity] duration-300 ease-in-out"
        style={{
          maxHeight: expanded ? `${contentHeight}px` : '0px',
          opacity: expanded ? 1 : 0,
        }}
        aria-hidden={!expanded}
      >
        <div
          ref={contentRef}
          className={cn(styles.content, contentClassName)}
        >
          {children}
        </div>
      </div>
    </div>
  );
};

/**
 * CollapsibleGroup component for managing multiple collapsible sections.
 * Supports accordion mode where only one section can be expanded at a time.
 */
export interface CollapsibleGroupProps {
  /** The collapsible sections */
  children: React.ReactNode;
  /** Only allow one section open at a time */
  accordion?: boolean;
  /** Default expanded section index (for accordion mode) */
  defaultExpandedIndex?: number;
  /** Additional class names */
  className?: string;
}

export const CollapsibleGroup: React.FC<CollapsibleGroupProps> = ({
  children,
  accordion = false,
  defaultExpandedIndex,
  className,
}) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(
    defaultExpandedIndex ?? null
  );

  if (!accordion) {
    return <div className={cn('space-y-0', className)}>{children}</div>;
  }

  // Clone children and inject controlled props for accordion behavior
  const childrenWithProps = React.Children.map(children, (child, index) => {
    if (!React.isValidElement(child)) return child;

    return React.cloneElement(child as React.ReactElement<CollapsibleSectionProps>, {
      expanded: expandedIndex === index,
      onExpandedChange: (expanded: boolean) => {
        setExpandedIndex(expanded ? index : null);
      },
    });
  });

  return <div className={cn('space-y-0', className)}>{childrenWithProps}</div>;
};

export default CollapsibleSection;
