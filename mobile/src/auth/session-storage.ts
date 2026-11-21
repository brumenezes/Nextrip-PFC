import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const TOKEN_KEY = 'nextrip.access-token';
const DISPLAY_NAME_KEY = 'nextrip.display-name';
const FULL_NAME_KEY = 'nextrip.full-name';
const EMAIL_KEY = 'nextrip.email';
let webSessionToken: string | null = null;
let webDisplayName: string | null = null;
const webKnownNames = new Map<string, string>();

function knownNameKey(email: string) {
  const safeEmail = email.trim().toLocaleLowerCase('pt-BR').replace(/[^a-z0-9]/g, '_');
  return `nextrip.known-name.${safeEmail}`;
}

export const sessionStorage = {
  getToken: async () => {
    if (Platform.OS === 'web') return webSessionToken;
    return SecureStore.getItemAsync(TOKEN_KEY);
  },
  setToken: async (token: string) => {
    if (Platform.OS === 'web') {
      webSessionToken = token;
      return;
    }
    await SecureStore.setItemAsync(TOKEN_KEY, token);
  },
  getDisplayName: async () => {
    if (Platform.OS === 'web') return webDisplayName;
    return SecureStore.getItemAsync(DISPLAY_NAME_KEY);
  },
  setDisplayName: async (displayName: string) => {
    if (Platform.OS === 'web') {
      webDisplayName = displayName;
      return;
    }
    await SecureStore.setItemAsync(DISPLAY_NAME_KEY, displayName);
  },
  setCurrentIdentity: async (identity: { fullName: string | null; email: string }) => {
    if (Platform.OS === 'web') {
      return;
    }
    const writes = [SecureStore.setItemAsync(EMAIL_KEY, identity.email)];
    if (identity.fullName) writes.push(SecureStore.setItemAsync(FULL_NAME_KEY, identity.fullName));
    await Promise.all(writes);
  },
  getKnownDisplayName: async (email: string) => {
    const key = knownNameKey(email);
    if (Platform.OS === 'web') return webKnownNames.get(key) ?? null;
    return SecureStore.getItemAsync(key);
  },
  setKnownDisplayName: async (email: string, displayName: string) => {
    const key = knownNameKey(email);
    if (Platform.OS === 'web') {
      webKnownNames.set(key, displayName);
      return;
    }
    await SecureStore.setItemAsync(key, displayName);
  },
  clearToken: async () => {
    if (Platform.OS === 'web') {
      webSessionToken = null;
      webDisplayName = null;
      return;
    }
    await Promise.all([
      SecureStore.deleteItemAsync(TOKEN_KEY),
      SecureStore.deleteItemAsync(DISPLAY_NAME_KEY),
      SecureStore.deleteItemAsync(FULL_NAME_KEY),
      SecureStore.deleteItemAsync(EMAIL_KEY),
    ]);
  },
};
