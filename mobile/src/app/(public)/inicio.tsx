import { router } from 'expo-router';
import { useEffect } from 'react';

import { AppLoading } from '@/components';

const INTRO_DURATION_MS = 1_600;

export default function IntroScreen() {
  useEffect(() => {
    const redirectTimer = setTimeout(() => {
      router.replace('/(public)/login');
    }, INTRO_DURATION_MS);

    return () => clearTimeout(redirectTimer);
  }, []);

  return <AppLoading />;
}
