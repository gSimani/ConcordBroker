# Capital Planning System - Complete Implementation

## Overview

The ConcordBroker Capital Planning System is a comprehensive solution for real estate investors to plan, track, and manage capital expenses across different property types. The system automatically adapts to property characteristics based on DOR (Department of Revenue) use codes and provides intelligent financial planning tools.

## Features Implemented

### ✅ 1. Editable Capital Planning Components
- **Interactive Expense Cards**: Each capital expense item can be edited in-place
- **Edit Dialog**: Full-featured edit modal for modifying:
  - Category name
  - Lifecycle years
  - Last replaced year
  - Condition (good/fair/poor)
  - Priority (high/medium/low)
  - Cost per square foot
  - Cost per unit
- **Add Custom Expenses**: Users can add property-specific expenses not in templates
- **Delete Functionality**: Remove expenses that don't apply to the property

### ✅ 2. Property-Type-Specific Templates
The system includes specialized templates for:

#### **Residential Properties** (DOR Codes 001-008)
- Roof (20-year lifecycle, $8/sqft)
- HVAC System ($7,000, 15 years)
- Exterior Paint (10 years, $3/sqft)
- Flooring (15 years, $5/sqft)
- Plumbing ($10,000, 30 years)
- Electrical ($8,000, 30 years)
- Windows ($15,000, 20 years)
- Appliances ($5,000, 10 years)

#### **Commercial Properties** (DOR Codes 003, 011-019)
- Commercial Roof System (25 years, $12/sqft)
- Commercial HVAC ($25,000, 20 years)
- Parking Lot/Asphalt (15 years, $4/sqft)
- Elevator System ($50,000, 25 years)
- Fire Safety Systems ($20,000, 20 years)
- Building Facade (30 years, $15/sqft)
- Commercial Plumbing ($30,000, 35 years)
- Electrical Panel/System ($25,000, 35 years)

#### **Industrial Properties** (DOR Codes 041-048)
- Industrial Roof (30 years, $15/sqft)
- Industrial HVAC/Ventilation ($50,000, 25 years)
- Loading Dock Equipment ($30,000, 20 years)
- Crane/Hoist System ($100,000, 30 years)
- Epoxy Floor Coating (10 years, $6/sqft)
- High-Voltage Electrical ($75,000, 40 years)

### ✅ 3. Sub-Category Support for Specialized Uses

#### **Hotels/Motels** (DOR Code 039)
- Hotel Roof (20 years, $10/sqft)
- Guest Room HVAC Units ($35,000, 15 years)
- Passenger Elevators ($60,000, 25 years)
- Pool & Spa Equipment ($25,000, 15 years)
- Furniture, Fixtures & Equipment ($150,000, 7 years)
- Guest Room Carpeting (7 years, $8/sqft)

#### **Churches** (DOR Code 071)
- Church Roof (25 years, $12/sqft)
- Sanctuary HVAC ($40,000, 20 years)
- Audio/Visual System ($50,000, 10 years)
- Pews/Seating ($30,000, 30 years)
- Parking Lot (15 years, $4/sqft)

### ✅ 4. Financial Analysis Metrics

The system calculates and displays:

#### **Key Metrics**
- **Property Age**: Calculated from year built
- **Total Reserves Needed**: Sum of all expenses within planning period
- **Annual Reserve Contribution**: Total reserves / planning years
- **Monthly Reserve Contribution**: Annual / 12

#### **Urgency Classification**
- **Immediate (0-2 years)**: Red badge, high priority
- **Soon (3-5 years)**: Yellow badge, medium priority
- **Future (6+ years)**: Green badge, low priority

#### **Planning Timeframes**
- 5-year plan
- 10-year plan
- 15-year plan (database support)
- 20-year plan (database support)

#### **Reserve Fund Analysis**
- Current balance tracking
- Shortfall calculations
- Recommended monthly contributions
- Transaction history
- Balance projections

### ✅ 5. Database Schema

**Tables Created:**

1. **capital_expense_templates**
   - Predefined templates by property type
   - DOR use code mapping
   - Cost structures (per sqft or per unit)
   - Lifecycle and priority data

2. **property_capital_plans**
   - Master plan per property (parcel_id + county unique)
   - Planning timeframe
   - Total reserves needed
   - Monthly/annual contributions
   - Current reserve balance

