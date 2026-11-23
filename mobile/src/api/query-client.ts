import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        const status = typeof error === 'object' && error && 'status' in error ? error.status : 0;
        return status !== 401 && status !== 403 && status !== 404 && failureCount < 2;
      },
      staleTime: 30_000,
    },
    mutations: { retry: false },
  },
});
