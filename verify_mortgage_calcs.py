import math

property_price = 628040

scenarios = {
    'Conservative': {
        'down_payment_pct': 25,
        'rate': 8.0,
        'term_years': 30
    },
    'Current': {
        'down_payment_pct': 25,
        'rate': 7.5,
        'term_years': 30
    },
    'Aggressive': {
        'down_payment_pct': 20,
        'rate': 7.25,
        'term_years': 30
    }
}

def calculate_monthly_payment(principal, annual_rate, term_months):
    if annual_rate == 0:
        return principal / term_months
    monthly_rate = annual_rate / 100.0 / 12.0
    payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
    return round(payment, 2)

print('Property Price: $628,040')
print('='*60)

for name, params in scenarios.items():
    down_payment = property_price * params['down_payment_pct'] / 100
    loan_amount = property_price - down_payment
    term_months = params['term_years'] * 12

    monthly_payment = calculate_monthly_payment(loan_amount, params['rate'], term_months)

    print(f'\n{name} Scenario:')
    print(f'  Down Payment: {params["down_payment_pct"]}% = ${down_payment:,.0f}')
    print(f'  Loan Amount: ${loan_amount:,.0f}')
    print(f'  Interest Rate: {params["rate"]}%')
    print(f'  Term: {params["term_years"]} years')
    print(f'  Calculated Monthly Payment: ${monthly_payment:,.2f}')

    # Show what was displayed in HTML
    displayed = {'Conservative': 3456, 'Current': 3294, 'Aggressive': 3427}
    print(f'  Displayed in HTML: ${displayed[name]:,}')

    # Calculate difference
    difference = displayed[name] - monthly_payment
    percent_error = abs(difference / monthly_payment * 100)

    if abs(difference) > 1:
        print(f'  ERROR: Off by ${abs(difference):.2f} ({percent_error:.1f}%)')
    else:
        print(f'  CORRECT: Within rounding tolerance')