/**
 * DataTable Component
 * ===================
 *
 * A reusable data table component with sorting, pagination, and selection.
 * Designed for displaying property data, sales history, and other records.
 *
 * Features:
 * - Column sorting
 * - Row selection (single and multi)
 * - Pagination
 * - Loading skeleton state
 * - Empty state
 * - Responsive design with horizontal scroll
 * - Keyboard navigation
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
  Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Column<T> {
  id: string;
  header: string;
  accessorKey?: keyof T;
  accessorFn?: (row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

export interface DataTableProps<T> {
  /** Data to display */
  data: T[];
  /** Column definitions */
  columns: Column<T>[];
  /** Unique key for each row */
  getRowId: (row: T) => string;
  /** Enable row selection */
  selectable?: boolean;
  /** Currently selected row IDs */
  selectedIds?: string[];
  /** Callback when selection changes */
  onSelectionChange?: (ids: string[]) => void;
  /** Callback when row is clicked */
  onRowClick?: (row: T) => void;
  /** Enable pagination */
  paginated?: boolean;
  /** Items per page */
  pageSize?: number;
  /** Current page (0-indexed) */
  currentPage?: number;
  /** Total items (for server-side pagination) */
  totalItems?: number;
  /** Callback when page changes */
  onPageChange?: (page: number) => void;
  /** Loading state */
  isLoading?: boolean;
  /** Empty state message */
  emptyMessage?: string;
  /** Additional class names */
  className?: string;
}

type SortDirection = 'asc' | 'desc' | null;

/**
 * DataTableSkeleton displays loading state for the table
 */
const DataTableSkeleton: React.FC<{ columns: number; rows: number }> = ({
  columns,
  rows,
}) => (
  <div className="animate-pulse">
    <div className="h-12 bg-neutral-100 rounded-t-lg" />
    {Array.from({ length: rows }).map((_, i) => (
      <div
        key={i}
        className="h-14 border-b border-neutral-100 flex items-center px-4 gap-4"
      >
        {Array.from({ length: columns }).map((_, j) => (
          <div
            key={j}
            className="h-4 bg-neutral-200 rounded flex-1"
            style={{ maxWidth: `${100 / columns}%` }}
          />
        ))}
      </div>
    ))}
  </div>
);

/**
 * DataTable component for displaying tabular data
 */
