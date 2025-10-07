import React from 'react';
import { CapitalExpenditureCalculator } from '../CapitalExpenditureCalculator';
import { useToast } from '@/components/ui/use-toast';

interface CapitalExpenditureTabProps {
  propertyData?: any;
}

export function CapitalExpenditureTab({ propertyData }: CapitalExpenditureTabProps) {
  const { toast } = useToast();

  const handleSave = (items: any[], total: number) => {
    // Here you could save to database or local storage
    console.log('Saving capital expenditure plan:', { items, total });

    toast({
      title: "Capital Expenditure Plan Saved",
      description: `Total budget: $${total.toLocaleString()}`,
    });

    // Save to localStorage for persistence
    const savedPlans = JSON.parse(localStorage.getItem('capitalExpenditurePlans') || '{}');
    const propertyId = propertyData?.parcel_id || propertyData?.folio || 'unknown';

    savedPlans[propertyId] = {
      propertyAddress: propertyData?.address,
      items,
      total,
      savedAt: new Date().toISOString()
    };

    localStorage.setItem('capitalExpenditurePlans', JSON.stringify(savedPlans));
  };

  return (
    <div id="capital-expenditure-tab-1" className="space-y-6">
      <div id="capital-tab-header-1" className="mb-6">
        <h2 className="text-2xl font-semibold mb-2">Renovation & Capital Expenditure Planning</h2>
        <p className="text-muted-foreground">
          Plan your property improvements and calculate the total investment needed.
          Select items, adjust quantities, and customize costs to build your renovation budget.
        </p>
      </div>

      <CapitalExpenditureCalculator
        propertyData={propertyData}
        onSave={handleSave}
      />

      {/* Property-specific recommendations */}
      {propertyData && (
        <div id="capital-recommendations-1" className="mt-8 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-lg font-medium mb-2 text-blue-900">Recommended Improvements</h3>
          <div className="space-y-2 text-sm text-blue-800">
            {getPropertyRecommendations(propertyData).map((rec, index) => (
              <div key={index} className="flex items-start gap-2">
                <span className="text-blue-600">•</span>
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function getPropertyRecommendations(propertyData: any): string[] {
  const recommendations: string[] = [];
  const yearBuilt = propertyData?.characteristics?.year_built ||
                   propertyData?.characteristics?.effective_year_built;
  const currentYear = new Date().getFullYear();
  const age = yearBuilt ? currentYear - yearBuilt : 0;

  // Age-based recommendations
  if (age > 30) {
    recommendations.push("Consider updating electrical panel and wiring (30+ year old property)");
    recommendations.push("Inspect and potentially replace plumbing if original");
  }
  if (age > 20) {
    recommendations.push("HVAC system may need replacement if original (typical 15-20 year lifespan)");
    recommendations.push("Roof inspection recommended - may need replacement soon");
  }
  if (age > 15) {
    recommendations.push("Water heater replacement if original (typical 10-15 year lifespan)");
    recommendations.push("Consider updating kitchen appliances for energy efficiency");
  }
  if (age > 10) {
    recommendations.push("Interior paint refresh can significantly improve appeal");
    recommendations.push("Flooring may benefit from updates in high-traffic areas");
  }

  // Property type based recommendations
  const useCode = propertyData?.characteristics?.use_code || '';
  if (useCode === '001') { // Single Family
    recommendations.push("Curb appeal improvements (landscaping, exterior paint) add significant value");
    recommendations.push("Kitchen and bathroom updates typically offer best ROI for single-family homes");
  }
  if (useCode === '004') { // Condo
    recommendations.push("Focus on interior improvements - kitchen, bathrooms, flooring");
    recommendations.push("Consider impact windows if in hurricane-prone area");
  }

  // Market-based recommendations
  const lastSalePrice = propertyData?.sales?.last_sale_price || 0;
  const marketValue = propertyData?.values?.market_value || 0;
  if (marketValue > lastSalePrice * 1.3) {
    recommendations.push("Property has appreciated significantly - strategic improvements could maximize value");
  }

  // Always recommend
  if (recommendations.length === 0) {
    recommendations.push("Regular maintenance and updates help preserve property value");
    recommendations.push("Energy-efficient upgrades can reduce operating costs and increase appeal");
  }

  return recommendations.slice(0, 5); // Limit to 5 recommendations
}