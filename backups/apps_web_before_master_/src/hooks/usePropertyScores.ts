/**
 * usePropertyScores Hook - Complete Property Scoring System
 * Provides investment scoring, market analysis, and comparable properties
 * Part of ConcordBroker 100% Supabase Integration
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '@/lib/supabase';
import { useToast } from '@/components/ui/use-toast';

// Types for property scores
export interface PropertyScores {
  id: string;
  parcel_id: string;
  county: string;
  investment_score: number;
  market_score: number;
  rental_yield_score: number;
  flip_potential_score: number;
  location_score: number;
  condition_score: number;
  liquidity_score: number;
  score_factors: Record<string, any>;
  last_calculated: string;
  created_at: string;
}

export interface ScoreBreakdown {
  category: string;
  score: number;
  weight: number;
  description: string;
  factors: string[];
}

export interface ComparableProperty {
  comparable_parcel_id: string;
  similarity_score: number;
  distance_miles: number;
  price_difference_pct: number;
  comparison_factors: Record<string, any>;
  property_data?: any; // Will be populated from florida_parcels
}

export interface ScoreCalculationResult {
  parcel_id: string;
  investment_score: number;
  market_score: number;
  rental_yield_score: number;
  flip_potential_score: number;
  location_score: number;
  condition_score: number;
  liquidity_score: number;
  score_factors: Record<string, any>;
  calculated_at: string;
}

interface PropertyScoresState {
  scoresByProperty: Map<string, PropertyScores>;
  loading: boolean;
  calculating: boolean;
  error: string | null;
  lastUpdated: string | null;
}

/**
 * Custom hook for managing property investment scores and analytics
 * Features:
 * - Real-time score calculations
 * - Comparable property analysis
 * - Score breakdown and explanations
 * - Caching for performance
 * - Batch score calculations
 */
