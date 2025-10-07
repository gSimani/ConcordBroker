import React from 'react';
import { DollarSign, Calendar, FileText, ExternalLink, Loader2 } from 'lucide-react';
import { useLastQualifiedSale } from '@/hooks/useLastQualifiedSale';

interface SalesHistoryProps {
  parcelId: string;
  county: string;
  // Sales data passed from parent component
  lastQualifiedSale?: {
    sale_date: string;
    sale_price: number;
    instrument_type?: string;
    book_page?: string;
    qualification?: string;
  } | null;
  hasQualifiedSale?: boolean;
  // Legacy props for backwards compatibility (will be overridden by dynamic data)
  salePrice?: number;
  saleDate?: string;
  saleQualification?: string;
  bookPage?: string;
  instrumentType?: string;
}

interface CountyClerkLink {
  name: string;
  url: string;
  searchParam?: string;
}

// County clerk official records links for Florida
const COUNTY_CLERK_LINKS: Record<string, CountyClerkLink> = {
  'MIAMI-DADE': {
    name: 'Miami-Dade Clerk',
    url: 'https://www.miami-dadeclerk.com/official-records-search',
  },
  'BROWARD': {
    name: 'Broward Clerk',
    url: 'https://officialrecords.broward.org/AcclaimWeb',
  },
  'PALM BEACH': {
    name: 'Palm Beach Clerk',
    url: 'https://officialrecords.mypalmbeachclerk.com/ORIPublicAccess',
  },
  'ORANGE': {
    name: 'Orange County Clerk',
    url: 'https://myorangeclerk.com/official-records/',
  },
  'HILLSBOROUGH': {
    name: 'Hillsborough Clerk',
    url: 'https://oncore.hillsclerk.com/',
  },
  'PINELLAS': {
    name: 'Pinellas Clerk',
    url: 'https://www.pinellasclerk.com/aspinclude2/ASPInclude.asp?PageURL=RecordsSearch.asp',
  },
  'DUVAL': {
    name: 'Duval Clerk',
    url: 'https://officialrecords.coj.net/AcclaimWeb/',
  },
  'LEE': {
    name: 'Lee County Clerk',
    url: 'https://recordings.leeclerk.org/',
  },
  'POLK': {
    name: 'Polk County Clerk',
    url: 'https://polk.clerk.of.courts.real.estate.records.search/',
  },
  'COLLIER': {
    name: 'Collier County Clerk',
    url: 'https://www.collierclerk.com/recording-information',
  },
  'MANATEE': {
    name: 'Manatee County Clerk',
    url: 'https://www.manateeclerk.com/recording-information',
  },
  'SARASOTA': {
    name: 'Sarasota County Clerk',
    url: 'https://www.sarasotaclerk.com/recording-information',
  }
};

const formatCurrency = (value?: number): string => {
  if (!value && value !== 0) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatSaleDate = (dateString?: string): string => {
  if (!dateString) return 'N/A';

  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  } catch {
    return 'N/A';
  }
};

const formatDeedType = (qualification?: string): string => {
  if (!qualification) return '';

  // Common deed type abbreviations and their full forms
  const deedTypes: Record<string, string> = {
    'WD': 'Warranty Deed',
    'QCD': 'Quick Claim Deed',
    'CD': 'Corrective Deed',
    'SD': 'Special Deed',
    'TD': 'Tax Deed',
    'DEED': 'Deed',
    'MORTGAGE': 'Mortgage',
    'LIEN': 'Lien',
    'FORECLOSURE': 'Foreclosure',
    'SHERIFF': 'Sheriff\'s Deed'
  };

  const upper = qualification.toUpperCase();
  return deedTypes[upper] || qualification;
};

const getCountyClerkLink = (county: string, parcelId: string): string => {
  const countyKey = county.toUpperCase().replace(/\s+/g, '-');
  const clerkInfo = COUNTY_CLERK_LINKS[countyKey];

  if (clerkInfo) {
    return clerkInfo.url;
  }

  // Generic search for Florida counties not in our list
  return `https://www.google.com/search?q="${parcelId}"+${encodeURIComponent(county)}+county+florida+official+records`;
};

const getCountyClerkName = (county: string): string => {
  const countyKey = county.toUpperCase().replace(/\s+/g, '-');
  const clerkInfo = COUNTY_CLERK_LINKS[countyKey];
  return clerkInfo ? clerkInfo.name : `${county} County Records`;
};

