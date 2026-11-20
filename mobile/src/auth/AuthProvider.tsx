import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';

import { configureApiSession } from '@/api/client';
import { queryClient } from '@/api/query-client';

import { sessionStorage } from './session-storage';
import { getUserIdFromToken } from './jwt';

type AuthContextValue = {
  token: string | null;
  userId: string | null;
  displayName: string | null;
  isRestoring: boolean;
  signIn: (token: string, displayName: string | null) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  const signOut = useCallback(async () => {
    setToken(null);
    setDisplayName(null);
    configureApiSession({ token: null });
    queryClient.clear();
    await sessionStorage.clearToken();
  }, []);

  const signIn = useCallback(async (newToken: string, newDisplayName: string | null) => {
    await sessionStorage.setToken(newToken);
    if (newDisplayName) await sessionStorage.setDisplayName(newDisplayName);
    setToken(newToken);
    setDisplayName(newDisplayName);
  }, []);

  useEffect(() => {
    sessionStorage
      .clearToken()
      .then(() => {
        setToken(null);
        setDisplayName(null);
      })
      .finally(() => setIsRestoring(false));
  }, []);

  useEffect(() => {
    configureApiSession({ token, onUnauthorized: () => void signOut() });
  }, [signOut, token]);

  const userId = useMemo(() => getUserIdFromToken(token), [token]);
  const value = useMemo(
    () => ({ token, userId, displayName, isRestoring, signIn, signOut }),
    [displayName, isRestoring, signIn, signOut, token, userId],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth deve ser usado dentro de AuthProvider.');
  return context;
}
