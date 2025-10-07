/**
 * Mortgage Service
 * Handles all mortgage-related API calls and calculations
 */

const MORTGAGE_API_BASE = process.env.VITE_MORTGAGE_API_URL || 'http://localhost:8005';

export interface MortgageCalculation {
  loan_amount: number;
  annual_rate: number;
  term_years: number;
  term_months: number;
  monthly_payment: number;
  total_interest: number;
  total_paid: number;
  interest_to_principal_ratio: number;
}

export interface PayoffProgress {
  original_amount: number;
  remaining_balance: number;
  principal_paid: number;
  pct_principal_paid: number;
  months_elapsed: number;
  months_remaining: number;
  monthly_payment: number;
  extra_principal_applied: number;
  years_elapsed: number;
  years_remaining: number;
}

export interface RefinanceAnalysis {
  current_monthly_payment: number;
  new_monthly_payment: number;
  monthly_savings: number;
  total_current_cost: number;
  total_new_cost: number;
  total_savings: number;
  closing_costs: number;
  breakeven_months: number | null;
  breakeven_years: number | null;
  recommended: boolean;
  interest_rate_reduction: number;
}

export interface AffordabilityResult {
  max_loan_amount: number;
  max_home_price: number;
  down_payment: number;
  monthly_payment_breakdown: {
    principal_interest: number;
    property_tax: number;
    insurance: number;
    pmi: number;
    total: number;
  };
  debt_ratios: {
    housing_ratio: number;
    total_debt_ratio: number;
    current_debt_ratio: number;
    projected_total_ratio: number;
  };
  affordable: boolean;
  reason?: string;
  loan_details?: {
    annual_rate: number;
    term_years: number;
    monthly_income: number;
    monthly_debts: number;
  };
}

export interface RateComparison {
  rate: number;
  monthly_payment: number;
  total_interest: number;
  total_paid: number;
}

export interface AmortizationPayment {
  payment_number: number;
  payment_amount: number;
  principal: number;
  interest: number;
  remaining_balance: number;
}

class MortgageService {
  /**
   * Calculate comprehensive mortgage details
   */
  async calculateMortgage(
    loanAmount: number,
    annualRate: number,
    years: number
  ): Promise<MortgageCalculation> {
    const response = await fetch(`${MORTGAGE_API_BASE}/mortgage/calculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        loan_amount: loanAmount,
        annual_rate: annualRate,
        years: years,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to calculate mortgage');
    }

    return response.json();
  }

  /**
   * Calculate loan payoff progress
   */
  async calculatePayoffProgress(
    originalAmount: number,
    annualRate: number,
    termMonths: number,
    monthsElapsed: number,
    extraPrincipal: number = 0
  ): Promise<PayoffProgress> {
    const response = await fetch(`${MORTGAGE_API_BASE}/mortgage/payoff-progress`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        original_amount: originalAmount,
        annual_rate: annualRate,
        term_months: termMonths,
        months_elapsed: monthsElapsed,
        extra_principal: extraPrincipal,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to calculate payoff progress');
    }

    return response.json();
  }

  /**
   * Analyze refinance opportunity
   */
  async analyzeRefinance(
    currentBalance: number,
    currentRate: number,
    currentMonthsRemaining: number,
    newRate: number,
    newTermYears: number,
    closingCosts: number = 0
  ): Promise<RefinanceAnalysis> {
    const response = await fetch(`${MORTGAGE_API_BASE}/mortgage/refinance-analysis`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        current_balance: currentBalance,
        current_rate: currentRate,
        current_months_remaining: currentMonthsRemaining,
        new_rate: newRate,
        new_term_years: newTermYears,
        closing_costs: closingCosts,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to analyze refinance');
    }

    return response.json();
  }

  /**
   * Calculate home affordability
   */
  async calculateAffordability(
    monthlyIncome: number,
    monthlyDebts: number = 0,
    downPayment: number,
    annualRate: number,
    loanTermYears: number = 30,
    propertyTaxAnnual: number = 0,
    insuranceAnnual: number = 0,
    pmiMonthly: number = 0
  ): Promise<AffordabilityResult> {
    const response = await fetch(`${MORTGAGE_API_BASE}/mortgage/affordability`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        monthly_income: monthlyIncome,
        monthly_debts: monthlyDebts,
        down_payment: downPayment,
        annual_rate: annualRate,
        loan_term_years: loanTermYears,
        property_tax_annual: propertyTaxAnnual,
        insurance_annual: insuranceAnnual,
        pmi_monthly: pmiMonthly,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to calculate affordability');
    }

    return response.json();
  }

  /**
   * Quick payment calculation
   */
  async quickPayment(
    amount: number,
    rate: number,
    years: number = 30
  ): Promise<{ monthly_payment: number }> {
    const response = await fetch(
      `${MORTGAGE_API_BASE}/mortgage/quick-payment?amount=${amount}&rate=${rate}&years=${years}`
    );

    if (!response.ok) {
      throw new Error('Failed to calculate payment');
    }

    return response.json();
  }

  /**
   * Compare different interest rates
   */
  async compareRates(
    amount: number,
    baseRate: number,
    years: number = 30
  ): Promise<{ rate_comparisons: RateComparison[] }> {
    const response = await fetch(
      `${MORTGAGE_API_BASE}/mortgage/rate-comparison?amount=${amount}&base_rate=${baseRate}&years=${years}`
    );

    if (!response.ok) {
      throw new Error('Failed to compare rates');
    }

    return response.json();
  }

  /**
   * Generate amortization schedule
   */
  async getAmortizationSchedule(
    amount: number,
    rate: number,
    years: number = 30,
    limit: number = 12
  ): Promise<{
    schedule: AmortizationPayment[];
    monthly_payment: number;
  }> {
    const response = await fetch(
      `${MORTGAGE_API_BASE}/mortgage/amortization-schedule?amount=${amount}&rate=${rate}&years=${years}&limit=${limit}`
    );

    if (!response.ok) {
      throw new Error('Failed to get amortization schedule');
    }

    return response.json();
  }

  /**
   * Format currency for display
   */
  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }

  /**
   * Format percentage for display
   */
  formatPercent(value: number, decimals: number = 2): string {
    return `${value.toFixed(decimals)}%`;
  }
}

export const mortgageService = new MortgageService();
export default mortgageService;