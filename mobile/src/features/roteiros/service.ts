import { apiRequest } from '@/api/client';

import type { GenerateItineraryInput, GeneratedItinerary, ItinerarySummary } from './types';

export function listItineraries() {
  return apiRequest<ItinerarySummary[]>('/roteiros', { authenticated: true });
}

export function generateItinerary(input: GenerateItineraryInput) {
  return apiRequest<GeneratedItinerary>('/roteiros/gerar', {
    authenticated: true,
    method: 'POST',
    body: input,
  });
}
