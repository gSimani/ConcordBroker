import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  TrendingUp, DollarSign, Calendar, AlertTriangle, CheckCircle,
  Building, Hammer, Paintbrush, Zap, Droplets, Wind, Shield,
  Calculator, PiggyBank, Clock, BarChart3, Target, Info,
  ChevronRight, Download, FileText, Settings
} from 'lucide-react';

interface CapitalPlanningTabProps {
  propertyData: any;
}

export function CapitalPlanningTab({ propertyData }: CapitalPlanningTabProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState('5year');
  const [viewMode, setViewMode] = useState('overview');

  const data = propertyData?.bcpaData || propertyData || {};

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  // Calculate property age and estimate capital expenses
  const currentYear = new Date().getFullYear();
  const rawYearBuilt = data.year_built || data.yearBuilt;
  const yearBuilt = (rawYearBuilt && parseInt(rawYearBuilt) > 0) ? parseInt(rawYearBuilt) : null;
  const propertyAge = yearBuilt ? currentYear - yearBuilt : null;
  const totalSqFt = data.total_sqft || data.living_area || data.tot_lvg_area || 2000;
  const propertyValue = data.just_value || data.assessed_value || 300000;

  // Capital expense categories with lifecycles and costs
  const capitalExpenses = [
    {
      category: 'Roof',
      icon: <Building className="w-5 h-5" />,
      lifecycle: 20,
      lastReplaced: yearBuilt,
      costPerSqFt: 8,
      priority: 'high',
      condition: propertyAge === null ? 'fair' : propertyAge > 15 ? 'poor' : propertyAge > 10 ? 'fair' : 'good'
    },
    {
      category: 'HVAC System',
      icon: <Wind className="w-5 h-5" />,
      lifecycle: 15,
      lastReplaced: yearBuilt ? yearBuilt + 5 : null,
      costPerUnit: 7000,
      priority: 'high',
      condition: propertyAge === null ? 'fair' : propertyAge > 12 ? 'poor' : propertyAge > 8 ? 'fair' : 'good'
    },
    {
      category: 'Exterior Paint',
      icon: <Paintbrush className="w-5 h-5" />,
      lifecycle: 10,
      lastReplaced: yearBuilt ? yearBuilt + 10 : null,
      costPerSqFt: 3,
      priority: 'medium',
      condition: propertyAge === null ? 'fair' : propertyAge > 8 ? 'poor' : propertyAge > 5 ? 'fair' : 'good'
    },
    {
      category: 'Flooring',
      icon: <Hammer className="w-5 h-5" />,
      lifecycle: 15,
      lastReplaced: yearBuilt ? yearBuilt + 5 : null,
      costPerSqFt: 5,
      priority: 'medium',
      condition: propertyAge === null ? 'fair' : propertyAge > 12 ? 'poor' : propertyAge > 8 ? 'fair' : 'good'
    },
    {
      category: 'Plumbing',
      icon: <Droplets className="w-5 h-5" />,
      lifecycle: 30,
      lastReplaced: yearBuilt,
      costPerUnit: 10000,
      priority: propertyAge === null ? 'low' : propertyAge > 25 ? 'high' : 'low',
      condition: propertyAge === null ? 'fair' : propertyAge > 25 ? 'poor' : propertyAge > 20 ? 'fair' : 'good'
    },
    {
      category: 'Electrical',
      icon: <Zap className="w-5 h-5" />,
      lifecycle: 30,
      lastReplaced: yearBuilt,
      costPerUnit: 8000,
      priority: propertyAge === null ? 'low' : propertyAge > 25 ? 'high' : 'low',
      condition: propertyAge === null ? 'fair' : propertyAge > 25 ? 'poor' : propertyAge > 20 ? 'fair' : 'good'
    },
    {
      category: 'Windows',
      icon: <Shield className="w-5 h-5" />,
      lifecycle: 20,
      lastReplaced: yearBuilt,
      costPerUnit: 15000,
      priority: propertyAge === null ? 'low' : propertyAge > 18 ? 'medium' : 'low',
      condition: propertyAge === null ? 'fair' : propertyAge > 18 ? 'poor' : propertyAge > 12 ? 'fair' : 'good'
    },
    {
      category: 'Appliances',
      icon: <Settings className="w-5 h-5" />,
      lifecycle: 10,
      lastReplaced: yearBuilt ? yearBuilt + 10 : null,
      costPerUnit: 5000,
      priority: 'medium',
      condition: propertyAge === null ? 'fair' : propertyAge > 8 ? 'poor' : propertyAge > 5 ? 'fair' : 'good'
    }
  ];

  // Calculate costs and timelines for each expense
  const expensesWithTimeline = capitalExpenses.map(expense => {
    // Use lifecycle midpoint as default estimate when lastReplaced is unknown
    const yearsSinceReplaced = expense.lastReplaced !== null
      ? currentYear - expense.lastReplaced
      : Math.floor(expense.lifecycle / 2);
    const remainingLife = Math.max(0, expense.lifecycle - yearsSinceReplaced);
    const replacementYear = currentYear + remainingLife;
    const estimatedCost = expense.costPerSqFt
      ? expense.costPerSqFt * totalSqFt
      : expense.costPerUnit;

    return {
      ...expense,
      yearsSinceReplaced,
      remainingLife,
      replacementYear,
      estimatedCost,
      urgency: remainingLife <= 2 ? 'immediate' : remainingLife <= 5 ? 'soon' : 'future'
    };
  });

  // Calculate total reserves needed
  const totalReservesNeeded = expensesWithTimeline.reduce((sum, expense) => {
    if (expense.remainingLife <= (selectedTimeframe === '5year' ? 5 : 10)) {
      return sum + expense.estimatedCost;
    }
    return sum;
  }, 0);

  const annualReserveContribution = totalReservesNeeded / (selectedTimeframe === '5year' ? 5 : 10);
  const monthlyReserveContribution = annualReserveContribution / 12;

  // Sort by urgency
  const sortedExpenses = [...expensesWithTimeline].sort((a, b) => a.remainingLife - b.remainingLife);

  const getConditionColor = (condition: string) => {
    switch (condition) {
      case 'good': return 'text-green-600 bg-green-100';
      case 'fair': return 'text-yellow-600 bg-yellow-100';
      case 'poor': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'immediate': return 'bg-red-500';
      case 'soon': return 'bg-yellow-500';
      case 'future': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-navy elegant-heading">Capital Planning & Reserves</h2>
          <p className="text-gray-600 mt-1 text-base elegant-text">
            Comprehensive capital expenditure planning for property maintenance
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={selectedTimeframe === '5year' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedTimeframe('5year')}
          >
            5 Year Plan
          </Button>
          <Button
            variant={selectedTimeframe === '10year' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedTimeframe('10year')}
          >
            10 Year Plan
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="elegant-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-base text-gray-600">Property Age</p>
                <p className="text-2xl font-bold text-navy">
                  {propertyAge !== null ? `${propertyAge} years` : 'Unknown'}
                </p>
              </div>
              <Building className="w-8 h-8 text-gold" />
            </div>
          </CardContent>
        </Card>

        <Card className="elegant-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-base text-gray-600">Total Reserves Needed</p>
                <p className="text-2xl font-bold text-navy">{formatCurrency(totalReservesNeeded)}</p>
              </div>
              <PiggyBank className="w-8 h-8 text-gold" />
            </div>
          </CardContent>
        </Card>

        <Card className="elegant-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-base text-gray-600">Annual Reserve</p>
                <p className="text-2xl font-bold text-navy">{formatCurrency(annualReserveContribution)}</p>
              </div>
              <Calendar className="w-8 h-8 text-gold" />
            </div>
          </CardContent>
        </Card>

        <Card className="elegant-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-base text-gray-600">Monthly Reserve</p>
                <p className="text-2xl font-bold text-navy">{formatCurrency(monthlyReserveContribution)}</p>
              </div>
              <DollarSign className="w-8 h-8 text-gold" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for different views */}
      <Tabs value={viewMode} onValueChange={setViewMode}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="calculator">Calculator</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Expense Categories */}
            <Card className="elegant-card">
              <CardHeader>
                <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
                  <h3 className="text-xl font-bold text-navy">Capital Expense Categories</h3>
                </div>
                <CardDescription className="text-gray-600">Major systems and components requiring planning</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {sortedExpenses.map((expense, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${getConditionColor(expense.condition)}`}>
                          {expense.icon}
                        </div>
                        <div>
                          <p className="font-medium text-navy">{expense.category}</p>
                          <p className="text-base text-muted-foreground">
                            {expense.remainingLife} years remaining
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-navy">{formatCurrency(expense.estimatedCost)}</p>
                        <Badge variant={expense.urgency === 'immediate' ? 'destructive' :
                                       expense.urgency === 'soon' ? 'secondary' : 'outline'}>
                          {expense.replacementYear}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Reserve Fund Status */}
            <Card className="elegant-card">
              <CardHeader>
                <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
                  <h3 className="text-xl font-bold text-navy">Reserve Fund Analysis</h3>
                </div>
                <CardDescription className="text-gray-600">Funding strategy for capital expenses</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-base font-medium text-navy">Current Reserve Fund</span>
                    <span className="text-base font-medium text-navy">$0</span>
                  </div>
                  <Progress value={0} className="h-2" />
                </div>

                <div className="space-y-3 pt-4">
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-base text-gray-600">Immediate Needs (0-2 years)</span>
                    <span className="font-semibold text-red-600">
                      {formatCurrency(sortedExpenses
                        .filter(e => e.remainingLife <= 2)
                        .reduce((sum, e) => sum + e.estimatedCost, 0))}
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-base text-gray-600">Near-term (3-5 years)</span>
                    <span className="font-semibold text-yellow-600">
                      {formatCurrency(sortedExpenses
                        .filter(e => e.remainingLife > 2 && e.remainingLife <= 5)
                        .reduce((sum, e) => sum + e.estimatedCost, 0))}
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-base text-gray-600">Long-term (6-10 years)</span>
                    <span className="font-semibold text-green-600">
                      {formatCurrency(sortedExpenses
                        .filter(e => e.remainingLife > 5 && e.remainingLife <= 10)
                        .reduce((sum, e) => sum + e.estimatedCost, 0))}
                    </span>
                  </div>
                </div>

                <div className="mt-6 p-4 rounded-lg" style={{background: 'linear-gradient(to right, rgba(212, 175, 55, 0.1), rgba(44, 62, 80, 0.1))'}}>
                  <div className="flex items-center gap-2 mb-2">
                    <Info className="w-4 h-4 text-gold" />
                    <span className="font-medium text-navy">Recommendation</span>
                  </div>
                  <p className="text-base text-navy">
                    Set aside {formatCurrency(monthlyReserveContribution)} per month to cover
                    anticipated capital expenses over the next {selectedTimeframe === '5year' ? '5' : '10'} years.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="timeline" className="mt-6">
          <Card className="elegant-card">
            <CardHeader>
              <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
                <h3 className="text-xl font-bold text-navy">Capital Expense Timeline</h3>
              </div>
              <CardDescription className="text-gray-600">Projected replacement schedule</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative">
                {/* Timeline */}
                <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200"></div>

                <div className="space-y-6">
                  {sortedExpenses.map((expense, index) => (
                    <div key={index} className="relative flex items-start">
                      <div className={`absolute left-6 w-4 h-4 rounded-full ${getUrgencyColor(expense.urgency)}`}></div>
                      <div className="ml-16">
                        <div className="flex items-center gap-3 mb-1">
                          <span className="font-semibold text-navy">{expense.category}</span>
                          <Badge variant="outline">{expense.replacementYear}</Badge>
                        </div>
                        <p className="text-base text-muted-foreground mb-1">
                          Estimated cost: {formatCurrency(expense.estimatedCost)}
                        </p>
                        <div className="flex items-center gap-2">
                          <Badge className={getConditionColor(expense.condition)}>
                            {expense.condition} condition
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            {expense.lifecycle} year lifecycle
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="calculator" className="mt-6">
          <Card className="elegant-card">
            <CardHeader>
              <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
                <h3 className="text-xl font-bold text-navy">Reserve Fund Calculator</h3>
              </div>
              <CardDescription className="text-gray-600">Calculate optimal reserve contributions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="font-semibold text-navy">Property Information</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Property Value</span>
                        <span className="font-medium">{formatCurrency(propertyValue)}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Square Footage</span>
                        <span className="font-medium">{totalSqFt.toLocaleString()} sq ft</span>
                      </div>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Year Built</span>
                        <span className="font-medium">{yearBuilt !== null ? yearBuilt : 'Unknown'}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Property Age</span>
                        <span className="font-medium">
                          {propertyAge !== null ? `${propertyAge} years` : 'Unknown'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-semibold text-navy">Reserve Calculations</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Total Capital Needs</span>
                        <span className="font-medium">{formatCurrency(totalReservesNeeded)}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Planning Period</span>
                        <span className="font-medium">{selectedTimeframe === '5year' ? '5' : '10'} years</span>
                      </div>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Annual Contribution</span>
                        <span className="font-medium">{formatCurrency(annualReserveContribution)}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Monthly Contribution</span>
                        <span className="font-medium text-navy">{formatCurrency(monthlyReserveContribution)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold mb-3">Reserve Fund Breakdown</h4>
                  <div className="space-y-2">
                    {sortedExpenses.slice(0, 5).map((expense, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="flex items-center gap-2">
                          {expense.icon}
                          {expense.category}
                        </span>
                        <span className="font-medium">{formatCurrency(expense.estimatedCost / (selectedTimeframe === '5year' ? 60 : 120))}/mo</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <Button className="flex-1">
                    <Download className="w-4 h-4 mr-2" />
                    Export Plan
                  </Button>
                  <Button variant="outline" className="flex-1">
                    <FileText className="w-4 h-4 mr-2" />
                    Generate Report
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}