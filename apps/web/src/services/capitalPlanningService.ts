import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

export interface CapitalExpenseTemplate {
  id?: string;
  template_name: string;
  property_type: string;
  category: string;
  icon: string;
  lifecycle_years: number;
  cost_per_sqft?: number;
  cost_per_unit?: number;
  priority: 'high' | 'medium' | 'low';
  description?: string;
  applicable_dor_codes?: string[];
  is_active?: boolean;
}

export interface PropertyCapitalPlan {
  id?: string;
  parcel_id: string;
  county: string;
  property_type: string;
  dor_use_code?: string;
  planning_timeframe: 5 | 10 | 15 | 20;
  total_reserves_needed: number;
  annual_contribution: number;
  monthly_contribution: number;
  current_reserve_balance: number;
  property_age?: number;
  property_sqft?: number;
  property_value?: number;
  created_by?: string;
  last_updated_by?: string;
}

export interface CapitalExpenseItem {
  id?: string;
  capital_plan_id: string;
  template_id?: string;
  category: string;
  icon: string;
  lifecycle_years: number;
  last_replaced_year?: number;
  replacement_year?: number;
  remaining_life_years?: number;
  cost_per_sqft?: number;
  cost_per_unit?: number;
  estimated_cost: number;
  actual_cost?: number;
  priority: 'high' | 'medium' | 'low';
  condition: 'good' | 'fair' | 'poor' | 'unknown';
  urgency?: 'immediate' | 'soon' | 'future';
  status?: 'planned' | 'in_progress' | 'completed' | 'deferred' | 'cancelled';
  notes?: string;
  is_custom: boolean;
}

export interface ReserveFundTransaction {
  id?: string;
  capital_plan_id: string;
  transaction_type: 'deposit' | 'withdrawal' | 'adjustment';
  amount: number;
  transaction_date: string;
  related_expense_id?: string;
  description?: string;
  balance_after?: number;
  created_by?: string;
}

/**
 * Capital Planning Service
 * Handles all database operations for capital planning and reserve management
 */
export class CapitalPlanningService {
  /**
   * Get all expense templates for a specific property type
   */
  static async getTemplatesByPropertyType(propertyType: string): Promise<CapitalExpenseTemplate[]> {
    const { data, error } = await supabase
      .from('capital_expense_templates')
      .select('*')
      .eq('property_type', propertyType)
      .eq('is_active', true)
      .order('priority', { ascending: false });

    if (error) {
      console.error('Error fetching capital expense templates:', error);
      throw error;
    }

    return data || [];
  }

  /**
   * Get templates by DOR use code
   */
  static async getTemplatesByDORCode(dorCode: string): Promise<CapitalExpenseTemplate[]> {
    const formattedCode = String(dorCode).padStart(3, '0');

    const { data, error } = await supabase
      .from('capital_expense_templates')
      .select('*')
      .contains('applicable_dor_codes', [formattedCode])
      .eq('is_active', true)
      .order('priority', { ascending: false });

    if (error) {
      console.error('Error fetching templates by DOR code:', error);
      throw error;
    }

    return data || [];
  }

  /**
   * Get or create capital plan for a property
   */
  static async getOrCreateCapitalPlan(
    parcelId: string,
    county: string,
    propertyData?: Partial<PropertyCapitalPlan>
  ): Promise<PropertyCapitalPlan | null> {
    // Try to get existing plan
    const { data: existing, error: fetchError } = await supabase
      .from('property_capital_plans')
      .select('*')
      .eq('parcel_id', parcelId)
      .eq('county', county)
      .single();

    if (existing) {
      return existing;
    }

    // Create new plan if doesn't exist
    if (!existing && propertyData) {
      const { data: newPlan, error: createError } = await supabase
        .from('property_capital_plans')
        .insert({
          parcel_id: parcelId,
          county: county,
          property_type: propertyData.property_type || 'RESIDENTIAL',
          dor_use_code: propertyData.dor_use_code,
          planning_timeframe: propertyData.planning_timeframe || 5,
          total_reserves_needed: propertyData.total_reserves_needed || 0,
          annual_contribution: propertyData.annual_contribution || 0,
          monthly_contribution: propertyData.monthly_contribution || 0,
          current_reserve_balance: 0,
          property_age: propertyData.property_age,
          property_sqft: propertyData.property_sqft,
          property_value: propertyData.property_value,
        })
        .select()
        .single();

      if (createError) {
        console.error('Error creating capital plan:', createError);
        throw createError;
      }

      return newPlan;
    }

    return null;
  }