3. **capital_expense_items**
   - Individual expense line items
   - Links to templates or custom entries
   - Replacement year calculations
   - Status tracking (planned/in_progress/completed/deferred/cancelled)
   - Condition and urgency auto-calculation

4. **capital_expense_history**
   - Audit trail of all changes
   - Previous vs. new values
   - Change reasons and timestamps

5. **reserve_fund_transactions**
   - Deposits and withdrawals
   - Running balance tracking
   - Links to related expenses

**Triggers Implemented:**
- Auto-update timestamps on all tables
- Auto-calculate remaining life and urgency
- Auto-update reserve fund balance on transactions

**Views Created:**
- `v_property_capital_plans_complete`: Plans with aggregated metrics
- `v_upcoming_capital_expenses`: Next 10 years of expenses by property

### ✅ 6. Save/Load Functionality

**CapitalPlanningService API:**

```typescript
// Get or create plan
getOrCreateCapitalPlan(parcelId, county, propertyData)

// Update plan
updateCapitalPlan(planId, updates)

// Get expense items
getExpenseItems(capitalPlanId)

// Create items from templates
createExpenseItemsFromTemplates(capitalPlanId, templates, propertyData)

// Create custom item
createCustomExpenseItem(item)

// Update item
updateExpenseItem(itemId, updates)

// Delete item
deleteExpenseItem(itemId)

// Get transactions
getReserveTransactions(capitalPlanId)

// Add transaction
addReserveTransaction(transaction)

// Save complete plan (atomic upsert)
saveCompletePlan(parcelId, county, planData, expenseItems)

// Generate report
generateReport(parcelId, county)
```

## Component Architecture

### Main Component: `CapitalPlanningTabEnhanced.tsx`

**Features:**
- Property type detection via DOR use codes
- Automatic template selection
- Three view modes (tabs):
  1. **Overview**: Expense categories and reserve fund analysis
  2. **Timeline**: Visual timeline of all expenses
  3. **Calculator**: Detailed calculations and breakdown

**State Management:**
- Local state for UI interactions
- Supabase integration for persistence
- Real-time expense calculations

### Dialog Components

1. **ExpenseEditDialog**
   - Inline editing of existing expenses
   - All fields editable
   - Validation and error handling

2. **AddExpenseDialog**
   - Create custom expense categories
   - Required fields: category name, lifecycle, cost
   - Optional fields: icon, priority, condition

## Usage

### Basic Usage

```tsx
import { CapitalPlanningTabEnhanced } from '@/components/property/tabs/CapitalPlanningTabEnhanced';

<CapitalPlanningTabEnhanced propertyData={propertyData} />
```

### Property Data Structure Expected

```typescript
{
  bcpaData: {
    dor_uc: string,           // DOR use code (e.g., "001", "039", "071")
    property_use: string,      // Alternative property use field
    year_built: number,        // Year property was built
    total_sqft: number,        // Total square footage
    just_value: number,        // Just/market value
    assessed_value: number,    // Assessed value
    parcel_id: string,         // Unique property identifier
    county: string             // County name
  }
}
```

### Programmatic Save Example

```typescript
import CapitalPlanningService from '@/services/capitalPlanningService';

// Save complete plan
const result = await CapitalPlanningService.saveCompletePlan(
  '402101327008',
  'MIAMI-DADE',
  {
    property_type: 'RESIDENTIAL',
    dor_use_code: '001',
    planning_timeframe: 10,
    property_age: 35,
    property_sqft: 2000,
    property_value: 450000
  },
  [
    {
      category: 'Custom Pool Heater',
      icon: 'Droplets',
      lifecycle_years: 12,
      cost_per_unit: 8500,
      estimated_cost: 8500,
      priority: 'medium',
      condition: 'fair',
      is_custom: true
    }
  ]
);
```

## Database Deployment

### Run Migration

```bash
# Connect to Supabase
supabase db push

# Or run SQL directly in Supabase SQL Editor
# Copy contents of: supabase/migrations/20250126_create_capital_planning_tables.sql
```

### Verify Installation

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'capital%';

-- Check templates loaded
SELECT property_type, COUNT(*)
FROM capital_expense_templates
GROUP BY property_type;

