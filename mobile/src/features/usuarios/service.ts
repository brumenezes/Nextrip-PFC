import { apiRequest } from '@/api/client';

import type { CreateUserRequest, UserResponse } from './types';

export function createUser(input: CreateUserRequest) {
  return apiRequest<UserResponse>('/usuarios', { method: 'POST', body: input });
}
