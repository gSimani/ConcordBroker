/**
 * Property Use Display Component
 *
 * Shows detailed property use information with category and sub-use
 * Fetches from dor_use_codes_std lookup table
 */

import React, { useEffect, useState } from 'react';
import { getPropertyUseInfo, getCategoryColor, type PropertyUseInfo } from '@/services/dorCodeService';

interface PropertyUseDisplayProps {
  propertyUse: string | number | null | undefined;
  county?: string | null;
  showFullCode?: boolean;
  showConfidence?: boolean;
  className?: string;
}

export function PropertyUseDisplay({
  propertyUse,
  county,
  showFullCode = false,
  showConfidence = false,
  className = ''
}: PropertyUseDisplayProps) {
  const [useInfo, setUseInfo] = useState<PropertyUseInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function loadUseInfo() {
      if (!propertyUse) {
        setLoading(false);
        return;
      }

      try {
        const info = await getPropertyUseInfo(propertyUse, county);
        if (mounted) {
          setUseInfo(info);
          setLoading(false);
        }
      } catch (error) {
        console.error('Failed to load property use info:', error);
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadUseInfo();

    return () => {
      mounted = false;
    };
  }, [propertyUse, county]);

  if (loading) {
    return <span className={className}>Loading...</span>;
  }

  if (!useInfo) {
    return <span className={className}>Unknown</span>;
  }

  const categoryColor = getCategoryColor(useInfo.category);

  return (
    <div className={`property-use-display ${className}`}>
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '4px 10px',
        borderRadius: '4px',
        backgroundColor: `${categoryColor}15`,
        border: `1px solid ${categoryColor}40`
      }}>
        {/* Category badge */}
        <span style={{
          fontSize: '0.75rem',
          fontWeight: '600',
          color: categoryColor,
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          {useInfo.category}
        </span>

        {/* Separator */}
        <span style={{
          width: '1px',
          height: '14px',
          backgroundColor: `${categoryColor}40`
        }} />

        {/* Description */}
        <span style={{
          fontSize: '0.875rem',
          color: '#2c3e50',
          fontWeight: '500'
        }}>
          {useInfo.description}
        </span>

        {/* Full code (optional) */}
        {showFullCode && (
          <>
            <span style={{
              width: '1px',
              height: '14px',
              backgroundColor: `${categoryColor}40`
            }} />
            <span style={{
              fontSize: '0.75rem',
              color: '#95a5a6',
              fontFamily: 'monospace'
            }}>
              {useInfo.full_code}
            </span>
          </>
        )}

        {/* Confidence indicator (optional) */}
        {showConfidence && useInfo.confidence !== 'exact' && (
          <span style={{
            fontSize: '0.7rem',
            color: '#95a5a6',
            fontStyle: 'italic'
          }}>
            ({useInfo.confidence})
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Inline variant for compact display
 */
export function PropertyUseInline({
  propertyUse,
  county,
  className = ''
}: Omit<PropertyUseDisplayProps, 'showFullCode' | 'showConfidence'>) {
  const [useInfo, setUseInfo] = useState<PropertyUseInfo | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadUseInfo() {
      if (!propertyUse) return;

      try {
        const info = await getPropertyUseInfo(propertyUse, county);
        if (mounted) {
          setUseInfo(info);
        }
      } catch (error) {
        console.error('Failed to load property use info:', error);
      }
    }

    loadUseInfo();

    return () => {
      mounted = false;
    };
  }, [propertyUse, county]);

  if (!useInfo) return null;

  const categoryColor = getCategoryColor(useInfo.category);

  return (
    <span
      className={className}
      style={{
        color: categoryColor,
        fontWeight: '600',
        fontSize: '0.875rem'
      }}
      title={`${useInfo.category}: ${useInfo.description} (${useInfo.full_code})`}
    >
      {useInfo.description}
    </span>
  );
}

export default PropertyUseDisplay;
