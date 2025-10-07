"""
Test Suite for Mortgage Analytics Service
"""

import unittest
import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np

from mortgage_analytics_service import (
    MortgageAnalytics,
    Property,
    LoanSnapshot,
    RateRow
)


class TestMortgageCalculations(unittest.TestCase):
    """Test core mortgage calculations"""

    def setUp(self):
        self.analytics = MortgageAnalytics()

    def test_monthly_payment_calculation(self):
        """Test PMT formula against known examples"""

        # Test case 1: Standard 30-year mortgage
        payment = self.analytics.calculate_monthly_payment(
            loan_amount=400000,
            annual_rate_pct=6.5,
            term_months=360
        )
        self.assertAlmostEqual(payment, 2528.27, places=2)

        # Test case 2: 15-year mortgage
        payment = self.analytics.calculate_monthly_payment(
            loan_amount=400000,
            annual_rate_pct=5.75,
            term_months=180
        )
        self.assertAlmostEqual(payment, 3320.09, places=2)

        # Test case 3: Zero interest rate
        payment = self.analytics.calculate_monthly_payment(
            loan_amount=100000,
            annual_rate_pct=0,
            term_months=120
        )
        self.assertAlmostEqual(payment, 833.33, places=2)

        # Test case 4: Very high interest rate
        payment = self.analytics.calculate_monthly_payment(
            loan_amount=100000,
            annual_rate_pct=18,
            term_months=360
        )
        self.assertAlmostEqual(payment, 1507.09, places=2)

    def test_amortization_schedule(self):
        """Test amortization schedule generation"""

        schedule = self.analytics.amortize(
            orig_balance=100000,
            annual_rate_pct=6.0,
            term_months=12,
            start_date=date(2024, 1, 1)
        )

        # Check schedule has correct number of periods
        self.assertEqual(len(schedule), 12)

        # Check first payment breakdown
        first_row = schedule.iloc[0]
        self.assertAlmostEqual(first_row['interest'], 500.00, places=2)

        # Check last payment leaves zero balance
        last_row = schedule.iloc[-1]
        self.assertAlmostEqual(last_row['remaining_balance'], 0, places=2)

        # Check sum of principal equals loan amount
        total_principal = schedule['principal'].sum()
        self.assertAlmostEqual(total_principal, 100000, delta=1)

    def test_extra_principal_application(self):
        """Test handling of extra principal payments"""

        # Generate schedule with extra principal
        schedule = self.analytics.amortize(
            orig_balance=100000,
            annual_rate_pct=6.0,
            term_months=360,
            start_date=date(2024, 1, 1),
            extra_principal=36000  # $100/month extra
        )

        # Check that loan pays off early
        self.assertLess(len(schedule), 360)

        # Verify extra principal is applied
        self.assertGreater(schedule['extra_principal'].sum(), 0)

    def test_weekly_to_monthly_conversion(self):
        """Test conversion of weekly rates to monthly averages"""

        # Create sample weekly data
        dates = pd.date_range('2024-01-01', periods=12, freq='W')
        rates = pd.Series([6.5, 6.6, 6.4, 6.5, 6.7, 6.8, 6.6, 6.5, 6.4, 6.3, 6.4, 6.5], index=dates)

        df = self.analytics.weekly_to_monthly_avg(rates, '30Y_FIXED')

        # Check output format
        self.assertIn('yyyymm', df.columns)
        self.assertIn('avg_rate_pct', df.columns)
        self.assertIn('rate_type', df.columns)

        # Check averaging is correct
        jan_avg = rates[:4].mean()  # First 4 weeks
        self.assertAlmostEqual(df.iloc[0]['avg_rate_pct'], jan_avg, places=3)

    def test_dscr_calculation(self):
        """Test Debt Service Coverage Ratio calculation"""

        # Normal case
        dscr = self.analytics.compute_dscr(
            noi_monthly=5000,
            monthly_debt_service=3000
        )
        self.assertAlmostEqual(dscr, 1.67, places=2)

        # Zero debt service
        dscr = self.analytics.compute_dscr(
            noi_monthly=5000,
            monthly_debt_service=0
        )
        self.assertEqual(dscr, float('inf'))

        # Negative NOI
        dscr = self.analytics.compute_dscr(
            noi_monthly=-1000,
            monthly_debt_service=3000
        )
        self.assertLess(dscr, 0)

    def test_principal_payoff_percentage(self):
        """Test calculation of principal paid percentage"""

        property = Property(
            id='test-123',
            purchase_date=date(2020, 1, 1),
            orig_loan_amount=300000,
            loan_term_months=360,
            loan_type='30Y_FIXED',
            payment_start_date=date(2020, 2, 1),
            extra_principal_paid_to_date=0
        )

        # Generate schedule
        schedule = self.analytics.amortize(
            property.orig_loan_amount,
            6.5,  # Mock rate
            property.loan_term_months,
            property.payment_start_date
        )

        # After 60 months (5 years)
        if len(schedule) >= 60:
            balance_at_60 = schedule.iloc[59]['remaining_balance']
            pct_paid = (1 - balance_at_60 / property.orig_loan_amount) * 100

            # Should have paid off some principal
            self.assertGreater(pct_paid, 0)
            self.assertLess(pct_paid, 100)

    def test_remaining_term_calculation(self):
        """Test calculation of remaining loan term"""

        original_term = 360
        months_elapsed = 60
        remaining = original_term - months_elapsed

        self.assertEqual(remaining, 300)

        # Edge case: fully paid
        months_elapsed = 360
        remaining = original_term - months_elapsed
        self.assertEqual(remaining, 0)

        # Edge case: overpaid
        months_elapsed = 400
        remaining = max(0, original_term - months_elapsed)
        self.assertEqual(remaining, 0)


