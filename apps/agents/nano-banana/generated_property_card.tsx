// Assume cn utility is defined elsewhere or inline for this single file output.
// For a complete project, this would typically be in `lib/utils.ts`.
// For the purpose of providing a complete, self-contained component, it is defined here.
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility function to conditionally join Tailwind CSS classes.
 * It merges conflicting classes and handles conditional class assignments.
 * @param inputs A list of class values, strings, or objects.
 * @returns A single string of merged Tailwind classes.
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

import React from 'react';
import { Heart } from 'lucide-react';

/**
 * Formats a number as USD currency.
 * @param value The number to format.
 * @returns A string representing the formatted currency.
 */
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Defines the possible property types.
 */
type PropertyType = 'residential' | 'commercial' | 'vacant land';

/**
 * Defines the possible property statuses.
 */
type PropertyStatus = 'active' | 'pending' | 'sold';

/**
 * Props for the PropertyCard component.
 */
interface PropertyCardProps {
  /** The unique identifier for the property parcel. */
  parcelId: string;
  /** The full street address of the property. */
  streetAddress: string;
  /** The city where the property is located. */
  city: string;
  /** The state where the property is located (e.g., "FL"). */
  state: string;
  /** The zip code of the property. */
  zipCode: string;
  /** The market value of the property. */
  justValue: number;
  /** The name of the current owner. */
  ownerName: string;
  /** The URL of the property image. If not provided, a placeholder will be shown. */
  imageUrl?: string;
  /** The type of the property. */
  propertyType: PropertyType;
  /** The current status of the property listing. */
  status: PropertyStatus;
  /** Indicates if the property is marked as a favorite by the user. */
  isFavorite: boolean;
  /** Indicates if the property is a premium/featured listing, affecting styling. Defaults to false. */
  isPremium?: boolean;
  /** Callback function to be called when the card is clicked. Receives the parcelId. */
  onClick: (parcelId: string) => void;
  /** Callback function to be called when the favorite button is toggled. Receives parcelId and new favorite state. */
  onToggleFavorite: (parcelId: string, isFavorite: boolean) => void;
  /** Optional loading state. If true, the skeleton loader will be displayed instead of the card content. Defaults to false. */
  isLoading?: boolean;
}

/**
 * PropertyCardSkeleton component displays a loading state for a property card.
 * It uses Tailwind's `animate-pulse` for a visual loading effect.
 */
const PropertyCardSkeleton: React.FC = () => (
  <div
    className="relative w-full lg:max-w-xs bg-white rounded-lg p-0
               border border-gray-100 overflow-hidden
               shadow-[0_2px_4px_rgba(0,0,0,0.05),_0_4px_8px_rgba(0,0,0,0.05)]
               flex flex-col animate-pulse"
    role="status"
    aria-live="polite"
    aria-label="Loading property card"
  >
    <div className="w-full h-40 bg-gray-200" />
    <div className="p-4 flex flex-col space-y-3 flex-grow">
      <div className="h-6 bg-gray-200 rounded-md w-3/4" /> {/* Address */}
      <div className="h-4 bg-gray-200 rounded-md w-1/2" /> {/* Value */}
      <div className="flex items-center space-x-2">
        <div className="h-4 bg-gray-200 rounded-full w-1/3" /> {/* Type badge */}
        <div className="h-4 bg-gray-200 rounded-full w-1/4" /> {/* Status badge */}
      </div>
      <div className="h-4 bg-gray-200 rounded-md w-2/3" /> {/* Owner */}
      <div className="h-4 bg-gray-200 rounded-md w-1/2" /> {/* Parcel ID */}
    </div>
    <div className="absolute top-4 right-4 h-8 w-8 rounded-full bg-gray-200" /> {/* Favorite button placeholder */}
  </div>
);

/**
 * PropertyCard component displays key information about a property.
 * It's designed for the ConcordBroker platform, adhering to its brand guidelines
 * and design principles, including mobile-first responsiveness, progressive disclosure,
 * and accessibility.
 *
 * @param {PropertyCardProps} props The properties for the component.
 * @returns A React functional component.
 */
