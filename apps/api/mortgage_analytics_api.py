"""
Production Mortgage Analytics API
Fast, reliable mortgage calculations with comprehensive endpoints
"""

import os
import logging
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class MortgageCalculationRequest(BaseModel):
    """Request model for mortgage calculations"""
    loan_amount: float = Field(..., gt=0, description="Loan principal amount")
    annual_rate: float = Field(..., ge=0, le=50, description="Annual interest rate (percentage)")
    years: int = Field(..., gt=0, le=50, description="Loan term in years")

class PayoffProgressRequest(BaseModel):
    """Request model for loan payoff progress"""
    original_amount: float = Field(..., gt=0, description="Original loan amount")
    annual_rate: float = Field(..., ge=0, le=50, description="Annual interest rate (percentage)")
    term_months: int = Field(..., gt=0, description="Total loan term in months")
    months_elapsed: int = Field(..., ge=0, description="Months since loan origination")
    extra_principal: float = Field(default=0, ge=0, description="Extra principal paid to date")

class RefinanceAnalysisRequest(BaseModel):
    """Request model for refinance analysis"""
    current_balance: float = Field(..., gt=0, description="Current loan balance")
    current_rate: float = Field(..., ge=0, le=50, description="Current interest rate")
    current_months_remaining: int = Field(..., gt=0, description="Months remaining on current loan")
    new_rate: float = Field(..., ge=0, le=50, description="Proposed new interest rate")
    new_term_years: int = Field(..., gt=0, le=50, description="New loan term in years")
    closing_costs: float = Field(default=0, ge=0, description="Refinancing closing costs")

class AffordabilityRequest(BaseModel):
    """Request model for affordability analysis"""
    monthly_income: float = Field(..., gt=0, description="Gross monthly income")
    monthly_debts: float = Field(default=0, ge=0, description="Other monthly debt payments")
    down_payment: float = Field(..., ge=0, description="Available down payment")
    annual_rate: float = Field(..., ge=0, le=50, description="Interest rate")
    loan_term_years: int = Field(default=30, gt=0, le=50, description="Loan term in years")
    property_tax_annual: float = Field(default=0, ge=0, description="Annual property taxes")
    insurance_annual: float = Field(default=0, ge=0, description="Annual insurance cost")
    pmi_monthly: float = Field(default=0, ge=0, description="Monthly PMI payment")

