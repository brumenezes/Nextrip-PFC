import { apiRequest } from '@/api/client';
import { ApiError } from '@/api/errors';

import type { Preferences, PreferencesInput } from './types';

export async function getPreferences(userId: string) {
  try {
    return await apiRequest<Preferences>(`/usuarios/${userId}/preferencias`, {
      authenticated: true,
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export function createPreferences(userId: string, input: PreferencesInput) {
  return apiRequest<Preferences>(`/usuarios/${userId}/preferencias`, {
    method: 'POST',
    authenticated: true,
    body: input,
  });
}

export function updatePreferences(userId: string, input: PreferencesInput) {
  return apiRequest<Preferences>(`/usuarios/${userId}/preferencias`, {
    method: 'PUT',
    authenticated: true,
    body: input,
  });
}
