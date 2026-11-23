const apiUrl = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/$/, '');

if (!apiUrl && !__DEV__) {
  throw new Error('EXPO_PUBLIC_API_URL não foi configurada.');
}

export const env = {
  apiUrl: apiUrl ?? 'http://10.0.2.2:8000',
} as const;