# Core calculation service
class MortgageCalculator:
    """High-performance mortgage calculation engine"""

    @staticmethod
    def calculate_monthly_payment(principal: float, annual_rate: float, term_months: int) -> float:
        """Calculate monthly mortgage payment using standard formula"""
        if annual_rate == 0:
            return principal / term_months

        monthly_rate = annual_rate / 100.0 / 12.0
        payment = principal * (
            monthly_rate * (1 + monthly_rate) ** term_months
        ) / (
            (1 + monthly_rate) ** term_months - 1
        )
        return round(payment, 2)

    @staticmethod
    def calculate_mortgage_details(loan_amount: float, annual_rate: float, years: int) -> Dict[str, Any]:
        """Complete mortgage calculation with all details"""
        term_months = years * 12
        monthly_payment = MortgageCalculator.calculate_monthly_payment(loan_amount, annual_rate, term_months)

        total_paid = monthly_payment * term_months
        total_interest = total_paid - loan_amount

        return {
            'loan_amount': round(loan_amount, 2),
            'annual_rate': annual_rate,
            'term_years': years,
            'term_months': term_months,
            'monthly_payment': monthly_payment,
            'total_interest': round(total_interest, 2),
            'total_paid': round(total_paid, 2),
            'interest_to_principal_ratio': round(total_interest / loan_amount, 3) if loan_amount > 0 else 0
        }

    @staticmethod
    def calculate_payoff_progress(
        original_amount: float,
        annual_rate: float,
        term_months: int,
        months_elapsed: int,
        extra_principal: float = 0
    ) -> Dict[str, Any]:
        """Calculate loan payoff progress and remaining balance"""
        monthly_rate = annual_rate / 100.0 / 12.0

        # Calculate original monthly payment
        if annual_rate == 0:
            monthly_payment = original_amount / term_months
        else:
            monthly_payment = original_amount * (
                monthly_rate * (1 + monthly_rate) ** term_months
            ) / (
                (1 + monthly_rate) ** term_months - 1
            )

        # Calculate remaining balance after elapsed months
        if months_elapsed == 0:
            remaining_balance = original_amount
        elif months_elapsed >= term_months:
            remaining_balance = 0
        else:
            remaining_balance = original_amount * (
                (1 + monthly_rate) ** term_months - (1 + monthly_rate) ** months_elapsed
            ) / (
                (1 + monthly_rate) ** term_months - 1
            )

        # Apply extra principal
        remaining_balance = max(0, remaining_balance - extra_principal)

        principal_paid = original_amount - remaining_balance
        pct_paid = (principal_paid / original_amount) * 100 if original_amount > 0 else 0

        months_remaining = max(0, term_months - months_elapsed)

        return {
            'original_amount': round(original_amount, 2),
            'remaining_balance': round(remaining_balance, 2),
            'principal_paid': round(principal_paid, 2),
            'pct_principal_paid': round(pct_paid, 2),
            'months_elapsed': months_elapsed,
            'months_remaining': months_remaining,
            'monthly_payment': round(monthly_payment, 2),
            'extra_principal_applied': extra_principal,
            'years_elapsed': round(months_elapsed / 12, 1),
            'years_remaining': round(months_remaining / 12, 1)
        }

    @staticmethod
    def analyze_refinance(
        current_balance: float,
        current_rate: float,
        current_months_remaining: int,
        new_rate: float,
        new_term_years: int,
        closing_costs: float = 0
    ) -> Dict[str, Any]:
        """Comprehensive refinance analysis"""
        # Current loan details
        current_payment = MortgageCalculator.calculate_monthly_payment(
            current_balance, current_rate, current_months_remaining
        )
        current_total_remaining = current_payment * current_months_remaining

        # New loan details
        new_term_months = new_term_years * 12
        new_payment = MortgageCalculator.calculate_monthly_payment(
            current_balance, new_rate, new_term_months
        )
        new_total_cost = new_payment * new_term_months + closing_costs

        # Analysis
        monthly_savings = current_payment - new_payment
        total_savings = current_total_remaining - new_total_cost
        breakeven_months = closing_costs / monthly_savings if monthly_savings > 0 else float('inf')

        return {
            'current_monthly_payment': round(current_payment, 2),
            'new_monthly_payment': round(new_payment, 2),
            'monthly_savings': round(monthly_savings, 2),
            'total_current_cost': round(current_total_remaining, 2),
            'total_new_cost': round(new_total_cost, 2),
            'total_savings': round(total_savings, 2),
            'closing_costs': closing_costs,
            'breakeven_months': round(breakeven_months, 1) if breakeven_months != float('inf') else None,
            'breakeven_years': round(breakeven_months / 12, 1) if breakeven_months != float('inf') else None,
            'recommended': monthly_savings > 0 and total_savings > 0,
            'interest_rate_reduction': round(current_rate - new_rate, 3)
        }

    @staticmethod
    def calculate_affordability(
        monthly_income: float,
        monthly_debts: float,
        down_payment: float,
        annual_rate: float,
        loan_term_years: int = 30,
        property_tax_annual: float = 0,
        insurance_annual: float = 0,
        pmi_monthly: float = 0
    ) -> Dict[str, Any]:
        """Calculate home affordability based on income and debts"""
        # Standard debt-to-income ratios
        max_housing_ratio = 0.28  # 28% of gross income for housing
        max_total_debt_ratio = 0.36  # 36% of gross income for total debts

        # Calculate maximum monthly housing payment
        max_housing_payment = monthly_income * max_housing_ratio
        max_total_debt_payment = monthly_income * max_total_debt_ratio
        available_for_housing = max_total_debt_payment - monthly_debts

        # Use the more restrictive limit
        max_monthly_payment = min(max_housing_payment, available_for_housing)

        # Subtract fixed housing costs
        monthly_property_tax = property_tax_annual / 12
        monthly_insurance = insurance_annual / 12
        available_for_principal_interest = max_monthly_payment - monthly_property_tax - monthly_insurance - pmi_monthly

        if available_for_principal_interest <= 0:
            return {
                'max_loan_amount': 0,
                'max_home_price': down_payment,
                'monthly_payment_breakdown': {
                    'principal_interest': 0,
                    'property_tax': monthly_property_tax,
                    'insurance': monthly_insurance,
                    'pmi': pmi_monthly,
                    'total': max_monthly_payment
                },
                'debt_ratios': {
                    'housing_ratio': max_housing_ratio * 100,
                    'total_debt_ratio': max_total_debt_ratio * 100,
                    'current_debt_ratio': (monthly_debts / monthly_income) * 100
                },
                'affordable': False,
                'reason': 'Existing debts and housing costs exceed income limits'
            }

        # Calculate maximum loan amount based on available P&I payment
        term_months = loan_term_years * 12
        monthly_rate = annual_rate / 100.0 / 12.0

        if monthly_rate == 0:
            max_loan_amount = available_for_principal_interest * term_months
        else:
            max_loan_amount = available_for_principal_interest * (
                (1 + monthly_rate) ** term_months - 1
            ) / (
                monthly_rate * (1 + monthly_rate) ** term_months
            )

        max_home_price = max_loan_amount + down_payment

        return {
            'max_loan_amount': round(max_loan_amount, 2),
            'max_home_price': round(max_home_price, 2),
            'down_payment': down_payment,
            'monthly_payment_breakdown': {
                'principal_interest': round(available_for_principal_interest, 2),
                'property_tax': round(monthly_property_tax, 2),
                'insurance': round(monthly_insurance, 2),
                'pmi': pmi_monthly,
                'total': round(max_monthly_payment, 2)
            },
            'debt_ratios': {
                'housing_ratio': round(max_housing_ratio * 100, 1),
                'total_debt_ratio': round(max_total_debt_ratio * 100, 1),
                'current_debt_ratio': round((monthly_debts / monthly_income) * 100, 1),
                'projected_total_ratio': round(((monthly_debts + max_monthly_payment) / monthly_income) * 100, 1)
            },
            'affordable': True,
            'loan_details': {
                'annual_rate': annual_rate,
                'term_years': loan_term_years,
                'monthly_income': monthly_income,
                'monthly_debts': monthly_debts
            }
        }


