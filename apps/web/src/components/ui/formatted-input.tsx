import React, { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { formatNumberWithCommas, formatCurrency, parseFormattedNumber } from '@/lib/numberFormatting';
import { cn } from '@/lib/utils';

interface FormattedInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange' | 'type'> {
  value: string;
  onChange: (value: string) => void;
  format?: 'number' | 'currency' | 'sqft';
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

  // Format the value for display when not focused
  useEffect(() => {
    if (!isFocused && value) {
      let formatted = '';
      switch (format) {
        case 'currency':
          formatted = formatCurrency(value);
          break;
        case 'sqft':
          formatted = formatNumberWithCommas(value);
          break;
        default:
          formatted = formatNumberWithCommas(value);
      }
      setDisplayValue(formatted);
    } else if (!value) {
      setDisplayValue('');
    }
  }, [value, format, isFocused]);

  // Format placeholder
  const formattedPlaceholder = React.useMemo(() => {
    if (!placeholder) return '';

    switch (format) {
      case 'currency':
        return formatCurrency(placeholder);
      case 'sqft':
        return `${formatNumberWithCommas(placeholder)} sq ft`;
      default:
        return formatNumberWithCommas(placeholder);
    }
  }, [placeholder, format]);

  const handleFocus = () => {
    setIsFocused(true);
    // Show raw numeric value when focused for easier editing
    setDisplayValue(value);
  };

  const handleBlur = () => {
    setIsFocused(false);
    // Format the value when focus is lost
    if (value) {
      let formatted = '';
      switch (format) {
        case 'currency':
          formatted = formatCurrency(value);
          break;
        case 'sqft':
          formatted = formatNumberWithCommas(value);
          break;
        default:
          formatted = formatNumberWithCommas(value);
      }
      setDisplayValue(formatted);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;

    // Allow empty input
    if (!input) {
      setDisplayValue('');
      onChange('');
      return;
    }

    // Parse to get numeric value
    const numeric = parseFormattedNumber(input);

    // Only allow valid numeric input
    if (!/^\d*\.?\d*$/.test(numeric)) {
      return;
    }

    // Update display and trigger onChange with numeric value
    setDisplayValue(input);
    onChange(numeric);
  };

  // Add prefix/suffix based on format
  const renderInput = () => {
    const inputElement = (
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
        className={cn(
          format === 'currency' && !isFocused && displayValue ? 'pl-8' : '',
          format === 'sqft' && !isFocused && displayValue ? 'pr-12' : '',
          className
        )}
      />
    );

    // Wrap with prefix/suffix if needed
    if (format === 'currency' && !isFocused && displayValue) {
      return (
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 z-10">$</span>
          {inputElement}
        </div>
      );
    }

    if (format === 'sqft' && !isFocused && displayValue) {
      return (
        <div className="relative">
          {inputElement}
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 text-xs z-10">sq ft</span>
        </div>
      );
    }

    return inputElement;
  };

  return renderInput();
}