-- Expected result:
-- RESIDENTIAL: 8
-- COMMERCIAL: 6
-- INDUSTRIAL: 4
-- HOTEL: 5
-- CHURCH: 4
```

## Property Type Mapping

The system uses Florida DOR use codes to determine property types:

| DOR Code | Property Type | Template Used |
|----------|---------------|---------------|
| 000-009 | Residential | RESIDENTIAL |
| 003 | Multi-Family 10+ | COMMERCIAL |
| 010-039 | Commercial | COMMERCIAL |
| 039 | Hotel/Motel | HOTEL |
| 040-049 | Industrial | INDUSTRIAL |
| 050-069 | Agricultural | RESIDENTIAL (basic) |
| 070-079 | Institutional | varies by code |
| 071 | Church | CHURCH |
| 080-089 | Governmental | COMMERCIAL |

## Financial Calculations

### Cost Calculation Logic

```typescript
// For square-foot based costs
estimatedCost = costPerSqFt * totalSqFt

// For unit-based costs
estimatedCost = costPerUnit

// Replacement year
replacementYear = lastReplacedYear + lifecycleYears

// Remaining life
remainingLife = lifecycleYears - (currentYear - lastReplacedYear)
```

### Urgency Determination

```typescript
if (remainingLife <= 2) urgency = 'immediate'
else if (remainingLife <= 5) urgency = 'soon'
else urgency = 'future'
```

### Reserve Contributions

```typescript
totalReserves = sum(allExpenses.withinPlanningPeriod)
annualContribution = totalReserves / planningYears
monthlyContribution = annualContribution / 12
```

## Best Practices

### For Different Property Types

1. **Residential**: Focus on roof, HVAC, and major systems
2. **Commercial**: Include parking, elevators, and life safety
3. **Industrial**: Consider specialized equipment and heavy infrastructure
4. **Hotels**: Plan for high FF&E turnover (7-year cycles)
5. **Churches**: Budget for A/V upgrades and sanctuary-specific needs

### Reserve Fund Management

1. Start with 5-year plan for new properties
2. Adjust to 10-year once reserve balance is established
3. Review and update annually
4. Track actual costs vs. estimates
5. Adjust future estimates based on actual expenses

### Customization Guidelines

1. Use templates as starting point
2. Adjust lifecycles based on actual property condition
3. Update costs based on local market rates
4. Add property-specific items (pools, special equipment)
5. Document all custom changes in notes field

## Integration Points

### With Investment Analysis Tab

Capital planning feeds into:
- Operating expense calculations
- Cash flow projections
- ROI analysis
- Property valuation models

### With Property Profile

Displays in property tabs alongside:
- Core property info
- Tax data
- Sales history
- Sunbiz entity info

## Future Enhancements

Planned features:
- [ ] Export to PDF/Excel
- [ ] Generate professional reports
- [ ] Email reserve fund reminders
- [ ] Vendor integration for quotes
- [ ] Historical cost benchmarking
- [ ] Multi-property portfolio planning
- [ ] Reserve fund investment tracking
- [ ] Tax benefit calculations for capital improvements

## Support & Documentation

- Database schema: `supabase/migrations/20250126_create_capital_planning_tables.sql`
- Service layer: `apps/web/src/services/capitalPlanningService.ts`
- Component: `apps/web/src/components/property/tabs/CapitalPlanningTabEnhanced.tsx`
- DOR codes: `apps/web/src/lib/dorUseCodes.ts`

## Testing Checklist

- [x] Residential property (DOR 001): Standard template loads
- [x] Commercial property (DOR 011): Office template loads
- [x] Hotel property (DOR 039): Hospitality template loads
- [x] Church property (DOR 071): Institutional template loads
- [x] Industrial property (DOR 041): Manufacturing template loads
- [x] Edit expense: Changes persist
- [x] Add custom expense: New items save
- [x] Delete expense: Items removed
- [x] 5-year vs 10-year plan: Calculations update
- [x] Save to database: Full plan persists
- [x] Load from database: Existing plans display
- [x] Reserve transactions: Balance updates correctly
- [x] Timeline view: All expenses show chronologically
- [x] Calculator view: Breakdown displays correctly

---

## Summary

The Capital Planning System is now **fully functional** with:
- ✅ Editable expense items
- ✅ Property-type-specific templates (Residential, Commercial, Industrial, Hotel, Church)
- ✅ Sub-category specialization
- ✅ Comprehensive financial metrics
- ✅ Complete database schema with triggers and views
- ✅ Full save/load/update functionality
- ✅ Professional UI with three view modes
- ✅ Integrated into property profile pages

All components are production-ready and tested for accuracy.
