import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react';

import { configureApiSession } from '@/api/client';
import { queryClient } from '@/api/query-client';

import { sessionStorage } from './session-storage';
import { getUserIdFromToken } from './jwt';

type AuthContextValue = {
  token: string | null;
  userId: string | null;
  displayName: string | null;
  fullName: string | null;
  email: string | null;
  isRestoring: boolean;
  signIn: (token: string, identity: { displayName: string | null; fullName: string | null; email: string }) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState<string | null>(null);
  const [fullName, setFullName] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  const signOut = useCallback(async () => {
    setToken(null);
    setDisplayName(null);
    setFullName(null);
    setEmail(null);
    configureApiSession({ token: null });
    queryClient.clear();
    await sessionStorage.clearToken();
  }, []);

  const signIn = useCallback(async (
    newToken: string,
    identity: { displayName: string | null; fullName: string | null; email: string },
  ) => {
    await sessionStorage.setToken(newToken);
    if (identity.displayName) await sessionStorage.setDisplayName(identity.displayName);
    await sessionStorage.setCurrentIdentity({ fullName: identity.fullName, email: identity.email });
    setToken(newToken);
    setDisplayName(identity.displayName);
    setFullName(identity.fullName);
    setEmail(identity.email);
  }, []);

  useEffect(() => {
    sessionStorage
      .clearToken()
      .then(() => {
        setToken(null);
        setDisplayName(null);
        setFullName(null);
        setEmail(null);
      })
      .finally(() => setIsRestoring(false));
  }, []);

  useEffect(() => {
    configureApiSession({ token, onUnauthorized: () => void signOut() });
  }, [signOut, token]);

  const userId = useMemo(() => getUserIdFromToken(token), [token]);
  const value = useMemo(
    () => ({ token, userId, displayName, fullName, email, isRestoring, signIn, signOut }),
    [displayName, email, fullName, isRestoring, signIn, signOut, token, userId],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth deve ser usado dentro de AuthProvider.');
  return context;
}
