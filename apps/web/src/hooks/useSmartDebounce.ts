/**
 * ==============================================================================
 * SMART DEBOUNCING HOOK
 * ==============================================================================
 * Purpose: Standardized debouncing with optimal delays for different input types
 * Author: Claude Code - Advanced Filter Optimization
 * Created: 2025-10-01
 * ==============================================================================
 *
 * Benefits:
 * - Consistent UX across all filter components
 * - Optimized delays based on user research and input type
 * - Prevents unnecessary API calls
 * - Improves perceived performance
 */

import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Input type classifications for optimal debouncing
 */
export type InputType =
  | 'text'      // Free-text inputs (search bars, owner names, addresses)
  | 'number'    // Numeric inputs (prices, square footage, year)
  | 'select'    // Dropdowns and selects (county, property type)
  | 'checkbox'  // Boolean toggles (tax exempt, has pool, waterfront)
  | 'slider'    // Range sliders (value ranges, sqft ranges)
  | 'date';     // Date pickers

/**
 * Optimal debounce delays (in milliseconds) based on research and testing
 */
const OPTIMAL_DELAYS: Record<InputType, number> = {
  text: 250,      // Autocomplete, search bars - balance between responsiveness and API load
  number: 400,    // Value/sqft ranges - users type slower, need validation time
  select: 100,    // Dropdowns - near instant (user made deliberate choice)
  checkbox: 50,   // Boolean filters - instant (single click)
  slider: 300,    // Range sliders - debounce while user drags
  date: 200,      // Date pickers - slightly delayed for validation
};

/**
 * Smart debounce hook with input-type-specific delays
 *
 * @param value - The value to debounce
 * @param inputType - The type of input (determines delay)
 * @param customDelay - Optional custom delay (overrides default)
 * @returns Debounced value
 *
 * @example
 * ```typescript
 * // Text input (250ms delay)
 * const debouncedSearch = useSmartDebounce(searchTerm, 'text');
 *
 * // Number input (400ms delay)
 * const debouncedPrice = useSmartDebounce(minPrice, 'number');
 *
 * // Dropdown (100ms delay)
 * const debouncedCounty = useSmartDebounce(county, 'select');
 *
 * // Checkbox (50ms delay)
 * const debouncedTaxExempt = useSmartDebounce(taxExempt, 'checkbox');
 *
 * // Custom delay
 * const debouncedCustom = useSmartDebounce(value, 'text', 500);
 * ```
 */
export function useSmartDebounce<T>(
  value: T,
  inputType: InputType,
  customDelay?: number
): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  // Use custom delay if provided, otherwise use optimal delay for input type
  const delay = customDelay ?? OPTIMAL_DELAYS[inputType];

  useEffect(() => {
    // Set up debounce timer
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Cleanup function - cancels timer on value change
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Advanced debounce hook with leading and trailing edge support
 *
 * @param value - The value to debounce
 * @param delay - Debounce delay in milliseconds
 * @param options - Debounce options
 * @returns Debounced value
 *
 * @example
 * ```typescript
 * // Trailing edge (default) - fires after user stops typing
 * const debounced = useAdvancedDebounce(value, 300);
 *
 * // Leading edge - fires immediately on first change, then debounces
 * const debouncedLeading = useAdvancedDebounce(value, 300, { leading: true });
 *
 * // Both edges - fires immediately AND after user stops
 * const debouncedBoth = useAdvancedDebounce(value, 300, {
 *   leading: true,
 *   trailing: true
 * });
 *
 * // With max wait - guarantees execution after maxWait even if still changing
 * const debouncedMax = useAdvancedDebounce(value, 300, { maxWait: 1000 });
 * ```
 */
export function useAdvancedDebounce<T>(
  value: T,
  delay: number,
  options: {
    leading?: boolean;
    trailing?: boolean;
    maxWait?: number;
  } = {}
): T {
  const {
    leading = false,
    trailing = true,
    maxWait,
  } = options;

  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const maxWaitTimeoutRef = useRef<NodeJS.Timeout>();
  const lastCallTimeRef = useRef<number>(0);
  const lastInvokeTimeRef = useRef<number>(0);

  const invoke = useCallback((newValue: T) => {
    setDebouncedValue(newValue);
    lastInvokeTimeRef.current = Date.now();
  }, []);

  useEffect(() => {
    const currentTime = Date.now();
    const timeSinceLastCall = currentTime - lastCallTimeRef.current;
    lastCallTimeRef.current = currentTime;

    // Leading edge: invoke immediately on first call
    if (leading && timeSinceLastCall >= delay) {
      invoke(value);
    }

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set up trailing edge timeout
    if (trailing) {
      timeoutRef.current = setTimeout(() => {
        invoke(value);
        if (maxWaitTimeoutRef.current) {
          clearTimeout(maxWaitTimeoutRef.current);
          maxWaitTimeoutRef.current = undefined;
        }
      }, delay);
    }

    // Set up maxWait timeout
    if (maxWait && !maxWaitTimeoutRef.current) {
      const timeSinceLastInvoke = currentTime - lastInvokeTimeRef.current;
      if (timeSinceLastInvoke >= maxWait) {
        invoke(value);
      } else {
        maxWaitTimeoutRef.current = setTimeout(() => {
          invoke(value);
          maxWaitTimeoutRef.current = undefined;
        }, maxWait - timeSinceLastInvoke);
      }
    }

    // Cleanup
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (maxWaitTimeoutRef.current) {
        clearTimeout(maxWaitTimeoutRef.current);
      }
    };
  }, [value, delay, leading, trailing, maxWait, invoke]);

  return debouncedValue;
}

/**
 * Debounce with callback function
 * Useful when you need to perform an action instead of just tracking a value
 *
 * @param callback - Function to call after debounce
 * @param delay - Debounce delay in milliseconds
 * @returns Debounced callback function
 *
 * @example
 * ```typescript
 * const debouncedSearch = useDebounceCallback(
 *   (searchTerm: string) => {
 *     performSearch(searchTerm);
 *   },
 *   300
 * );
 *
 * // Usage
 * <input onChange={(e) => debouncedSearch(e.target.value)} />
 * ```
 */
export function useDebounceCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<NodeJS.Timeout>();
  const callbackRef = useRef(callback);

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  return useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      callbackRef.current(...args);
    }, delay);
  }, [delay]);
}

