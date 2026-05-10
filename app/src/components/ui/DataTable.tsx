import { type ReactNode, useState } from 'react';
import { ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => ReactNode;
  className?: string;
  sortable?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  page?: number;
  total_pages?: number;
  onPageChange?: (page: number) => void;
  onRowClick?: (item: T) => void;
  className?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (column: string) => void;
}

/* Design.md: Forbid horizontal and vertical divider lines.
   Separation via alternating row fills. Headers: all-caps with 0.05em spacing. */
export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  page = 1,
  total_pages = 1,
  onPageChange,
  onRowClick,
  className,
  sortBy,
  sortOrder,
  onSort,
}: DataTableProps<T>) {
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  const renderSortIcon = (colKey: string) => {
    if (sortBy !== colKey) return <ArrowUpDown size={11} className="ml-1 opacity-30" />;
    return sortOrder === 'asc' ? <ArrowUp size={11} className="ml-1" /> : <ArrowDown size={11} className="ml-1" />;
  };

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full text-sm">
        <thead>
          <tr>
            {columns.map(col => (
              <th
                key={col.key}
                className={cn(
                  'text-left px-4 py-3 text-[11px] font-medium uppercase tracking-architectural text-tertiary',
                  col.sortable && 'cursor-pointer select-none hover:text-on-surface transition-colors',
                  col.className,
                )}
                onClick={() => col.sortable && onSort?.(col.key)}
              >
                <span className="inline-flex items-center">
                  {col.header}
                  {col.sortable && renderSortIcon(col.key)}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => {
            const key = keyExtractor(item);
            return (
              <tr
                key={key}
                onClick={() => onRowClick?.(item)}
                onMouseEnter={() => setHoveredRow(key)}
                onMouseLeave={() => setHoveredRow(null)}
                className={cn(
                  'transition-colors',
                  onRowClick && 'cursor-pointer',
                  /* Alternating row fills */
                  index % 2 === 0 ? 'bg-[var(--bg-layer2)]' : 'bg-[var(--bg-layer1)]',
                  hoveredRow === key && 'bg-surface-container-low!',
                )}
              >
                {columns.map(col => (
                  <td key={col.key} className={cn('px-4 py-3 leading-relaxed', col.className)}>
                    {col.render
                      ? col.render(item)
                      : String((item as Record<string, unknown>)[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      {total_pages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 mt-1">
          <span className="text-xs text-tertiary">Page {page} of {total_pages}</span>
          <div className="flex gap-1">
            <button
              onClick={() => onPageChange?.(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="p-1 rounded hover:bg-surface-container-low disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => onPageChange?.(Math.min(total_pages, page + 1))}
              disabled={page >= total_pages}
              className="p-1 rounded hover:bg-surface-container-low disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
