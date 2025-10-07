import { Link } from 'react-router-dom'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ExternalLink, Map, FileText } from 'lucide-react'
import { formatCurrency, formatNumber, getScoreColor, USE_CODES } from '@/lib/constants'

interface Property {
  folio: string
  city: string
  main_use: string
  sub_use?: string
  situs_addr?: string
  owner_raw?: string
  just_value?: number
  assessed_soh?: number
  taxable?: number
  land_sf?: number
  score?: number
  last_sale_date?: string
  last_sale_price?: number
}

interface PropertyTableProps {
  properties: Property[]
}

export function PropertyTable({ properties }: PropertyTableProps) {
  return (
    <div className="relative overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Folio</TableHead>
            <TableHead>Address</TableHead>
            <TableHead>City</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Owner</TableHead>
            <TableHead className="text-right">Value</TableHead>
            <TableHead className="text-right">Land SF</TableHead>
            <TableHead className="text-center">Score</TableHead>
            <TableHead>Last Sale</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {properties.map((property) => (
            <TableRow key={property.folio}>
              <TableCell className="font-medium">
                <Link
                  to={`/property/${property.folio}`}
                  className="text-primary hover:underline"
                >
                  {property.folio}
                </Link>
              </TableCell>
              <TableCell>
                {property.situs_addr || 'N/A'}
              </TableCell>
              <TableCell>{property.city}</TableCell>
              <TableCell>
                <Badge variant="secondary">
                  {USE_CODES[property.main_use] || property.main_use}
                </Badge>
              </TableCell>
              <TableCell className="max-w-[200px] truncate">
                {property.owner_raw || 'N/A'}
              </TableCell>
              <TableCell className="text-right">
                {property.just_value ? formatCurrency(property.just_value) : 'N/A'}
              </TableCell>
              <TableCell className="text-right">
                {property.land_sf ? formatNumber(property.land_sf) : 'N/A'}
              </TableCell>
              <TableCell className="text-center">
                {property.score ? (
                  <Badge className={getScoreColor(property.score)}>
                    {property.score.toFixed(0)}
                  </Badge>
                ) : (
                  'N/A'
                )}
              </TableCell>
              <TableCell>
                {property.last_sale_date ? (
                  <div className="text-sm">
                    <div>{new Date(property.last_sale_date).toLocaleDateString()}</div>
                    {property.last_sale_price && (
                      <div className="text-muted-foreground">
                        {formatCurrency(property.last_sale_price)}
                      </div>
                    )}
                  </div>
                ) : (
                  'N/A'
                )}
              </TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Button
                    size="icon"
                    variant="ghost"
                    asChild
                  >
                    <a
                      href={`https://web.bcpa.net/BcpaClient/#/Property/${property.folio}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="BCPA Record"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    asChild
                  >
                    <a
                      href={`https://www.google.com/maps/search/${encodeURIComponent(
                        property.situs_addr || property.city
                      )}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Google Maps"
                    >
                      <Map className="h-4 w-4" />
                    </a>
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    asChild
                  >
                    <Link
                      to={`/property/${property.folio}`}
                      title="View Details"
                    >
                      <FileText className="h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}