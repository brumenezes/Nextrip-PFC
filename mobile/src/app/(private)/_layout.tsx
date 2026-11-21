import { Redirect, Stack } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { AppLoading } from '@/components';
import { colors } from '@/design-system';

export default function PrivateLayout() {
  const { token, isRestoring } = useAuth();

  if (isRestoring) return <AppLoading />;
  if (!token) return <Redirect href="/(public)/login" />;

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.background },
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="(tabs)" options={{ animation: 'none' }} />
      <Stack.Screen name="novo-roteiro" />
      <Stack.Screen name="atracoes/[id]" />
      <Stack.Screen name="roteiros/[id]" />
      <Stack.Screen name="trocar-senha" />
      <Stack.Screen name="diagnostico-api" />
    </Stack>
  );
}
