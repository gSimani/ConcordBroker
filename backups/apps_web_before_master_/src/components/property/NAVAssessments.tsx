import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Receipt, Building2, AlertCircle, RefreshCw } from 'lucide-react';
import {
  useNAVAssessments,
  formatNAVAmount,
  getNAVAssessmentIcon,
  getNAVAssessmentColor,
  NAVAssessment
} from '@/hooks/useNAVAssessments';
import { generateElementId } from '@/utils/generateElementId';

interface NAVAssessmentsProps {
  parcelId: string;
  showHeader?: boolean;
  compact?: boolean;
}

const NAVAssessmentItem: React.FC<{ assessment: NAVAssessment; index: number }> = ({
  assessment,
  index
}) => (
  <div
    id={generateElementId('nav', 'assessment', 'item', index)}
    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
  >
    <div id={generateElementId('nav', 'assessment', 'details', index)} className="flex items-center space-x-3">
      <span
        id={generateElementId('nav', 'assessment', 'icon', index)}
        className="text-xl"
      >
        {getNAVAssessmentIcon(assessment.assessment_description)}
      </span>
      <div id={generateElementId('nav', 'assessment', 'info', index)}>
        <p
          id={generateElementId('nav', 'assessment', 'description', index)}
          className={`font-medium text-sm ${getNAVAssessmentColor(assessment.assessment_description)}`}
        >
          {assessment.assessment_description}
        </p>
        <p
          id={generateElementId('nav', 'assessment', 'metadata', index)}
          className="text-xs text-gray-500"
        >
          Code: {assessment.levy_description_code} • Function: {assessment.function_code}
        </p>
      </div>
    </div>
    <div id={generateElementId('nav', 'assessment', 'amount', index)} className="text-right">
      <p className="font-semibold text-gray-900">
        {formatNAVAmount(assessment.assessment_amount)}
      </p>
    </div>
  </div>
);

