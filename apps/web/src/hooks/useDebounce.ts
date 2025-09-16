/**
 * Advanced Debouncing Hook with Smart Delay Management
 * Provides intelligent debouncing with adaptive delays based on input patterns
 */

import { useCallback, useRef, useEffect } from 'react';

interface DebounceOptions {
  leading?: boolean;  // Execute immediately on first call
  trailing?: boolean; // Execute after delay (default behavior)
  maxWait?: number;   // Maximum time to wait before forcing execution
  adaptive?: boolean; // Adjust delay based on typing patterns
}

export function useDebounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number,
  options: DebounceOptions = {}
): [T, { cancel: () => void; flush: () => void; pending: () => boolean }] {
  const {
    leading = false,
    trailing = true,
    maxWait,
    adaptive = false
  } = options;

  const timeoutRef = useRef<NodeJS.Timeout>();
  const maxTimeoutRef = useRef<NodeJS.Timeout>();
  const lastCallTimeRef = useRef<number>();
  const lastInvokeTimeRef = useRef<number>(0);
  const argsRef = useRef<Parameters<T>>();
  const funcRef = useRef(func);
  const adaptiveDelayRef = useRef(delay);
  const typingPatternRef = useRef<number[]>([]);

  // Update function reference
  useEffect(() => {
    funcRef.current = func;
  });

  // Smart adaptive delay calculation
  const calculateAdaptiveDelay = useCallback(() => {
    if (!adaptive) return delay;

    const now = Date.now();
    typingPatternRef.current.push(now);

    // Keep only last 5 typing events
    if (typingPatternRef.current.length > 5) {
      typingPatternRef.current = typingPatternRef.current.slice(-5);
    }

    if (typingPatternRef.current.length < 2) {
      return delay;
    }

    // Calculate typing speed (events per second)
    const timeSpan = now - typingPatternRef.current[0];
    const eventsPerSecond = (typingPatternRef.current.length - 1) / (timeSpan / 1000);

    // Adjust delay based on typing speed
    if (eventsPerSecond > 4) {
      // Fast typing - longer delay
      adaptiveDelayRef.current = Math.min(delay * 2, 1000);
    } else if (eventsPerSecond < 1) {
      // Slow typing - shorter delay
      adaptiveDelayRef.current = Math.max(delay * 0.5, 100);
    } else {
      // Normal typing - standard delay
      adaptiveDelayRef.current = delay;
    }

    return adaptiveDelayRef.current;
  }, [delay, adaptive]);

  const invokeFunc = useCallback(() => {
    const args = argsRef.current;
    if (args) {
      lastInvokeTimeRef.current = Date.now();
      return funcRef.current(...args);
    }
  }, []);

  const leadingEdge = useCallback(() => {
    lastInvokeTimeRef.current = Date.now();
    timeoutRef.current = setTimeout(timerExpired, calculateAdaptiveDelay());
    return leading ? invokeFunc() : undefined;
  }, [leading]);

  const remainingWait = useCallback((time: number) => {
    const timeSinceLastCall = time - (lastCallTimeRef.current || 0);
    const timeSinceLastInvoke = time - lastInvokeTimeRef.current;
    const timeWaiting = calculateAdaptiveDelay() - timeSinceLastCall;

    return maxWait !== undefined
      ? Math.min(timeWaiting, maxWait - timeSinceLastInvoke)
      : timeWaiting;
  }, [maxWait]);

  const shouldInvoke = useCallback((time: number) => {
    const timeSinceLastCall = time - (lastCallTimeRef.current || 0);
    const timeSinceLastInvoke = time - lastInvokeTimeRef.current;

    return (
      lastCallTimeRef.current === undefined ||
      timeSinceLastCall >= calculateAdaptiveDelay() ||
      timeSinceLastCall < 0 ||
      (maxWait !== undefined && timeSinceLastInvoke >= maxWait)
    );
  }, [maxWait]);

  const timerExpired = useCallback(() => {
    const time = Date.now();
    if (shouldInvoke(time)) {
      return trailingEdge(time);
    }
    timeoutRef.current = setTimeout(timerExpired, remainingWait(time));
  }, [shouldInvoke, remainingWait]);

  const trailingEdge = useCallback((time: number) => {
    timeoutRef.current = undefined;

    if (trailing && argsRef.current) {
      return invokeFunc();
    }
    argsRef.current = undefined;
  }, [trailing, invokeFunc]);

  const cancel = useCallback(() => {
    if (timeoutRef.current !== undefined) {
      clearTimeout(timeoutRef.current);
    }
    if (maxTimeoutRef.current !== undefined) {
      clearTimeout(maxTimeoutRef.current);
    }
    lastInvokeTimeRef.current = 0;
    lastCallTimeRef.current = undefined;
    argsRef.current = undefined;
    timeoutRef.current = undefined;
    maxTimeoutRef.current = undefined;
    typingPatternRef.current = [];
  }, []);

  const flush = useCallback(() => {
    return timeoutRef.current === undefined ? undefined : trailingEdge(Date.now());
  }, [trailingEdge]);

  const pending = useCallback(() => {
    return timeoutRef.current !== undefined;
  }, []);

  const debounced = useCallback(
    (...args: Parameters<T>) => {
      const time = Date.now();
      const isInvoking = shouldInvoke(time);

      lastCallTimeRef.current = time;
      argsRef.current = args;

      if (isInvoking) {
        if (timeoutRef.current === undefined) {
          return leadingEdge();
        }
        if (maxWait !== undefined) {
          timeoutRef.current = setTimeout(timerExpired, calculateAdaptiveDelay());
          maxTimeoutRef.current = setTimeout(timerExpired, maxWait);
          return leading ? invokeFunc() : undefined;
        }
      }
      if (timeoutRef.current === undefined) {
        timeoutRef.current = setTimeout(timerExpired, calculateAdaptiveDelay());
      }
    },
    [shouldInvoke, leadingEdge, timerExpired, leading, invokeFunc, maxWait]
  ) as T;

  // Cleanup on unmount
  useEffect(() => {
    return cancel;
  }, [cancel]);

  return [debounced, { cancel, flush, pending }];
}

/**
 * Simpler debounce hook for basic use cases
 */
export function useSimpleDebounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  const [debouncedFunc] = useDebounce(func, delay);
  return debouncedFunc;
}

/**
 * Smart search debounce with instant results for cached queries
 */
export function useSearchDebounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number = 300,
  instantCheck?: (args: Parameters<T>) => boolean
): T {
  const timeoutRef = useRef<NodeJS.Timeout>();
  const funcRef = useRef(func);

  useEffect(() => {
    funcRef.current = func;
  });

  const debouncedFunc = useCallback(
    (...args: Parameters<T>) => {
      // Check if we can return instant results
      if (instantCheck && instantCheck(args)) {
        return funcRef.current(...args);
      }

      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set new timeout
      timeoutRef.current = setTimeout(() => {
        funcRef.current(...args);
      }, delay);
    },
    [delay, instantCheck]
  ) as T;

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedFunc;
}