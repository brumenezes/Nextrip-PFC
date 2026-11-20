import { Redirect, Stack } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { AppLoading } from '@/components';

export default function PublicLayout() {
  const { token, isRestoring } = useAuth();

  if (isRestoring) {
    return <AppLoading />;
  }
  if (token) return <Redirect href="/(private)" />;

  return <Stack screenOptions={{ headerShown: false }} />;
}
