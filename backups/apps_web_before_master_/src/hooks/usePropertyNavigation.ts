/**
 * Hook for navigating to property detail pages
 * Provides consistent navigation across all components that display properties
 */

import { useNavigate } from 'react-router-dom';
import { generatePropertyUrl, generatePropertyTitle, PropertyRouteParams } from '@/utils/propertyRouting';

interface PropertyNavigationData {
  parcelId: string;
  county?: string;
  city?: string;
  address?: string;
  ownerName?: string;
  phy_city?: string;
  phy_addr1?: string;
  owner_name?: string;
  own_name?: string;
}

export function usePropertyNavigation() {
  const navigate = useNavigate();

  /**
   * Navigate to a property's detail page
   */
  const navigateToProperty = (data: PropertyNavigationData) => {
    const routeParams: PropertyRouteParams = {
      parcelId: data.parcelId,
      county: data.county,
      city: data.city || data.phy_city,
      address: data.address || data.phy_addr1,
      ownerName: data.ownerName || data.owner_name || data.own_name
    };

    const propertyUrl = generatePropertyUrl(routeParams);
    navigate(propertyUrl);
  };

  /**
   * Generate a property URL without navigating
   */
  const getPropertyUrl = (data: PropertyNavigationData): string => {
    const routeParams: PropertyRouteParams = {
      parcelId: data.parcelId,
      county: data.county,
      city: data.city || data.phy_city,
      address: data.address || data.phy_addr1,
      ownerName: data.ownerName || data.owner_name || data.own_name
    };

    return generatePropertyUrl(routeParams);
  };

  /**
   * Generate a property title for display
   */
  const getPropertyTitle = (data: PropertyNavigationData): string => {
    const routeParams: PropertyRouteParams = {
      parcelId: data.parcelId,
      county: data.county,
      city: data.city || data.phy_city,
      address: data.address || data.phy_addr1,
      ownerName: data.ownerName || data.owner_name || data.own_name
    };

    return generatePropertyTitle(routeParams);
  };

  /**
   * Open property in new tab
   */
  const openPropertyInNewTab = (data: PropertyNavigationData) => {
    const url = getPropertyUrl(data);
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return {
    navigateToProperty,
    getPropertyUrl,
    getPropertyTitle,
    openPropertyInNewTab
  };
}

/**
 * Hook for property URL generation (lightweight version)
 */
export function usePropertyUrl(data: PropertyNavigationData): {
  url: string;
  title: string;
} {
  const routeParams: PropertyRouteParams = {
    parcelId: data.parcelId,
    county: data.county,
    city: data.city || data.phy_city,
    address: data.address || data.phy_addr1,
    ownerName: data.ownerName || data.owner_name || data.own_name
  };

  return {
    url: generatePropertyUrl(routeParams),
    title: generatePropertyTitle(routeParams)
  };
}