export function DataTable<T>({
  data,
  columns,
  getRowId,
  selectable = false,
  selectedIds = [],
  onSelectionChange,
  onRowClick,
  paginated = false,
  pageSize = 10,
  currentPage = 0,
  totalItems,
  onPageChange,
  isLoading = false,
  emptyMessage = 'No data available',
  className,
}: DataTableProps<T>) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  // Handle sorting
  const handleSort = useCallback((columnId: string) => {
    setSortColumn((prev) => {
      if (prev !== columnId) {
        setSortDirection('asc');
        return columnId;
      }
      setSortDirection((dir) => {
        if (dir === 'asc') return 'desc';
        if (dir === 'desc') return null;
        return 'asc';
      });
      return dir === 'desc' ? null : columnId;
    });
  }, []);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return data;

    const column = columns.find((c) => c.id === sortColumn);
    if (!column) return data;

    return [...data].sort((a, b) => {
      let aVal: any;
      let bVal: any;

      if (column.accessorFn) {
        aVal = column.accessorFn(a);
        bVal = column.accessorFn(b);
      } else if (column.accessorKey) {
        aVal = a[column.accessorKey];
        bVal = b[column.accessorKey];
      }

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = aVal < bVal ? -1 : 1;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [data, columns, sortColumn, sortDirection]);

  // Paginate data (client-side)
  const paginatedData = useMemo(() => {
    if (!paginated || totalItems !== undefined) return sortedData;
    const start = currentPage * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, paginated, currentPage, pageSize, totalItems]);

  // Calculate total pages
  const totalPages = useMemo(() => {
    const total = totalItems ?? data.length;
    return Math.ceil(total / pageSize);
  }, [totalItems, data.length, pageSize]);

  // Handle row selection
  const handleSelectAll = useCallback(() => {
    if (!onSelectionChange) return;
    const allIds = paginatedData.map(getRowId);
    const allSelected = allIds.every((id) => selectedIds.includes(id));
    if (allSelected) {
      onSelectionChange(selectedIds.filter((id) => !allIds.includes(id)));
    } else {
      onSelectionChange([...new Set([...selectedIds, ...allIds])]);
    }
  }, [paginatedData, getRowId, selectedIds, onSelectionChange]);

  const handleSelectRow = useCallback(
    (id: string) => {
      if (!onSelectionChange) return;
      if (selectedIds.includes(id)) {
        onSelectionChange(selectedIds.filter((i) => i !== id));
      } else {
        onSelectionChange([...selectedIds, id]);
      }
    },
    [selectedIds, onSelectionChange]
  );

  // Loading state
  if (isLoading) {
    return (
      <div className={cn('rounded-lg border border-neutral-200 overflow-hidden', className)}>
        <DataTableSkeleton columns={columns.length} rows={pageSize} />
      </div>
    );
  }

  // Empty state
  if (data.length === 0) {
    return (
      <div
        className={cn(
          'rounded-lg border border-neutral-200 bg-white p-8 text-center',
          className
        )}
      >
        <p className="text-neutral-500">{emptyMessage}</p>
      </div>
    );
  }

  const allRowsSelected = paginatedData.every((row) =>
    selectedIds.includes(getRowId(row))
  );
  const someRowsSelected =
    !allRowsSelected &&
    paginatedData.some((row) => selectedIds.includes(getRowId(row)));

  return (
    <div
      className={cn(
        'rounded-lg border border-neutral-200 bg-white overflow-hidden',
        className
      )}
    >
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-neutral-50 border-b border-neutral-200">
              {/* Selection checkbox column */}
              {selectable && (
                <th className="w-12 px-4 py-3">
                  <button
                    onClick={handleSelectAll}
                    className={cn(
                      'w-5 h-5 rounded border-2 flex items-center justify-center',
                      'transition-colors duration-150',
                      allRowsSelected
                        ? 'bg-[#0ABAB5] border-[#0ABAB5]'
                        : someRowsSelected
                        ? 'bg-[#0ABAB5]/50 border-[#0ABAB5]'
                        : 'border-neutral-300 hover:border-neutral-400'
                    )}
                    aria-label="Select all rows"
                  >
                    {(allRowsSelected || someRowsSelected) && (
                      <Check size={14} className="text-white" />
                    )}
                  </button>
                </th>
              )}

              {/* Column headers */}
              {columns.map((column) => (
                <th
                  key={column.id}
                  className={cn(
                    'px-4 py-3 text-sm font-semibold text-neutral-700',
                    column.align === 'center' && 'text-center',
                    column.align === 'right' && 'text-right',
                    column.className
                  )}
                  style={{ width: column.width }}
                >
                  {column.sortable !== false ? (
                    <button
                      onClick={() => handleSort(column.id)}
                      className="inline-flex items-center gap-1 hover:text-neutral-900"
                    >
                      {column.header}
                      {sortColumn === column.id ? (
                        sortDirection === 'asc' ? (
                          <ChevronUp size={16} />
                        ) : (
                          <ChevronDown size={16} />
                        )
                      ) : (
                        <ChevronsUpDown size={16} className="text-neutral-400" />
                      )}
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row) => {
              const rowId = getRowId(row);
              const isSelected = selectedIds.includes(rowId);

              return (
                <tr
                  key={rowId}
                  onClick={() => onRowClick?.(row)}
                  className={cn(
                    'border-b border-neutral-100 last:border-0',
                    'transition-colors duration-150',
                    onRowClick && 'cursor-pointer hover:bg-neutral-50',
                    isSelected && 'bg-[#0ABAB5]/5'
                  )}
                >
                  {/* Selection checkbox */}
                  {selectable && (
                    <td className="px-4 py-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectRow(rowId);
                        }}
                        className={cn(
                          'w-5 h-5 rounded border-2 flex items-center justify-center',
                          'transition-colors duration-150',
                          isSelected
                            ? 'bg-[#0ABAB5] border-[#0ABAB5]'
                            : 'border-neutral-300 hover:border-neutral-400'
                        )}
                        aria-label={`Select row ${rowId}`}
                      >
                        {isSelected && <Check size={14} className="text-white" />}
                      </button>
                    </td>
                  )}

                  {/* Data cells */}
                  {columns.map((column) => (
                    <td
                      key={column.id}
                      className={cn(
                        'px-4 py-3 text-sm text-neutral-700',
                        column.align === 'center' && 'text-center',
                        column.align === 'right' && 'text-right',
                        column.className
                      )}
                    >
                      {column.accessorFn
                        ? column.accessorFn(row)
                        : column.accessorKey
                        ? String(row[column.accessorKey] ?? '')
                        : null}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {paginated && totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-neutral-200 bg-neutral-50">
          <div className="text-sm text-neutral-500">
            Showing {currentPage * pageSize + 1} to{' '}
            {Math.min((currentPage + 1) * pageSize, totalItems ?? data.length)} of{' '}
            {totalItems ?? data.length}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange?.(currentPage - 1)}
              disabled={currentPage === 0}
              className={cn(
                'p-2 rounded-lg transition-colors',
                currentPage === 0
                  ? 'text-neutral-300 cursor-not-allowed'
                  : 'text-neutral-600 hover:bg-neutral-200'
              )}
              aria-label="Previous page"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="text-sm text-neutral-600">
              Page {currentPage + 1} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange?.(currentPage + 1)}
              disabled={currentPage >= totalPages - 1}
              className={cn(
                'p-2 rounded-lg transition-colors',
                currentPage >= totalPages - 1
                  ? 'text-neutral-300 cursor-not-allowed'
                  : 'text-neutral-600 hover:bg-neutral-200'
              )}
              aria-label="Next page"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataTable;
