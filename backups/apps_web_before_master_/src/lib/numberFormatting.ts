/**
 * Number formatting utilities for property search filters
 */

/**
 * Format a number with commas as thousand separators
 * @param value - The numeric value or string to format
 * @returns Formatted string with commas
 */
export function formatNumberWithCommas(value: string | number): string {
  // Remove any existing commas and non-numeric characters except decimal point
  const cleanValue = String(value).replace(/[^0-9.]/g, '');

  if (!cleanValue) return '';

  // Split into integer and decimal parts
  const parts = cleanValue.split('.');

  // Add commas to integer part
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');

  // Join parts back together
  return parts.join('.');
}

/**
 * Format a value as currency with dollar sign and commas
 * @param value - The numeric value or string to format
 * @returns Formatted currency string
 */
export function formatCurrency(value: string | number): string {
  const formatted = formatNumberWithCommas(value);
  return formatted ? `$${formatted}` : '';
}

/**
 * Parse a formatted number/currency string back to numeric value
 * @param value - The formatted string
 * @returns Clean numeric string
 */
export function parseFormattedNumber(value: string): string {
  // Remove dollar signs, commas, and spaces
  return value.replace(/[$,\s]/g, '');
}

/**
 * Format square footage with commas and 'sq ft' suffix
 * @param value - The numeric value or string to format
 * @returns Formatted string with commas and suffix
 */
export function formatSquareFeet(value: string | number): string {
  const formatted = formatNumberWithCommas(value);
  return formatted ? `${formatted} sq ft` : '';
}

/**
 * Handle input change for formatted number fields
 * @param value - The input value
 * @param isCurrency - Whether to format as currency
 * @returns Object with display value and numeric value
 */
export function handleFormattedInput(
  value: string,
  isCurrency: boolean = false
): { display: string; numeric: string } {
  // Parse the input to get numeric value
  const numeric = parseFormattedNumber(value);

  // Format for display
  const display = isCurrency
    ? formatCurrency(numeric)
    : formatNumberWithCommas(numeric);

  return { display, numeric };
}

/**
 * Custom hook for formatted number input
 */
export function useFormattedNumberInput(
  initialValue: string = '',
  isCurrency: boolean = false
) {
  const [displayValue, setDisplayValue] = React.useState(() => {
    if (!initialValue) return '';
    return isCurrency ? formatCurrency(initialValue) : formatNumberWithCommas(initialValue);
  });

  const [numericValue, setNumericValue] = React.useState(initialValue);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;

    // Allow empty input
    if (!input) {
      setDisplayValue('');
      setNumericValue('');
      return;
    }

    // Parse and format
    const { display, numeric } = handleFormattedInput(input, isCurrency);
    setDisplayValue(display);
    setNumericValue(numeric);
  };

  return {
    displayValue,
    numericValue,
    handleChange,
    setDisplayValue,
    setNumericValue
  };
}

// Import React for the hook
import React from 'react';