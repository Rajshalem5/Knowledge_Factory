import { api } from './client';

export const selectionApi = {
  getRanking: (cycleId: string) => api.get(`/api/selection/ranking/${cycleId}`),
};
