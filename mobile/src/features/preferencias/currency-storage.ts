import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

export type TravelCurrency = 'BRL';

export const TRAVEL_CURRENCIES: readonly {
  code: TravelCurrency;
  label: string;
  symbol: string;
}[] = [
  { code: 'BRL', label: 'Real', symbol: 'R$' },
];

const webCurrencies = new Map<string, TravelCurrency>();

function storageKey(userId: string) {
  return `nextrip.currency.${userId}`;
}

function isTravelCurrency(value: string | null): value is TravelCurrency {
  return TRAVEL_CURRENCIES.some((currency) => currency.code === value);
}

export async function getPreferredCurrency(userId: string): Promise<TravelCurrency> {
  if (Platform.OS === 'web') return webCurrencies.get(userId) ?? 'BRL';
  const storedCurrency = await SecureStore.getItemAsync(storageKey(userId));
  return isTravelCurrency(storedCurrency) ? storedCurrency : 'BRL';
}

export async function setPreferredCurrency(userId: string, currency: TravelCurrency) {
  if (Platform.OS === 'web') {
    webCurrencies.set(userId, currency);
    return;
  }
  await SecureStore.setItemAsync(storageKey(userId), currency);
}
