import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PropertyData } from '@/hooks/usePropertyData'

interface OwnershipTabProps {
  data: PropertyData
}

export function OwnershipTab({ data }: OwnershipTabProps) {
  const { bcpaData, sunbizData, tppData } = data

  return (
    <div className="space-y-6">
      {/* Current Owner Information */}
      <Card>
        <CardHeader>
          <CardTitle>Current Owner</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <span className="text-muted-foreground">Owner Name</span>
              <p className="text-xl font-semibold">
                {bcpaData?.owner_name || 'Unknown Owner'}
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <span className="text-muted-foreground">Mailing Address</span>
                <div className="text-sm">
                  {bcpaData?.owner_address_line_1 && <p>{bcpaData.owner_address_line_1}</p>}
                  {bcpaData?.owner_address_line_2 && <p>{bcpaData.owner_address_line_2}</p>}
                  {bcpaData?.owner_city && bcpaData?.owner_state && (
                    <p>{bcpaData.owner_city}, {bcpaData.owner_state} {bcpaData.owner_zip}</p>
                  )}
                </div>
              </div>
              
              <div>
                <span className="text-muted-foreground">Owner Type</span>
                <div className="space-y-2">
                  {sunbizData.length > 0 ? (
                    <Badge variant="secondary">Business Entity</Badge>
                  ) : (
                    <Badge variant="outline">Individual/Trust</Badge>
                  )}
                  {bcpaData?.homestead_exemption && (
                    <Badge variant="default">Homesteaded</Badge>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Business Entity Information */}
      {sunbizData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Business Entity Details ({sunbizData.length} entities found)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {sunbizData.map((entity, index) => (
                <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm text-muted-foreground">Entity Name</span>
                      <p className="font-semibold">{entity.entity_name || 'Unknown'}</p>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Entity Type</span>
                      <p className="font-semibold">{entity.entity_type || 'Unknown'}</p>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Status</span>
                      <Badge 
                        variant={entity.entity_status === 'ACTIVE' ? 'default' : 'secondary'}
                      >
                        {entity.entity_status || 'Unknown'}
                      </Badge>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Filing Date</span>
                      <p className="font-semibold">
                        {entity.filing_date ? new Date(entity.filing_date).toLocaleDateString() : 'Unknown'}
                      </p>
                    </div>
                  </div>
                  
                  {entity.registered_agent && (
                    <div className="mt-4 pt-4 border-t">
                      <span className="text-sm text-muted-foreground">Registered Agent</span>
                      <p className="font-semibold">{entity.registered_agent}</p>
                      {entity.registered_agent_address && (
                        <p className="text-sm text-muted-foreground">{entity.registered_agent_address}</p>
                      )}
                    </div>
                  )}
                  
                  {entity.principal_address && (
                    <div className="mt-2">
                      <span className="text-sm text-muted-foreground">Principal Address</span>
                      <p className="text-sm">{entity.principal_address}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tangible Personal Property */}
      {tppData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Business Personal Property ({tppData.length} accounts)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {tppData.map((tpp, index) => (
                <div key={index} className="p-3 bg-gray-50 rounded border">
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <span className="text-sm text-muted-foreground">Business Name</span>
                      <p className="font-semibold">{tpp.business_name || 'Unknown'}</p>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Account Value</span>
                      <p className="font-semibold">
                        ${tpp.assessed_value ? parseInt(tpp.assessed_value).toLocaleString() : '-'}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Tax Year</span>
                      <p className="font-semibold">{tpp.tax_year || 'Unknown'}</p>
                    </div>
                  </div>
                  
                  {tpp.business_description && (
                    <div className="mt-3 pt-3 border-t">
                      <span className="text-sm text-muted-foreground">Business Type</span>
                      <p className="text-sm">{tpp.business_description}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Investment Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Ownership Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sunbizData.length > 0 ? (
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-700 mb-2">🏢 Business Ownership Detected</h4>
                <ul className="text-sm space-y-1">
                  <li>• Property owned by business entity - may indicate investment property</li>
                  <li>• Potential for portfolio/bulk acquisition opportunities</li>
                  <li>• Consider reaching out to registered agent or business principals</li>
                  <li>• May have more flexible negotiation terms than individual owners</li>
                </ul>
              </div>
            ) : bcpaData?.homestead_exemption ? (
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-700 mb-2">🏠 Owner-Occupied Property</h4>
                <ul className="text-sm space-y-1">
                  <li>• Homesteaded property - likely owner-occupied</li>
                  <li>• May be less motivated to sell</li>
                  <li>• Consider market timing and personal circumstances</li>
                  <li>• Homestead exemption provides tax benefits to owner</li>
                </ul>
              </div>
            ) : (
              <div className="p-4 bg-orange-50 rounded-lg">
                <h4 className="font-semibold text-orange-700 mb-2">❓ Investment Property Potential</h4>
                <ul className="text-sm space-y-1">
                  <li>• No homestead exemption - likely investment/rental property</li>
                  <li>• Owner may be more motivated to sell</li>
                  <li>• Consider cash flow and cap rate analysis</li>
                  <li>• May be part of larger investment portfolio</li>
                </ul>
              </div>
            )}
            
            {tppData.length > 0 && (
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-semibold text-purple-700 mb-2">🏪 Commercial Activity</h4>
                <ul className="text-sm space-y-1">
                  <li>• Business personal property on site</li>
                  <li>• May have commercial zoning or mixed-use potential</li>
                  <li>• Consider business operations impact on property value</li>
                  <li>• Potential for higher income generation</li>
                </ul>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
