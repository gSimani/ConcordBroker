import React from 'react';
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Lucide React Icons
import {
  ArrowUp,
  ArrowDown,
  LucideIcon,
  Home,
  DollarSign,
  ScrollText,
  TrendingUp,
} from 'lucide-react';

/**
 * A utility function to conditionally join Tailwind CSS classes.
 * It uses `clsx` for conditional class strings and `tailwind-merge`
 * to intelligently merge conflicting Tailwind classes.
 * @param {...ClassValue[]} inputs - Class values to be merged.
 * @returns {string} The merged Tailwind class string.
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Props for the MetricCard component.
 */
interface MetricCardProps {
  /**
   * The label/title for the metric (e.g., "Total Properties").
   */
  label: string;
  /**
   * The main value of the metric (e.g., "9,113,150", "$325,000").
   */
  value: string | number;
  /**
   * The Lucide icon component representing the metric type.
   */
  icon: LucideIcon;
  /**
   * Optional percentage change value. Positive for up, negative for down.
   */
  comparisonValue?: number;
  /**
   * Optional data for a sparkline/mini chart.
   * (Current implementation uses a placeholder div for visual representation)
   */
  sparklineData?: number[];
  /**
   * The size of the card: 'sm', 'md', or 'lg'. Defaults to 'md'.
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * If true, the card will be highlighted with the premium Gold accent color.
   */
  isGold?: boolean;
  /**
   * If true, the card will display a loading skeleton state.
   */
  isLoading?: boolean;
  /**
   * Additional CSS class names to apply to the card wrapper.
   */
  className?: string;
  /**
   * Optional click handler for the card. If provided, the card will be interactive.
   */
  onClick?: () => void;
  /**
   * Aria label for accessibility. Defaults to a generated label based on content.
   */
  ariaLabel?: string;
}

/**
 * A MetricCard component for ConcordBroker's Florida property analytics dashboard.
 * Displays a single metric with a label, value, an icon, and optional comparison data.
 * It supports different sizes, a loading skeleton state, premium highlighting, and hover effects.
 *
 * @param {MetricCardProps} props - The properties for the MetricCard.
 * @returns {JSX.Element} A React component displaying a single metric.
 */
export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon: Icon,
  comparisonValue,
  sparklineData,
  size = 'md',
  isGold = false,
  isLoading = false,
  className,
  onClick,
  ariaLabel,
}) => {
  const isPositive = comparisonValue !== undefined && comparisonValue > 0;
  const isNegative = comparisonValue !== undefined && comparisonValue < 0;

  // Determine trend color based on value
  const trendColorClass = isPositive ? 'text-[#0ABAB5]' : isNegative ? 'text-red-500' : 'text-gray-500';
  // Determine trend icon based on value
  const trendIcon = isPositive ? ArrowUp : ArrowDown;

  // Tailwind classes for responsive padding based on size
  const cardPadding = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-5',
  };

  // Tailwind classes for label font size based on size
  const labelClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  // Tailwind classes for value font size and weight based on size
  const valueClasses = {
    sm: 'text-xl font-semibold',
    md: 'text-2xl font-semibold',
    lg: 'text-3xl font-semibold',
  };

  // Tailwind classes for comparison text font size based on size
  const comparisonClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  // Lucide icon size based on card size
  const iconSize = {
    sm: 16,
    md: 20,
    lg: 24,
  };

  // Common classes for skeleton elements
  const skeletonClasses = 'bg-gray-200 animate-pulse rounded';

  // Construct a default aria-label for accessibility
  const defaultAriaLabel = ariaLabel || `${label}: ${value}${
    comparisonValue !== undefined ? `, change of ${comparisonValue.toFixed(1)} percent` : ''
  }`;

  return (
    <div
      className={cn(
        'relative flex flex-col justify-between rounded-lg border',
        'font-inter bg-white shadow-md transition-all duration-200 ease-in-out',
        'hover:shadow-lg hover:bg-[#FAFAFA]', // Subtle hover effect as per brand guidelines
        isGold ? 'border-[#D4AF37] hover:border-[#D4AF37]/80' : 'border-gray-200',
        cardPadding[size],
        onClick && 'cursor-pointer', // Indicate interactivity if onClick is provided
        className,
      )}
      role={onClick ? 'button' : 'status'} // Role depends on interactivity
      aria-label={defaultAriaLabel} // Comprehensive label for screen readers
      onClick={onClick}
      tabIndex={onClick ? 0 : -1} // Make clickable if onClick is provided
    >
      {isLoading ? (
        // Loading Skeleton State
        <>
          <div className="flex items-center justify-between mb-2">
            <div className={cn(skeletonClasses, labelClasses[size], 'w-2/3 h-4')}></div>
            <div className={cn(skeletonClasses, `w-${iconSize[size] / 1.5} h-${iconSize[size] / 1.5}`)}></div>
          </div>
          <div className={cn(skeletonClasses, valueClasses[size], 'w-1/2 h-8 mb-2')}></div>
          <div className="flex items-center justify-between mt-2">
            <div className={cn(skeletonClasses, comparisonClasses[size], 'w-1/4 h-4')}></div>
            {sparklineData && (
              <div className={cn(skeletonClasses, 'w-1/3 h-8')}></div>
            )}
          </div>
        </>
      ) : (
        // Normal Display State
        <>
          {/* Header: Label and Icon */}
          <div className="flex items-center justify-between mb-2">
            <p className={cn('text-gray-600 font-medium', labelClasses[size])}>
              {label}
            </p>
            {Icon && (
              <Icon
                className={cn(
                  'text-gray-400',
                  isGold && 'text-[#D4AF37]', // Gold icon for premium metrics
                )}
                size={iconSize[size]}
                aria-hidden="true" // Icon is decorative, label covers its meaning
              />
            )}
          </div>

          {/* Metric Value */}
          <p className={cn('text-gray-900', valueClasses[size])}>
            {value}
          </p>

          {/* Comparison and Sparkline */}
          <div className="flex items-end justify-between mt-2 gap-2">
            {comparisonValue !== undefined && (
              <div
                className={cn('flex items-center gap-1', trendColorClass, comparisonClasses[size])}
                aria-live="polite" // Announce changes in comparison value
              >
                {/* Dynamically render ArrowUp or ArrowDown */}
                {React.createElement(trendIcon, {
                  size: iconSize[size] / 1.5,
                  className: 'inline-block',
                  'aria-hidden': 'true', // Icon is purely visual
                })}
                <span>
                  {`${isPositive ? '+' : ''}${comparisonValue.toFixed(1)}%`}
                </span>
              </div>
            )}

            {sparklineData && (
              // Sparkline/Mini Chart Placeholder
              <div
                className={cn(
                  'flex-grow h-8 rounded-md flex items-center justify-center text-gray-400 text-xs',
                  isGold ? 'bg-gradient-to-r from-[#D4AF37]/30 to-[#D4AF37]/50' : 'bg-[#0ABAB5]/20',
                  size === 'sm' && 'h-6',
                  size === 'lg' && 'h-10'
                )}
                aria-hidden="true" // Sparkline is visual, value is in aria-label
              >
                Chart Placeholder
                {/* A real sparkline component (e.g., Recharts, Nivo) would be rendered here */}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};