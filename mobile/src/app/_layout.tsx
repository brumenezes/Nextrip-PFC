import { QueryClientProvider } from '@tanstack/react-query';
import {
  Inter_400Regular,
  Inter_500Medium,
  Inter_600SemiBold,
  Inter_700Bold,
  useFonts,
} from '@expo-google-fonts/inter';
import * as SplashScreen from 'expo-splash-screen';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useState } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { queryClient } from '@/api/query-client';
import { AuthProvider, useAuth } from '@/auth/AuthProvider';
import { AnimatedSplash } from '@/components';
import { colors } from '@/design-system';

void SplashScreen.preventAutoHideAsync();

const rootScreenOptions = {
  headerShown: false,
  animation: 'none',
  contentStyle: { backgroundColor: colors.background },
} as const;

function AppNavigator() {
  const { isRestoring } = useAuth();
  const [startupFinished, setStartupFinished] = useState(false);
  const finishStartup = useCallback(() => setStartupFinished(true), []);

  if (!startupFinished) {
    return <AnimatedSplash ready={!isRestoring} onFinish={finishStartup} />;
  }

  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={rootScreenOptions}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(public)" />
        <Stack.Screen name="(private)" />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Inter_700Bold,
  });

  useEffect(() => {
    if (fontsLoaded) void SplashScreen.hideAsync();
  }, [fontsLoaded]);

  if (!fontsLoaded) return null;

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AppNavigator />
        </AuthProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
