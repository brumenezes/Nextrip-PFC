import { Redirect } from 'expo-router';

import { useAuth } from '@/auth/AuthProvider';
import { AppLoading } from '@/components';

export default function IndexScreen() {
  const { token, isRestoring } = useAuth();

  if (isRestoring) {
    return <AppLoading />;
  }

  return <Redirect href={token ? '/(private)' : '/(public)/inicio'} />;
}
