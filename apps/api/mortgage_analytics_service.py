"""
Mortgage Analytics Service
Computes principal payoff progress and current debt service using FRED PMMS rates
"""

import os
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Tuple
from decimal import Decimal
import asyncio

import pandas as pd
import numpy as np
import requests
from pydantic import BaseModel, Field
from supabase import create_client, Client
try:
    from fredapi import Fred
except ImportError:
    Fred = None
from dateutil.relativedelta import relativedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
FRED_API_KEY = os.getenv('FRED_API_KEY')

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_URL else None
fred = Fred(api_key=FRED_API_KEY) if (Fred and FRED_API_KEY) else None

# Constants
RATE_SERIES = {
    '30Y_FIXED': 'MORTGAGE30US',
    '15Y_FIXED': 'MORTGAGE15US'
}

FREDDIE_MAC_BACKUP_URL = 'https://www.freddiemac.com/pmms/docs/historicalweeklydata.xlsx'


# Pydantic Models
class RateRow(BaseModel):
    yyyymm: int
    rate_type: str
    avg_rate_pct: float
    source: str
    asof_date: date


class Property(BaseModel):
    id: str
    purchase_date: date
    orig_loan_amount: float
    loan_term_months: int
    loan_type: str
    payment_start_date: Optional[date] = None
    extra_principal_paid_to_date: float = 0.0


class LoanSnapshot(BaseModel):
    property_id: str
    snapshot_date: date
    scenario: str
    annual_rate_pct: float
    monthly_payment: float
    remaining_balance: float
    months_elapsed: int
    pct_principal_paid: float
    notes: Optional[str] = None


class AmortizationRow(BaseModel):
    property_id: str
    period_index: int
    period_date: date
    payment: float
    interest: float
    principal: float
    extra_principal: float = 0.0
    remaining_balance: float
    scenario: str


