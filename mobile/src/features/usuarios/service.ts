import { apiRequest } from '@/api/client';

import type { ChangePasswordRequest, CreateUserRequest, UserResponse } from './types';

export function createUser(input: CreateUserRequest) {
  return apiRequest<UserResponse>('/usuarios', { method: 'POST', body: input });
}

export function changePassword(input: ChangePasswordRequest) {
  return apiRequest<void>('/usuarios/me/senha', {
    authenticated: true,
    method: 'PUT',
    body: input,
  });
}
