import { type ReactNode, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  page?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  onRowClick?: (item: T) => void;
  className?: string;
}

/* Design.md: Forbid horizontal and vertical divider lines.
   Separation via alternating row fills. Headers: all-caps with 0.05em spacing. */
export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  page = 1,
  totalPages = 1,
  onPageChange,
  onRowClick,
  className,
}: DataTableProps<T>) {
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

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
                  col.className,
                )}
              >
                {col.header}
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
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 mt-1">
          <span className="text-xs text-tertiary">Page {page} of {totalPages}</span>
          <div className="flex gap-1">
            <button
              onClick={() => onPageChange?.(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="p-1 rounded hover:bg-surface-container-low disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => onPageChange?.(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
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
