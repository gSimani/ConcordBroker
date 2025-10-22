#!/bin/bash
# Auto-generated hook deletion script
# Run this to delete redundant hooks that have no active imports

cd "$(dirname "$0")/.."
echo "🗑️  Deleting redundant hooks..."

echo "Deleting useBatchSalesData..."
rm -f apps/web/src/hooks/useBatchSalesData.ts
echo "Deleting useCompletePropertyData..."
rm -f apps/web/src/hooks/useCompletePropertyData.ts
echo "Deleting useComprehensivePropertyData..."
rm -f apps/web/src/hooks/useComprehensivePropertyData.ts
echo "Deleting useJupyterPropertyData..."
rm -f apps/web/src/hooks/useJupyterPropertyData.ts
echo "Deleting useOptimizedPropertySearchV2..."
rm -f apps/web/src/hooks/useOptimizedPropertySearchV2.ts
echo "Deleting useOptimizedSearch..."
rm -f apps/web/src/hooks/useOptimizedSearch.ts
echo "Deleting useOptimizedSupabase..."
rm -f apps/web/src/hooks/useOptimizedSupabase.ts
echo "Deleting useOwnerProperties..."
rm -f apps/web/src/hooks/useOwnerProperties.ts
echo "Deleting usePropertyAppraiser..."
rm -f apps/web/src/hooks/usePropertyAppraiser.ts
echo "Deleting usePropertyAutocomplete..."
rm -f apps/web/src/hooks/usePropertyAutocomplete.ts
echo "Deleting usePropertyData..."
rm -f apps/web/src/hooks/usePropertyData.ts
echo "Deleting usePropertyDataImproved..."
rm -f apps/web/src/hooks/usePropertyDataImproved.ts
echo "Deleting usePropertyDataOptimized..."
rm -f apps/web/src/hooks/usePropertyDataOptimized.ts
echo "Deleting usePySparkData..."
rm -f apps/web/src/hooks/usePySparkData.ts
echo "Deleting useSmartDebounce..."
rm -f apps/web/src/hooks/useSmartDebounce.ts
echo "Deleting useSQLAlchemyData..."
rm -f apps/web/src/hooks/useSQLAlchemyData.ts
echo "Deleting useSupabaseProperties..."
rm -f apps/web/src/hooks/useSupabaseProperties.ts
echo "Deleting useTrackedData..."
rm -f apps/web/src/hooks/useTrackedData.ts

echo "✅ Deleted ${18} redundant hooks"
echo "Run: git status"