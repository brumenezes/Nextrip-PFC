import { apiRequest } from '@/api/client';

import type { DetailedItinerary, GenerateItineraryInput, GeneratedItinerary, ItinerarySummary } from './types';

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

export function getItinerary(itineraryId: string) {
  return apiRequest<DetailedItinerary>(`/roteiros/${itineraryId}`, { authenticated: true });
}