  /**
   * Update capital plan
   */
  static async updateCapitalPlan(
    planId: string,
    updates: Partial<PropertyCapitalPlan>
  ): Promise<PropertyCapitalPlan | null> {
    const { data, error } = await supabase
      .from('property_capital_plans')
      .update(updates)
      .eq('id', planId)
      .select()
      .single();

    if (error) {
      console.error('Error updating capital plan:', error);
      throw error;
    }

    return data;
  }

  /**
   * Get all expense items for a capital plan
   */
  static async getExpenseItems(capitalPlanId: string): Promise<CapitalExpenseItem[]> {
    const { data, error } = await supabase
      .from('capital_expense_items')
      .select('*')
      .eq('capital_plan_id', capitalPlanId)
      .order('replacement_year', { ascending: true });

    if (error) {
      console.error('Error fetching expense items:', error);
      throw error;
    }

    return data || [];
  }

  /**
   * Create multiple expense items from templates
   */
  static async createExpenseItemsFromTemplates(
    capitalPlanId: string,
    templates: CapitalExpenseTemplate[],
    propertyData: {
      yearBuilt: number;
      totalSqFt: number;
    }
  ): Promise<CapitalExpenseItem[]> {
    const currentYear = new Date().getFullYear();

    const expenseItems: Omit<CapitalExpenseItem, 'id'>[] = templates.map(template => {
      const lastReplaced = propertyData.yearBuilt + Math.floor(template.lifecycle_years / 2);
      const estimatedCost = template.cost_per_sqft
        ? template.cost_per_sqft * propertyData.totalSqFt
        : template.cost_per_unit || 0;

      return {
        capital_plan_id: capitalPlanId,
        template_id: template.id,
        category: template.category,
        icon: template.icon,
        lifecycle_years: template.lifecycle_years,
        last_replaced_year: lastReplaced,
        cost_per_sqft: template.cost_per_sqft,
        cost_per_unit: template.cost_per_unit,
        estimated_cost: estimatedCost,
        priority: template.priority,
        condition: 'good',
        status: 'planned',
        is_custom: false,
      };
    });

    const { data, error } = await supabase
      .from('capital_expense_items')
      .insert(expenseItems)
      .select();

    if (error) {
      console.error('Error creating expense items:', error);
      throw error;
    }

    return data || [];
  }

  /**
   * Create a single custom expense item
   */
  static async createCustomExpenseItem(
    item: Omit<CapitalExpenseItem, 'id'>
  ): Promise<CapitalExpenseItem | null> {
    const { data, error } = await supabase
      .from('capital_expense_items')
      .insert({ ...item, is_custom: true })
      .select()
      .single();

    if (error) {
      console.error('Error creating custom expense item:', error);
      throw error;
    }

    return data;
  }

  /**
   * Update expense item
   */
  static async updateExpenseItem(
    itemId: string,
    updates: Partial<CapitalExpenseItem>
  ): Promise<CapitalExpenseItem | null> {
    const { data, error } = await supabase
      .from('capital_expense_items')
      .update(updates)
      .eq('id', itemId)
      .select()
      .single();

    if (error) {
      console.error('Error updating expense item:', error);
      throw error;
    }

    // Log the change to history
    if (data) {
      await this.logExpenseHistory(itemId, 'updated', updates);
    }

    return data;
  }

  /**
   * Delete expense item
   */
  static async deleteExpenseItem(itemId: string): Promise<boolean> {
    const { error } = await supabase
      .from('capital_expense_items')
      .delete()
      .eq('id', itemId);

    if (error) {
      console.error('Error deleting expense item:', error);
      throw error;
    }

    return true;
  }

  /**
   * Log expense history
   */
  private static async logExpenseHistory(
    expenseItemId: string,
    action: string,
    changes: Partial<CapitalExpenseItem>
  ): Promise<void> {
    const historyEntry = {
      expense_item_id: expenseItemId,
      action,
      new_cost: changes.estimated_cost,
      new_year: changes.replacement_year,
      change_reason: changes.notes,
    };

    const { error } = await supabase
      .from('capital_expense_history')
      .insert(historyEntry);

    if (error) {
      console.error('Error logging expense history:', error);
    }
  }