export const PropertyCard: React.FC<PropertyCardProps> = ({
  parcelId,
  streetAddress,
  city,
  state,
  zipCode,
  justValue,
  ownerName,
  imageUrl,
  propertyType,
  status,
  isFavorite,
  isPremium = false,
  onClick,
  onToggleFavorite,
  isLoading = false,
}) => {
  if (isLoading) {
    return <PropertyCardSkeleton />;
  }

  const fullAddress = `${streetAddress}, ${city}, ${state} ${zipCode}`;

  // Dynamically assign Tailwind classes for status badges based on ConcordBroker branding and common patterns
  const statusColors: Record<PropertyStatus, string> = {
    active: 'bg-[#0ABAB5]/10 text-[#0ABAB5] border-[#0ABAB5]/30', // Tiffany green for active
    pending: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    sold: 'bg-red-100 text-red-700 border-red-300',
  };

  // Dynamically assign Tailwind classes for property type badges
  const propertyTypeColors: Record<PropertyType, string> = {
    residential: 'bg-blue-100 text-blue-700 border-blue-300',
    commercial: 'bg-purple-100 text-purple-700 border-purple-300',
    'vacant land': 'bg-green-100 text-green-700 border-green-300',
  };

  /** Handles the click event for the entire card to navigate to property details. */
  const handleCardClick = () => onClick(parcelId);

  /**
   * Handles the click event for the favorite button.
   * Stops event propagation to prevent triggering the card's onClick.
   * @param e The mouse event.
   */
  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleFavorite(parcelId, !isFavorite);
  };

  return (
    <div
      className={cn(
        "relative w-full lg:max-w-xs bg-white rounded-lg p-0 cursor-pointer",
        "border border-gray-100 overflow-hidden",
        "shadow-[0_2px_4px_rgba(0,0,0,0.05),_0_4px_8px_rgba(0,0,0,0.05)]", // Subtle layered shadows
        "hover:translate-y-[-2px] hover:shadow-lg transition-all duration-200 ease-in-out", // Hover lift effect
        "flex flex-col font-inter", // Ensure content flows nicely and apply Inter font
        isPremium && "border-2 border-[#D4AF37]" // Gold border for premium properties
      )}
      onClick={handleCardClick}
      role="link"
      tabIndex={0}
      aria-label={`View details for property at ${fullAddress}, valued at ${formatCurrency(justValue)}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleCardClick();
        }
      }}
    >
      {/* Property Image or Placeholder */}
      <div className="w-full h-40 bg-[#F5F5F5] flex items-center justify-center overflow-hidden">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={`Property at ${fullAddress}`}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <span className="text-gray-400 text-sm italic p-4 text-center">No image available</span>
        )}
      </div>

      {/* Content Section */}
      <div className="p-4 flex flex-col space-y-2 flex-grow">
        {/* Value - Prominently displayed */}
        <p
          className={cn(
            "font-extrabold text-2xl",
            isPremium ? "text-[#D4AF37]" : "text-[#0ABAB5]" // Gold for premium, Tiffany otherwise
          )}
          aria-label={`Market value: ${formatCurrency(justValue)}`}
        >
          {formatCurrency(justValue)}
        </p>

        {/* Address */}
        <p className="text-gray-800 text-base line-clamp-2" aria-label={`Property address: ${fullAddress}`}>
          {fullAddress}
        </p>

        {/* Badges for Property Type and Status */}
        <div className="flex flex-wrap gap-2 pt-1 pb-2">
          <span
            className={cn(
              "text-xs font-semibold px-2 py-1 rounded-full border",
              propertyTypeColors[propertyType]
            )}
            aria-label={`Property type: ${propertyType}`}
          >
            {propertyType.charAt(0).toUpperCase() + propertyType.slice(1)}
          </span>
          <span
            className={cn(
              "text-xs font-semibold px-2 py-1 rounded-full border",
              statusColors[status]
            )}
            aria-label={`Property status: ${status}`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        </div>

        {/* Owner Name */}
        <p className="text-gray-600 text-sm" aria-label={`Owner: ${ownerName}`}>
          Owner: <span className="font-semibold">{ownerName}</span>
        </p>

        {/* Parcel ID in monospace font */}
        <p className="text-gray-500 text-xs" aria-label={`Parcel ID: ${parcelId}`}>
          Parcel ID: <code className="font-mono text-gray-700 bg-[#FAFAFA] px-1 py-0.5 rounded text-[0.7rem] border border-gray-100">{parcelId}</code>
        </p>
      </div>

      {/* Favorite/Bookmark Button */}
      <button
        onClick={handleFavoriteClick}
        className={cn(
          "absolute top-4 right-4 p-2 rounded-full",
          "bg-white shadow-md hover:scale-110 transition-transform duration-150 ease-in-out",
          "focus:outline-none focus:ring-2 focus:ring-[#0ABAB5] focus:ring-opacity-75" // Tiffany ring for focus
        )}
        aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
        role="checkbox"
        aria-checked={isFavorite}
      >
        <Heart
          size={20}
          className={cn(
            isFavorite ? 'fill-red-500 text-red-500' : 'text-gray-400'
          )}
        />
      </button>
    </div>
  );
};