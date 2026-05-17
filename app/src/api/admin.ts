/**
 * Admin API client
 * /api/admin endpoints
 */

import { api } from './client';

export const adminApi = {
  getAuditLogs: (page = 1, limit = 100) =>
    api.get<{ data: any[]; page: number; limit: number }>(`/api/admin/audit-logs?page=${page}&limit=${limit}`),

  exportDatabase: () =>
    api.get<Record<string, any>>('/api/admin/export-db'),
};