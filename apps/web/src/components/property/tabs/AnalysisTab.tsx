import { PropertyData } from '@/hooks/usePropertyData'
import { TrendingUp, TrendingDown, Calculator, DollarSign, Percent, Target, BarChart3, AlertTriangle, CheckCircle2, Star, Eye, PieChart, Activity, Clock, Home, Search } from 'lucide-react'
import { motion } from 'framer-motion'

interface AnalysisTabProps {
  data: PropertyData
  sqlAlchemyData?: any
  dataServiceHealthy?: boolean
}

export function AnalysisTab({ data }: AnalysisTabProps) {
  // Add null check and provide defaults
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <p className="text-gray-600">No property data available for analysis</p>
        </div>
      </div>
    )
  }

  const { 
    bcpaData = {}, 
    lastSale = {}, 
    sdfData = [], 
    investmentScore = 0, 
    totalNavAssessment = 0, 
    isInCDD = false 
  } = data || {}

  // Calculate investment metrics
  const calculateMetrics = () => {
    const salePrice = parseFloat(lastSale?.sale_price || '0')
    const marketValue = parseFloat(bcpaData?.market_value || '0')
    const livingArea = parseFloat(bcpaData?.living_area || '0')
    const yearBuilt = parseInt(bcpaData?.year_built || '0')
    const currentYear = new Date().getFullYear()

    // Estimated rental income (rough calculation based on market value)
    const monthlyRent = marketValue > 0 ? Math.round(marketValue * 0.008) : 0 // 0.8% of market value
    const annualRent = monthlyRent * 12

    // Cap rate calculation (if we had rental data, this would be more accurate)
    const capRate = marketValue > 0 ? ((annualRent - totalNavAssessment) / marketValue) * 100 : 0

    // Price per square foot
    const pricePerSqft = livingArea > 0 && salePrice > 0 ? salePrice / livingArea : 0

    // Property age - handle NULL year_built
    const propertyAge = yearBuilt > 0 ? currentYear - yearBuilt : null
    
    // Appreciation potential (based on recent sales if available)
    let appreciationTrend = 0
    if (sdfData.length >= 2) {
      const recentSale = parseFloat(sdfData[0]?.sale_price || '0')
      const previousSale = parseFloat(sdfData[1]?.sale_price || '0')
      if (recentSale > 0 && previousSale > 0) {
        appreciationTrend = ((recentSale - previousSale) / previousSale) * 100
      }
    }
    
    return {
      monthlyRent,
      annualRent,
      capRate,
      pricePerSqft,
      propertyAge,
      appreciationTrend,
      marketValue,
      salePrice
    }
  }

  const metrics = calculateMetrics()
  
  // Debug logging
  console.log('AnalysisTab - Data received:', data)
  console.log('AnalysisTab - Metrics calculated:', metrics)
  console.log('AnalysisTab - Investment Score:', investmentScore)

  const getScoreColor = (score: number) => {
    return 'text-navy'
  }

  const getProgressColor = (score: number) => {
    return 'bg-navy'
  }

  return (
    <div className="space-y-8">
      {/* Executive Investment Score */}
      <div className="card-executive animate-elegant">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center justify-between">
            <div className="flex items-center">
              <div className="p-2 rounded-lg mr-3" style={{background: '#2c3e50'}}>
                <Target className="w-4 h-4 text-white" />
              </div>
              Investment Analysis
            </div>
            <div className="text-center p-3 rounded-lg" style={{background: 'linear-gradient(135deg, #f4e5c2 0%, #fff 100%)'}}>
              <div className={`text-3xl font-light mb-1 text-navy`}>
                {investmentScore}/100
              </div>
              <p className="text-xs uppercase tracking-wider text-gray-elegant">Investment Score</p>
            </div>
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Comprehensive algorithmic analysis of investment potential</p>
        </div>
        <div className="pt-8">
          {/* Score Visualization */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-3">
              <span className="elegant-text text-navy font-medium">Overall Investment Rating</span>
              <span className={`font-light text-2xl text-navy`}>
                {investmentScore >= 80 ? 'Excellent' : investmentScore >= 60 ? 'Good' : 'Poor'}
              </span>
            </div>
            <div className="relative h-3 bg-gray-light rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${investmentScore}%` }}
                transition={{ duration: 1.5, ease: "easeOut" }}
                className={`h-full rounded-full`}
                style={{ background: '#2c3e50' }}
              />
            </div>
          </div>
          
          {/* Score Factor Analysis */}
          <div className="grid md:grid-cols-2 gap-8">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-6 rounded-lg border border-gray-100"
            >
              <h4 className="font-medium text-navy mb-4 flex items-center">
                <CheckCircle2 className="w-5 h-5 mr-2" />
                Investment Strengths
              </h4>
              <ul className="space-y-3 text-sm">
                {lastSale?.is_distressed && (
                  <li className="flex items-center text-navy">
                    <Star className="w-4 h-4 mr-2" />
                    <span>Distressed property opportunity (+15 points)</span>
                  </li>
                )}
                {lastSale?.is_bank_sale && (
                  <li className="flex items-center text-navy">
                    <Star className="w-4 h-4 mr-2" />
                    <span>Bank-owned/REO sale (+10 points)</span>
                  </li>
                )}
                {bcpaData?.property_use_code === 'SINGLE FAMILY' && (
                  <li className="flex items-center text-navy">
                    <Home className="w-4 h-4 mr-2" />
                    <span>Single family residential (+5 points)</span>
                  </li>
                )}
                {metrics.pricePerSqft > 0 && metrics.pricePerSqft < 200 && (
                  <li className="flex items-center text-navy">
                    <Calculator className="w-4 h-4 mr-2" />
                    <span>Below-market price per sqft (+5 points)</span>
                  </li>
                )}
                {metrics.capRate > 7 && (
                  <li className="flex items-center text-navy">
                    <Percent className="w-4 h-4 mr-2" />
                    <span>Strong cap rate potential (+10 points)</span>
                  </li>
                )}
              </ul>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-6 rounded-lg border border-gray-100"
            >
              <h4 className="font-medium text-navy mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2" />
                Risk Considerations
              </h4>
              <ul className="space-y-3 text-sm">
                {isInCDD && (
                  <li className="flex items-center text-navy">
                    <AlertTriangle className="w-4 h-4 mr-2" />
                    <span>Located in CDD district (-5 points)</span>
                  </li>
                )}
                {totalNavAssessment > 5000 && (
                  <li className="flex items-center text-navy">
                    <AlertTriangle className="w-4 h-4 mr-2" />
                    <span>High special assessments (-10 points)</span>
                  </li>
                )}
                {metrics.pricePerSqft > 400 && (
                  <li className="flex items-center text-navy">
                    <Calculator className="w-4 h-4 mr-2" />
                    <span>Above-market price per sqft (-5 points)</span>
                  </li>
                )}
                {metrics.propertyAge !== null && metrics.propertyAge > 50 && (
                  <li className="flex items-center text-navy">
                    <Clock className="w-4 h-4 mr-2" />
                    <span>Older property requiring updates (-5 points)</span>
                  </li>
                )}
                {(!lastSale?.is_distressed && !lastSale?.is_bank_sale && totalNavAssessment === 0 && metrics.pricePerSqft <= 400 && (metrics.propertyAge === null || metrics.propertyAge <= 50)) && (
                  <li className="flex items-center text-gray-600">
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    <span>No significant risk factors identified</span>
                  </li>
                )}
              </ul>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Financial Metrics Dashboard */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-executive p-6"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs uppercase tracking-wider text-gray-elegant">Est. Monthly Rent</span>
            <DollarSign className="w-5 h-5 text-navy" />
          </div>
          <p className="text-3xl font-light text-navy mb-1">
            ${metrics.monthlyRent.toLocaleString()}
          </p>
          <p className="text-xs text-gray-elegant">Market rate estimate</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-executive p-6"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs uppercase tracking-wider text-gray-elegant">Cap Rate</span>
            <Percent className="w-5 h-5 text-navy" />
          </div>
          <p className={`text-3xl font-light mb-1 ${
            'text-navy'
          }`}>
            {metrics.capRate.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-elegant">Annual return potential</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-executive p-6"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs uppercase tracking-wider text-gray-elegant">Price per SqFt</span>
            <Calculator className="w-5 h-5 text-navy" />
          </div>
          <p className={`text-3xl font-light mb-1 ${
            'text-navy'
          }`}>
            ${metrics.pricePerSqft > 0 ? Math.round(metrics.pricePerSqft) : '-'}
          </p>
          <p className="text-xs text-gray-elegant">Market comparison</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card-executive p-6"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs uppercase tracking-wider text-gray-elegant">Property Age</span>
            <Clock className="w-5 h-5 text-gray-600" />
          </div>
          <p className={`text-3xl font-light mb-1 ${
            metrics.propertyAge === null ? 'text-gray-600' :
            'text-navy'
          }`}>
            {metrics.propertyAge === null ? 'Unknown' : `${metrics.propertyAge} yrs`}
          </p>
          <p className="text-xs text-gray-elegant">
            {metrics.propertyAge === null ? 'Year built not available' :
             metrics.propertyAge < 20 ? 'Modern property' :
             metrics.propertyAge < 40 ? 'Established home' : 'Mature property'}
          </p>
        </motion.div>
      </div>

      {/* Market Performance Analysis */}
      <div className="card-executive animate-elegant">
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 bg-navy rounded-lg mr-3">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            Market Performance Analysis
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Historical trends and comparative market position</p>
        </div>
        <div className="pt-8">
          {/* Appreciation Trend */}
          {metrics.appreciationTrend !== 0 && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-6 rounded-lg border border-gray-100 mb-8"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-navy mb-2 flex items-center">
                    <Activity className="w-5 h-5 mr-2" />
                    Recent Market Appreciation
                  </h4>
                  <p className="text-sm text-gray-elegant">Based on historical sales data</p>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-1">
                      {metrics.appreciationTrend > 0 ? (
                        <TrendingUp className="h-8 w-8 text-navy" />
                      ) : (
                        <TrendingDown className="h-8 w-8 text-navy" />
                      )}
                    </div>
                    <span className={`text-3xl font-light ${
                      'text-navy'
                    }`}>
                      {metrics.appreciationTrend > 0 ? '+' : ''}{metrics.appreciationTrend.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
          
          {/* Comparative Analysis */}
          <div className="grid lg:grid-cols-2 gap-8">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-6 rounded-lg border border-gray-elegant bg-white"
            >
              <h4 className="font-medium elegant-heading text-navy mb-6 flex items-center">
                <PieChart className="w-5 h-5 mr-2 text-gold" />
                Valuation Analysis
              </h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-gray-light">
                  <span className="text-gray-elegant text-sm">Current Market Value</span>
                  <span className="font-medium text-navy text-lg">
                    ${metrics.marketValue.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-light">
                  <span className="text-gray-elegant text-sm">Last Sale Price</span>
                  <span className="font-medium text-navy text-lg">
                    ${metrics.salePrice.toLocaleString()}
                  </span>
                </div>
                {metrics.marketValue > 0 && metrics.salePrice > 0 && (
                  <div className="flex justify-between items-center py-3 border-t border-gold bg-gold-light rounded p-3">
                    <span className="text-navy font-medium">Market Premium/Discount</span>
                    <span className={`text-xl font-light ${
                      'text-navy'
                    }`}>
                      {metrics.marketValue > metrics.salePrice ? '+' : ''}
                      {((metrics.marketValue - metrics.salePrice) / metrics.salePrice * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-6 rounded-lg border border-gray-elegant bg-white"
            >
              <h4 className="font-medium elegant-heading text-navy mb-6 flex items-center">
                <DollarSign className="w-5 h-5 mr-2 text-gold" />
                Investment Returns Projection
              </h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-gray-light">
                  <span className="text-gray-elegant text-sm">Estimated Annual Rental</span>
                  <span className="font-medium text-green-600 text-lg">
                    ${metrics.annualRent.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-light">
                  <span className="text-gray-elegant text-sm">Annual Assessments</span>
                  <span className="font-medium text-red-600 text-lg">
                    -${totalNavAssessment.toFixed(0)}
                  </span>
                </div>
                <div className="flex justify-between items-center py-3 border-t border-gold bg-gold-light rounded p-3">
                  <span className="text-navy font-medium">Net Annual Income</span>
                  <span className="text-xl font-light text-navy">
                    ${(metrics.annualRent - totalNavAssessment).toLocaleString()}
                  </span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Data Visualization Section - Charts temporarily disabled for build
        Charts include:
        - Price History Chart
        - Market Analysis Charts Grid
        - Tax Breakdown
        - ROI Analysis
        - Property Metrics Radar
        - Cash Flow Analysis
        - Property Stats Summary

        These will be re-enabled once chart dependencies are properly configured
      */}

      {/* Executive Investment Recommendation */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-executive animate-elegant"
      >
        <div className="elegant-card-header">
          <h3 className="elegant-card-title gold-accent flex items-center">
            <div className="p-2 bg-gold rounded-lg mr-3">
              <Eye className="w-4 h-4 text-navy" />
            </div>
            Strategic Investment Recommendation
          </h3>
          <p className="text-sm mt-4 text-gray-elegant">Executive summary and actionable investment guidance</p>
        </div>
        <div className="pt-8">
          {investmentScore >= 80 ? (
            <div className="p-8 rounded-lg border-l-4 border-green-500" style={{background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)'}}>
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h4 className="text-2xl font-light elegant-text text-navy mb-2 flex items-center">
                    <Target className="w-6 h-6 mr-3" />
                    Strong Investment Opportunity
                  </h4>
                  <p className="text-navy mb-4">
                    This property demonstrates excellent investment potential with multiple favorable factors aligning for superior returns.
                  </p>
                </div>
                <span className="badge-elegant badge-gold text-sm">RECOMMENDED</span>
              </div>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h5 className="font-medium text-navy mb-3">Strategic Advantages</h5>
                  <ul className="space-y-2 text-sm text-navy">
                    <li className="flex items-start">
                      <CheckCircle2 className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>High investment score indicates strong fundamentals</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle2 className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Multiple positive investment factors identified</span>
                    </li>
                    <li className="flex items-start">
                      <CheckCircle2 className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Strong rental income potential</span>
                    </li>
                  </ul>
                </div>
                <div>
                  <h5 className="font-medium text-navy mb-3">Recommended Actions</h5>
                  <ul className="space-y-2 text-sm text-navy">
                    <li className="flex items-start">
                      <Star className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Prioritize this opportunity for acquisition</span>
                    </li>
                    <li className="flex items-start">
                      <Star className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Verify rental estimates with comparable market data</span>
                    </li>
                    <li className="flex items-start">
                      <Star className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Schedule comprehensive property inspection</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          ) : investmentScore >= 60 ? (
            <div className="p-8 rounded-lg border-l-4 border-yellow-500" style={{background: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)'}}>
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h4 className="text-2xl font-light elegant-text text-navy mb-2 flex items-center">
                    <BarChart3 className="w-6 h-6 mr-3" />
                    Moderate Investment Potential
                  </h4>
                  <p className="text-navy mb-4">
                    This property shows reasonable investment merit but requires careful analysis of risk factors and market conditions.
                  </p>
                </div>
                <span className="badge-elegant text-sm">CONDITIONAL</span>
              </div>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h5 className="font-medium text-navy mb-3">Due Diligence Required</h5>
                  <ul className="space-y-2 text-sm text-navy">
                    <li className="flex items-start">
                      <Eye className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Analyze all risk factors comprehensively</span>
                    </li>
                    <li className="flex items-start">
                      <Calculator className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Verify financial projections with market data</span>
                    </li>
                    <li className="flex items-start">
                      <Activity className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Consider negotiating based on identified issues</span>
                    </li>
                  </ul>
                </div>
                <div>
                  <h5 className="font-medium text-navy mb-3">Strategic Considerations</h5>
                  <ul className="space-y-2 text-sm text-navy">
                    <li className="flex items-start">
                      <Target className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>May suit specific investment strategies</span>
                    </li>
                    <li className="flex items-start">
                      <DollarSign className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Price adjustments may improve viability</span>
                    </li>
                    <li className="flex items-start">
                      <TrendingUp className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Monitor for market condition improvements</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-lg border-l-4 border-red-500" style={{background: 'linear-gradient(135deg, #fef2f2 0%, #fecaca 100%)'}}>
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h4 className="text-2xl font-light elegant-text text-navy mb-2 flex items-center">
                    <AlertTriangle className="w-6 h-6 mr-3" />
                    High-Risk Investment Profile
                  </h4>
                  <p className="text-navy mb-4">
                    This property presents significant risk factors that require careful evaluation. Proceed with extensive due diligence.
                  </p>
                </div>
                <span className="badge-elegant text-sm">CAUTION</span>
              </div>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h5 className="font-medium text-navy mb-3">Risk Mitigation</h5>
                  <ul className="space-y-2 text-sm text-navy">
                    <li className="flex items-start">
                      <AlertTriangle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Comprehensive risk analysis essential</span>
                    </li>
                    <li className="flex items-start">
                      <Calculator className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Evaluate if risks can be priced into offer</span>
                    </li>
                    <li className="flex items-start">
                      <TrendingDown className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Significant price reduction likely required</span>
                    </li>
                  </ul>
                </div>
                <div>
                  <h5 className="font-medium text-navy mb-3">Alternative Strategy</h5>
                  <ul className="space-y-2 text-sm text-navy">
                    <li className="flex items-start">
                      <Search className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Consider alternative opportunities in market</span>
                    </li>
                    <li className="flex items-start">
                      <Eye className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Monitor for fundamental changes</span>
                    </li>
                    <li className="flex items-start">
                      <Target className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                      <span>Focus resources on higher-scoring properties</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}
