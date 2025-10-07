import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { supabase } from '@/lib/supabase'
import type { EntityMatch } from '@/types/api'
import { useElementId } from '@/utils/generateElementId'
import '@/styles/elegant-property.css'
import {
  Building2,
  User,
  Briefcase,
  Link,
  TrendingUp,
  Calendar,
  MapPin,
  DollarSign,
  CheckCircle,
  AlertCircle,
  Info,
  ExternalLink,
  Network,
  FileText,
  Users
} from 'lucide-react'

interface BusinessEntitySectionProps {
  parcelId: string
  ownerName: string
  address?: string
}

// Use EntityMatch from types/api.ts

interface EntityDetails {
  entity: any
  events: any[]
  portfolio: {
    property_count: number
    total_value: number
    cities: string[]
  }
  related_entities: any[]
}

export function BusinessEntitySection({ parcelId, ownerName, address }: BusinessEntitySectionProps) {
  const { generateId, generateTestId } = useElementId('business-entity');
  const [matches, setMatches] = useState<EntityMatch[]>([])
  const [selectedEntity, setSelectedEntity] = useState<EntityMatch | null>(null)
  const [entityDetails, setEntityDetails] = useState<EntityDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)

  useEffect(() => {
    fetchEntityMatches()
  }, [parcelId])

  const fetchEntityMatches = async () => {
    setLoading(true)
    try {
      // Get existing matches from database
      const { data: existingMatches } = await supabase
        .from('property_entity_matches')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('match_confidence', { ascending: false })

      if (existingMatches && existingMatches.length > 0) {
        setMatches(existingMatches)
        setSelectedEntity(existingMatches[0])
        await fetchEntityDetails(existingMatches[0].entity_doc_number)
      } else {
        // Trigger new matching
        await runEntityMatching()
      }
    } catch (error) {
      console.error('Error fetching entity matches:', error)
    } finally {
      setLoading(false)
    }
  }

  const runEntityMatching = async () => {
    try {
      // Call API to run matching algorithm
      const response = await fetch('/api/match-entity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parcel_id: parcelId,
          owner_name: ownerName,
          owner_addr: address
        })
      })

      if (response.ok) {
        const newMatches = await response.json()
        setMatches(newMatches)
        if (newMatches.length > 0) {
          setSelectedEntity(newMatches[0])
          await fetchEntityDetails(newMatches[0].entity_doc_number)
        }
      }
    } catch (error) {
      console.error('Error running entity matching:', error)
    }
  }

  const fetchEntityDetails = async (docNumber: string) => {
    try {
      // Get entity from Sunbiz tables
      const { data: corporate } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .eq('doc_number', docNumber)
        .single()

      const { data: events } = await supabase
        .from('sunbiz_corporate_events')
        .select('*')
        .eq('doc_number', docNumber)
        .order('event_date', { ascending: false })
        .limit(10)

      // Get portfolio summary
      const { data: portfolio } = await supabase
        .from('entity_portfolio_summary')
        .select('*')
        .eq('entity_doc_number', docNumber)
        .single()

      // Get related entities
      const { data: related } = await supabase
        .from('entity_relationships')
        .select('*')
        .or(`entity1_doc_number.eq.${docNumber},entity2_doc_number.eq.${docNumber}`)
        .limit(5)

      setEntityDetails({
        entity: corporate,
        events: events || [],
        portfolio: portfolio || {
          property_count: 1,
          total_value: 0,
          cities: []
        },
        related_entities: related || []
      })
    } catch (error) {
      console.error('Error fetching entity details:', error)
    }
  }

  const verifyMatch = async (match: EntityMatch) => {
    setVerifying(true)
    try {
      const { error } = await supabase
        .from('property_entity_matches')
        .update({
          verified: true,
          verified_date: new Date().toISOString()
        })
        .eq('parcel_id', parcelId)
        .eq('entity_doc_number', match.entity_doc_number)

      if (!error) {
        // Refresh matches
        await fetchEntityMatches()
      }
    } catch (error) {
      console.error('Error verifying match:', error)
    } finally {
      setVerifying(false)
    }
  }

  const getConfidenceBadge = (score: number) => {
    if (score >= 90) return <Badge className="badge-elegant badge-gold">Very High</Badge>
    if (score >= 80) return <Badge className="badge-elegant">High</Badge>
    if (score >= 70) return <Badge className="badge-elegant">Medium</Badge>
    return <Badge className="badge-elegant">Low</Badge>
  }

  const getMatchTypeIcon = (type: string) => {
    switch (type) {
      case 'exact': return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'fuzzy': return <Info className="h-4 w-4 text-blue-600" />
      case 'pattern': return <AlertCircle className="h-4 w-4 text-yellow-600" />
      case 'address': return <MapPin className="h-4 w-4 text-purple-600" />
      case 'agent': return <User className="h-4 w-4 text-orange-600" />
      default: return <Building2 className="h-4 w-4 text-gray-600" />
    }
  }

  if (loading) {
    return (
      <Card id={generateId('loading', 'container', 1)}>
        <CardContent className="p-6">
          <div id={generateId('loading', 'skeleton', 1)} className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card id={generateId('main', 'container', 1)} className="elegant-card animate-elegant">
      <CardHeader className="elegant-card-header">
        <CardTitle className="elegant-card-title flex items-center gap-2 gold-accent">
          <Building2 className="h-5 w-5" />
          Business Entity Information
        </CardTitle>
      </CardHeader>
      <CardContent>
        {matches.length === 0 ? (
          <div id={generateId('empty', 'state', 1)} className="text-center py-8">
            <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">No business entity matches found</p>
            <Button
              onClick={runEntityMatching}
              className="btn-outline-executive"
              data-testid={generateTestId('run', 'entity-matching')}
            >
              <span>Run Entity Matching</span>
            </Button>
          </div>
        ) : (
          <div id={generateId('content', 'tabs-container', 1)}>
            <Tabs defaultValue="matches" className="w-full">
              <div id={generateId('tabs', 'navigation', 1)} className="tabs-executive flex justify-center mb-6">
                <TabsTrigger
                  value="matches"
                  className="tab-executive"
                  data-testid={generateTestId('tab', 'matches')}
                >
                  Matches ({matches.length})
                </TabsTrigger>
                <TabsTrigger
                  value="details"
                  className="tab-executive"
                  data-testid={generateTestId('tab', 'details')}
                >
                  Entity Details
                </TabsTrigger>
                <TabsTrigger
                  value="portfolio"
                  className="tab-executive"
                  data-testid={generateTestId('tab', 'portfolio')}
                >
                  Portfolio
                </TabsTrigger>
                <TabsTrigger
                  value="network"
                  className="tab-executive"
                  data-testid={generateTestId('tab', 'network')}
                >
                  Network
                </TabsTrigger>
              </div>

            <TabsContent value="matches" className="space-y-4">
              {matches.map((match, idx) => (
                <div
                  key={match.entity_doc_number}
                  id={generateId('match', 'item', idx + 1)}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedEntity?.entity_doc_number === match.entity_doc_number
                      ? 'border-blue-600 bg-blue-50'
                      : 'hover:border-gray-400'
                  }`}
                  onClick={() => {
                    setSelectedEntity(match)
                    fetchEntityDetails(match.entity_doc_number)
                  }}
                  data-testid={generateTestId('select', `match-${idx + 1}`)}
                >
                  <div id={generateId('match', 'content', idx + 1)} className="flex justify-between items-start">
                    <div id={generateId('match', 'details', idx + 1)} className="flex-1">
                      <div id={generateId('match', 'header', idx + 1)} className="flex items-center gap-2 mb-2">
                        {getMatchTypeIcon(match.match_type)}
                        <h4 className="font-semibold">{match.entity_name}</h4>
                        {idx === 0 && <Badge variant="default">Best Match</Badge>}
                      </div>

                      <div id={generateId('match', 'info-grid', idx + 1)} className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Document #:</span>
                          <span className="ml-2 font-mono">{match.entity_doc_number}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Type:</span>
                          <span className="ml-2 capitalize">{match.entity_type}</span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="mb-2">
                        {getConfidenceBadge(match.match_confidence)}
                      </div>
                      <div className="text-sm text-gray-600">
                        {match.match_confidence.toFixed(1)}% match
                      </div>
                      {!match.verified && (
                        <Button
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            verifyMatch(match)
                          }}
                          disabled={verifying}
                          className="btn-outline-executive mt-2"
                        >
                          <span>Verify</span>
                        </Button>
                      )}
                    </div>
                  </div>

                  <Progress value={match.match_confidence} className="mt-3 h-2" />
                </div>
              ))}
            </TabsContent>

            <TabsContent value="details">
              {selectedEntity && entityDetails?.entity && (
                <div className="space-y-4">
                  {/* Entity Information */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold mb-2">Registration Details</h4>
                      <dl className="space-y-2 text-sm">
                        <div>
                          <dt className="text-gray-600">Status:</dt>
                          <dd className="font-medium">
                            <Badge variant={entityDetails.entity.status === 'ACTIVE' ? 'default' : 'secondary'}>
                              {entityDetails.entity.status}
                            </Badge>
                          </dd>
                        </div>
                        <div>
                          <dt className="text-gray-600">Filing Date:</dt>
                          <dd>{new Date(entityDetails.entity.filing_date).toLocaleDateString()}</dd>
                        </div>
                        <div>
                          <dt className="text-gray-600">State:</dt>
                          <dd>{entityDetails.entity.state_country || 'Florida'}</dd>
                        </div>
                        <div>
                          <dt className="text-gray-600">EIN:</dt>
                          <dd className="font-mono">{entityDetails.entity.ein || 'N/A'}</dd>
                        </div>
                      </dl>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2">Registered Agent</h4>
                      <p className="text-sm">{entityDetails.entity.registered_agent || 'Not specified'}</p>
                      
                      <h4 className="font-semibold mt-4 mb-2">Principal Address</h4>
                      <p className="text-sm">
                        {entityDetails.entity.prin_addr1}<br />
                        {entityDetails.entity.prin_city}, {entityDetails.entity.prin_state} {entityDetails.entity.prin_zip}
                      </p>
                    </div>
                  </div>

                  {/* Recent Events */}
                  {entityDetails.events.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Recent Events</h4>
                      <div className="space-y-2">
                        {entityDetails.events.slice(0, 5).map((event, idx) => (
                          <div key={idx} className="flex items-center gap-3 text-sm">
                            <Calendar className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-600">
                              {new Date(event.event_date).toLocaleDateString()}
                            </span>
                            <span>{event.event_type}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <Button
                    className="btn-outline-executive w-full"
                    onClick={() => window.open(`https://dos.fl.gov/sunbiz/search`, '_blank')}
                  >
                    <span className="flex items-center">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View on Sunbiz
                    </span>
                  </Button>
                </div>
              )}
            </TabsContent>

            <TabsContent value="portfolio">
              {entityDetails?.portfolio && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Building2 className="h-4 w-4 text-blue-600" />
                          <span className="text-sm text-gray-600">Properties</span>
                        </div>
                        <p className="text-2xl font-bold">
                          {entityDetails.portfolio.property_count || 1}
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <DollarSign className="h-4 w-4 text-green-600" />
                          <span className="text-sm text-gray-600">Portfolio Value</span>
                        </div>
                        <p className="text-2xl font-bold">
                          ${((entityDetails.portfolio.total_value || 0) / 1000000).toFixed(1)}M
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <MapPin className="h-4 w-4 text-purple-600" />
                          <span className="text-sm text-gray-600">Cities</span>
                        </div>
                        <p className="text-2xl font-bold">
                          {entityDetails.portfolio.cities?.length || 1}
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {entityDetails.portfolio.cities && (
                    <div>
                      <h4 className="font-semibold mb-2">Property Locations</h4>
                      <div className="flex flex-wrap gap-2">
                        {entityDetails.portfolio.cities.map(city => (
                          <Badge key={city} variant="outline">{city}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>

            <TabsContent value="network">
              {entityDetails?.related_entities && entityDetails.related_entities.length > 0 ? (
                <div className="space-y-4">
                  <h4 className="font-semibold">Related Entities</h4>
                  {entityDetails.related_entities.map((rel, idx) => (
                    <div key={idx} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Network className="h-4 w-4 text-blue-600" />
                          <span className="font-medium">
                            {rel.entity2_name || rel.entity1_name}
                          </span>
                        </div>
                        <Badge variant="outline">{rel.relationship_type}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-600">
                  No related entities found
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
        )}
      </CardContent>
    </Card>
  )
}