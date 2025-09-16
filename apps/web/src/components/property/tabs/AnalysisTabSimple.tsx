import { PropertyData } from '@/hooks/usePropertyData'
import { TrendingUp, DollarSign, Calculator, Home, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface AnalysisTabProps {
  data: PropertyData
}

export function AnalysisTabSimple({ data }: AnalysisTabProps) {
  // Safety check
  if (!data) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
              <p className="text-gray-600">Loading property analysis...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Extract data with defaults
  const marketValue = parseFloat(data?.bcpaData?.market_value || '0')
  const assessedValue = parseFloat(data?.bcpaData?.assessed_value || '0')
  const livingArea = parseFloat(data?.bcpaData?.living_area || '0')
  const yearBuilt = parseInt(data?.bcpaData?.year_built || '0')
  const lastSalePrice = parseFloat(data?.lastSale?.sale_price || '0')
  const investmentScore = data?.investmentScore || 0

  // Simple calculations
  const pricePerSqft = livingArea > 0 ? Math.round(marketValue / livingArea) : 0
  const propertyAge = new Date().getFullYear() - yearBuilt
  const capRate = marketValue > 0 ? ((marketValue * 0.08 * 12) / marketValue * 100).toFixed(1) : '0'

  return (
    <div className="space-y-6">
      {/* Investment Score Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Investment Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Investment Score */}
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Investment Score</div>
              <div className={`text-3xl font-bold ${
                investmentScore >= 80 ? 'text-green-600' :
                investmentScore >= 60 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {investmentScore || 'N/A'}
              </div>
              <div className="text-xs text-gray-500">out of 100</div>
            </div>

            {/* Market Value */}
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Market Value</div>
              <div className="text-2xl font-bold text-blue-600">
                ${marketValue.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">current estimate</div>
            </div>

            {/* Price per SqFt */}
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Price/SqFt</div>
              <div className="text-2xl font-bold text-purple-600">
                ${pricePerSqft}
              </div>
              <div className="text-xs text-gray-500">market rate</div>
            </div>

            {/* Cap Rate */}
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Est. Cap Rate</div>
              <div className="text-2xl font-bold text-green-600">
                {capRate}%
              </div>
              <div className="text-xs text-gray-500">annual return</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Property Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="w-5 h-5" />
            Property Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">Living Area</span>
              <span className="font-semibold">{livingArea.toLocaleString()} sq ft</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">Year Built</span>
              <span className="font-semibold">{yearBuilt || 'N/A'} ({propertyAge} years old)</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">Assessed Value</span>
              <span className="font-semibold">${assessedValue.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">Last Sale Price</span>
              <span className="font-semibold">${lastSalePrice.toLocaleString()}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Investment Recommendation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Home className="w-5 h-5" />
            Investment Recommendation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`p-4 rounded-lg ${
            investmentScore >= 80 ? 'bg-green-50 border border-green-200' :
            investmentScore >= 60 ? 'bg-yellow-50 border border-yellow-200' :
            'bg-red-50 border border-red-200'
          }`}>
            <h4 className={`font-semibold mb-2 ${
              investmentScore >= 80 ? 'text-green-800' :
              investmentScore >= 60 ? 'text-yellow-800' :
              'text-red-800'
            }`}>
              {investmentScore >= 80 ? 'Strong Investment Opportunity' :
               investmentScore >= 60 ? 'Moderate Investment Potential' :
               'Consider Alternative Options'}
            </h4>
            <p className="text-sm text-gray-700">
              {investmentScore >= 80 ? 
                'This property shows strong investment potential with good market value, reasonable price per square foot, and solid fundamentals.' :
               investmentScore >= 60 ?
                'This property has moderate investment potential. Consider additional due diligence and market comparisons before proceeding.' :
                'This property may not offer the best investment opportunity. Consider exploring other options in the market.'}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}