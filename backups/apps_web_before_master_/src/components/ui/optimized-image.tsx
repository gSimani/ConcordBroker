/**
 * Optimized Image Component with Advanced Performance Features
 * - Lazy loading with intersection observer
 * - WebP/AVIF format support with fallbacks
 * - Responsive image sizing
 * - Progressive loading with blur-up effect
 * - Error handling and retry logic
 */

import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { cn } from '@/lib/utils';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  priority?: boolean; // Load immediately without lazy loading
  placeholder?: 'blur' | 'empty';
  blurDataURL?: string;
  sizes?: string; // Responsive image sizes
  quality?: number; // Image quality (1-100)
  loading?: 'lazy' | 'eager';
  onLoad?: () => void;
  onError?: (error: Error) => void;
  fallbackSrc?: string;
  retryCount?: number;
  aspectRatio?: string; // e.g., "16/9", "4/3", "1/1"
}

interface ImageState {
  isLoaded: boolean;
  isLoading: boolean;
  hasError: boolean;
  currentSrc: string;
  retryAttempts: number;
}

export const OptimizedImage = memo(function OptimizedImage({
  src,
  alt,
  width,
  height,
  className,
  priority = false,
  placeholder = 'blur',
  blurDataURL,
  sizes = '100vw',
  quality = 85,
  loading = 'lazy',
  onLoad,
  onError,
  fallbackSrc,
  retryCount = 2,
  aspectRatio,
}: OptimizedImageProps) {
  const [state, setState] = useState<ImageState>({
    isLoaded: false,
    isLoading: false,
    hasError: false,
    currentSrc: '',
    retryAttempts: 0,
  });

  const [isInView, setIsInView] = useState(priority);
  const imgRef = useRef<HTMLImageElement>(null);
  const intersectionObserverRef = useRef<IntersectionObserver | null>(null);

  // Generate optimized image sources with multiple formats
  const generateSources = useCallback((baseSrc: string) => {
    const url = new URL(baseSrc, window.location.origin);
    const params = new URLSearchParams();

    if (width) params.set('w', width.toString());
    if (height) params.set('h', height.toString());
    if (quality !== 85) params.set('q', quality.toString());

    const baseUrl = `${url.pathname}?${params.toString()}`;

    return {
      avif: `${baseUrl}&f=avif`,
      webp: `${baseUrl}&f=webp`,
      original: `${baseUrl}&f=auto`,
      fallback: baseSrc,
    };
  }, [width, height, quality]);

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (priority || isInView) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting) {
          setIsInView(true);
          if (intersectionObserverRef.current) {
            intersectionObserverRef.current.disconnect();
          }
        }
      },
      {
        rootMargin: '50px', // Start loading 50px before image is visible
        threshold: 0.1,
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
      intersectionObserverRef.current = observer;
    }

    return () => {
      if (intersectionObserverRef.current) {
        intersectionObserverRef.current.disconnect();
      }
    };
  }, [priority, isInView]);

  // Load image with format fallback
  const loadImage = useCallback(async (imageSrc: string) => {
    setState(prev => ({ ...prev, isLoading: true, hasError: false }));

    const sources = generateSources(imageSrc);
    const formatOrder = ['avif', 'webp', 'original'] as const;

    for (const format of formatOrder) {
      try {
        const img = new Image();
        const srcUrl = sources[format];

        await new Promise<void>((resolve, reject) => {
          img.onload = () => resolve();
          img.onerror = () => reject(new Error(`Failed to load ${format} format`));
          img.src = srcUrl;
        });

        // If we get here, the image loaded successfully
        setState(prev => ({
          ...prev,
          isLoaded: true,
          isLoading: false,
          currentSrc: srcUrl,
          hasError: false,
        }));

        onLoad?.();
        return;

      } catch (error) {
        console.log(`[OptimizedImage] ${format} format failed, trying next`);
        continue;
      }
    }

    // All formats failed, try fallback
    if (fallbackSrc && state.retryAttempts < retryCount) {
      setState(prev => ({
        ...prev,
        retryAttempts: prev.retryAttempts + 1
      }));

      setTimeout(() => {
        loadImage(fallbackSrc);
      }, 1000 * Math.pow(2, state.retryAttempts)); // Exponential backoff
      return;
    }

    // Complete failure
    setState(prev => ({
      ...prev,
      isLoading: false,
      hasError: true,
    }));

    onError?.(new Error('Failed to load image in any format'));
  }, [generateSources, fallbackSrc, retryCount, state.retryAttempts, onLoad, onError]);

  // Start loading when in view
  useEffect(() => {
    if (isInView && !state.isLoaded && !state.isLoading && !state.hasError) {
      loadImage(src);
    }
  }, [isInView, src, state.isLoaded, state.isLoading, state.hasError, loadImage]);

  // Retry function for manual retry
  const retry = useCallback(() => {
    setState(prev => ({
      ...prev,
      hasError: false,
      retryAttempts: 0
    }));
    loadImage(src);
  }, [src, loadImage]);

  // Generate blur placeholder
  const blurPlaceholder = blurDataURL ||
    'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImciPjxzdG9wIHN0b3AtY29sb3I9IiNmM2Y0ZjYiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiNlNWU3ZWIiLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2cpIi8+PC9zdmc+';

  // Container styles with aspect ratio
  const containerStyles: React.CSSProperties = {
    aspectRatio: aspectRatio || (width && height ? `${width}/${height}` : undefined),
    width: width || '100%',
    height: height || 'auto',
  };

  // Image styles
  const imageStyles: React.CSSProperties = {
    transition: 'opacity 0.3s ease-in-out, filter 0.3s ease-in-out',
    opacity: state.isLoaded ? 1 : 0,
    filter: state.isLoaded ? 'none' : 'blur(8px)',
  };

  return (
    <div
      className={cn(
        'relative overflow-hidden bg-gray-100',
        className
      )}
      style={containerStyles}
    >
      {/* Blur placeholder */}
      {placeholder === 'blur' && !state.isLoaded && (
        <img
          src={blurPlaceholder}
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
          aria-hidden="true"
        />
      )}

      {/* Loading indicator */}
      {state.isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Error state */}
      {state.hasError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100 text-gray-500">
          <svg
            className="w-8 h-8 mb-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <span className="text-sm mb-2">Failed to load image</span>
          {state.retryAttempts < retryCount && (
            <button
              onClick={retry}
              className="text-xs text-blue-500 hover:text-blue-600 underline"
            >
              Retry
            </button>
          )}
        </div>
      )}

      {/* Main image */}
      {(isInView || priority) && (
        <img
          ref={imgRef}
          src={state.currentSrc || src}
          alt={alt}
          loading={loading}
          sizes={sizes}
          className="absolute inset-0 w-full h-full object-cover"
          style={imageStyles}
          draggable={false}
        />
      )}

      {/* Overlay for progressive enhancement */}
      {!state.isLoaded && isInView && (
        <div className="absolute inset-0 bg-gradient-to-br from-gray-200 to-gray-300 animate-pulse" />
      )}
    </div>
  );
});

