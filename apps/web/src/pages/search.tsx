import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Search, Filter, MapPin, Building, DollarSign, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { PropertyTable } from '@/components/property-table'
import { api } from '@/api/client'
import { CITIES, USE_CODES } from '@/lib/constants'

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  
  // Filter states
  const [city, setCity] = useState(searchParams.get('city') || '')
  const [useCode, setUseCode] = useState(searchParams.get('use_code') || '')
  const [minValue, setMinValue] = useState(Number(searchParams.get('min_value')) || 0)
  const [maxValue, setMaxValue] = useState(Number(searchParams.get('max_value')) || 10000000)
  const [minScore, setMinScore] = useState(Number(searchParams.get('min_score')) || 0)
  
  // Build query params
  const queryParams = new URLSearchParams()
  if (city) queryParams.append('city', city)
  if (useCode) queryParams.append('main_use', useCode)
  if (minValue > 0) queryParams.append('min_value', minValue.toString())
  if (maxValue < 10000000) queryParams.append('max_value', maxValue.toString())
  if (minScore > 0) queryParams.append('min_score', minScore.toString())
  
  // Fetch properties
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['properties', queryParams.toString()],
    queryFn: () => api.searchProperties(queryParams),
  })
  
  const handleSearch = () => {
    // Update URL params
    const params = new URLSearchParams()
    if (city) params.set('city', city)
    if (useCode) params.set('use_code', useCode)
    if (minValue > 0) params.set('min_value', minValue.toString())
    if (maxValue < 10000000) params.set('max_value', maxValue.toString())
    if (minScore > 0) params.set('min_score', minScore.toString())
    setSearchParams(params)
    
    refetch()
  }
  
  const handleReset = () => {
    setCity('')
    setUseCode('')
    setMinValue(0)
    setMaxValue(10000000)
    setMinScore(0)
    setSearchParams(new URLSearchParams())
    refetch()
  }
  
  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Property Search</h1>
          <p className="text-muted-foreground">
            Search and filter Broward County investment properties
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleReset}>
            Reset Filters
          </Button>
          <Button onClick={handleSearch}>
            <Search className="mr-2 h-4 w-4" />
            Search
          </Button>
        </div>
      </div>
      
      {/* Filters Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Search Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* City Filter */}
          <div className="space-y-2">
            <Label htmlFor="city" className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              City
            </Label>
            <Select value={city} onValueChange={setCity}>
              <SelectTrigger>
                <SelectValue placeholder="Select a city" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Cities</SelectItem>
                {CITIES.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Use Code Filter */}
          <div className="space-y-2">
            <Label htmlFor="use-code" className="flex items-center gap-2">
              <Building className="h-4 w-4" />
              Property Type
            </Label>
            <Select value={useCode} onValueChange={setUseCode}>
              <SelectTrigger>
                <SelectValue placeholder="Select property type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Types</SelectItem>
                {Object.entries(USE_CODES).map(([code, name]) => (
                  <SelectItem key={code} value={code}>
                    {name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Value Range */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Value Range
            </Label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                placeholder="Min"
                value={minValue || ''}
                onChange={(e) => setMinValue(Number(e.target.value))}
                className="w-24"
              />
              <span>to</span>
              <Input
                type="number"
                placeholder="Max"
                value={maxValue === 10000000 ? '' : maxValue}
                onChange={(e) => setMaxValue(Number(e.target.value) || 10000000)}
                className="w-24"
              />
            </div>
          </div>
          
          {/* Score Filter */}
          <div className="space-y-2 col-span-full">
            <Label className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Minimum Score: {minScore}
            </Label>
            <Slider
              value={[minScore]}
              onValueChange={([value]) => setMinScore(value)}
              max={100}
              step={5}
              className="w-full"
            />
          </div>
        </CardContent>
      </Card>
      
      {/* Results Stats */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">{data.length}</div>
              <p className="text-sm text-muted-foreground">Properties Found</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">
                ${(data.reduce((sum: number, p: any) => sum + (p.just_value || 0), 0) / 1000000).toFixed(1)}M
              </div>
              <p className="text-sm text-muted-foreground">Total Value</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">
                {data.length > 0 ? (data.reduce((sum: number, p: any) => sum + (p.score || 0), 0) / data.length).toFixed(1) : '0'}
              </div>
              <p className="text-sm text-muted-foreground">Avg Score</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">
                {data.filter((p: any) => p.score >= 70).length}
              </div>
              <p className="text-sm text-muted-foreground">High Opportunity</p>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>Search Results</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">Loading properties...</div>
          ) : error ? (
            <div className="text-center py-8 text-red-500">
              Error loading properties. Please try again.
            </div>
          ) : data && data.length > 0 ? (
            <PropertyTable properties={data} />
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No properties found. Try adjusting your filters.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}