import { useQuery } from '@tanstack/react-query';
import { hiringCyclesApi } from '../api/hiring-cycles';

export function useHiringCycles() {
  return useQuery({
    queryKey: ['hiring-cycles'],
    queryFn: hiringCyclesApi.getAll,
  });
}
