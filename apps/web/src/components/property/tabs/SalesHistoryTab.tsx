import { PropertyData } from '@/hooks/usePropertyData'
import { SalesHistoryTabUpdated } from './SalesHistoryTabUpdated'

interface SalesHistoryTabProps {
  data: PropertyData
}

export function SalesHistoryTab({ data }: SalesHistoryTabProps) {
  // Extract parcel ID from the property data
  const parcelId = data.parcelId || data.parcel_id || (data as any).id || '';

  // Use the updated sales history component that fetches its own data
  return <SalesHistoryTabUpdated parcelId={parcelId} data={data} />;
}