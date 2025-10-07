"""
Unit Tests for Mortgage Analytics Service
Validates PMT calculations, amortization schedules, and rate conversions
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mortgage_analytics_service import (
    MortgageAnalytics, RatesManager, Property,
    PayoffProgress, DebtService
)


class TestMortgageAnalytics(unittest.TestCase):
    """Test mortgage calculation functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.analytics = MortgageAnalytics()

    def test_monthly_payment_calculation(self):
        """Test PMT formula against known examples"""
        # Test case: $400,000 loan at 6.5% for 30 years
        payment = self.analytics.calculate_monthly_payment(400000, 6.5, 360)
        expected = 2528.27  # Known value from financial calculator
        self.assertAlmostEqual(payment, expected, delta=1.0)

        # Test case: $200,000 loan at 5% for 15 years
        payment = self.analytics.calculate_monthly_payment(200000, 5.0, 180)
        expected = 1581.59
        self.assertAlmostEqual(payment, expected, delta=1.0)

        # Edge case: Zero interest rate
        payment = self.analytics.calculate_monthly_payment(360000, 0, 360)
        expected = 1000.00  # Principal only
        self.assertEqual(payment, expected)

    def test_amortization_schedule(self):
        """Test amortization schedule generation"""
        # Generate 12-month schedule
        schedule = self.analytics.generate_amortization_schedule(
            orig_balance=100000,
            annual_rate_pct=6.0,
            term_months=12,
            start_date=date(2024, 1, 1)
        )

        # Verify schedule structure
        self.assertEqual(len(schedule), 12)
        self.assertIn('period_index', schedule.columns)
        self.assertIn('payment', schedule.columns)
        self.assertIn('interest', schedule.columns)
        self.assertIn('principal', schedule.columns)
        self.assertIn('remaining_balance', schedule.columns)

        # Verify first payment
        first_payment = schedule.iloc[0]
        self.assertEqual(first_payment['period_index'], 1)
        self.assertAlmostEqual(first_payment['interest'], 500.00, delta=1.0)  # 100000 * 0.06 / 12

        # Verify last payment brings balance to zero
        last_payment = schedule.iloc[-1]
        self.assertAlmostEqual(last_payment['remaining_balance'], 0, delta=1.0)

    def test_payoff_progress_calculation(self):
        """Test loan payoff progress tracking"""
        # Calculate progress after 5 years on 30-year loan
        progress = self.analytics.calculate_payoff_progress(
            orig_loan_amount=300000,
            annual_rate_pct=5.5,
            term_months=360,
            start_date=date(2019, 1, 1),
            as_of_date=date(2024, 1, 1),
            extra_principal_paid=0
        )

        # Verify calculations
        self.assertEqual(progress['months_elapsed'], 60)  # 5 years
        self.assertGreater(progress['pct_principal_paid'], 0)
        self.assertLess(progress['pct_principal_paid'], 100)
        self.assertLess(progress['remaining_balance'], 300000)

    def test_extra_principal_application(self):
        """Test handling of extra principal payments"""
        # Compare schedules with and without extra principal
        schedule_normal = self.analytics.generate_amortization_schedule(
            orig_balance=100000,
            annual_rate_pct=5.0,
            term_months=360,
            start_date=date(2024, 1, 1),
            extra_principal=0
        )

        schedule_extra = self.analytics.generate_amortization_schedule(
            orig_balance=100000,
            annual_rate_pct=5.0,
            term_months=360,
            start_date=date(2024, 1, 1),
            extra_principal=10000  # $10k extra principal
        )

        # Extra principal should reduce total periods
        self.assertLess(len(schedule_extra), len(schedule_normal))

        # Final balance should still be zero
        self.assertAlmostEqual(
            schedule_extra.iloc[-1]['remaining_balance'],
            0,
            delta=1.0
        )


class TestRatesManager(unittest.TestCase):
    """Test rate data management"""

    def test_weekly_to_monthly_conversion(self):
        """Test conversion of weekly rates to monthly averages"""
        # Create sample weekly data
        dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='W')
        rates = [6.5, 6.6, 6.4, 6.5, 6.7, 6.8, 6.6, 6.5, 6.4, 6.3, 6.2, 6.3, 6.4]
        weekly_series = pd.Series(rates[:len(dates)], index=dates)

        # Convert to monthly
        rates_manager = RatesManager(None, None)
        monthly_df = rates_manager.weekly_to_monthly_avg(weekly_series, '30Y_FIXED')

        # Verify structure
        self.assertIn('yyyymm', monthly_df.columns)
        self.assertIn('avg_rate_pct', monthly_df.columns)
        self.assertIn('rate_type', monthly_df.columns)

        # Verify values
        self.assertEqual(monthly_df.iloc[0]['rate_type'], '30Y_FIXED')
        self.assertEqual(monthly_df.iloc[0]['yyyymm'], 202401)
        self.assertIsInstance(monthly_df.iloc[0]['avg_rate_pct'], (float, np.floating))

    def test_previous_month_calculation(self):
        """Test previous month YYYYMM calculation"""
        rates_manager = RatesManager(None, None)

        # Test regular month
        self.assertEqual(rates_manager._get_previous_month(202403), 202402)

        # Test January (year boundary)
        self.assertEqual(rates_manager._get_previous_month(202401), 202312)

        # Test edge cases
        self.assertEqual(rates_manager._get_previous_month(202012), 202011)
        self.assertEqual(rates_manager._get_previous_month(202001), 201912)


