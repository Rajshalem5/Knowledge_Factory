/**
 * CSV export utility
 */

export function exportToCsv(
  data: Record<string, unknown>[],
  columns: { key: string; header: string }[],
  filename = 'export.csv'
): void {
  if (data.length === 0) return;

  const headerRow = columns.map(c => c.header).join(',');
  const rows = data.map(item =>
    columns
      .map(c => {
        const val = item[c.key];
        if (val == null) return '';
        const str = String(val);
        // Escape quotes and wrap in quotes if contains comma, quote, or newline
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      })
      .join(',')
  );

  const csv = [headerRow, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
