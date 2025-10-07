import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger
} from '@/components/ui/dialog';
import {
  TrendingUp, DollarSign, Calendar, AlertTriangle, CheckCircle,
  Building, Hammer, Paintbrush, Zap, Droplets, Wind, Shield,
  Calculator, PiggyBank, Clock, BarChart3, Target, Info,
  ChevronRight, Download, FileText, Settings, Edit, Plus, Save,
  Trash2, Copy, RefreshCw
} from 'lucide-react';
import { getPropertyCategory, getUseCodeInfo } from '@/lib/dorUseCodes';

interface CapitalExpense {
  id: string;
  category: string;
  icon: string;
  lifecycle: number;
  lastReplaced: number;
  costPerSqFt?: number;
  costPerUnit?: number;
  priority: 'high' | 'medium' | 'low';
  condition: 'good' | 'fair' | 'poor';
  customizable: boolean;
  propertyTypes: string[];
}

interface CapitalPlanningTabEnhancedProps {
  propertyData: any;
}

// Define property-type-specific expense templates
const PROPERTY_TYPE_TEMPLATES: Record<string, CapitalExpense[]> = {
  RESIDENTIAL: [
    { id: 'roof', category: 'Roof', icon: 'Building', lifecycle: 20, lastReplaced: 0, costPerSqFt: 8, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['RESIDENTIAL'] },
    { id: 'hvac', category: 'HVAC System', icon: 'Wind', lifecycle: 15, lastReplaced: 0, costPerUnit: 7000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['RESIDENTIAL'] },
    { id: 'paint_ext', category: 'Exterior Paint', icon: 'Paintbrush', lifecycle: 10, lastReplaced: 0, costPerSqFt: 3, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['RESIDENTIAL'] },
    { id: 'flooring', category: 'Flooring', icon: 'Hammer', lifecycle: 15, lastReplaced: 0, costPerSqFt: 5, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['RESIDENTIAL'] },
    { id: 'plumbing', category: 'Plumbing', icon: 'Droplets', lifecycle: 30, lastReplaced: 0, costPerUnit: 10000, priority: 'low', condition: 'good', customizable: true, propertyTypes: ['RESIDENTIAL'] },
    { id: 'electrical', category: 'Electrical', icon: 'Zap', lifecycle: 30, lastReplaced: 0, costPerUnit: 8000, priority: 'low', condition: 'good', customizable: true, propertyTypes: ['RESIDENTIAL'] },
    { id: 'windows', category: 'Windows', icon: 'Shield', lifecycle: 20, lastReplaced: 0, costPerUnit: 15000, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['RESIDENTIAL'] },
    { id: 'appliances', category: 'Appliances', icon: 'Settings', lifecycle: 10, lastReplaced: 0, costPerUnit: 5000, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['RESIDENTIAL'] },
  ],
  COMMERCIAL: [
    { id: 'roof_commercial', category: 'Commercial Roof System', icon: 'Building', lifecycle: 25, lastReplaced: 0, costPerSqFt: 12, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'hvac_commercial', category: 'Commercial HVAC', icon: 'Wind', lifecycle: 20, lastReplaced: 0, costPerUnit: 25000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'parking', category: 'Parking Lot/Asphalt', icon: 'Building', lifecycle: 15, lastReplaced: 0, costPerSqFt: 4, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'elevator', category: 'Elevator System', icon: 'Settings', lifecycle: 25, lastReplaced: 0, costPerUnit: 50000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'fire_safety', category: 'Fire Safety Systems', icon: 'Shield', lifecycle: 20, lastReplaced: 0, costPerUnit: 20000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'facade', category: 'Building Facade', icon: 'Building', lifecycle: 30, lastReplaced: 0, costPerSqFt: 15, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'plumbing_commercial', category: 'Commercial Plumbing', icon: 'Droplets', lifecycle: 35, lastReplaced: 0, costPerUnit: 30000, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'electrical_commercial', category: 'Electrical Panel/System', icon: 'Zap', lifecycle: 35, lastReplaced: 0, costPerUnit: 25000, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
  ],
  INDUSTRIAL: [
    { id: 'roof_industrial', category: 'Industrial Roof', icon: 'Building', lifecycle: 30, lastReplaced: 0, costPerSqFt: 15, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['INDUSTRIAL'] },
    { id: 'hvac_industrial', category: 'Industrial HVAC/Ventilation', icon: 'Wind', lifecycle: 25, lastReplaced: 0, costPerUnit: 50000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['INDUSTRIAL'] },
    { id: 'loading_dock', category: 'Loading Dock Equipment', icon: 'Building', lifecycle: 20, lastReplaced: 0, costPerUnit: 30000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['INDUSTRIAL'] },
    { id: 'crane_system', category: 'Crane/Hoist System', icon: 'Settings', lifecycle: 30, lastReplaced: 0, costPerUnit: 100000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['INDUSTRIAL'] },
    { id: 'floor_coating', category: 'Epoxy Floor Coating', icon: 'Hammer', lifecycle: 10, lastReplaced: 0, costPerSqFt: 6, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['INDUSTRIAL'] },
    { id: 'electrical_industrial', category: 'High-Voltage Electrical', icon: 'Zap', lifecycle: 40, lastReplaced: 0, costPerUnit: 75000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['INDUSTRIAL'] },
  ],
  HOTEL: [
    { id: 'roof_hotel', category: 'Hotel Roof', icon: 'Building', lifecycle: 20, lastReplaced: 0, costPerSqFt: 10, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'hvac_hotel', category: 'Guest Room HVAC Units', icon: 'Wind', lifecycle: 15, lastReplaced: 0, costPerUnit: 35000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'elevators_hotel', category: 'Passenger Elevators', icon: 'Settings', lifecycle: 25, lastReplaced: 0, costPerUnit: 60000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'pool_spa', category: 'Pool & Spa Equipment', icon: 'Droplets', lifecycle: 15, lastReplaced: 0, costPerUnit: 25000, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'ff_e', category: 'Furniture, Fixtures & Equipment', icon: 'Settings', lifecycle: 7, lastReplaced: 0, costPerUnit: 150000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
    { id: 'carpeting', category: 'Guest Room Carpeting', icon: 'Hammer', lifecycle: 7, lastReplaced: 0, costPerSqFt: 8, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['COMMERCIAL'] },
  ],
  CHURCH: [
    { id: 'roof_church', category: 'Church Roof', icon: 'Building', lifecycle: 25, lastReplaced: 0, costPerSqFt: 12, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['INSTITUTIONAL'] },
    { id: 'hvac_church', category: 'Sanctuary HVAC', icon: 'Wind', lifecycle: 20, lastReplaced: 0, costPerUnit: 40000, priority: 'high', condition: 'good', customizable: true, propertyTypes: ['INSTITUTIONAL'] },
    { id: 'sound_system', category: 'Audio/Visual System', icon: 'Settings', lifecycle: 10, lastReplaced: 0, costPerUnit: 50000, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['INSTITUTIONAL'] },
    { id: 'seating', category: 'Pews/Seating', icon: 'Building', lifecycle: 30, lastReplaced: 0, costPerUnit: 30000, priority: 'low', condition: 'good', customizable: true, propertyTypes: ['INSTITUTIONAL'] },
    { id: 'parking_church', category: 'Parking Lot', icon: 'Building', lifecycle: 15, lastReplaced: 0, costPerSqFt: 4, priority: 'medium', condition: 'good', customizable: true, propertyTypes: ['INSTITUTIONAL'] },
  ],
};

export function CapitalPlanningTabEnhanced({ propertyData }: CapitalPlanningTabEnhancedProps) {
  const [selectedTimeframe, setSelectedTimeframe] = useState('5year');
  const [viewMode, setViewMode] = useState('overview');
  const [expenses, setExpenses] = useState<CapitalExpense[]>([]);
  const [editingExpense, setEditingExpense] = useState<CapitalExpense | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);

  const data = propertyData?.bcpaData || propertyData || {};

  // Get property type from DOR use code
  const dorUseCode = data.dor_uc || data.property_use || data.property_use_code;
  const propertyCategory = getPropertyCategory(dorUseCode);
  const useCodeInfo = getUseCodeInfo(dorUseCode);

  // Determine specific property subtype
  const getPropertySubtype = (): string => {
    if (!dorUseCode) return 'RESIDENTIAL';
    const code = String(dorUseCode).padStart(3, '0');

    // Hotels/Motels
    if (code === '039') return 'HOTEL';
    // Churches
    if (code === '071') return 'CHURCH';
    // Multi-family 10+ units
    if (code === '003') return 'COMMERCIAL';

    return propertyCategory;
  };

  const propertySubtype = getPropertySubtype();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  // Initialize expenses based on property type
  useEffect(() => {
    const template = PROPERTY_TYPE_TEMPLATES[propertySubtype] || PROPERTY_TYPE_TEMPLATES.RESIDENTIAL;
    const currentYear = new Date().getFullYear();
    const yearBuilt = data.year_built || data.yearBuilt || currentYear - 20;

    const initializedExpenses = template.map(expense => ({
      ...expense,
      lastReplaced: yearBuilt + Math.floor(expense.lifecycle / 2)
    }));

    setExpenses(initializedExpenses);
  }, [propertySubtype, data]);

  const currentYear = new Date().getFullYear();
  const yearBuilt = data.year_built || data.yearBuilt || 1990;
  const propertyAge = currentYear - yearBuilt;
  const totalSqFt = data.total_sqft || data.living_area || data.tot_lvg_area || 2000;
  const propertyValue = data.just_value || data.assessed_value || 300000;

  // Calculate costs and timelines for each expense
  const expensesWithTimeline = expenses.map(expense => {
    const yearsSinceReplaced = currentYear - expense.lastReplaced;
    const remainingLife = Math.max(0, expense.lifecycle - yearsSinceReplaced);
    const replacementYear = currentYear + remainingLife;
    const estimatedCost = expense.costPerSqFt
      ? expense.costPerSqFt * totalSqFt
      : expense.costPerUnit || 0;

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

  const getIconComponent = (iconName: string) => {
    const icons: Record<string, any> = {
      Building, Wind, Paintbrush, Hammer, Droplets, Zap, Shield, Settings
    };
    const IconComponent = icons[iconName] || Building;
    return <IconComponent className="w-5 h-5" />;
  };

  const handleEditExpense = (expense: any) => {
    setEditingExpense(expense);
  };

  const handleSaveExpense = (updatedExpense: Partial<CapitalExpense>) => {
    setExpenses(prev => prev.map(exp =>
      exp.id === updatedExpense.id ? { ...exp, ...updatedExpense } : exp
    ));
    setEditingExpense(null);
  };

  const handleAddExpense = (newExpense: CapitalExpense) => {
    setExpenses(prev => [...prev, { ...newExpense, id: `custom_${Date.now()}` }]);
    setShowAddDialog(false);
  };

  const handleDeleteExpense = (expenseId: string) => {
    setExpenses(prev => prev.filter(exp => exp.id !== expenseId));
  };

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-navy elegant-heading">Capital Planning & Reserves</h2>
          <p className="text-gray-600 mt-1 text-base elegant-text">
            Comprehensive capital expenditure planning for {useCodeInfo?.shortName || 'property'} ({propertyCategory})
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
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddDialog(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Expense
          </Button>
        </div>
      </div>

      {/* Property Type Badge */}
      <div className="flex gap-2 items-center">
        <Badge variant="outline" className="text-base py-1 px-3">
          Property Type: {propertySubtype}
        </Badge>
        {dorUseCode && (
          <Badge variant="secondary" className="text-base py-1 px-3">
            DOR Code: {String(dorUseCode).padStart(3, '0')} - {useCodeInfo?.shortName}
          </Badge>
        )}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="elegant-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-base text-gray-600">Property Age</p>
                <p className="text-2xl font-bold text-navy">{propertyAge} years</p>
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
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg group hover:border-gold transition-colors">
                      <div className="flex items-center gap-3 flex-1">
                        <div className={`p-2 rounded-lg ${getConditionColor(expense.condition)}`}>
                          {getIconComponent(expense.icon)}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-navy">{expense.category}</p>
                          <p className="text-base text-muted-foreground">
                            {expense.remainingLife} years remaining
                          </p>
                        </div>
                      </div>
                      <div className="text-right flex items-center gap-2">
                        <div>
                          <p className="font-semibold text-navy">{formatCurrency(expense.estimatedCost)}</p>
                          <Badge variant={expense.urgency === 'immediate' ? 'destructive' :
                                         expense.urgency === 'soon' ? 'secondary' : 'outline'}>
                            {expense.replacementYear}
                          </Badge>
                        </div>
                        {expense.customizable && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                            onClick={() => handleEditExpense(expense)}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                        )}
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
                        <span className="font-medium">{yearBuilt}</span>
                      </div>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Property Age</span>
                        <span className="font-medium">{propertyAge} years</span>
                      </div>
                      <div className="flex justify-between py-2 border-b">
                        <span className="text-base text-gray-600">Property Type</span>
                        <span className="font-medium">{propertySubtype}</span>
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
                          {getIconComponent(expense.icon)}
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
                  <Button variant="outline" className="flex-1">
                    <Save className="w-4 h-4 mr-2" />
                    Save to Database
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Expense Dialog */}
      {editingExpense && (
        <ExpenseEditDialog
          expense={editingExpense}
          onSave={handleSaveExpense}
          onClose={() => setEditingExpense(null)}
        />
      )}

      {/* Add Expense Dialog */}
      {showAddDialog && (
        <AddExpenseDialog
          propertyType={propertySubtype}
          onAdd={handleAddExpense}
          onClose={() => setShowAddDialog(false)}
        />
      )}
    </div>
  );
}

// Expense Edit Dialog Component
function ExpenseEditDialog({ expense, onSave, onClose }: any) {
  const [formData, setFormData] = useState(expense);

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Edit Capital Expense</DialogTitle>
          <DialogDescription>
            Customize the details for this capital expense item
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-4 py-4">
          <div className="space-y-2">
            <Label>Category Name</Label>
            <Input
              value={formData.category}
              onChange={e => setFormData({...formData, category: e.target.value})}
            />
          </div>

          <div className="space-y-2">
            <Label>Lifecycle (years)</Label>
            <Input
              type="number"
              value={formData.lifecycle}
              onChange={e => setFormData({...formData, lifecycle: parseInt(e.target.value)})}
            />
          </div>

          <div className="space-y-2">
            <Label>Last Replaced (year)</Label>
            <Input
              type="number"
              value={formData.lastReplaced}
              onChange={e => setFormData({...formData, lastReplaced: parseInt(e.target.value)})}
            />
          </div>

          <div className="space-y-2">
            <Label>Condition</Label>
            <Select value={formData.condition} onValueChange={val => setFormData({...formData, condition: val})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="good">Good</SelectItem>
                <SelectItem value="fair">Fair</SelectItem>
                <SelectItem value="poor">Poor</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Priority</Label>
            <Select value={formData.priority} onValueChange={val => setFormData({...formData, priority: val})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Cost Per Sq Ft ($)</Label>
            <Input
              type="number"
              step="0.01"
              value={formData.costPerSqFt || ''}
              onChange={e => setFormData({...formData, costPerSqFt: parseFloat(e.target.value) || undefined})}
            />
          </div>

          <div className="space-y-2">
            <Label>Cost Per Unit ($)</Label>
            <Input
              type="number"
              value={formData.costPerUnit || ''}
              onChange={e => setFormData({...formData, costPerUnit: parseFloat(e.target.value) || undefined})}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={() => onSave(formData)}>Save Changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Add Expense Dialog Component
function AddExpenseDialog({ propertyType, onAdd, onClose }: any) {
  const [formData, setFormData] = useState({
    category: '',
    icon: 'Building',
    lifecycle: 20,
    lastReplaced: new Date().getFullYear(),
    costPerSqFt: undefined,
    costPerUnit: undefined,
    priority: 'medium',
    condition: 'good',
    customizable: true,
    propertyTypes: [propertyType]
  });

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Add Custom Capital Expense</DialogTitle>
          <DialogDescription>
            Create a new capital expense item for this property
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-4 py-4">
          <div className="space-y-2">
            <Label>Category Name *</Label>
            <Input
              value={formData.category}
              onChange={e => setFormData({...formData, category: e.target.value})}
              placeholder="e.g., Pool Equipment"
            />
          </div>

          <div className="space-y-2">
            <Label>Lifecycle (years) *</Label>
            <Input
              type="number"
              value={formData.lifecycle}
              onChange={e => setFormData({...formData, lifecycle: parseInt(e.target.value)})}
            />
          </div>

          <div className="space-y-2">
            <Label>Last Replaced (year)</Label>
            <Input
              type="number"
              value={formData.lastReplaced}
              onChange={e => setFormData({...formData, lastReplaced: parseInt(e.target.value)})}
            />
          </div>

          <div className="space-y-2">
            <Label>Condition</Label>
            <Select value={formData.condition} onValueChange={val => setFormData({...formData, condition: val as any})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="good">Good</SelectItem>
                <SelectItem value="fair">Fair</SelectItem>
                <SelectItem value="poor">Poor</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Priority</Label>
            <Select value={formData.priority} onValueChange={val => setFormData({...formData, priority: val as any})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Cost Per Sq Ft ($)</Label>
            <Input
              type="number"
              step="0.01"
              value={formData.costPerSqFt || ''}
              onChange={e => setFormData({...formData, costPerSqFt: parseFloat(e.target.value) || undefined})}
              placeholder="Optional"
            />
          </div>

          <div className="space-y-2 col-span-2">
            <Label>OR Cost Per Unit ($)</Label>
            <Input
              type="number"
              value={formData.costPerUnit || ''}
              onChange={e => setFormData({...formData, costPerUnit: parseFloat(e.target.value) || undefined})}
              placeholder="Optional - Fixed cost regardless of size"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button
            onClick={() => onAdd(formData)}
            disabled={!formData.category || (!formData.costPerSqFt && !formData.costPerUnit)}
          >
            Add Expense
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
