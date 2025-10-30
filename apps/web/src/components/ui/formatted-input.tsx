import React, { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { formatNumberWithCommas, formatCurrency, parseFormattedNumber } from '@/lib/numberFormatting';
import { cn } from '@/lib/utils';

interface FormattedInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange' | 'type'> {
  value: string;
  onChange: (value: string) => void;
  format?: 'number' | 'currency' | 'sqft' | 'year';
  className?: string;
}

export function FormattedInput({
  value,
  onChange,
  format = 'number',
  className,
  placeholder,
  ...props
}: FormattedInputProps) {
  const [displayValue, setDisplayValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Format the value for display (always formatted, even when focused)
  useEffect(() => {
    if (value) {
      let formatted = '';
      switch (format) {
        case 'currency':
          formatted = formatCurrency(value);
          break;
        case 'sqft':
          formatted = `${formatNumberWithCommas(value)} sq ft`;
          break;
        case 'year':
          formatted = value; // No commas for years (1990, not 1,990)
          break;
        default:
          formatted = formatNumberWithCommas(value);
      }
      setDisplayValue(formatted);
    } else {
      setDisplayValue('');
    }
  }, [value, format]);

  // Format placeholder
  const formattedPlaceholder = React.useMemo(() => {
    if (!placeholder) return '';

    switch (format) {
      case 'currency':
        return formatCurrency(placeholder);
      case 'sqft':
        return `${formatNumberWithCommas(placeholder)} sq ft`;
      case 'year':
        return placeholder; // No commas for year placeholders
      default:
        return formatNumberWithCommas(placeholder);
    }
  }, [placeholder, format]);

  const handleFocus = () => {
    setIsFocused(true);
    // Keep formatted value visible while typing
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;

    // Allow empty input
    if (!input) {
      setDisplayValue('');
      onChange('');
      return;
    }

    // Parse to get numeric value (removes $, commas, etc.)
    const numeric = parseFormattedNumber(input);

    // Only allow valid numeric input
    if (!/^\d*\.?\d*$/.test(numeric)) {
      return;
    }

    // Format immediately for display
    let formatted = '';
    switch (format) {
      case 'currency':
        formatted = formatCurrency(numeric);
        break;
      case 'sqft':
        formatted = `${formatNumberWithCommas(numeric)} sq ft`;
        break;
      case 'year':
        formatted = numeric; // No commas for years
        break;
      default:
        formatted = formatNumberWithCommas(numeric);
    }

    // Update display with formatted value and trigger onChange with raw numeric value
    setDisplayValue(formatted);
    onChange(numeric);
  };

  // Currency format: display value already includes $, no need for wrapper
  // Just render the input directly
  return (
    <Input
      {...props}
      ref={inputRef}
      type="text"
      inputMode="decimal"
      value={displayValue}
      onChange={handleChange}
      onFocus={handleFocus}
      onBlur={handleBlur}
      placeholder={formattedPlaceholder}
      className={className}
    />
  );
}