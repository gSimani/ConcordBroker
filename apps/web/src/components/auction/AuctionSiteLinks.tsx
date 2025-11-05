import { ExternalLink, Gavel, FileText, Info, Key } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useAuctionSites } from '@/hooks/useAuctionSites'
import { cn } from '@/lib/utils'

interface AuctionSiteLinksProps {
  county: string | null | undefined
  /** Show as inline buttons instead of card (default: false) */
  inline?: boolean
  /** Show only foreclosure auctions (default: show all available) */
  foreclosureOnly?: boolean
  /** Show only tax deed auctions (default: show all available) */
  taxDeedOnly?: boolean
  /** Custom className */
  className?: string
}

export function AuctionSiteLinks({
  county,
  inline = false,
  foreclosureOnly = false,
  taxDeedOnly = false,
  className
}: AuctionSiteLinksProps) {
  const { auctionSite, loading, error, credentials } = useAuctionSites(county)

  // Don't render if no county provided
  if (!county) return null

  // Loading state
  if (loading) {
    return (
      <div className={cn('flex items-center gap-2 text-sm text-muted-foreground', className)}>
        <span className="animate-pulse">Loading auction sites...</span>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <Alert variant="destructive" className={className}>
        <AlertDescription>
          Failed to load auction sites: {error.message}
        </AlertDescription>
      </Alert>
    )
  }

  // No auction site found for this county
  if (!auctionSite) {
    return (
      <Alert className={className}>
        <Info className="h-4 w-4" />
        <AlertDescription>
          No online auction sites found for {county} County.
        </AlertDescription>
      </Alert>
    )
  }

  // Coming soon state
  if (auctionSite.site_type === 'coming_soon') {
    return (
      <Alert className={className}>
        <Info className="h-4 w-4" />
        <AlertDescription>
          {county} County auction sites are coming soon to RealAuction.
        </AlertDescription>
      </Alert>
    )
  }

  // Filter based on props
  const showForeclosure = !taxDeedOnly && auctionSite.has_foreclosure
  const showTaxDeed = !foreclosureOnly && auctionSite.has_tax_deed

  // If nothing to show after filtering
  if (!showForeclosure && !showTaxDeed) {
    return null
  }

  // Inline button layout
  if (inline) {
    return (
      <div className={cn('flex flex-wrap items-center gap-2', className)}>
        {showForeclosure && auctionSite.foreclosure_url && (
          <Button
            variant="outline"
            size="sm"
            asChild
            className="gap-2"
          >
            <a
              href={auctionSite.foreclosure_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Gavel className="h-4 w-4" />
              Foreclosure Auctions
              <ExternalLink className="h-3 w-3" />
            </a>
          </Button>
        )}

        {showTaxDeed && auctionSite.tax_deed_url && (
          <Button
            variant="outline"
            size="sm"
            asChild
            className="gap-2"
          >
            <a
              href={auctionSite.tax_deed_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <FileText className="h-4 w-4" />
              Tax Deed Auctions
              <ExternalLink className="h-3 w-3" />
            </a>
          </Button>
        )}

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-2">
                <Key className="h-4 w-4" />
                Login
              </Button>
            </TooltipTrigger>
            <TooltipContent className="space-y-1">
              <p className="font-semibold">RealAuction Login</p>
              <p className="text-xs">Username: <span className="font-mono">{credentials.username}</span></p>
              <p className="text-xs">Password: <span className="font-mono">{credentials.password}</span></p>
              <p className="text-xs text-muted-foreground mt-2">{auctionSite.login_location}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    )
  }

  // Card layout (default)
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Auction Sites</CardTitle>
            <CardDescription>{county} County</CardDescription>
          </div>
          <Badge variant="secondary" className="text-xs">
            {auctionSite.site_type === 'combined' ? 'Combined Site' : 'RealAuction'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Auction Site Buttons */}
        <div className="flex flex-col gap-2">
          {showForeclosure && auctionSite.foreclosure_url && (
            <Button
              variant="default"
              asChild
              className="w-full justify-start gap-2"
            >
              <a
                href={auctionSite.foreclosure_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Gavel className="h-4 w-4" />
                <span className="flex-1 text-left">Foreclosure Auctions</span>
                <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
          )}

          {showTaxDeed && auctionSite.tax_deed_url && (
            <Button
              variant="default"
              asChild
              className="w-full justify-start gap-2"
            >
              <a
                href={auctionSite.tax_deed_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <FileText className="h-4 w-4" />
                <span className="flex-1 text-left">Tax Deed Auctions</span>
                <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
          )}
        </div>

        {/* Login Credentials */}
        <Alert>
          <Key className="h-4 w-4" />
          <AlertDescription className="space-y-2">
            <p className="font-semibold text-sm">Login Credentials</p>
            <div className="space-y-1 text-xs">
              <p>
                <span className="text-muted-foreground">Username:</span>{' '}
                <span className="font-mono font-semibold">{credentials.username}</span>
              </p>
              <p>
                <span className="text-muted-foreground">Password:</span>{' '}
                <span className="font-mono font-semibold">{credentials.password}</span>
              </p>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {auctionSite.login_location}
            </p>
          </AlertDescription>
        </Alert>

        {/* Additional Notes */}
        {auctionSite.notes && (
          <p className="text-xs text-muted-foreground">
            <Info className="h-3 w-3 inline mr-1" />
            {auctionSite.notes}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