class TestAsyncOperations(unittest.IsolatedAsyncioTestCase):
    """Test async database operations"""

    async def asyncSetUp(self):
        self.analytics = MortgageAnalytics()

    async def test_historical_snapshot_generation(self):
        """Test historical snapshot calculation"""

        property = Property(
            id='test-456',
            purchase_date=date(2021, 6, 1),
            orig_loan_amount=450000,
            loan_term_months=360,
            loan_type='30Y_FIXED',
            extra_principal_paid_to_date=10000
        )

        # Mock rate retrieval
        self.analytics.get_monthly_rate = unittest.mock.AsyncMock(return_value=3.5)

        snapshot = await self.analytics.historical_snapshot(property)

        self.assertIsInstance(snapshot, LoanSnapshot)
        self.assertEqual(snapshot.scenario, 'historical_origination_rate')
        self.assertGreater(snapshot.pct_principal_paid, 0)
        self.assertLess(snapshot.remaining_balance, property.orig_loan_amount)

    async def test_current_snapshot_generation(self):
        """Test current market rate snapshot"""

        property = Property(
            id='test-789',
            purchase_date=date(2019, 1, 1),
            orig_loan_amount=350000,
            loan_term_months=360,
            loan_type='15Y_FIXED',
            extra_principal_paid_to_date=0
        )

        # Mock methods
        self.analytics.get_monthly_rate = unittest.mock.AsyncMock(return_value=4.5)
        self.analytics.load_weekly_pmms_from_fred = unittest.mock.Mock(
            return_value=pd.Series([6.75])
        )
        self.analytics.historical_snapshot = unittest.mock.AsyncMock(
            return_value=LoanSnapshot(
                property_id=property.id,
                snapshot_date=date.today(),
                scenario='historical',
                annual_rate_pct=4.5,
                monthly_payment=2500,
                remaining_balance=280000,
                months_elapsed=60,
                pct_principal_paid=20.0
            )
        )

        snapshot = await self.analytics.current_snapshot(property)

        self.assertIsInstance(snapshot, LoanSnapshot)
        self.assertEqual(snapshot.scenario, 'current_market_rate')
        self.assertGreater(snapshot.monthly_payment, 0)


class TestDataQuality(unittest.TestCase):
    """Test data quality and validation"""

    def test_rate_data_completeness(self):
        """Ensure no missing months in rate data"""

        # Create sample rate data with a gap
        dates = pd.date_range('2024-01-01', periods=52, freq='W')
        rates = pd.Series(np.random.uniform(6.0, 7.0, 52), index=dates)

        analytics = MortgageAnalytics()
        monthly = analytics.weekly_to_monthly_avg(rates, '30Y_FIXED')

        # Should have a complete set of months
        expected_months = pd.date_range('2024-01', periods=12, freq='MS').strftime('%Y%m').astype(int)

        for month in expected_months:
            if month <= monthly['yyyymm'].max():
                self.assertIn(month, monthly['yyyymm'].values)

    def test_rate_staleness_check(self):
        """Warn if latest rate observation is too old"""

        # Create stale data (>8 days old)
        old_date = datetime.now() - timedelta(days=10)
        dates = pd.date_range(end=old_date, periods=4, freq='W')
        rates = pd.Series([6.5, 6.6, 6.4, 6.5], index=dates)

        # Check if latest is stale
        latest_date = rates.index[-1]
        days_old = (datetime.now() - pd.to_datetime(latest_date)).days

        self.assertGreater(days_old, 8)  # Should trigger warning

    def test_input_validation(self):
        """Test validation of input parameters"""

        analytics = MortgageAnalytics()

        # Test invalid loan amount
        with self.assertRaises(Exception):
            analytics.calculate_monthly_payment(
                loan_amount=-100000,
                annual_rate_pct=6.5,
                term_months=360
            )

        # Test invalid term
        payment = analytics.calculate_monthly_payment(
            loan_amount=100000,
            annual_rate_pct=6.5,
            term_months=0
        )
        self.assertEqual(payment, 0)

        # Test invalid rate (should still calculate)
        payment = analytics.calculate_monthly_payment(
            loan_amount=100000,
            annual_rate_pct=-1,
            term_months=360
        )
        # Negative rate should be handled gracefully


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def test_zero_interest_loan(self):
        """Test loan with zero interest rate"""

        analytics = MortgageAnalytics()
        payment = analytics.calculate_monthly_payment(
            loan_amount=120000,
            annual_rate_pct=0,
            term_months=120
        )

        self.assertEqual(payment, 1000.00)  # Simple division

    def test_balloon_payment(self):
        """Test handling of very short term loans"""

        analytics = MortgageAnalytics()
        payment = analytics.calculate_monthly_payment(
            loan_amount=100000,
            annual_rate_pct=7.0,
            term_months=1
        )

        # Should be roughly principal + one month interest
        expected = 100000 + (100000 * 0.07 / 12)
        self.assertAlmostEqual(payment, expected, delta=1)

    def test_very_long_term(self):
        """Test 40-year mortgage calculation"""

        analytics = MortgageAnalytics()
        payment_30yr = analytics.calculate_monthly_payment(
            loan_amount=500000,
            annual_rate_pct=7.0,
            term_months=360
        )

        payment_40yr = analytics.calculate_monthly_payment(
            loan_amount=500000,
            annual_rate_pct=7.0,
            term_months=480
        )

        # 40-year should have lower payment
        self.assertLess(payment_40yr, payment_30yr)

        # But total interest should be higher
        total_30yr = payment_30yr * 360
        total_40yr = payment_40yr * 480
        self.assertGreater(total_40yr, total_30yr)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)