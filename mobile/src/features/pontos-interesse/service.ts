import { apiRequest } from '@/api/client';

import type { PointOfInterest } from './types';

export function listPointsOfInterest() {
  return apiRequest<PointOfInterest[]>('/pontos-interesse');
}