  /**
   * Get reserve fund transactions
   */
  static async getReserveTransactions(
    capitalPlanId: string
  ): Promise<ReserveFundTransaction[]> {
    const { data, error } = await supabase
      .from('reserve_fund_transactions')
      .select('*')
      .eq('capital_plan_id', capitalPlanId)
      .order('transaction_date', { ascending: false });

    if (error) {
      console.error('Error fetching reserve transactions:', error);
      throw error;
    }

    return data || [];
  }

  /**
   * Add reserve fund transaction
   */
  static async addReserveTransaction(
    transaction: Omit<ReserveFundTransaction, 'id' | 'balance_after'>
  ): Promise<ReserveFundTransaction | null> {
    const { data, error } = await supabase
      .from('reserve_fund_transactions')
      .insert(transaction)
      .select()
      .single();

    if (error) {
      console.error('Error adding reserve transaction:', error);
      throw error;
    }

    return data;
  }

  /**
   * Get complete capital plan with all items
   */
  static async getCompletePlan(parcelId: string, county: string): Promise<{
    plan: PropertyCapitalPlan | null;
    items: CapitalExpenseItem[];
    transactions: ReserveFundTransaction[];
  }> {
    const plan = await this.getOrCreateCapitalPlan(parcelId, county);

    if (!plan) {
      return { plan: null, items: [], transactions: [] };
    }

    const [items, transactions] = await Promise.all([
      this.getExpenseItems(plan.id!),
      this.getReserveTransactions(plan.id!),
    ]);

    return { plan, items, transactions };
  }

  /**
   * Save complete capital plan (upsert plan and items)
   */
  static async saveCompletePlan(
    parcelId: string,
    county: string,
    planData: Partial<PropertyCapitalPlan>,
    expenseItems: Omit<CapitalExpenseItem, 'id' | 'capital_plan_id'>[]
  ): Promise<{
    plan: PropertyCapitalPlan;
    items: CapitalExpenseItem[];
  }> {
    // Create or get plan
    const plan = await this.getOrCreateCapitalPlan(parcelId, county, planData);

    if (!plan) {
      throw new Error('Failed to create or retrieve capital plan');
    }

    // Delete existing items (we'll recreate them)
    await supabase
      .from('capital_expense_items')
      .delete()
      .eq('capital_plan_id', plan.id!);

    // Insert new items
    const itemsWithPlanId = expenseItems.map(item => ({
      ...item,
      capital_plan_id: plan.id!,
    }));

    const { data: items, error } = await supabase
      .from('capital_expense_items')
      .insert(itemsWithPlanId)
      .select();

    if (error) {
      console.error('Error saving expense items:', error);
      throw error;
    }

    // Update plan totals
    const totalReserves = items.reduce((sum, item) => sum + (item.estimated_cost || 0), 0);
    const updatedPlan = await this.updateCapitalPlan(plan.id!, {
      total_reserves_needed: totalReserves,
      annual_contribution: totalReserves / (planData.planning_timeframe || 5),
      monthly_contribution: totalReserves / ((planData.planning_timeframe || 5) * 12),
    });

    return {
      plan: updatedPlan || plan,
      items: items || [],
    };
  }

  /**
   * Generate capital planning report data
   */
  static async generateReport(parcelId: string, county: string): Promise<any> {
    const { plan, items, transactions } = await this.getCompletePlan(parcelId, county);

    if (!plan) {
      return null;
    }

    const currentYear = new Date().getFullYear();

    const immediateItems = items.filter(item =>
      item.remaining_life_years !== undefined && item.remaining_life_years <= 2
    );

    const soonItems = items.filter(item =>
      item.remaining_life_years !== undefined &&
      item.remaining_life_years > 2 &&
      item.remaining_life_years <= 5
    );

    const longTermItems = items.filter(item =>
      item.remaining_life_years !== undefined && item.remaining_life_years > 5
    );

    return {
      plan,
      summary: {
        totalItems: items.length,
        immediateCount: immediateItems.length,
        soonCount: soonItems.length,
        longTermCount: longTermItems.length,
        totalReserves: plan.total_reserves_needed,
        currentBalance: plan.current_reserve_balance,
        shortfall: plan.total_reserves_needed - plan.current_reserve_balance,
        monthlyContribution: plan.monthly_contribution,
        annualContribution: plan.annual_contribution,
      },
      items: {
        immediate: immediateItems,
        soon: soonItems,
        longTerm: longTermItems,
      },
      transactions: transactions.slice(0, 10), // Last 10 transactions
    };
  }
}

export default CapitalPlanningService;