export function SalesHistoryCard({ parcelId, county, lastQualifiedSale, hasQualifiedSale }: SalesHistoryProps) {
  // Only use hook if no props data provided
  const shouldUseHook = !lastQualifiedSale && hasQualifiedSale === undefined;
  const { sale: hookSale, loading, error } = useLastQualifiedSale(shouldUseHook ? parcelId : '');

  // Debug logging to trace data flow (only when sales data exists)
  if (lastQualifiedSale || hasQualifiedSale) {
    console.log(`[SalesHistoryCard] Sales data found for ${parcelId}:`, {
      lastQualifiedSale,
      hasQualifiedSale,
      hookSale,
      shouldUseHook
    });
  }

  // Strict priority: Props first, then hook as fallback
  let sale = null;
  let hasSale = false;

  if (lastQualifiedSale || hasQualifiedSale !== undefined) {
    // Use props data (from parent/API)
    sale = lastQualifiedSale;
    hasSale = hasQualifiedSale || false;
    if (lastQualifiedSale) {
      console.log(`[SalesHistoryCard] Using props sale data for ${parcelId}: $${sale?.sale_price}`);
    }
  } else if (shouldUseHook) {
    // Fallback to hook data
    sale = hookSale;
    hasSale = hookSale !== null;
    if (hookSale) {
      console.log(`[SalesHistoryCard] Using hook sale data for ${parcelId}: $${sale?.sale_price}`);
    }
  }

  const clerkLink = getCountyClerkLink(county, parcelId);
  const clerkName = getCountyClerkName(county);

  // Loading state - only show if using hook
  if (shouldUseHook && loading) {
    return (
      <div
        id={`sales-history-${parcelId}`}
        className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 rounded-lg"
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 bg-gray-200 rounded-full">
            <Loader2 className="w-4 h-4 text-gray-500 animate-spin" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-1">Sales History</h3>
            <p className="text-sm text-gray-600">Loading recent sales...</p>
          </div>
        </div>
      </div>
    );
  }

  // No sale found, error state, or sale price too low
  if (!hasSale || !sale || (shouldUseHook && error) || (sale && sale.sale_price < 1000)) {
    return (
      <div
        id={`sales-history-${parcelId}`}
        className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 rounded-lg"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 bg-gray-200 rounded-full">
              <DollarSign className="w-4 h-4 text-gray-500" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-1">Sales History</h3>
              <p className="text-sm text-gray-600">No recent sales over $1,000 on record</p>
            </div>
          </div>

          <a
            href={clerkLink}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-300 rounded-md text-xs font-medium text-gray-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200"
            onClick={(e) => e.stopPropagation()}
            title={`Search ${clerkName} for parcel ${parcelId}`}
          >
            <FileText className="w-3 h-3" />
            County Records
            <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
          </a>
        </div>
      </div>
    );
  }

  // Sale found - show enhanced design
  return (
    <div
      id={`sales-history-${parcelId}`}
      className="p-4 bg-gradient-to-br from-emerald-50 via-blue-50 to-indigo-50 border-2 border-emerald-200 rounded-lg hover:shadow-lg hover:border-emerald-300 transition-all duration-300"
    >
      <div className="space-y-3">
        {/* Header with enhanced styling */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full shadow-sm">
              <DollarSign className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-emerald-800 mb-0.5">Last Sale</h3>
              <div className="flex items-center gap-2 text-xs text-emerald-600">
                <Calendar className="w-3 h-3" />
                <span className="font-medium">{formatSaleDate(sale.sale_date)}</span>
              </div>
            </div>
          </div>

          {/* Sale price prominently displayed */}
          <div className="text-right">
            <div className="text-lg font-bold text-emerald-800 leading-none">
              {formatCurrency(sale.sale_price)}
            </div>
            <div className="text-xs text-emerald-600 mt-0.5">
              Sale Price
            </div>
          </div>
        </div>

        {/* Sale details */}
        <div className="space-y-2 pt-1 border-t border-emerald-100">
          {/* Deed type and book/page */}
          <div className="flex items-center justify-between text-xs">
            {sale.instrument_type && (
              <div className="flex items-center gap-1.5">
                <FileText className="w-3 h-3 text-emerald-600" />
                <span className="text-emerald-700 font-medium">
                  {sale.instrument_type}
                </span>
              </div>
            )}

            {sale.book_page && (
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-emerald-600 rounded-sm flex items-center justify-center">
                  <span className="text-[6px] font-bold text-white">#</span>
                </div>
                <span className="text-emerald-700 font-medium">
                  {sale.book_page}
                </span>
              </div>
            )}
          </div>

          {/* County records link - improved styling */}
          <div className="flex justify-end pt-2">
            <a
              href={clerkLink}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center gap-2 px-3 py-2 bg-white/80 backdrop-blur-sm border border-emerald-300 rounded-md text-xs font-medium text-emerald-700 hover:text-emerald-800 hover:border-emerald-400 hover:bg-white transition-all duration-200 shadow-sm hover:shadow-md"
              onClick={(e) => e.stopPropagation()}
              title={`View deed records for parcel ${parcelId} on ${clerkName}`}
            >
              <ExternalLink className="w-3 h-3" />
              <span>View Deed</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}