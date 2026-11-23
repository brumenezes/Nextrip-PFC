import { apiRequest } from '@/api/client';

import type { ChangePasswordRequest, CreateUserRequest, UpdateUserRequest, UserResponse } from './types';

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

export function getCurrentUser() {
  return apiRequest<UserResponse>('/usuarios/me', { authenticated: true });
}

export function updateCurrentUser(input: UpdateUserRequest) {
  return apiRequest<UserResponse>('/usuarios/me', {
    authenticated: true,
    method: 'PATCH',
    body: input,
  });
}
