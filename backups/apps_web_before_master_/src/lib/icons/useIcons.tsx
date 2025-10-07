/**
 * Centralized Icon Mapping for Property Use Categories
 *
 * This module provides a single source of truth for icons used across the application
 * for property use categories. It ensures consistency between autocomplete suggestions,
 * filter chips, property cards, and any other components that display use category icons.
 */

import React from 'react';
import {
  Grid3X3,
  Home,
  Building,
  Building2,
  Factory,
  Wheat,
  MapPin,
  TreePine,
  Church,
  Gavel,
  HelpCircle,
  LucideIcon
} from 'lucide-react';

export interface UseIconConfig {
  icon: LucideIcon;
  emoji: string;
  color: string;
  label: string;
}

/**
 * Centralized mapping of use categories to their icons, colors, and labels
 * Normalized to match database use_category values
 */
export const USE_ICON_MAP: Record<string, UseIconConfig> = {
  // All/Default
  'all': {
    icon: Grid3X3,
    emoji: '🏘️',
    color: '#d4af37', // Gold
    label: 'All Properties'
  },

  // Residential
  'residential': {
    icon: Home,
    emoji: '🏠',
    color: '#22c55e', // Green
    label: 'Residential'
  },

  // Commercial
  'commercial': {
    icon: Building,
    emoji: '🏢',
    color: '#3b82f6', // Blue
    label: 'Commercial'
  },

  // Industrial
  'industrial': {
    icon: Factory,
    emoji: '🏭',
    color: '#fb923c', // Orange
    label: 'Industrial'
  },

  // Agricultural
  'agricultural': {
    icon: Wheat,
    emoji: '🌾',
    color: '#f59e0b', // Amber
    label: 'Agricultural'
  },

  // Vacant Land
  'vacant land': {
    icon: MapPin,
    emoji: '🏞️',
    color: '#6b7280', // Gray
    label: 'Vacant Land'
  },

  // Government
  'government': {
    icon: Building2,
    emoji: '🏛️',
    color: '#ef4444', // Red
    label: 'Government'
  },

  // Conservation
  'conservation': {
    icon: TreePine,
    emoji: '🌲',
    color: '#059669', // Emerald
    label: 'Conservation'
  },

  // Religious
  'religious': {
    icon: Church,
    emoji: '⛪',
    color: '#7c3aed', // Violet
    label: 'Religious'
  },

  // Institutional (hospitals, schools, etc.)
  'institutional': {
    icon: Building2,
    emoji: '🏥',
    color: '#ec4899', // Pink
    label: 'Institutional'
  },

  // Tax Deed Sales
  'tax deed sales': {
    icon: Gavel,
    emoji: '⚖️',
    color: '#dc2626', // Red-600
    label: 'Tax Deed Sales'
  },

  // Unknown/Other
  'unknown': {
    icon: HelpCircle,
    emoji: '❓',
    color: '#9ca3af', // Gray-400
    label: 'Other'
  }
};

/**
 * Get icon configuration for a given use category
 * @param category - The use category from the database (case-insensitive)
 * @param defaultCategory - Default category if not found (defaults to 'residential')
 * @returns UseIconConfig object with icon, emoji, color, and label
 */
export function getUseIcon(
  category: string | null | undefined,
  defaultCategory: string = 'residential'
): UseIconConfig {
  if (!category) {
    return USE_ICON_MAP[defaultCategory.toLowerCase()] || USE_ICON_MAP.residential;
  }

  const normalized = category.toLowerCase().trim();

  // Direct match
  if (USE_ICON_MAP[normalized]) {
    return USE_ICON_MAP[normalized];
  }

  // Try to find partial matches
  if (normalized.includes('residential') || normalized.includes('single') || normalized.includes('condo')) {
    return USE_ICON_MAP.residential;
  }

  if (normalized.includes('commercial') || normalized.includes('retail') || normalized.includes('office')) {
    return USE_ICON_MAP.commercial;
  }

  if (normalized.includes('industrial') || normalized.includes('warehouse') || normalized.includes('manufacturing')) {
    return USE_ICON_MAP.industrial;
  }

  if (normalized.includes('agricultural') || normalized.includes('farm') || normalized.includes('ranch')) {
    return USE_ICON_MAP.agricultural;
  }

  if (normalized.includes('vacant') || normalized.includes('land')) {
    return USE_ICON_MAP['vacant land'];
  }

  if (normalized.includes('government') || normalized.includes('public') || normalized.includes('municipal')) {
    return USE_ICON_MAP.government;
  }

  if (normalized.includes('conservation') || normalized.includes('park') || normalized.includes('preserve')) {
    return USE_ICON_MAP.conservation;
  }

  if (normalized.includes('religious') || normalized.includes('church') || normalized.includes('worship')) {
    return USE_ICON_MAP.religious;
  }

  if (normalized.includes('institutional') || normalized.includes('hospital') || normalized.includes('school')) {
    return USE_ICON_MAP.institutional;
  }

  if (normalized.includes('tax deed') || normalized.includes('foreclosure')) {
    return USE_ICON_MAP['tax deed sales'];
  }

  // Default fallback
  return USE_ICON_MAP.unknown;
}

/**
 * Icon Component Props
 */
export interface UseIconProps {
  category: string | null | undefined;
  size?: number | string;
  className?: string;
  showEmoji?: boolean;
  showLabel?: boolean;
  iconClassName?: string;
  style?: React.CSSProperties;
}

/**
 * UseIcon Component - Renders the appropriate icon for a use category
 *
 * @example
 * <UseIcon category="Residential" size={20} />
 * <UseIcon category={property.use_category} showEmoji className="mr-2" />
 */
export const UseIcon: React.FC<UseIconProps> = ({
  category,
  size = 20,
  className = '',
  showEmoji = false,
  showLabel = false,
  iconClassName = '',
  style
}) => {
  const config = getUseIcon(category);
  const Icon = config.icon;

  if (showEmoji) {
    return (
      <span
        className={className}
        style={{
          fontSize: typeof size === 'number' ? `${size}px` : size,
          fontFamily: 'emoji',
          ...style
        }}
        aria-hidden="true"
      >
        {config.emoji}
        {showLabel && <span className="ml-1">{config.label}</span>}
      </span>
    );
  }

  return (
    <span className={className} style={style}>
      <Icon
        size={size}
        className={iconClassName}
        style={{ color: config.color }}
        aria-hidden="true"
      />
      {showLabel && <span className="ml-1">{config.label}</span>}
    </span>
  );
};

/**
 * Get all available use categories for filter chips
 */
export function getAllUseCategories(): Array<{ value: string; label: string; config: UseIconConfig }> {
  return [
    { value: '', label: 'All', config: USE_ICON_MAP.all },
    { value: 'Residential', label: 'Residential', config: USE_ICON_MAP.residential },
    { value: 'Commercial', label: 'Commercial', config: USE_ICON_MAP.commercial },
    { value: 'Industrial', label: 'Industrial', config: USE_ICON_MAP.industrial },
    { value: 'Agricultural', label: 'Agricultural', config: USE_ICON_MAP.agricultural },
    { value: 'Vacant Land', label: 'Vacant Land', config: USE_ICON_MAP['vacant land'] },
    { value: 'Government', label: 'Government', config: USE_ICON_MAP.government },
    { value: 'Conservation', label: 'Conservation', config: USE_ICON_MAP.conservation },
    { value: 'Religious', label: 'Religious', config: USE_ICON_MAP.religious },
    { value: 'Tax Deed Sales', label: 'Tax Deed', config: USE_ICON_MAP['tax deed sales'] }
  ];
}