/**
 * Immediate debounce - fires immediately on first call, then debounces subsequent calls
 * Useful for actions that should provide instant feedback
 *
 * @param callback - Function to call
 * @param delay - Cooldown period after first call
 * @returns Immediate debounced callback
 *
 * @example
 * ```typescript
 * const handleClick = useImmediateDebounce(
 *   () => {
 *     // Fires immediately on first click
 *     // Then ignored for next 1000ms
 *   },
 *   1000
 * );
 * ```
 */
export function useImmediateDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<NodeJS.Timeout>();
  const canCallRef = useRef(true);
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  return useCallback((...args: Parameters<T>) => {
    if (canCallRef.current) {
      // Immediate execution
      callbackRef.current(...args);
      canCallRef.current = false;

      // Set cooldown
      timeoutRef.current = setTimeout(() => {
        canCallRef.current = true;
      }, delay);
    }
  }, [delay]);
}

/**
 * Hook to track if a value is currently being debounced
 * Useful for showing loading indicators
 *
 * @param value - Value to track
 * @param delay - Debounce delay
 * @returns Object with debounced value and isDebouncing flag
 *
 * @example
 * ```typescript
 * const { value: debouncedSearch, isDebouncing } = useDebounceWithStatus(searchTerm, 300);
 *
 * return (
 *   <div>
 *     <input value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
 *     {isDebouncing && <Spinner />}
 *   </div>
 * );
 * ```
 */
export function useDebounceWithStatus<T>(
  value: T,
  delay: number
): { value: T; isDebouncing: boolean } {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const [isDebouncing, setIsDebouncing] = useState(false);

  useEffect(() => {
    setIsDebouncing(true);

    const handler = setTimeout(() => {
      setDebouncedValue(value);
      setIsDebouncing(false);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return { value: debouncedValue, isDebouncing };
}

/**
 * Adaptive debounce - adjusts delay based on typing speed
 * Faster typing = longer delay (user still thinking)
 * Slower typing = shorter delay (user probably done)
 *
 * @param value - Value to debounce
 * @param baseDelay - Base delay in milliseconds
 * @returns Debounced value
 *
 * @example
 * ```typescript
 * // If user types quickly: uses 500ms delay
 * // If user types slowly: uses 200ms delay
 * const debouncedSearch = useAdaptiveDebounce(searchTerm, 300);
 * ```
 */
export function useAdaptiveDebounce<T>(
  value: T,
  baseDelay: number = 300
): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const lastChangeTimeRef = useRef<number>(Date.now());
  const typingSpeedRef = useRef<number>(0);

  useEffect(() => {
    const currentTime = Date.now();
    const timeSinceLastChange = currentTime - lastChangeTimeRef.current;
    lastChangeTimeRef.current = currentTime;

    // Calculate typing speed (lower = faster)
    typingSpeedRef.current = timeSinceLastChange;

    // Adaptive delay:
    // - Fast typing (< 100ms between changes): longer delay (still composing thought)
    // - Slow typing (> 500ms between changes): shorter delay (probably done)
    let adaptiveDelay = baseDelay;
    if (typingSpeedRef.current < 100) {
      adaptiveDelay = baseDelay * 1.5; // 50% longer
    } else if (typingSpeedRef.current > 500) {
      adaptiveDelay = baseDelay * 0.7; // 30% shorter
    }

    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, adaptiveDelay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, baseDelay]);

  return debouncedValue;
}

// Export optimal delays for external use
export { OPTIMAL_DELAYS };