# Initialize FastAPI app
app = FastAPI(
    title="Mortgage Analytics API",
    description="Comprehensive mortgage calculations and analytics for real estate professionals",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "service": "mortgage_analytics_api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Mortgage calculation endpoints
@app.post("/mortgage/calculate")
async def calculate_mortgage(request: MortgageCalculationRequest):
    """
    Calculate comprehensive mortgage details

    Returns monthly payment, total interest, and payment breakdown
    """
    try:
        result = MortgageCalculator.calculate_mortgage_details(
            request.loan_amount,
            request.annual_rate,
            request.years
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error calculating mortgage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mortgage/payoff-progress")
async def calculate_payoff_progress(request: PayoffProgressRequest):
    """
    Calculate loan payoff progress and remaining balance

    Shows how much principal has been paid and what remains
    """
    try:
        result = MortgageCalculator.calculate_payoff_progress(
            request.original_amount,
            request.annual_rate,
            request.term_months,
            request.months_elapsed,
            request.extra_principal
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error calculating payoff progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mortgage/refinance-analysis")
async def analyze_refinance(request: RefinanceAnalysisRequest):
    """
    Comprehensive refinance analysis

    Compares current loan vs. proposed refinance with breakeven analysis
    """
    try:
        result = MortgageCalculator.analyze_refinance(
            request.current_balance,
            request.current_rate,
            request.current_months_remaining,
            request.new_rate,
            request.new_term_years,
            request.closing_costs
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error analyzing refinance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mortgage/affordability")
async def calculate_affordability(request: AffordabilityRequest):
    """
    Calculate home affordability based on income and debts

    Uses standard 28/36 debt-to-income ratios
    """
    try:
        result = MortgageCalculator.calculate_affordability(
            request.monthly_income,
            request.monthly_debts,
            request.down_payment,
            request.annual_rate,
            request.loan_term_years,
            request.property_tax_annual,
            request.insurance_annual,
            request.pmi_monthly
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error calculating affordability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Quick calculation endpoints
@app.get("/mortgage/quick-payment")
async def quick_payment_calculation(
    amount: float = Query(..., gt=0, description="Loan amount"),
    rate: float = Query(..., ge=0, le=50, description="Annual interest rate (%)"),
    years: int = Query(30, gt=0, le=50, description="Loan term in years")
):
    """Quick monthly payment calculation"""
    try:
        payment = MortgageCalculator.calculate_monthly_payment(amount, rate, years * 12)
        return {
            "loan_amount": amount,
            "annual_rate": rate,
            "term_years": years,
            "monthly_payment": payment
        }
    except Exception as e:
        logger.error(f"Error in quick payment calculation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mortgage/rate-comparison")
async def rate_comparison(
    amount: float = Query(..., gt=0, description="Loan amount"),
    base_rate: float = Query(..., ge=0, le=50, description="Base interest rate (%)"),
    years: int = Query(30, gt=0, le=50, description="Loan term in years")
):
    """Compare payments across different interest rates"""
    try:
        rates = [base_rate - 0.5, base_rate, base_rate + 0.5, base_rate + 1.0]
        rates = [r for r in rates if r >= 0]  # Filter out negative rates

        comparisons = []
        for rate in rates:
            payment = MortgageCalculator.calculate_monthly_payment(amount, rate, years * 12)
            total_paid = payment * years * 12
            total_interest = total_paid - amount

            comparisons.append({
                "rate": rate,
                "monthly_payment": payment,
                "total_interest": round(total_interest, 2),
                "total_paid": round(total_paid, 2)
            })

        return {
            "loan_amount": amount,
            "term_years": years,
            "rate_comparisons": comparisons
        }
    except Exception as e:
        logger.error(f"Error in rate comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility endpoints
@app.get("/mortgage/amortization-schedule")
async def generate_amortization_schedule(
    amount: float = Query(..., gt=0, description="Loan amount"),
    rate: float = Query(..., ge=0, le=50, description="Annual interest rate (%)"),
    years: int = Query(30, gt=0, le=50, description="Loan term in years"),
    limit: int = Query(12, ge=1, le=360, description="Number of payments to return")
):
    """Generate amortization schedule (first N payments)"""
    try:
        term_months = years * 12
        monthly_payment = MortgageCalculator.calculate_monthly_payment(amount, rate, term_months)
        monthly_rate = rate / 100.0 / 12.0

        schedule = []
        remaining_balance = amount

        for month in range(1, min(limit + 1, term_months + 1)):
            interest = remaining_balance * monthly_rate
            principal = monthly_payment - interest
            remaining_balance = max(0, remaining_balance - principal)

            schedule.append({
                "payment_number": month,
                "payment_amount": round(monthly_payment, 2),
                "principal": round(principal, 2),
                "interest": round(interest, 2),
                "remaining_balance": round(remaining_balance, 2)
            })

            if remaining_balance == 0:
                break

        return {
            "loan_amount": amount,
            "annual_rate": rate,
            "term_years": years,
            "monthly_payment": monthly_payment,
            "schedule": schedule,
            "showing_first_n_payments": len(schedule)
        }
    except Exception as e:
        logger.error(f"Error generating amortization schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    uvicorn.run(
        "mortgage_analytics_api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )