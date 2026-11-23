import type { TravelCurrency } from '@/features/preferencias/currency-storage';
import { convertCurrency, type ExchangeRates } from '@/features/preferencias/exchange-rates';

export function formatCurrency(value: number | null, currency: TravelCurrency = 'BRL') {
  if (value === null) return 'Não informado';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(value);
}

export function formatBrlInCurrency(
  value: number | null,
  currency: TravelCurrency,
  exchangeRates?: ExchangeRates,
) {
  if (value === null) return 'Não informado';
  if (currency !== 'BRL' && !exchangeRates) return 'Cotação indisponível';
  return formatCurrency(convertCurrency(value, 'BRL', currency, exchangeRates), currency);
}

export function formatAdmissionPrice(value: number | null, currency: TravelCurrency = 'BRL') {
  if (value === null) return 'Preço não informado';
  if (value === 0) return 'Entrada gratuita';
  return formatCurrency(value, currency);
}

export function formatCivilDate(value: string) {
  const [year, month, day] = value.split('-');
  return year && month && day ? `${day}/${month}/${year}` : value;
}