export const usePropertyScores = (parcelId?: string) => {
  const { toast } = useToast();

  // State management
  const [state, setState] = useState<PropertyScoresState>({
    scoresByProperty: new Map(),
    loading: false,
    calculating: false,
    error: null,
    lastUpdated: null,
  });

  // Get scores for specific property
  const propertyScores = useMemo(() => {
    if (!parcelId) return null;
    return state.scoresByProperty.get(parcelId) || null;
  }, [state.scoresByProperty, parcelId]);

  /**
   * Fetch existing scores from database
   */
  const fetchPropertyScores = useCallback(async (targetParcelId: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const { data, error } = await supabase
        .from('property_scores')
        .select('*')
        .eq('parcel_id', targetParcelId)
        .single();

      if (error && error.code !== 'PGRST116') { // PGRST116 = not found
        throw error;
      }

      setState(prev => {
        const newScoresByProperty = new Map(prev.scoresByProperty);
        if (data) {
          newScoresByProperty.set(targetParcelId, data);
        }

        return {
          ...prev,
          scoresByProperty: newScoresByProperty,
          loading: false,
          lastUpdated: new Date().toISOString(),
        };
      });

      return data;

    } catch (error: any) {
      console.error('Error fetching property scores:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to fetch property scores',
        loading: false,
      }));

      toast({
        title: "Error Loading Scores",
        description: "Failed to load property scores. Please try again.",
        variant: "destructive",
      });

      return null;
    }
  }, [toast]);

  /**
   * Calculate scores for a property using Supabase function
   */
  const calculateScores = useCallback(async (targetParcelId: string, forceRecalculate: boolean = false) => {
    // Check if we have recent scores (less than 24 hours old) and not forcing recalculation
    const existingScores = state.scoresByProperty.get(targetParcelId);
    if (!forceRecalculate && existingScores) {
      const lastCalculated = new Date(existingScores.last_calculated);
      const now = new Date();
      const hoursDiff = (now.getTime() - lastCalculated.getTime()) / (1000 * 60 * 60);

      if (hoursDiff < 24) {
        return existingScores;
      }
    }

    setState(prev => ({ ...prev, calculating: true, error: null }));

    try {
      // Call the Supabase function to calculate scores
      const { data: calculationResult, error: calcError } = await supabase
        .rpc('calculate_investment_score', { p_parcel_id: targetParcelId });

      if (calcError) throw calcError;

      if (calculationResult?.error) {
        throw new Error(calculationResult.error);
      }

      // Insert or update the scores in the database
      const scoresData = {
        parcel_id: targetParcelId,
        county: calculationResult.score_factors?.county || '',
        investment_score: calculationResult.investment_score,
        market_score: calculationResult.market_score,
        rental_yield_score: calculationResult.rental_yield_score,
        flip_potential_score: calculationResult.flip_potential_score,
        location_score: calculationResult.location_score,
        condition_score: calculationResult.condition_score,
        liquidity_score: calculationResult.liquidity_score,
        score_factors: calculationResult.score_factors,
        last_calculated: calculationResult.calculated_at,
      };

      const { data, error } = await supabase
        .from('property_scores')
        .upsert(scoresData, {
          onConflict: 'parcel_id',
          ignoreDuplicates: false
        })
        .select()
        .single();

      if (error) throw error;

      // Update state with new scores
      setState(prev => {
        const newScoresByProperty = new Map(prev.scoresByProperty);
        newScoresByProperty.set(targetParcelId, data);

        return {
          ...prev,
          scoresByProperty: newScoresByProperty,
          calculating: false,
          lastUpdated: new Date().toISOString(),
        };
      });

      toast({
        title: "Scores Calculated",
        description: `Investment score: ${Math.round(data.investment_score)}/100`,
        variant: "default",
      });

      return data;

    } catch (error: any) {
      console.error('Error calculating property scores:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to calculate property scores',
        calculating: false,
      }));

      toast({
        title: "Error Calculating Scores",
        description: "Failed to calculate property scores. Please try again.",
        variant: "destructive",
      });

      return null;
    }
  }, [state.scoresByProperty, toast]);

  /**
   * Get comparable properties
   */
  const getComparableProperties = useCallback(async (
    targetParcelId: string,
    radiusMiles: number = 5,
    limit: number = 10
  ): Promise<ComparableProperty[]> => {
    try {
      // Call the Supabase function to find comparables
      const { data, error } = await supabase
        .rpc('find_comparable_properties', {
          p_parcel_id: targetParcelId,
          p_radius_miles: radiusMiles,
          p_limit: limit
        });

      if (error) throw error;

      // Enhance with property data
      const comparablesWithData = await Promise.all(
        (data || []).map(async (comp: any) => {
          // Fetch basic property data for each comparable
          const { data: propertyData } = await supabase
            .from('florida_parcels')
            .select('parcel_id, phy_addr1, phy_city, just_value, total_living_area, year_built')
            .eq('parcel_id', comp.comparable_parcel_id)
            .single();

          return {
            ...comp,
            property_data: propertyData,
          };
        })
      );

      return comparablesWithData;

    } catch (error: any) {
      console.error('Error fetching comparable properties:', error);

      toast({
        title: "Error Loading Comparables",
        description: "Failed to load comparable properties. Please try again.",
        variant: "destructive",
      });

      return [];
    }
  }, [toast]);

  /**
   * Get score breakdown with explanations
   */
  const getScoreBreakdown = useCallback((scores: PropertyScores): ScoreBreakdown[] => {
    return [
      {
        category: 'Market Score',
        score: scores.market_score,
        weight: 25,
        description: 'Property value relative to market trends',
        factors: [
          'Current market value vs. area median',
          'Value-to-land ratio',
          'Price appreciation potential',
          'Market demand indicators'
        ]
      },
      {
        category: 'Rental Yield',
        score: scores.rental_yield_score,
        weight: 20,
        description: 'Expected rental income potential',
        factors: [
          'Price per square foot efficiency',
          'Area rental rates',
          'Property size and layout',
          'Rental demand in area'
        ]
      },
      {
        category: 'Flip Potential',
        score: scores.flip_potential_score,
        weight: 15,
        description: 'Property improvement and resale potential',
        factors: [
          'Property age and condition',
          'Renovation potential',
          'Market appreciation trends',
          'Comparable sales activity'
        ]
      },
      {
        category: 'Location',
        score: scores.location_score,
        weight: 15,
        description: 'Geographic and neighborhood factors',
        factors: [
          'Area desirability',
          'Growth potential',
          'Infrastructure access',
          'Neighborhood stability'
        ]
      },
      {
        category: 'Condition',
        score: scores.condition_score,
        weight: 15,
        description: 'Estimated property condition',
        factors: [
          'Building-to-land value ratio',
          'Property age',
          'Improvement quality indicators',
          'Maintenance requirements'
        ]
      },
      {
        category: 'Liquidity',
        score: scores.liquidity_score,
        weight: 10,
        description: 'How easily the property can be sold',
        factors: [
          'Recent sales activity',
          'Market velocity',
          'Property type desirability',
          'Financing accessibility'
        ]
      }
    ];
  }, []);

  /**
   * Get investment recommendation based on scores
   */
  const getInvestmentRecommendation = useCallback((scores: PropertyScores): {
    recommendation: 'Strong Buy' | 'Buy' | 'Hold' | 'Pass';
    reasoning: string[];
    riskFactors: string[];
  } => {
    const { investment_score } = scores;
    const breakdown = getScoreBreakdown(scores);

    let recommendation: 'Strong Buy' | 'Buy' | 'Hold' | 'Pass';
    const reasoning: string[] = [];
    const riskFactors: string[] = [];

    if (investment_score >= 80) {
      recommendation = 'Strong Buy';
      reasoning.push('Exceptional investment potential across multiple metrics');
    } else if (investment_score >= 65) {
      recommendation = 'Buy';
      reasoning.push('Good investment potential with favorable metrics');
    } else if (investment_score >= 50) {
      recommendation = 'Hold';
      reasoning.push('Moderate investment potential, consider timing');
    } else {
      recommendation = 'Pass';
      reasoning.push('Lower investment potential, consider other options');
    }

    // Add specific reasoning based on high-performing categories
    breakdown.forEach(category => {
      if (category.score >= 75) {
        reasoning.push(`Strong ${category.category.toLowerCase()}: ${category.description}`);
      } else if (category.score <= 40) {
        riskFactors.push(`Low ${category.category.toLowerCase()}: ${category.description}`);
      }
    });

    return { recommendation, reasoning, riskFactors };
  }, [getScoreBreakdown]);

  /**
   * Batch calculate scores for multiple properties
   */
  const batchCalculateScores = useCallback(async (parcelIds: string[]): Promise<PropertyScores[]> => {
    setState(prev => ({ ...prev, calculating: true, error: null }));

    const results: PropertyScores[] = [];

    try {
      // Process in batches of 5 to avoid overwhelming the database
      const BATCH_SIZE = 5;
      for (let i = 0; i < parcelIds.length; i += BATCH_SIZE) {
        const batch = parcelIds.slice(i, i + BATCH_SIZE);
        const batchPromises = batch.map(parcelId => calculateScores(parcelId, false));
        const batchResults = await Promise.allSettled(batchPromises);

        batchResults.forEach((result, index) => {
          if (result.status === 'fulfilled' && result.value) {
            results.push(result.value);
          } else {
            console.error(`Failed to calculate scores for ${batch[index]}:`, result);
          }
        });

        // Small delay between batches
        if (i + BATCH_SIZE < parcelIds.length) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      toast({
        title: "Batch Calculation Complete",
        description: `Calculated scores for ${results.length} of ${parcelIds.length} properties`,
        variant: "default",
      });

      return results;

    } catch (error: any) {
      console.error('Error in batch calculation:', error);

      toast({
        title: "Batch Calculation Error",
        description: "Some property scores could not be calculated",
        variant: "destructive",
      });

      return results;
    } finally {
      setState(prev => ({ ...prev, calculating: false }));
    }
  }, [calculateScores, toast]);

  // Fetch scores when parcelId changes
  useEffect(() => {
    if (parcelId && !state.scoresByProperty.has(parcelId)) {
      fetchPropertyScores(parcelId);
    }
  }, [parcelId, state.scoresByProperty, fetchPropertyScores]);

  return {
    // State
    propertyScores,
    loading: state.loading,
    calculating: state.calculating,
    error: state.error,
    lastUpdated: state.lastUpdated,

    // Actions
    calculateScores,
    fetchPropertyScores,
    getComparableProperties,
    batchCalculateScores,

    // Analysis functions
    getScoreBreakdown,
    getInvestmentRecommendation,

    // Computed values
    hasScores: !!propertyScores,
    isRecentlyCalculated: propertyScores ?
      (new Date().getTime() - new Date(propertyScores.last_calculated).getTime()) < (24 * 60 * 60 * 1000) :
      false,
  };
};