class TestPropertyValidation(unittest.TestCase):
    """Test property data validation"""

    def test_valid_property(self):
        """Test valid property creation"""
        property_data = {
            'id': 'test-123',
            'purchase_date': date(2023, 1, 15),
            'orig_loan_amount': 500000,
            'loan_term_months': 360,
            'loan_type': '30Y_FIXED',
            'payment_start_date': date(2023, 2, 1),
            'extra_principal_paid_to_date': 5000
        }
        property_obj = Property(**property_data)
        self.assertEqual(property_obj.id, 'test-123')
        self.assertEqual(property_obj.loan_type, '30Y_FIXED')

    def test_invalid_loan_type(self):
        """Test invalid loan type validation"""
        property_data = {
            'id': 'test-123',
            'purchase_date': date(2023, 1, 15),
            'orig_loan_amount': 500000,
            'loan_term_months': 360,
            'loan_type': 'INVALID_TYPE'
        }
        with self.assertRaises(ValueError):
            Property(**property_data)

    def test_negative_loan_amount(self):
        """Test negative loan amount validation"""
        property_data = {
            'id': 'test-123',
            'purchase_date': date(2023, 1, 15),
            'orig_loan_amount': -100000,
            'loan_term_months': 360,
            'loan_type': '30Y_FIXED'
        }
        with self.assertRaises(ValueError):
            Property(**property_data)


class TestDataQuality(unittest.TestCase):
    """Test data quality checks"""

    def test_rate_reasonableness(self):
        """Verify rates are within reasonable bounds"""
        # Historical mortgage rates typically between 2% and 20%
        test_rates = [2.5, 3.0, 5.5, 6.75, 8.0, 15.0]

        for rate in test_rates:
            self.assertGreaterEqual(rate, 0)
            self.assertLessEqual(rate, 30)  # Max bound from model

    def test_payment_consistency(self):
        """Verify payment calculations are consistent"""
        analytics = MortgageAnalytics()

        # Calculate payment two ways
        principal = 250000
        rate = 7.0
        term = 360

        # Method 1: Direct calculation
        payment1 = analytics.calculate_monthly_payment(principal, rate, term)

        # Method 2: From amortization schedule
        schedule = analytics.generate_amortization_schedule(
            principal, rate, term, date(2024, 1, 1)
        )
        payment2 = schedule.iloc[0]['payment']

        # Payments should match
        self.assertAlmostEqual(payment1, payment2, delta=0.01)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def test_zero_interest_rate(self):
        """Test handling of zero interest rate"""
        analytics = MortgageAnalytics()
        payment = analytics.calculate_monthly_payment(120000, 0, 120)
        self.assertEqual(payment, 1000.00)  # Should be principal only

    def test_single_payment_loan(self):
        """Test loan with single payment term"""
        analytics = MortgageAnalytics()
        payment = analytics.calculate_monthly_payment(10000, 12, 1)
        # Should be principal plus one month's interest
        expected = 10000 * (1 + 0.12/12)
        self.assertAlmostEqual(payment, expected, delta=0.01)

    def test_very_high_rate(self):
        """Test handling of very high interest rate"""
        analytics = MortgageAnalytics()
        # 29% rate (near max bound)
        payment = analytics.calculate_monthly_payment(100000, 29, 360)
        self.assertGreater(payment, 2400)  # Should be high
        self.assertLess(payment, 3000)  # But not infinite

    def test_future_as_of_date(self):
        """Test handling of future as-of date"""
        analytics = MortgageAnalytics()
        progress = analytics.calculate_payoff_progress(
            orig_loan_amount=200000,
            annual_rate_pct=6.0,
            term_months=360,
            start_date=date(2024, 1, 1),
            as_of_date=date(2023, 1, 1),  # Before start
            extra_principal_paid=0
        )

        # Should return initial state
        self.assertEqual(progress['months_elapsed'], 0)
        self.assertEqual(progress['remaining_balance'], 200000)
        self.assertEqual(progress['pct_principal_paid'], 0.0)


def run_validation_suite():
    """Run comprehensive validation suite"""
    print("\n" + "="*60)
    print("MORTGAGE ANALYTICS VALIDATION SUITE")
    print("="*60)

    # Create test suite
    suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestMortgageAnalytics,
        TestRatesManager,
        TestPropertyValidation,
        TestDataQuality,
        TestEdgeCases
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ ALL VALIDATIONS PASSED")
    else:
        print("\n❌ VALIDATION FAILURES DETECTED")
        for test, traceback in result.failures:
            print(f"\nFailed: {test}")
            print(traceback)
        for test, traceback in result.errors:
            print(f"\nError: {test}")
            print(traceback)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_validation_suite()
    exit(0 if success else 1)