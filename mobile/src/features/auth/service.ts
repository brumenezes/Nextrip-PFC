import { apiRequest } from '@/api/client';

import type { LoginRequest, TokenResponse } from './types';

export function login(input: LoginRequest) {
  return apiRequest<TokenResponse>('/auth/login', { method: 'POST', body: input });
}