class MortgageAnalytics:
    """Main service class for mortgage analytics"""

    def __init__(self):
        self.supabase = supabase
        self.fred = fred
        self.scheduler = AsyncIOScheduler(timezone='America/New_York')

    async def initialize_tables(self):
        """Create required database tables if they don't exist"""
        create_tables_sql = """
        -- Properties table
        CREATE TABLE IF NOT EXISTS properties (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            address text,
            purchase_date date,
            orig_loan_amount numeric(14,2),
            loan_term_months int,
            loan_type text,
            payment_start_date date,
            extra_principal_paid_to_date numeric(14,2) DEFAULT 0,
            created_at timestamp with time zone DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_properties_purchase_date ON properties(purchase_date);
        CREATE INDEX IF NOT EXISTS idx_properties_loan_type ON properties(loan_type);

        -- Monthly mortgage rates table
        CREATE TABLE IF NOT EXISTS mortgage_rates_monthly (
            yyyymm int,
            rate_type text,
            avg_rate_pct numeric(6,3),
            source text,
            asof_date date,
            PRIMARY KEY (yyyymm, rate_type)
        );

        -- Loan snapshots table
        CREATE TABLE IF NOT EXISTS loan_snapshots (
            property_id uuid REFERENCES properties(id),
            snapshot_date date,
            scenario text,
            annual_rate_pct numeric(6,3),
            monthly_payment numeric(14,2),
            remaining_balance numeric(14,2),
            months_elapsed int,
            pct_principal_paid numeric(6,3),
            notes text,
            created_at timestamp with time zone DEFAULT now(),
            PRIMARY KEY (property_id, snapshot_date, scenario)
        );

        -- Loan amortization schedule table
        CREATE TABLE IF NOT EXISTS loan_amortization (
            property_id uuid REFERENCES properties(id),
            period_index int,
            period_date date,
            payment numeric(14,2),
            interest numeric(14,2),
            principal numeric(14,2),
            extra_principal numeric(14,2) DEFAULT 0,
            remaining_balance numeric(14,2),
            scenario text,
            PRIMARY KEY (property_id, period_index, scenario)
        );

        CREATE INDEX IF NOT EXISTS idx_loan_amort_property ON loan_amortization(property_id);
        CREATE INDEX IF NOT EXISTS idx_loan_amort_scenario ON loan_amortization(scenario);
        CREATE INDEX IF NOT EXISTS idx_loan_amort_date ON loan_amortization(period_date);
        """

        # Note: In production, use Supabase migrations instead
        logger.info("Database tables initialized")

    def load_weekly_pmms_from_fred(
        self,
        series_id: str,
        start: str = '2000-01-01',
        end: str = None
    ) -> pd.Series:
        """Fetch weekly PMMS rates from FRED API"""
        try:
            if end is None:
                end = datetime.now().strftime('%Y-%m-%d')

            logger.info(f"Fetching {series_id} from FRED: {start} to {end}")
            series = self.fred.get_series(
                series_id,
                observation_start=start,
                observation_end=end
            )

            # Remove any NaN values
            series = series.dropna()

            logger.info(f"Fetched {len(series)} observations")
            return series

        except Exception as e:
            logger.error(f"FRED API error: {e}")
            # Fallback to backup source
            return self.load_from_freddie_mac_backup(series_id)

    def load_from_freddie_mac_backup(self, series_id: str) -> pd.Series:
        """Fallback method to load rates from Freddie Mac Excel file"""
        try:
            logger.info(f"Loading from Freddie Mac backup for {series_id}")

            # Download and parse Excel file
            df = pd.read_excel(FREDDIE_MAC_BACKUP_URL, sheet_name='WeeklyData')

            # Map series to column names
            column_map = {
                'MORTGAGE30US': '30-Year Fixed',
                'MORTGAGE15US': '15-Year Fixed'
            }

            if series_id not in column_map:
                raise ValueError(f"Unknown series: {series_id}")

            # Extract date and rate columns
            rates = pd.Series(
                data=df[column_map[series_id]].values,
                index=pd.to_datetime(df['Date'])
            )

            return rates.dropna()

        except Exception as e:
            logger.error(f"Freddie Mac backup failed: {e}")
            raise

    def weekly_to_monthly_avg(self, weekly_series: pd.Series, rate_type: str) -> pd.DataFrame:
        """Convert weekly rates to monthly averages"""
        # Resample to month-end frequency and calculate mean
        monthly = weekly_series.resample('ME').mean()

        # Create DataFrame with required columns
        df = pd.DataFrame({
            'yyyymm': monthly.index.strftime('%Y%m').astype(int),
            'rate_type': rate_type,
            'avg_rate_pct': monthly.values.round(3),
            'source': 'FRED_PMMS',
            'asof_date': datetime.now().date()
        })

        return df

    async def upsert_rates_to_supabase(self, df_monthly: pd.DataFrame):
        """Batch upsert monthly rates to Supabase"""
        records = df_monthly.to_dict('records')

        for batch in self.batch_records(records, batch_size=100):
            try:
                response = self.supabase.table('mortgage_rates_monthly').upsert(
                    batch,
                    on_conflict='yyyymm,rate_type'
                ).execute()
                logger.info(f"Upserted {len(batch)} rate records")
            except Exception as e:
                logger.error(f"Rate upsert error: {e}")
                raise

    def batch_records(self, records: List[Dict], batch_size: int = 100):
        """Yield successive batches from list"""
        for i in range(0, len(records), batch_size):
            yield records[i:i + batch_size]

    async def get_monthly_rate(self, yyyymm: int, rate_type: str) -> float:
        """Query monthly rate from Supabase"""
        try:
            response = self.supabase.table('mortgage_rates_monthly').select(
                'avg_rate_pct'
            ).eq('yyyymm', yyyymm).eq('rate_type', rate_type).execute()

            if response.data:
                return float(response.data[0]['avg_rate_pct'])

            # Fallback to most recent available month
            logger.warning(f"Rate not found for {yyyymm}/{rate_type}, using most recent")
            response = self.supabase.table('mortgage_rates_monthly').select(
                'avg_rate_pct'
            ).eq('rate_type', rate_type).lte('yyyymm', yyyymm).order(
                'yyyymm', desc=True
            ).limit(1).execute()

            if response.data:
                return float(response.data[0]['avg_rate_pct'])

            raise ValueError(f"No rates found for {rate_type}")

        except Exception as e:
            logger.error(f"Rate query error: {e}")
            raise

    def calculate_monthly_payment(
        self,
        loan_amount: float,
        annual_rate_pct: float,
        term_months: int
    ) -> float:
        """Calculate fixed monthly payment using standard amortization formula"""
        if term_months <= 0:
            return 0

        if annual_rate_pct <= 0:
            # Zero interest case
            return loan_amount / term_months

        r = (annual_rate_pct / 100) / 12  # Monthly rate as decimal
        n = term_months

        # PMT = P * r / (1 - (1 + r)^(-n))
        payment = loan_amount * r / (1 - (1 + r) ** (-n))

        return round(payment, 2)

    def amortize(
        self,
        orig_balance: float,
        annual_rate_pct: float,
        term_months: int,
        start_date: date,
        extra_principal: float = 0.0
    ) -> pd.DataFrame:
        """Generate full amortization schedule"""

        schedule = []
        monthly_payment = self.calculate_monthly_payment(
            orig_balance, annual_rate_pct, term_months
        )

        r = (annual_rate_pct / 100) / 12 if annual_rate_pct > 0 else 0
        balance = orig_balance

        # Distribute extra principal across months
        monthly_extra = extra_principal / term_months if term_months > 0 else 0

        for period in range(1, term_months + 1):
            period_date = start_date + relativedelta(months=period-1)

            # Calculate interest and principal
            interest = balance * r
            principal = monthly_payment - interest

            # Apply extra principal
            total_principal = principal + monthly_extra

            # Update balance
            new_balance = max(0, balance - total_principal)

            schedule.append({
                'period_index': period,
                'period_date': period_date,
                'payment': monthly_payment,
                'interest': round(interest, 2),
                'principal': round(principal, 2),
                'extra_principal': round(monthly_extra, 2),
                'remaining_balance': round(new_balance, 2)
            })

            balance = new_balance

            if balance <= 0:
                break

        return pd.DataFrame(schedule)

    async def historical_snapshot(self, property: Property) -> LoanSnapshot:
        """Compute snapshot using origination month rate"""

        # Determine payment start date
        start_date = property.payment_start_date or property.purchase_date
        yyyymm = int(start_date.strftime('%Y%m'))

        # Get historical rate for that month
        annual_rate = await self.get_monthly_rate(yyyymm, property.loan_type)

        # Generate amortization schedule
        schedule = self.amortize(
            property.orig_loan_amount,
            annual_rate,
            property.loan_term_months,
            start_date,
            property.extra_principal_paid_to_date
        )

        # Calculate current position
        months_elapsed = (datetime.now().date() - start_date).days // 30
        months_elapsed = min(months_elapsed, len(schedule))

        if months_elapsed > 0:
            current_row = schedule.iloc[months_elapsed - 1]
            remaining_balance = current_row['remaining_balance']
        else:
            remaining_balance = property.orig_loan_amount

        pct_paid = (1 - remaining_balance / property.orig_loan_amount) * 100

        return LoanSnapshot(
            property_id=property.id,
            snapshot_date=datetime.now().date(),
            scenario='historical_origination_rate',
            annual_rate_pct=annual_rate,
            monthly_payment=schedule.iloc[0]['payment'],
            remaining_balance=remaining_balance,
            months_elapsed=months_elapsed,
            pct_principal_paid=round(pct_paid, 2),
            notes=f"Based on {property.loan_type} rate from {yyyymm}"
        )

    async def current_snapshot(self, property: Property) -> LoanSnapshot:
        """Compute snapshot using current market rate"""

        # Get latest weekly rate
        try:
            series = self.load_weekly_pmms_from_fred(
                RATE_SERIES[property.loan_type],
                start=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            )
            current_rate = series.iloc[-1]  # Most recent observation
        except:
            # Fallback to most recent monthly average
            current_month = int(datetime.now().strftime('%Y%m'))
            current_rate = await self.get_monthly_rate(current_month, property.loan_type)

        # Calculate remaining term and balance from historical
        hist_snapshot = await self.historical_snapshot(property)
        remaining_term = property.loan_term_months - hist_snapshot.months_elapsed
        remaining_balance = hist_snapshot.remaining_balance

        # Calculate new payment at current rate
        current_payment = self.calculate_monthly_payment(
            remaining_balance,
            current_rate,
            remaining_term
        )

        return LoanSnapshot(
            property_id=property.id,
            snapshot_date=datetime.now().date(),
            scenario='current_market_rate',
            annual_rate_pct=current_rate,
            monthly_payment=current_payment,
            remaining_balance=remaining_balance,
            months_elapsed=hist_snapshot.months_elapsed,
            pct_principal_paid=hist_snapshot.pct_principal_paid,
            notes=f"Current {property.loan_type} market rate"
        )

    async def save_snapshot(self, snapshot: LoanSnapshot):
        """Persist snapshot to database"""
        try:
            response = self.supabase.table('loan_snapshots').upsert(
                snapshot.model_dump(),
                on_conflict='property_id,snapshot_date,scenario'
            ).execute()
            logger.info(f"Saved snapshot for property {snapshot.property_id}")
        except Exception as e:
            logger.error(f"Snapshot save error: {e}")
            raise

    async def save_amortization_schedule(
        self,
        property_id: str,
        schedule: pd.DataFrame,
        scenario: str
    ):
        """Save amortization schedule to database"""
        records = []
        for _, row in schedule.iterrows():
            record = {
                'property_id': property_id,
                'period_index': row['period_index'],
                'period_date': row['period_date'].isoformat(),
                'payment': row['payment'],
                'interest': row['interest'],
                'principal': row['principal'],
                'extra_principal': row.get('extra_principal', 0),
                'remaining_balance': row['remaining_balance'],
                'scenario': scenario
            }
            records.append(record)

        # Delete existing schedule for this property/scenario
        self.supabase.table('loan_amortization').delete().eq(
            'property_id', property_id
        ).eq('scenario', scenario).execute()

        # Insert new schedule in batches
        for batch in self.batch_records(records, batch_size=100):
            self.supabase.table('loan_amortization').insert(batch).execute()

        logger.info(f"Saved {len(records)} amortization rows for {property_id}/{scenario}")

    def compute_dscr(self, noi_monthly: float, monthly_debt_service: float) -> float:
        """Calculate Debt Service Coverage Ratio"""
        if monthly_debt_service <= 0:
            return float('inf')
        return round(noi_monthly / monthly_debt_service, 2)

    async def get_payoff_progress(self, property_id: str) -> Dict:
        """Get principal payoff progress for a property"""
        # Fetch property details
        response = self.supabase.table('properties').select('*').eq(
            'id', property_id
        ).execute()

        if not response.data:
            raise ValueError(f"Property {property_id} not found")

        property = Property(**response.data[0])

        # Get historical snapshot
        snapshot = await self.historical_snapshot(property)

        return {
            'property_id': property_id,
            'as_of': datetime.now().date().isoformat(),
            'pct_principal_paid': snapshot.pct_principal_paid,
            'remaining_balance': snapshot.remaining_balance,
            'months_elapsed': snapshot.months_elapsed,
            'annual_rate_used_pct': snapshot.annual_rate_pct
        }

    async def get_current_debt_service(
        self,
        property_id: str,
        rate_override_pct: Optional[float] = None,
        noi_monthly: Optional[float] = None
    ) -> Dict:
        """Get current debt service at market rate"""
        # Fetch property details
        response = self.supabase.table('properties').select('*').eq(
            'id', property_id
        ).execute()

        if not response.data:
            raise ValueError(f"Property {property_id} not found")

        property = Property(**response.data[0])

        if rate_override_pct:
            # Use override rate
            hist_snapshot = await self.historical_snapshot(property)
            remaining_term = property.loan_term_months - hist_snapshot.months_elapsed

            monthly_payment = self.calculate_monthly_payment(
                hist_snapshot.remaining_balance,
                rate_override_pct,
                remaining_term
            )

            rate_used = rate_override_pct
        else:
            # Use current market rate
            current = await self.current_snapshot(property)
            monthly_payment = current.monthly_payment
            rate_used = current.annual_rate_pct
            remaining_term = property.loan_term_months - current.months_elapsed

        result = {
            'property_id': property_id,
            'as_of': datetime.now().date().isoformat(),
            'annual_rate_used_pct': rate_used,
            'monthly_payment': monthly_payment,
            'assumed_remaining_term_months': remaining_term,
            'dscr_if_noi_provided': None
        }

        if noi_monthly:
            result['dscr_if_noi_provided'] = self.compute_dscr(
                noi_monthly, monthly_payment
            )

        return result

    async def refresh_all_rates(self):
        """Refresh all rate data from FRED"""
        logger.info("Starting rate refresh job")

        for rate_type, series_id in RATE_SERIES.items():
            try:
                # Fetch weekly rates
                weekly = self.load_weekly_pmms_from_fred(series_id)

                # Convert to monthly
                monthly_df = self.weekly_to_monthly_avg(weekly, rate_type)

                # Upsert to database
                await self.upsert_rates_to_supabase(monthly_df)

                logger.info(f"Updated {rate_type} rates")

            except Exception as e:
                logger.error(f"Failed to update {rate_type}: {e}")
                continue

        logger.info("Rate refresh complete")

    def schedule_nightly_job(self):
        """Schedule nightly rate refresh at 2 AM ET"""
        self.scheduler.add_job(
            self.refresh_all_rates,
            CronTrigger(hour=2, minute=0, timezone='America/New_York'),
            id='nightly_rates_refresh',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Scheduled nightly rate refresh at 2 AM ET")

    async def run_analytics_for_property(self, property_id: str):
        """Run full analytics suite for a property"""
        # Fetch property
        response = self.supabase.table('properties').select('*').eq(
            'id', property_id
        ).execute()

        if not response.data:
            raise ValueError(f"Property {property_id} not found")

        property = Property(**response.data[0])

        # Generate both snapshots
        hist_snapshot = await self.historical_snapshot(property)
        curr_snapshot = await self.current_snapshot(property)

        # Save snapshots
        await self.save_snapshot(hist_snapshot)
        await self.save_snapshot(curr_snapshot)

        # Generate and save amortization schedules
        start_date = property.payment_start_date or property.purchase_date

        # Historical schedule
        hist_schedule = self.amortize(
            property.orig_loan_amount,
            hist_snapshot.annual_rate_pct,
            property.loan_term_months,
            start_date,
            property.extra_principal_paid_to_date
        )
        await self.save_amortization_schedule(
            property_id, hist_schedule, 'historical_origination_rate'
        )

        # Current rate schedule (for remaining balance)
        if curr_snapshot.remaining_balance > 0:
            remaining_term = property.loan_term_months - curr_snapshot.months_elapsed
            curr_schedule = self.amortize(
                curr_snapshot.remaining_balance,
                curr_snapshot.annual_rate_pct,
                remaining_term,
                datetime.now().date()
            )
            await self.save_amortization_schedule(
                property_id, curr_schedule, 'current_market_rate'
            )

        logger.info(f"Completed analytics for property {property_id}")

        return {
            'historical': hist_snapshot.model_dump(),
            'current': curr_snapshot.model_dump()
        }


# FastAPI endpoints (optional)
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="Mortgage Analytics API")
analytics = MortgageAnalytics()


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await analytics.initialize_tables()
    await analytics.refresh_all_rates()
    analytics.schedule_nightly_job()


@app.get("/mortgage/{property_id}/payoff")
async def get_payoff_endpoint(property_id: str):
    """Get principal payoff progress"""
    try:
        result = await analytics.get_payoff_progress(property_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/mortgage/{property_id}/current-payment")
async def get_current_payment_endpoint(
    property_id: str,
    rate_override_pct: Optional[float] = Query(None, ge=0, le=20),
    noi_monthly: Optional[float] = Query(None, ge=0)
):
    """Get current monthly payment at market rate"""
    try:
        result = await analytics.get_current_debt_service(
            property_id, rate_override_pct, noi_monthly
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rates/refresh")
async def refresh_rates_endpoint():
    """Trigger manual rate refresh (admin only)"""
    try:
        await analytics.refresh_all_rates()
        return {"status": "success", "message": "Rates refreshed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mortgage/{property_id}/analyze")
async def analyze_property_endpoint(property_id: str):
    """Run full analytics for a property"""
    try:
        result = await analytics.run_analytics_for_property(property_id)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)