const NAVAssessments: React.FC<NAVAssessmentsProps> = ({
  parcelId,
  showHeader = true,
  compact = false
}) => {
  const { navData, isLoading, error, refetch } = useNAVAssessments(parcelId);

  if (isLoading) {
    return (
      <Card id={generateElementId('nav', 'assessments', 'loading-card', 1)}>
        {showHeader && (
          <CardHeader id={generateElementId('nav', 'assessments', 'loading-header', 1)}>
            <CardTitle id={generateElementId('nav', 'assessments', 'loading-title', 1)} className="flex items-center space-x-2">
              <Receipt className="w-5 h-5" />
              <span>NAV Assessments</span>
            </CardTitle>
          </CardHeader>
        )}
        <CardContent id={generateElementId('nav', 'assessments', 'loading-content', 1)} className="space-y-3">
          <Skeleton id={generateElementId('nav', 'assessments', 'skeleton', 1)} className="h-4 w-3/4" />
          <Skeleton id={generateElementId('nav', 'assessments', 'skeleton', 2)} className="h-12 w-full" />
          <Skeleton id={generateElementId('nav', 'assessments', 'skeleton', 3)} className="h-12 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card id={generateElementId('nav', 'assessments', 'error-card', 1)}>
        {showHeader && (
          <CardHeader id={generateElementId('nav', 'assessments', 'error-header', 1)}>
            <CardTitle id={generateElementId('nav', 'assessments', 'error-title', 1)} className="flex items-center space-x-2">
              <Receipt className="w-5 h-5" />
              <span>NAV Assessments</span>
            </CardTitle>
          </CardHeader>
        )}
        <CardContent id={generateElementId('nav', 'assessments', 'error-content', 1)}>
          <Alert id={generateElementId('nav', 'assessments', 'error-alert', 1)}>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription id={generateElementId('nav', 'assessments', 'error-description', 1)}>
              Error loading NAV assessments: {error}
              <button
                id={generateElementId('nav', 'assessments', 'retry-button', 1)}
                onClick={refetch}
                className="ml-2 text-blue-600 hover:text-blue-700 underline"
              >
                Try again
              </button>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!navData) {
    return (
      <Card id={generateElementId('nav', 'assessments', 'no-data-card', 1)}>
        {showHeader && (
          <CardHeader id={generateElementId('nav', 'assessments', 'no-data-header', 1)}>
            <CardTitle id={generateElementId('nav', 'assessments', 'no-data-title', 1)} className="flex items-center space-x-2">
              <Receipt className="w-5 h-5" />
              <span>NAV Assessments</span>
            </CardTitle>
          </CardHeader>
        )}
        <CardContent id={generateElementId('nav', 'assessments', 'no-data-content', 1)}>
          <div id={generateElementId('nav', 'assessments', 'no-data-message', 1)} className="text-center py-6 text-gray-500">
            <Building2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No Non-Ad Valorem assessments found for this property.</p>
            <p className="text-sm mt-1">This property may not have special assessments.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const CompactView = () => (
    <div id={generateElementId('nav', 'assessments', 'compact-view', 1)} className="space-y-2">
      <div id={generateElementId('nav', 'assessments', 'compact-header', 1)} className="flex items-center justify-between">
        <div id={generateElementId('nav', 'assessments', 'compact-title', 1)} className="flex items-center space-x-2">
          <Receipt className="w-4 h-4" />
          <span className="font-medium text-sm">NAV Assessments</span>
          <Badge id={generateElementId('nav', 'assessments', 'count-badge', 1)} variant="secondary" className="text-xs">
            {navData.assessment_count}
          </Badge>
        </div>
        <div id={generateElementId('nav', 'assessments', 'compact-total', 1)} className="text-sm font-semibold">
          {formatNAVAmount(navData.total_assessments)}
        </div>
      </div>

      {navData.assessments.slice(0, 2).map((assessment, index) => (
        <div
          key={index}
          id={generateElementId('nav', 'assessments', 'compact-item', index)}
          className="flex items-center justify-between text-xs p-2 bg-gray-50 rounded"
        >
          <span id={generateElementId('nav', 'assessments', 'compact-desc', index)} className="flex items-center space-x-1">
            <span>{getNAVAssessmentIcon(assessment.assessment_description)}</span>
            <span className="truncate max-w-32">{assessment.assessment_description}</span>
          </span>
          <span id={generateElementId('nav', 'assessments', 'compact-amount', index)} className="font-medium">
            {formatNAVAmount(assessment.assessment_amount)}
          </span>
        </div>
      ))}

      {navData.assessments.length > 2 && (
        <p id={generateElementId('nav', 'assessments', 'more-indicator', 1)} className="text-xs text-gray-500 text-center">
          +{navData.assessments.length - 2} more assessments
        </p>
      )}
    </div>
  );

  if (compact) {
    return <CompactView />;
  }

  return (
    <Card id={generateElementId('nav', 'assessments', 'full-card', 1)}>
      {showHeader && (
        <CardHeader id={generateElementId('nav', 'assessments', 'full-header', 1)}>
          <CardTitle id={generateElementId('nav', 'assessments', 'full-title', 1)} className="flex items-center justify-between">
            <div id={generateElementId('nav', 'assessments', 'title-section', 1)} className="flex items-center space-x-2">
              <Receipt className="w-5 h-5" />
              <span>Non-Ad Valorem Assessments</span>
              <Badge id={generateElementId('nav', 'assessments', 'year-badge', 1)} variant="outline">
                {navData.tax_year}
              </Badge>
            </div>
            <div id={generateElementId('nav', 'assessments', 'summary-section', 1)} className="text-right">
              <p className="text-lg font-bold text-green-600">
                {formatNAVAmount(navData.total_assessments)}
              </p>
              <p className="text-xs text-gray-500">
                {navData.assessment_count} assessment{navData.assessment_count !== 1 ? 's' : ''}
              </p>
            </div>
          </CardTitle>
        </CardHeader>
      )}

      <CardContent id={generateElementId('nav', 'assessments', 'full-content', 1)}>
        <div id={generateElementId('nav', 'assessments', 'county-info', 1)} className="mb-4 p-3 bg-blue-50 rounded-lg">
          <div id={generateElementId('nav', 'assessments', 'county-details', 1)} className="flex items-center justify-between">
            <div id={generateElementId('nav', 'assessments', 'county-name', 1)}>
              <p className="font-medium text-blue-900">{navData.county_name} County</p>
              <p className="text-sm text-blue-700">Parcel: {navData.parcel_id}</p>
            </div>
            <Badge id={generateElementId('nav', 'assessments', 'county-badge', 1)} className="bg-blue-600">
              Code {navData.county_code}
            </Badge>
          </div>
        </div>

        <div id={generateElementId('nav', 'assessments', 'assessments-list', 1)} className="space-y-3">
          {navData.assessments.map((assessment, index) => (
            <NAVAssessmentItem
              key={index}
              assessment={assessment}
              index={index + 1}
            />
          ))}
        </div>

        <div id={generateElementId('nav', 'assessments', 'footer-info', 1)} className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600">
            Non-Ad Valorem (NAV) assessments are special charges for specific services like
            fire protection, waste collection, or drainage improvements. These are separate
            from regular property taxes and appear on your tax bill.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default NAVAssessments;