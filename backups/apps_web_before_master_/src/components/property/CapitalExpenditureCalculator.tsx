import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import {
  Check,
  Plus,
  Minus,
  Calculator,
  Home,
  Wrench,
  DollarSign,
  AlertCircle,
  Trash2,
  Save,
  Download,
  RotateCcw
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface RenovationItem {
  id: string;
  name: string;
  category: string;
  unit: 'each' | 'sqft' | 'percentage' | 'lf'; // linear feet
  defaultCost: number;
  minQuantity: number;
  maxQuantity: number;
  description: string;
  lifespan?: number; // years
  icon?: string;
}

interface SelectedItem {
  itemId: string;
  quantity: number;
  customCost?: number;
  notes?: string;
}

const RENOVATION_ITEMS: RenovationItem[] = [
  // HVAC
  {
    id: 'hvac-unit',
    name: 'HVAC Unit',
    category: 'HVAC',
    unit: 'each',
    defaultCost: 7500,
    minQuantity: 1,
    maxQuantity: 10,
    description: 'Central air conditioning and heating unit',
    lifespan: 15,
    icon: '❄️'
  },
  {
    id: 'mini-split',
    name: 'Mini Split AC',
    category: 'HVAC',
    unit: 'each',
    defaultCost: 3500,
    minQuantity: 1,
    maxQuantity: 10,
    description: 'Ductless mini-split air conditioning unit',
    lifespan: 20,
    icon: '🌡️'
  },
  {
    id: 'ductwork',
    name: 'Ductwork',
    category: 'HVAC',
    unit: 'sqft',
    defaultCost: 8,
    minQuantity: 100,
    maxQuantity: 5000,
    description: 'HVAC ductwork installation/replacement per sq ft',
    lifespan: 30,
    icon: '🔧'
  },

  // Roofing
  {
    id: 'roof-shingle',
    name: 'Roof - Shingle',
    category: 'Roofing',
    unit: 'percentage',
    defaultCost: 15000,
    minQuantity: 10,
    maxQuantity: 100,
    description: 'Asphalt shingle roof replacement (% of total roof)',
    lifespan: 25,
    icon: '🏠'
  },
  {
    id: 'roof-tile',
    name: 'Roof - Tile',
    category: 'Roofing',
    unit: 'percentage',
    defaultCost: 25000,
    minQuantity: 10,
    maxQuantity: 100,
    description: 'Tile roof replacement (% of total roof)',
    lifespan: 50,
    icon: '🏡'
  },
  {
    id: 'roof-metal',
    name: 'Roof - Metal',
    category: 'Roofing',
    unit: 'percentage',
    defaultCost: 20000,
    minQuantity: 10,
    maxQuantity: 100,
    description: 'Metal roof replacement (% of total roof)',
    lifespan: 40,
    icon: '🏗️'
  },

  // Flooring
  {
    id: 'floor-tile',
    name: 'Flooring - Tile',
    category: 'Flooring',
    unit: 'sqft',
    defaultCost: 8,
    minQuantity: 50,
    maxQuantity: 10000,
    description: 'Ceramic/porcelain tile flooring per sq ft',
    lifespan: 30,
    icon: '◼'
  },
  {
    id: 'floor-hardwood',
    name: 'Flooring - Hardwood',
    category: 'Flooring',
    unit: 'sqft',
    defaultCost: 12,
    minQuantity: 50,
    maxQuantity: 10000,
    description: 'Hardwood flooring installation per sq ft',
    lifespan: 50,
    icon: '🪵'
  },
  {
    id: 'floor-luxury-vinyl',
    name: 'Flooring - LVP',
    category: 'Flooring',
    unit: 'sqft',
    defaultCost: 6,
    minQuantity: 50,
    maxQuantity: 10000,
    description: 'Luxury vinyl plank flooring per sq ft',
    lifespan: 20,
    icon: '📦'
  },
  {
    id: 'floor-carpet',
    name: 'Flooring - Carpet',
    category: 'Flooring',
    unit: 'sqft',
    defaultCost: 4,
    minQuantity: 50,
    maxQuantity: 10000,
    description: 'Carpet installation per sq ft',
    lifespan: 10,
    icon: '🟫'
  },

  // Appliances
  {
    id: 'refrigerator',
    name: 'Refrigerator',
    category: 'Appliances',
    unit: 'each',
    defaultCost: 2000,
    minQuantity: 1,
    maxQuantity: 5,
    description: 'Standard refrigerator',
    lifespan: 15,
    icon: '🧊'
  },
  {
    id: 'stove-range',
    name: 'Stove/Range',
    category: 'Appliances',
    unit: 'each',
    defaultCost: 1500,
    minQuantity: 1,
    maxQuantity: 5,
    description: 'Electric or gas range',
    lifespan: 15,
    icon: '🔥'
  },
  {
    id: 'dishwasher',
    name: 'Dishwasher',
    category: 'Appliances',
    unit: 'each',
    defaultCost: 800,
    minQuantity: 1,
    maxQuantity: 5,
    description: 'Built-in dishwasher',
    lifespan: 10,
    icon: '🍽️'
  },
  {
    id: 'microwave',
    name: 'Microwave',
    category: 'Appliances',
    unit: 'each',
    defaultCost: 400,
    minQuantity: 1,
    maxQuantity: 5,
    description: 'Over-range or countertop microwave',
    lifespan: 10,
    icon: '📡'
  },
  {
    id: 'washer',
    name: 'Washer',
    category: 'Appliances',
    unit: 'each',
    defaultCost: 800,
    minQuantity: 1,
    maxQuantity: 5,
    description: 'Washing machine',
    lifespan: 12,
    icon: '🌊'
  },
  {
    id: 'dryer',
    name: 'Dryer',
    category: 'Appliances',
    unit: 'each',
    defaultCost: 800,
    minQuantity: 1,
    maxQuantity: 5,
    description: 'Clothes dryer',
    lifespan: 12,
    icon: '♨️'
  },

  // Windows & Doors
  {
    id: 'window-standard',
    name: 'Window - Standard',
    category: 'Windows & Doors',
    unit: 'each',
    defaultCost: 800,
    minQuantity: 1,
    maxQuantity: 50,
    description: 'Standard double-hung window',
    lifespan: 25,
    icon: '🪟'
  },
  {
    id: 'window-impact',
    name: 'Window - Impact',
    category: 'Windows & Doors',
    unit: 'each',
    defaultCost: 1500,
    minQuantity: 1,
    maxQuantity: 50,
    description: 'Hurricane impact window',
    lifespan: 30,
    icon: '🛡️'
  },
  {
    id: 'door-entry',
    name: 'Entry Door',
    category: 'Windows & Doors',
    unit: 'each',
    defaultCost: 2000,
    minQuantity: 1,
    maxQuantity: 10,
    description: 'Front entry door with frame',
    lifespan: 30,
    icon: '🚪'
  },
  {
    id: 'door-interior',
    name: 'Interior Door',
    category: 'Windows & Doors',
    unit: 'each',
    defaultCost: 400,
    minQuantity: 1,
    maxQuantity: 30,
    description: 'Interior door with frame',
    lifespan: 30,
    icon: '🚪'
  },
  {
    id: 'garage-door',
    name: 'Garage Door',
    category: 'Windows & Doors',
    unit: 'each',
    defaultCost: 2500,
    minQuantity: 1,
    maxQuantity: 4,
    description: 'Garage door with opener',
    lifespan: 20,
    icon: '🚗'
  },

  // Paint & Finishes
  {
    id: 'paint-interior',
    name: 'Paint - Interior',
    category: 'Paint & Finishes',
    unit: 'sqft',
    defaultCost: 3,
    minQuantity: 100,
    maxQuantity: 20000,
    description: 'Interior painting per sq ft of wall space',
    lifespan: 7,
    icon: '🎨'
  },
  {
    id: 'paint-exterior',
    name: 'Paint - Exterior',
    category: 'Paint & Finishes',
    unit: 'sqft',
    defaultCost: 4,
    minQuantity: 100,
    maxQuantity: 10000,
    description: 'Exterior painting per sq ft',
    lifespan: 10,
    icon: '🏠'
  },
  {
    id: 'cabinet-refinish',
    name: 'Cabinet Refinishing',
    category: 'Paint & Finishes',
    unit: 'lf',
    defaultCost: 150,
    minQuantity: 10,
    maxQuantity: 200,
    description: 'Cabinet refinishing per linear foot',
    lifespan: 15,
    icon: '🗄️'
  },

  // Kitchen & Bath
  {
    id: 'kitchen-countertop-granite',
    name: 'Granite Countertop',
    category: 'Kitchen & Bath',
    unit: 'sqft',
    defaultCost: 80,
    minQuantity: 10,
    maxQuantity: 200,
    description: 'Granite countertop per sq ft',
    lifespan: 30,
    icon: '💎'
  },
  {
    id: 'kitchen-countertop-quartz',
    name: 'Quartz Countertop',
    category: 'Kitchen & Bath',
    unit: 'sqft',
    defaultCost: 90,
    minQuantity: 10,
    maxQuantity: 200,
    description: 'Quartz countertop per sq ft',
    lifespan: 30,
    icon: '✨'
  },
  {
    id: 'kitchen-cabinets',
    name: 'Kitchen Cabinets',
    category: 'Kitchen & Bath',
    unit: 'lf',
    defaultCost: 500,
    minQuantity: 10,
    maxQuantity: 100,
    description: 'Kitchen cabinet replacement per linear foot',
    lifespan: 25,
    icon: '🗄️'
  },
  {
    id: 'bathroom-vanity',
    name: 'Bathroom Vanity',
    category: 'Kitchen & Bath',
    unit: 'each',
    defaultCost: 1500,
    minQuantity: 1,
    maxQuantity: 10,
    description: 'Bathroom vanity with sink and faucet',
    lifespan: 20,
    icon: '🚿'
  },
  {
    id: 'toilet',
    name: 'Toilet',
    category: 'Kitchen & Bath',
    unit: 'each',
    defaultCost: 500,
    minQuantity: 1,
    maxQuantity: 10,
    description: 'Toilet replacement',
    lifespan: 25,
    icon: '🚽'
  },
  {
    id: 'shower-tub',
    name: 'Shower/Tub',
    category: 'Kitchen & Bath',
    unit: 'each',
    defaultCost: 3000,
    minQuantity: 1,
    maxQuantity: 5,
    description: 'Shower or tub replacement',
    lifespan: 20,
    icon: '🛁'
  },

  // Electrical & Plumbing
  {
    id: 'electrical-panel',
    name: 'Electrical Panel',
    category: 'Electrical',
    unit: 'each',
    defaultCost: 3000,
    minQuantity: 1,
    maxQuantity: 2,
    description: 'Main electrical panel upgrade',
    lifespan: 30,
    icon: '⚡'
  },
  {
    id: 'water-heater',
    name: 'Water Heater',
    category: 'Plumbing',
    unit: 'each',
    defaultCost: 1800,
    minQuantity: 1,
    maxQuantity: 3,
    description: 'Tank or tankless water heater',
    lifespan: 12,
    icon: '♨️'
  },
  {
    id: 'plumbing-repipe',
    name: 'Plumbing Re-pipe',
    category: 'Plumbing',
    unit: 'sqft',
    defaultCost: 5,
    minQuantity: 500,
    maxQuantity: 5000,
    description: 'Complete plumbing replacement per sq ft',
    lifespan: 50,
    icon: '🔧'
  },

  // Exterior
  {
    id: 'siding',
    name: 'Siding',
    category: 'Exterior',
    unit: 'sqft',
    defaultCost: 8,
    minQuantity: 100,
    maxQuantity: 5000,
    description: 'Vinyl or fiber cement siding per sq ft',
    lifespan: 25,
    icon: '🏠'
  },
  {
    id: 'fence',
    name: 'Fence',
    category: 'Exterior',
    unit: 'lf',
    defaultCost: 35,
    minQuantity: 20,
    maxQuantity: 1000,
    description: 'Wood or vinyl fence per linear foot',
    lifespan: 20,
    icon: '🚧'
  },
  {
    id: 'driveway-concrete',
    name: 'Driveway - Concrete',
    category: 'Exterior',
    unit: 'sqft',
    defaultCost: 10,
    minQuantity: 100,
    maxQuantity: 5000,
    description: 'Concrete driveway per sq ft',
    lifespan: 30,
    icon: '🚗'
  },
  {
    id: 'landscaping',
    name: 'Landscaping',
    category: 'Exterior',
    unit: 'sqft',
    defaultCost: 5,
    minQuantity: 100,
    maxQuantity: 10000,
    description: 'Basic landscaping per sq ft',
    lifespan: 10,
    icon: '🌳'
  }
];

interface CapitalExpenditureCalculatorProps {
  propertyData?: any;
  onSave?: (items: SelectedItem[], total: number) => void;
}

export function CapitalExpenditureCalculator({ propertyData, onSave }: CapitalExpenditureCalculatorProps) {
  const [selectedItems, setSelectedItems] = useState<SelectedItem[]>([]);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [showSummary, setShowSummary] = useState(true);

  // Get unique categories
  const categories = Array.from(new Set(RENOVATION_ITEMS.map(item => item.category)));

  // Filter items based on search
  const filteredItems = RENOVATION_ITEMS.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group items by category
  const itemsByCategory = categories.reduce((acc, category) => {
    acc[category] = filteredItems.filter(item => item.category === category);
    return acc;
  }, {} as Record<string, RenovationItem[]>);

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleItem = (itemId: string) => {
    const existingIndex = selectedItems.findIndex(si => si.itemId === itemId);
    if (existingIndex >= 0) {
      setSelectedItems(selectedItems.filter(si => si.itemId !== itemId));
    } else {
      const item = RENOVATION_ITEMS.find(i => i.id === itemId);
      if (item) {
        setSelectedItems([...selectedItems, {
          itemId,
          quantity: item.minQuantity
        }]);
      }
    }
  };

  const updateItemQuantity = (itemId: string, quantity: number) => {
    setSelectedItems(selectedItems.map(si =>
      si.itemId === itemId ? { ...si, quantity } : si
    ));
  };

  const updateItemCost = (itemId: string, customCost: number) => {
    setSelectedItems(selectedItems.map(si =>
      si.itemId === itemId ? { ...si, customCost } : si
    ));
  };

  const updateItemNotes = (itemId: string, notes: string) => {
    setSelectedItems(selectedItems.map(si =>
      si.itemId === itemId ? { ...si, notes } : si
    ));
  };

  const getItemCost = (selectedItem: SelectedItem): number => {
    const item = RENOVATION_ITEMS.find(i => i.id === selectedItem.itemId);
    if (!item) return 0;
    const unitCost = selectedItem.customCost || item.defaultCost;

    if (item.unit === 'percentage') {
      return (unitCost * selectedItem.quantity) / 100;
    }
    return unitCost * selectedItem.quantity;
  };

  const getTotalCost = (): number => {
    return selectedItems.reduce((sum, si) => sum + getItemCost(si), 0);
  };

  const getUnitLabel = (unit: string, quantity: number): string => {
    switch (unit) {
      case 'each': return quantity === 1 ? 'unit' : 'units';
      case 'sqft': return 'sq ft';
      case 'percentage': return '%';
      case 'lf': return 'linear ft';
      default: return unit;
    }
  };

  const resetCalculator = () => {
    setSelectedItems([]);
    setSearchTerm('');
  };

  const exportData = () => {
    const data = {
      property: propertyData?.address || 'Unknown Property',
      date: new Date().toISOString(),
      items: selectedItems.map(si => {
        const item = RENOVATION_ITEMS.find(i => i.id === si.itemId);
        return {
          name: item?.name,
          category: item?.category,
          quantity: si.quantity,
          unit: item?.unit,
          unitCost: si.customCost || item?.defaultCost,
          totalCost: getItemCost(si),
          notes: si.notes
        };
      }),
      totalCost: getTotalCost()
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `capital-expenditure-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card id="capital-header-main-1">
        <CardHeader id="capital-header-content-1">
          <div id="capital-header-title-row-1" className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5 text-primary" />
              Capital Expenditure Calculator
            </CardTitle>
            <div id="capital-header-actions-1" className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={resetCalculator}
                disabled={selectedItems.length === 0}
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Reset
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={exportData}
                disabled={selectedItems.length === 0}
              >
                <Download className="h-4 w-4 mr-1" />
                Export
              </Button>
              {onSave && (
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => onSave(selectedItems, getTotalCost())}
                  disabled={selectedItems.length === 0}
                >
                  <Save className="h-4 w-4 mr-1" />
                  Save
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent id="capital-header-stats-1">
          <div id="capital-stats-grid-1" className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div id="capital-stat-total-1" className="text-center">
              <p className="text-sm text-muted-foreground">Total Investment</p>
              <p className="text-2xl font-bold text-primary">
                ${getTotalCost().toLocaleString()}
              </p>
            </div>
            <div id="capital-stat-items-1" className="text-center">
              <p className="text-sm text-muted-foreground">Selected Items</p>
              <p className="text-2xl font-bold">{selectedItems.length}</p>
            </div>
            <div id="capital-stat-categories-1" className="text-center">
              <p className="text-sm text-muted-foreground">Categories</p>
              <p className="text-2xl font-bold">
                {new Set(selectedItems.map(si =>
                  RENOVATION_ITEMS.find(i => i.id === si.itemId)?.category
                )).size}
              </p>
            </div>
            <div id="capital-stat-roi-1" className="text-center">
              <p className="text-sm text-muted-foreground">Est. Value Add</p>
              <p className="text-2xl font-bold text-green-600">
                ${(getTotalCost() * 1.3).toLocaleString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Search */}
      <div id="capital-search-container-1">
        <Input
          placeholder="Search renovation items..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full"
        />
      </div>

      <div id="capital-main-content-1" className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Item Selection */}
        <div id="capital-items-section-1" className="lg:col-span-2 space-y-4">
          {categories.map(category => {
            const categoryItems = itemsByCategory[category];
            if (categoryItems.length === 0) return null;

            const isExpanded = expandedCategories.has(category);
            const selectedCount = selectedItems.filter(si =>
              categoryItems.some(item => item.id === si.itemId)
            ).length;

            return (
              <Card key={category} id={`capital-category-${category.toLowerCase().replace(/\s+/g, '-')}-1`}>
                <CardHeader
                  className="cursor-pointer"
                  onClick={() => toggleCategory(category)}
                  id={`capital-category-header-${category.toLowerCase().replace(/\s+/g, '-')}-1`}
                >
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Wrench className="h-4 w-4" />
                      {category}
                      {selectedCount > 0 && (
                        <Badge variant="secondary">{selectedCount}</Badge>
                      )}
                    </CardTitle>
                    <Button variant="ghost" size="sm">
                      {isExpanded ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                    </Button>
                  </div>
                </CardHeader>
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      id={`capital-category-content-${category.toLowerCase().replace(/\s+/g, '-')}-1`}
                    >
                      <CardContent className="space-y-3">
                        {categoryItems.map(item => {
                          const isSelected = selectedItems.some(si => si.itemId === item.id);
                          const selectedItem = selectedItems.find(si => si.itemId === item.id);

                          return (
                            <div
                              key={item.id}
                              id={`capital-item-${item.id}-1`}
                              className={`p-4 rounded-lg border transition-all ${
                                isSelected ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-gray-300'
                              }`}
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-start gap-3">
                                  <button
                                    onClick={() => toggleItem(item.id)}
                                    className={`mt-1 w-5 h-5 rounded border-2 transition-colors ${
                                      isSelected
                                        ? 'bg-primary border-primary'
                                        : 'border-gray-300 hover:border-primary'
                                    }`}
                                  >
                                    {isSelected && <Check className="w-3 h-3 text-white" />}
                                  </button>
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                      <span className="text-lg">{item.icon}</span>
                                      <h4 className="font-medium">{item.name}</h4>
                                      <Badge variant="outline" className="text-xs">
                                        ${item.defaultCost.toLocaleString()}/{getUnitLabel(item.unit, 1)}
                                      </Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground mt-1">
                                      {item.description}
                                    </p>
                                    {item.lifespan && (
                                      <p className="text-xs text-muted-foreground mt-1">
                                        Lifespan: ~{item.lifespan} years
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {isSelected && selectedItem && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: 'auto', opacity: 1 }}
                                  className="mt-4 space-y-3 border-t pt-3"
                                  id={`capital-item-controls-${item.id}-1`}
                                >
                                  <div className="grid grid-cols-2 gap-3">
                                    <div>
                                      <Label className="text-xs">
                                        Quantity ({getUnitLabel(item.unit, selectedItem.quantity)})
                                      </Label>
                                      {item.unit === 'percentage' ? (
                                        <div className="space-y-2">
                                          <Slider
                                            value={[selectedItem.quantity]}
                                            onValueChange={([v]) => updateItemQuantity(item.id, v)}
                                            min={item.minQuantity}
                                            max={item.maxQuantity}
                                            step={10}
                                            className="mt-2"
                                          />
                                          <div className="text-center font-medium">
                                            {selectedItem.quantity}%
                                          </div>
                                        </div>
                                      ) : (
                                        <Input
                                          type="number"
                                          value={selectedItem.quantity}
                                          onChange={(e) => updateItemQuantity(item.id, Number(e.target.value))}
                                          min={item.minQuantity}
                                          max={item.maxQuantity}
                                          className="mt-1"
                                        />
                                      )}
                                    </div>
                                    <div>
                                      <Label className="text-xs">
                                        Cost per {getUnitLabel(item.unit, 1)}
                                      </Label>
                                      <Input
                                        type="number"
                                        value={selectedItem.customCost || item.defaultCost}
                                        onChange={(e) => updateItemCost(item.id, Number(e.target.value))}
                                        className="mt-1"
                                      />
                                    </div>
                                  </div>
                                  <div>
                                    <Label className="text-xs">Notes (optional)</Label>
                                    <Input
                                      placeholder="Add notes..."
                                      value={selectedItem.notes || ''}
                                      onChange={(e) => updateItemNotes(item.id, e.target.value)}
                                      className="mt-1"
                                    />
                                  </div>
                                  <div className="flex items-center justify-between pt-2 border-t">
                                    <span className="text-sm font-medium">Item Total:</span>
                                    <span className="text-lg font-bold text-primary">
                                      ${getItemCost(selectedItem).toLocaleString()}
                                    </span>
                                  </div>
                                </motion.div>
                              )}
                            </div>
                          );
                        })}
                      </CardContent>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>
            );
          })}
        </div>

        {/* Summary Sidebar */}
        <div id="capital-summary-section-1" className="space-y-4">
          <Card className="sticky top-4">
            <CardHeader id="capital-summary-header-1">
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5" />
                  Investment Summary
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSummary(!showSummary)}
                >
                  {showSummary ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                </Button>
              </CardTitle>
            </CardHeader>
            {showSummary && (
              <CardContent id="capital-summary-content-1" className="space-y-4">
                {selectedItems.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <AlertCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No items selected</p>
                    <p className="text-sm mt-1">Click items to add them to your budget</p>
                  </div>
                ) : (
                  <>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {selectedItems.map(si => {
                        const item = RENOVATION_ITEMS.find(i => i.id === si.itemId);
                        if (!item) return null;

                        return (
                          <div
                            key={si.itemId}
                            id={`capital-summary-item-${si.itemId}-1`}
                            className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span>{item.icon}</span>
                                <span className="text-sm font-medium">{item.name}</span>
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {si.quantity} {getUnitLabel(item.unit, si.quantity)}
                                {si.customCost && si.customCost !== item.defaultCost && (
                                  <span className="ml-1">@ ${si.customCost}</span>
                                )}
                              </div>
                              {si.notes && (
                                <div className="text-xs text-blue-600 mt-1">{si.notes}</div>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">
                                ${getItemCost(si).toLocaleString()}
                              </span>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleItem(si.itemId)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="pt-4 border-t space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Subtotal</span>
                        <span className="font-medium">${getTotalCost().toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Contingency (10%)</span>
                        <span className="font-medium">
                          ${(getTotalCost() * 0.1).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center pt-2 border-t">
                        <span className="font-medium">Total Budget</span>
                        <span className="text-xl font-bold text-primary">
                          ${(getTotalCost() * 1.1).toLocaleString()}
                        </span>
                      </div>
                    </div>

                    {/* ROI Estimate */}
                    <div className="bg-green-50 rounded-lg p-3">
                      <h4 className="text-sm font-medium text-green-800 mb-2">
                        Estimated Value Add
                      </h4>
                      <div className="space-y-1 text-xs text-green-700">
                        <div className="flex justify-between">
                          <span>Conservative (70% ROI)</span>
                          <span className="font-medium">
                            ${(getTotalCost() * 0.7).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Moderate (100% ROI)</span>
                          <span className="font-medium">
                            ${getTotalCost().toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Optimistic (130% ROI)</span>
                          <span className="font-medium">
                            ${(getTotalCost() * 1.3).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}