// Hook for image preloading
export function useImagePreloader() {
  const preloadedImages = useRef(new Set<string>());

  const preloadImage = useCallback((src: string, priority: boolean = false) => {
    if (preloadedImages.current.has(src)) return Promise.resolve();

    return new Promise<void>((resolve, reject) => {
      const img = new Image();

      img.onload = () => {
        preloadedImages.current.add(src);
        resolve();
      };

      img.onerror = () => {
        reject(new Error(`Failed to preload image: ${src}`));
      };

      // Set priority hints
      if (priority) {
        img.loading = 'eager';
        img.fetchPriority = 'high';
      }

      img.src = src;
    });
  }, []);

  const preloadImages = useCallback(async (sources: string[], priority: boolean = false) => {
    const promises = sources.map(src =>
      preloadImage(src, priority).catch(error => {
        console.warn('Failed to preload image:', src, error);
        return null; // Continue with other images
      })
    );

    await Promise.all(promises);
  }, [preloadImage]);

  return { preloadImage, preloadImages };
}

// Image optimization utilities
export const imageUtils = {
  // Generate responsive image sizes
  generateSizes: (breakpoints: Record<string, number>) => {
    const entries = Object.entries(breakpoints).sort(([, a], [, b]) => b - a);
    return entries
      .map(([size, width], index) => {
        if (index === entries.length - 1) {
          return `${width}px`; // Last breakpoint doesn't need media query
        }
        return `(min-width: ${width}px) ${width}px`;
      })
      .join(', ');
  },

  // Check if WebP is supported
  supportsWebP: (() => {
    let supported: boolean | undefined;
    return () => {
      if (supported !== undefined) return supported;

      const canvas = document.createElement('canvas');
      canvas.width = canvas.height = 1;
      supported = canvas.toDataURL('image/webp').indexOf('webp') > -1;
      return supported;
    };
  })(),

  // Check if AVIF is supported
  supportsAVIF: (() => {
    let supported: boolean | undefined;
    return async () => {
      if (supported !== undefined) return supported;

      try {
        const response = await fetch('data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAEAAAABAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQAMAAAAABNjb2xybmNseAACAAIABoAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgABogQEAwgMg8f8D///8WfhwB8+ErK42A=');
        supported = response.ok;
      } catch {
        supported = false;
      }

      return supported;
    };
  })(),

  // Get optimal image format
  getOptimalFormat: async () => {
    if (await imageUtils.supportsAVIF()) return 'avif';
    if (imageUtils.supportsWebP()) return 'webp';
    return 'auto';
  },
};

export default OptimizedImage;